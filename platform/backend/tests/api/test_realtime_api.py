from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from agentic_platform.api.app import ApplicationDependencies, create_app
from agentic_platform.domain.ids import EventId, UserId, WorkspaceId
from agentic_platform.domain.workspaces import MembershipRole
from agentic_platform.ports.event_bus import EventCursor, WorkspaceEvent
from agentic_platform.services.realtime import RealtimeConfig
from agentic_platform.storage.memory import MemoryDatabase, MemoryUnitOfWork


NOW = datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)


class FakeHermesCatalog:
    async def list_channels(self):
        return ()

    async def list_providers(self):
        return ()

    async def list_tools(self):
        return ()

    async def ready(self) -> bool:
        return True


def _headers(workspace_id: WorkspaceId) -> dict[str, str]:
    return {
        "X-User-ID": str(UserId.new()),
        "X-Workspace-ID": str(workspace_id),
        "X-Workspace-Role": MembershipRole.OPERATOR.value,
    }


def _seed_events_sync(
    database: MemoryDatabase,
    workspace_id: WorkspaceId,
    cursors: tuple[int, ...],
    *,
    payload: dict[str, object] | None = None,
) -> None:
    async def seed() -> None:
        async with MemoryUnitOfWork(database) as unit_of_work:
            for cursor in cursors:
                await unit_of_work.outbox.append(
                    workspace_id,
                    WorkspaceEvent.create(
                        workspace_id=workspace_id,
                        cursor=EventCursor(cursor),
                        event_id=EventId.new(),
                        aggregate_type="message",
                        aggregate_id=f"message-{cursor}",
                        event_type="message.created",
                        payload=payload or {"cursor": cursor},
                        occurred_at=NOW,
                    ),
                )
            await unit_of_work.commit()

    asyncio.run(seed())


def _client(
    database: MemoryDatabase,
    *,
    realtime_config: RealtimeConfig | None = None,
) -> TestClient:
    return TestClient(
        create_app(
            ApplicationDependencies(
                unit_of_work_factory=lambda: MemoryUnitOfWork(database),
                hermes_catalog=FakeHermesCatalog(),
                realtime_config=realtime_config or RealtimeConfig(),
            )
        )
    )


def test_websocket_resumes_and_serializes_workspace_event() -> None:
    database = MemoryDatabase()
    workspace_id = WorkspaceId.new()
    _seed_events_sync(database, workspace_id, (1, 2))
    client = _client(database)

    with client.websocket_connect(
        f"/api/workspaces/{workspace_id}/realtime?after=1",
        headers=_headers(workspace_id),
    ) as websocket:
        payload = websocket.receive_json()

    assert payload == {
        "type": "workspace_event",
        "cursor": "2",
        "event_id": payload["event_id"],
        "aggregate_type": "message",
        "aggregate_id": "message-2",
        "event_type": "message.created",
        "payload": {"cursor": 2},
        "occurred_at": NOW.isoformat(),
    }


def test_websocket_closes_slow_consumer_with_resume_cursor() -> None:
    database = MemoryDatabase()
    workspace_id = WorkspaceId.new()
    _seed_events_sync(database, workspace_id, (1, 2))
    client = _client(
        database,
        realtime_config=RealtimeConfig(max_buffered_events=1),
    )

    with client.websocket_connect(
        f"/api/workspaces/{workspace_id}/realtime",
        headers=_headers(workspace_id),
    ) as websocket:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            websocket.receive_json()

    assert exc_info.value.code == 4413
    assert json.loads(exc_info.value.reason) == {
        "error": {
            "code": "slow_consumer",
            "message": "reconnect with the supplied cursor",
            "resume_after": "0",
        }
    }


def test_websocket_cross_workspace_access_closes_not_found_safe() -> None:
    database = MemoryDatabase()
    requested_workspace_id = WorkspaceId.new()
    principal_workspace_id = WorkspaceId.new()
    client = _client(database)

    with client.websocket_connect(
        f"/api/workspaces/{requested_workspace_id}/realtime",
        headers=_headers(principal_workspace_id),
    ) as websocket:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            websocket.receive_json()

    assert exc_info.value.code == 4403
    assert json.loads(exc_info.value.reason) == {
        "error": {
            "code": "authorization_failed",
            "message": "authorization failed",
        }
    }


def test_websocket_redacts_secret_material_from_event_payload() -> None:
    database = MemoryDatabase()
    workspace_id = WorkspaceId.new()
    _seed_events_sync(
        database,
        workspace_id,
        (1,),
        payload={
            "message": "safe",
            "api_key": "should-not-leak",
            "nested": {"token": "hidden", "safe": "visible"},
        },
    )
    client = _client(database)

    with client.websocket_connect(
        f"/api/workspaces/{workspace_id}/realtime",
        headers=_headers(workspace_id),
    ) as websocket:
        event = websocket.receive_json()

    assert event["payload"] == {
        "message": "safe",
        "nested": {"safe": "visible"},
    }


def test_websocket_invalid_cursor_closes_with_stable_request_error() -> None:
    database = MemoryDatabase()
    workspace_id = WorkspaceId.new()
    client = _client(database)

    with client.websocket_connect(
        f"/api/workspaces/{workspace_id}/realtime?after=not-a-cursor",
        headers=_headers(workspace_id),
    ) as websocket:
        with pytest.raises(WebSocketDisconnect) as exc_info:
            websocket.receive_json()

    assert exc_info.value.code == 4400
    assert json.loads(exc_info.value.reason)["error"]["code"] == "invalid_request"
