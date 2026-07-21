from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from .channels import ChannelConnection, NativeReference
from .errors import CrossWorkspaceError, DomainValidationError, InvalidTransitionError
from .ids import ConnectionId, ConversationId, MessageId, WorkspaceId
from .time import require_utc


class ConversationType(StrEnum):
    DIRECT = "direct"
    GROUP = "group"
    CHANNEL = "channel"
    THREAD = "thread"
    TOPIC = "topic"
    MAILBOX = "mailbox"
    NOTIFICATION = "notification"


class ConversationStatus(StrEnum):
    OPEN = "open"
    PENDING = "pending"
    SNOOZED = "snoozed"
    RESOLVED = "resolved"
    CLOSED = "closed"


class MessageDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"


class DeliveryState(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


_ALLOWED_TRANSITIONS: dict[ConversationStatus, frozenset[ConversationStatus]] = {
    ConversationStatus.OPEN: frozenset(
        {
            ConversationStatus.PENDING,
            ConversationStatus.SNOOZED,
            ConversationStatus.RESOLVED,
            ConversationStatus.CLOSED,
        }
    ),
    ConversationStatus.PENDING: frozenset(
        {
            ConversationStatus.OPEN,
            ConversationStatus.SNOOZED,
            ConversationStatus.RESOLVED,
            ConversationStatus.CLOSED,
        }
    ),
    ConversationStatus.SNOOZED: frozenset(
        {
            ConversationStatus.OPEN,
            ConversationStatus.PENDING,
            ConversationStatus.CLOSED,
        }
    ),
    ConversationStatus.RESOLVED: frozenset(
        {ConversationStatus.OPEN, ConversationStatus.CLOSED}
    ),
    ConversationStatus.CLOSED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class Conversation:
    id: ConversationId
    workspace_id: WorkspaceId
    connection_id: ConnectionId
    native: NativeReference
    conversation_type: ConversationType
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        workspace_id: WorkspaceId,
        connection: ChannelConnection,
        native: NativeReference,
        conversation_type: ConversationType,
        created_at: datetime,
    ) -> Conversation:
        if workspace_id != connection.workspace_id:
            raise CrossWorkspaceError(
                "conversation and channel connection must share a workspace"
            )
        if native.platform_id != connection.platform_id:
            raise DomainValidationError(
                "conversation platform must match the channel connection"
            )
        if not isinstance(conversation_type, ConversationType):
            raise DomainValidationError("conversation type is invalid")
        timestamp = require_utc(created_at, field="conversation created_at")
        return cls(
            id=ConversationId.new(),
            workspace_id=workspace_id,
            connection_id=connection.id,
            native=native,
            conversation_type=conversation_type,
            status=ConversationStatus.OPEN,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def transition(self, target: ConversationStatus, *, at: datetime) -> Conversation:
        if not isinstance(target, ConversationStatus):
            raise DomainValidationError("conversation status is invalid")
        timestamp = require_utc(at, field="conversation transition time")
        if timestamp < self.updated_at:
            raise DomainValidationError(
                "conversation transition time cannot precede the current state"
            )
        if target is self.status:
            return self
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise InvalidTransitionError(
                f"conversation cannot transition from {self.status.value} to {target.value}"
            )
        return replace(self, status=target, updated_at=timestamp)


@dataclass(frozen=True, slots=True)
class Message:
    id: MessageId
    workspace_id: WorkspaceId
    conversation_id: ConversationId
    native: NativeReference
    direction: MessageDirection
    text: str | None
    sent_at: datetime
    delivery_state: DeliveryState

    @classmethod
    def create(
        cls,
        *,
        workspace_id: WorkspaceId,
        conversation: Conversation,
        native: NativeReference,
        direction: MessageDirection,
        text: str | None,
        sent_at: datetime,
        delivery_state: DeliveryState,
    ) -> Message:
        if workspace_id != conversation.workspace_id:
            raise CrossWorkspaceError(
                "message and conversation must share a workspace"
            )
        if native.platform_id != conversation.native.platform_id:
            raise DomainValidationError(
                "message platform must match the conversation platform"
            )
        if not isinstance(direction, MessageDirection):
            raise DomainValidationError("message direction is invalid")
        if not isinstance(delivery_state, DeliveryState):
            raise DomainValidationError("delivery state is invalid")
        normalized_text = text.strip() if isinstance(text, str) else None
        return cls(
            id=MessageId.new(),
            workspace_id=workspace_id,
            conversation_id=conversation.id,
            native=native,
            direction=direction,
            text=normalized_text or None,
            sent_at=require_utc(sent_at, field="message sent_at"),
            delivery_state=delivery_state,
        )
