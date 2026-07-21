from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from agentic_platform.api.dependencies import principal_from_values
from agentic_platform.auth.service import AuthorizationDenied, ResourceNotFound
from agentic_platform.domain.errors import DomainValidationError
from agentic_platform.domain.ids import WorkspaceId
from agentic_platform.ports.event_bus import EventCursor, WorkspaceEvent
from agentic_platform.services.realtime import RealtimeService, SlowConsumerError


router = APIRouter(prefix="/api/workspaces/{workspace_id}")


_SENSITIVE_PAYLOAD_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "cookie",
        "credential",
        "credentials",
        "password",
        "private_key",
        "refresh_token",
        "secret",
        "set_cookie",
        "token",
    }
)


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_")
    return normalized in _SENSITIVE_PAYLOAD_KEYS or normalized.endswith(
        ("_api_key", "_password", "_private_key", "_secret", "_token")
    )


def _sanitize_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _sanitize_payload(item)
            for key, item in value.items()
            if not _is_sensitive_key(key)
        }
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [_sanitize_payload(item) for item in value]
    return value


def _event_payload(event: WorkspaceEvent) -> dict[str, Any]:
    return {
        "type": "workspace_event",
        "cursor": str(event.cursor),
        "event_id": str(event.event_id),
        "aggregate_type": event.aggregate_type,
        "aggregate_id": event.aggregate_id,
        "event_type": event.event_type,
        "payload": _sanitize_payload(event.payload),
        "occurred_at": event.occurred_at.isoformat(),
    }


def _close_reason(code: str, message: str, **details: str) -> str:
    return json.dumps(
        {"error": {"code": code, "message": message, **details}},
        separators=(",", ":"),
        sort_keys=True,
    )


@router.websocket("/realtime")
async def workspace_realtime(websocket: WebSocket, workspace_id: str) -> None:
    await websocket.accept()
    try:
        parsed_workspace_id = WorkspaceId.parse(workspace_id)
        after_raw = websocket.query_params.get("after")
        after = EventCursor.parse(after_raw) if after_raw is not None else None
        principal = principal_from_values(
            user_id=websocket.headers.get("X-User-ID", ""),
            workspace_id=websocket.headers.get("X-Workspace-ID", ""),
            role=websocket.headers.get("X-Workspace-Role", ""),
        )
        dependencies = websocket.app.state.dependencies
        service = RealtimeService(
            unit_of_work_factory=dependencies.unit_of_work_factory,
            authorization=dependencies.authorization,
            principal_resolver=dependencies.principal_resolver,
            config=dependencies.realtime_config,
        )
        async for event in service.subscribe(
            principal=principal,
            workspace_id=parsed_workspace_id,
            after=after,
        ):
            await websocket.send_json(_event_payload(event))
    except WebSocketDisconnect:
        return
    except SlowConsumerError as exc:
        await websocket.close(
            code=4413,
            reason=_close_reason(
                "slow_consumer",
                str(exc),
                resume_after=str(exc.last_delivered_cursor),
            ),
        )
    except (AuthorizationDenied, ResourceNotFound):
        await websocket.close(
            code=4403,
            reason=_close_reason("authorization_failed", "authorization failed"),
        )
    except DomainValidationError as exc:
        await websocket.close(
            code=4400,
            reason=_close_reason("invalid_request", str(exc)),
        )
