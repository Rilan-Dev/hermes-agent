from datetime import datetime, timezone

import pytest

from agentic_platform.domain.channels import ChannelConnection, NativeReference
from agentic_platform.domain.errors import CrossWorkspaceError, InvalidTransitionError
from agentic_platform.domain.ids import WorkspaceId
from agentic_platform.domain.inbox import (
    Conversation,
    ConversationStatus,
    ConversationType,
    DeliveryState,
    Message,
    MessageDirection,
)


NOW = datetime(2026, 7, 21, 10, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 7, 21, 10, 5, tzinfo=timezone.utc)


def _connection() -> ChannelConnection:
    return ChannelConnection.create(
        workspace_id=WorkspaceId.new(),
        platform_id="slack",
        display_name="Customer Success",
        created_at=NOW,
    )


def test_conversation_creation_preserves_native_identity_and_workspace() -> None:
    connection = _connection()
    conversation = Conversation.create(
        workspace_id=connection.workspace_id,
        connection=connection,
        native=NativeReference("slack", "C0123:thread-99"),
        conversation_type=ConversationType.THREAD,
        created_at=NOW,
    )

    assert conversation.workspace_id == connection.workspace_id
    assert conversation.connection_id == connection.id
    assert conversation.native.native_id == "C0123:thread-99"
    assert conversation.status is ConversationStatus.OPEN


def test_conversation_creation_rejects_cross_workspace_connection() -> None:
    connection = _connection()

    with pytest.raises(CrossWorkspaceError):
        Conversation.create(
            workspace_id=WorkspaceId.new(),
            connection=connection,
            native=NativeReference("slack", "C0123"),
            conversation_type=ConversationType.CHANNEL,
            created_at=NOW,
        )


def test_conversation_transition_is_immutable_and_closed_is_terminal() -> None:
    connection = _connection()
    conversation = Conversation.create(
        workspace_id=connection.workspace_id,
        connection=connection,
        native=NativeReference("slack", "C0123"),
        conversation_type=ConversationType.CHANNEL,
        created_at=NOW,
    )

    resolved = conversation.transition(ConversationStatus.RESOLVED, at=LATER)
    closed = resolved.transition(ConversationStatus.CLOSED, at=LATER)

    assert conversation.status is ConversationStatus.OPEN
    assert resolved.status is ConversationStatus.RESOLVED
    assert closed.status is ConversationStatus.CLOSED

    with pytest.raises(InvalidTransitionError, match="closed"):
        closed.transition(ConversationStatus.OPEN, at=LATER)


def test_message_creation_rejects_cross_workspace_relationship() -> None:
    connection = _connection()
    conversation = Conversation.create(
        workspace_id=connection.workspace_id,
        connection=connection,
        native=NativeReference("slack", "C0123"),
        conversation_type=ConversationType.CHANNEL,
        created_at=NOW,
    )

    with pytest.raises(CrossWorkspaceError):
        Message.create(
            workspace_id=WorkspaceId.new(),
            conversation=conversation,
            native=NativeReference("slack", "message-1"),
            direction=MessageDirection.INBOUND,
            text="Hello",
            sent_at=NOW,
            delivery_state=DeliveryState.DELIVERED,
        )
