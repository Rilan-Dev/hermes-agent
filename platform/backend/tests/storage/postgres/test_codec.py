from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from agentic_platform.domain.channels import Contact, ExternalIdentity, NativeReference
from agentic_platform.domain.events import ChannelEvent, ChannelEventKind
from agentic_platform.domain.ids import (
    ConnectionId,
    ContactId,
    ConversationId,
    EventId,
    ExternalIdentityId,
    MessageId,
    WorkspaceId,
)
from agentic_platform.domain.inbox import (
    Conversation,
    ConversationStatus,
    ConversationType,
    DeliveryState,
    Message,
    MessageDirection,
)
from agentic_platform.domain.workspaces import Workspace
from agentic_platform.ports.event_bus import EventCursor, WorkspaceEvent
from agentic_platform.storage.postgres.codec import (
    channel_event_from_row,
    contact_from_row,
    conversation_from_row,
    external_identity_from_row,
    message_from_row,
    workspace_event_from_row,
    workspace_from_row,
)


NOW = datetime(2026, 7, 21, 13, 0, tzinfo=timezone.utc)


def test_workspace_contact_and_identity_rows_preserve_strong_ids() -> None:
    workspace_id = uuid4()
    contact_id = uuid4()
    identity_id = uuid4()
    connection_id = uuid4()

    workspace = workspace_from_row(
        {"id": workspace_id, "name": "Acme", "created_at": NOW}
    )
    contact = contact_from_row(
        {
            "workspace_id": workspace_id,
            "id": contact_id,
            "display_name": "Asha",
            "created_at": NOW,
        }
    )
    identity = external_identity_from_row(
        {
            "workspace_id": workspace_id,
            "id": identity_id,
            "connection_id": connection_id,
            "contact_id": contact_id,
            "platform_id": "telegram",
            "native_id": "user-7",
            "display_name": "Asha",
            "created_at": NOW,
        }
    )

    assert workspace == Workspace(WorkspaceId(workspace_id), "Acme", NOW)
    assert contact == Contact(
        ContactId(contact_id),
        WorkspaceId(workspace_id),
        "Asha",
        NOW,
    )
    assert identity == ExternalIdentity(
        id=ExternalIdentityId(identity_id),
        workspace_id=WorkspaceId(workspace_id),
        connection_id=ConnectionId(connection_id),
        contact_id=ContactId(contact_id),
        native=NativeReference("telegram", "user-7"),
        created_at=NOW,
        display_name="Asha",
    )


def test_conversation_and_message_rows_restore_enums_and_native_references() -> None:
    workspace_id = uuid4()
    connection_id = uuid4()
    conversation_id = uuid4()
    message_id = uuid4()

    conversation = conversation_from_row(
        {
            "workspace_id": workspace_id,
            "id": conversation_id,
            "connection_id": connection_id,
            "platform_id": "slack",
            "native_id": "C123",
            "conversation_type": "channel",
            "status": "pending",
            "created_at": NOW,
            "updated_at": NOW,
            "unread_count": 3,
            "last_message_text": "Hello",
            "last_message_at": NOW,
        }
    )
    message = message_from_row(
        {
            "workspace_id": workspace_id,
            "id": message_id,
            "conversation_id": conversation_id,
            "platform_id": "slack",
            "native_id": "171.1",
            "direction": "inbound",
            "text": "Hello",
            "sent_at": NOW,
            "delivery_state": "read",
            "reply_to_native_id": "170.9",
            "thread_native_id": "170.0",
        }
    )

    assert conversation == Conversation(
        id=ConversationId(conversation_id),
        workspace_id=WorkspaceId(workspace_id),
        connection_id=ConnectionId(connection_id),
        native=NativeReference("slack", "C123"),
        conversation_type=ConversationType.CHANNEL,
        status=ConversationStatus.PENDING,
        created_at=NOW,
        updated_at=NOW,
        unread_count=3,
        last_message_text="Hello",
        last_message_at=NOW,
    )
    assert message == Message(
        id=MessageId(message_id),
        workspace_id=WorkspaceId(workspace_id),
        conversation_id=ConversationId(conversation_id),
        native=NativeReference("slack", "171.1"),
        direction=MessageDirection.INBOUND,
        text="Hello",
        sent_at=NOW,
        delivery_state=DeliveryState.READ,
        reply_to_native_id="170.9",
        thread_native_id="170.0",
    )


def test_channel_and_workspace_event_rows_restore_optional_targets_and_payloads() -> None:
    workspace_id = uuid4()
    connection_id = uuid4()
    channel_event_id = uuid4()
    outbox_event_id = uuid4()

    channel_event = channel_event_from_row(
        {
            "workspace_id": workspace_id,
            "id": channel_event_id,
            "connection_id": connection_id,
            "platform_event_id": "update-9",
            "kind": "message_edit",
            "occurred_at": NOW,
            "native_target_platform_id": "telegram",
            "native_target_id": "msg-5",
            "raw_payload_ref": "objects/raw/9",
        }
    )
    workspace_event = workspace_event_from_row(
        {
            "workspace_id": workspace_id,
            "cursor": 12,
            "event_id": outbox_event_id,
            "aggregate_type": "message",
            "aggregate_id": "message-5",
            "event_type": "message.updated",
            "payload": {"message_id": "message-5"},
            "occurred_at": NOW,
        }
    )

    assert channel_event == ChannelEvent(
        id=EventId(channel_event_id),
        workspace_id=WorkspaceId(workspace_id),
        connection_id=ConnectionId(connection_id),
        platform_event_id="update-9",
        kind=ChannelEventKind.MESSAGE_EDIT,
        occurred_at=NOW,
        native_target=NativeReference("telegram", "msg-5"),
        raw_payload_ref="objects/raw/9",
    )
    assert workspace_event == WorkspaceEvent.create(
        workspace_id=WorkspaceId(workspace_id),
        cursor=EventCursor(12),
        event_id=EventId(outbox_event_id),
        aggregate_type="message",
        aggregate_id="message-5",
        event_type="message.updated",
        payload={"message_id": "message-5"},
        occurred_at=NOW,
    )


def test_workspace_event_codec_accepts_json_text_from_driver() -> None:
    workspace_id = uuid4()
    event = workspace_event_from_row(
        {
            "workspace_id": workspace_id,
            "cursor": 1,
            "event_id": uuid4(),
            "aggregate_type": "message",
            "aggregate_id": "message-1",
            "event_type": "message.created",
            "payload": '{"message_id":"message-1"}',
            "occurred_at": NOW,
        }
    )

    assert dict(event.payload) == {"message_id": "message-1"}
