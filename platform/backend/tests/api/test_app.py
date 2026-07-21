from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from agentic_platform.api.app import ApplicationDependencies, create_app
from agentic_platform.domain.channels import ChannelConnection, NativeReference
from agentic_platform.domain.ids import UserId, WorkspaceId
from agentic_platform.domain.inbox import (
    Conversation,
    ConversationType,
    DeliveryState,
    Message,
    MessageDirection,
)
from agentic_platform.domain.workspaces import MembershipRole
from agentic_platform.storage.memory import MemoryDatabase, MemoryUnitOfWork


NOW = datetime(2026, 7, 21, 10, 0, tzinfo=timezone.utc)


class FakeHermesCatalog:
    def __init__(self, ready: bool = True) -> None:
        self._ready = ready

    async def list_channels(self):
        return ()

    async def list_providers(self):
        return ()

    async def list_tools(self):
        return ()

    async def ready(self) -> bool:
        return self._ready


def _headers(workspace_id: WorkspaceId, role: MembershipRole = MembershipRole.OPERATOR):
    return {
        "X-User-ID": str(UserId.new()),
        "X-Workspace-ID": str(workspace_id),
        "X-Workspace-Role": role.value,
    }


def _client(database: MemoryDatabase, *, hermes_ready: bool = True) -> TestClient:
    app = create_app(
        ApplicationDependencies(
            unit_of_work_factory=lambda: MemoryUnitOfWork(database),
            hermes_catalog=FakeHermesCatalog(hermes_ready),
        )
    )
    return TestClient(app)


def _seed_conversation(
    database: MemoryDatabase,
    workspace_id: WorkspaceId,
    *,
    suffix: str = "1",
) -> Conversation:
    async def seed() -> Conversation:
        connection = ChannelConnection.create(
            workspace_id=workspace_id,
            platform_id="telegram",
            display_name="Support Bot",
            created_at=NOW,
        )
        conversation = Conversation.create(
            workspace_id=workspace_id,
            connection=connection,
            native=NativeReference("telegram", f"chat-{suffix}"),
            conversation_type=ConversationType.DIRECT,
            created_at=NOW,
        )
        message = Message.create(
            workspace_id=workspace_id,
            conversation=conversation,
            native=NativeReference("telegram", f"message-{suffix}"),
            direction=MessageDirection.INBOUND,
            text="Hello",
            sent_at=NOW,
            delivery_state=DeliveryState.DELIVERED,
        )
        conversation = conversation.record_message(message)
        async with MemoryUnitOfWork(database) as uow:
            await uow.conversations.save(workspace_id, conversation)
            await uow.messages.save(workspace_id, message)
            await uow.commit()
        return conversation

    return asyncio.run(seed())


def test_health_distinguishes_storage_and_hermes_readiness() -> None:
    database = MemoryDatabase()

    response = _client(database, hermes_ready=False).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "process": "healthy",
        "storage": "ready",
        "hermes": "unready",
    }


def test_inbox_conversations_are_workspace_scoped_and_cursor_paginated() -> None:
    database = MemoryDatabase()
    workspace_id = WorkspaceId.new()
    other_workspace_id = WorkspaceId.new()
    conversation = _seed_conversation(database, workspace_id)
    _seed_conversation(database, other_workspace_id)
    client = _client(database)

    response = client.get(
        f"/api/workspaces/{workspace_id}/inbox/conversations?limit=1",
        headers=_headers(workspace_id),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == str(conversation.id)
    assert payload["items"][0]["native_id"] == "chat-1"
    assert "secret_ref" not in payload["items"][0]
    assert payload["next_cursor"] is None


def test_cross_workspace_inbox_access_is_not_found_safe() -> None:
    database = MemoryDatabase()
    requested_workspace_id = WorkspaceId.new()
    principal_workspace_id = WorkspaceId.new()

    response = _client(database).get(
        f"/api/workspaces/{requested_workspace_id}/inbox/conversations",
        headers=_headers(principal_workspace_id, MembershipRole.ADMIN),
    )

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "resource_not_found",
            "message": "resource was not found",
        }
    }


def test_viewer_cannot_use_inbox_write_permission() -> None:
    database = MemoryDatabase()
    workspace_id = WorkspaceId.new()
    client = _client(database)

    response = client.post(
        f"/api/workspaces/{workspace_id}/inbox/authorize-write",
        headers=_headers(workspace_id, MembershipRole.VIEWER),
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "permission_denied"


def test_inbox_cursor_resumes_after_last_returned_conversation() -> None:
    database = MemoryDatabase()
    workspace_id = WorkspaceId.new()
    first = _seed_conversation(database, workspace_id, suffix="1")
    second = _seed_conversation(database, workspace_id, suffix="2")
    client = _client(database)

    page_one = client.get(
        f"/api/workspaces/{workspace_id}/inbox/conversations?limit=1",
        headers=_headers(workspace_id),
    )
    assert page_one.status_code == 200
    cursor = page_one.json()["next_cursor"]
    assert cursor is not None

    page_two = client.get(
        f"/api/workspaces/{workspace_id}/inbox/conversations?limit=1&after={cursor}",
        headers=_headers(workspace_id),
    )
    assert page_two.status_code == 200
    returned_ids = {
        page_one.json()["items"][0]["id"],
        page_two.json()["items"][0]["id"],
    }
    assert returned_ids == {str(first.id), str(second.id)}
    assert page_two.json()["next_cursor"] is None
