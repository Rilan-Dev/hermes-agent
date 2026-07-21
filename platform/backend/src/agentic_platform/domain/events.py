from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .channels import ChannelConnection, NativeReference
from .errors import CrossWorkspaceError, DomainValidationError
from .ids import ConnectionId, EventId, WorkspaceId
from .time import require_utc


class ChannelEventKind(StrEnum):
    MESSAGE = "message"
    MESSAGE_EDIT = "message_edit"
    MESSAGE_DELETE = "message_delete"
    REACTION = "reaction"
    RECEIPT = "receipt"
    TYPING = "typing"
    MEMBERSHIP = "membership"
    CONNECTION_STATE = "connection_state"


@dataclass(frozen=True, slots=True)
class ChannelEvent:
    id: EventId
    workspace_id: WorkspaceId
    connection_id: ConnectionId
    platform_event_id: str
    kind: ChannelEventKind
    occurred_at: datetime
    native_target: NativeReference | None = None

    @classmethod
    def create(
        cls,
        *,
        workspace_id: WorkspaceId,
        connection: ChannelConnection,
        platform_event_id: str,
        kind: ChannelEventKind,
        occurred_at: datetime,
        native_target: NativeReference | None = None,
    ) -> ChannelEvent:
        if workspace_id != connection.workspace_id:
            raise CrossWorkspaceError(
                "channel event and connection must share a workspace"
            )
        normalized_event_id = (
            platform_event_id.strip() if isinstance(platform_event_id, str) else ""
        )
        if not normalized_event_id:
            raise DomainValidationError("platform event ID must not be blank")
        if not isinstance(kind, ChannelEventKind):
            raise DomainValidationError("channel event kind is invalid")
        if native_target is not None and native_target.platform_id != connection.platform_id:
            raise DomainValidationError(
                "event target platform must match the channel connection"
            )
        return cls(
            id=EventId.new(),
            workspace_id=workspace_id,
            connection_id=connection.id,
            platform_event_id=normalized_event_id,
            kind=kind,
            occurred_at=require_utc(occurred_at, field="channel event occurred_at"),
            native_target=native_target,
        )

    @property
    def idempotency_key(self) -> tuple[WorkspaceId, ConnectionId, str]:
        return (self.workspace_id, self.connection_id, self.platform_event_id)
