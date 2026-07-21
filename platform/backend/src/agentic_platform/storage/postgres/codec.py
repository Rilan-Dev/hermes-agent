from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

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
from agentic_platform.domain.time import require_utc
from agentic_platform.domain.workspaces import Workspace
from agentic_platform.ports.event_bus import EventCursor, WorkspaceEvent


Row = Mapping[str, Any]


def workspace_from_row(row: Row) -> Workspace:
    return Workspace(
        id=WorkspaceId.parse(row["id"]),
        name=str(row["name"]),
        created_at=require_utc(row["created_at"], field="workspace created_at"),
    )


def contact_from_row(row: Row) -> Contact:
    return Contact(
        id=ContactId.parse(row["id"]),
        workspace_id=WorkspaceId.parse(row["workspace_id"]),
        display_name=str(row["display_name"]),
        created_at=require_utc(row["created_at"], field="contact created_at"),
    )


def external_identity_from_row(row: Row) -> ExternalIdentity:
    return ExternalIdentity(
        id=ExternalIdentityId.parse(row["id"]),
        workspace_id=WorkspaceId.parse(row["workspace_id"]),
        connection_id=ConnectionId.parse(row["connection_id"]),
        contact_id=ContactId.parse(row["contact_id"]),
        native=NativeReference(str(row["platform_id"]), str(row["native_id"])),
        created_at=require_utc(
            row["created_at"], field="external identity created_at"
        ),
        display_name=(
            str(row["display_name"]) if row.get("display_name") is not None else None
        ),
    )


def conversation_from_row(row: Row) -> Conversation:
    return Conversation(
        id=ConversationId.parse(row["id"]),
        workspace_id=WorkspaceId.parse(row["workspace_id"]),
        connection_id=ConnectionId.parse(row["connection_id"]),
        native=NativeReference(str(row["platform_id"]), str(row["native_id"])),
        conversation_type=ConversationType(str(row["conversation_type"])),
        status=ConversationStatus(str(row["status"])),
        created_at=require_utc(row["created_at"], field="conversation created_at"),
        updated_at=require_utc(row["updated_at"], field="conversation updated_at"),
        unread_count=int(row["unread_count"]),
        last_message_text=(
            str(row["last_message_text"])
            if row.get("last_message_text") is not None
            else None
        ),
        last_message_at=(
            require_utc(row["last_message_at"], field="conversation last_message_at")
            if row.get("last_message_at") is not None
            else None
        ),
    )


def message_from_row(row: Row) -> Message:
    return Message(
        id=MessageId.parse(row["id"]),
        workspace_id=WorkspaceId.parse(row["workspace_id"]),
        conversation_id=ConversationId.parse(row["conversation_id"]),
        native=NativeReference(str(row["platform_id"]), str(row["native_id"])),
        direction=MessageDirection(str(row["direction"])),
        text=str(row["text"]) if row.get("text") is not None else None,
        sent_at=require_utc(row["sent_at"], field="message sent_at"),
        delivery_state=DeliveryState(str(row["delivery_state"])),
        reply_to_native_id=(
            str(row["reply_to_native_id"])
            if row.get("reply_to_native_id") is not None
            else None
        ),
        thread_native_id=(
            str(row["thread_native_id"])
            if row.get("thread_native_id") is not None
            else None
        ),
    )


def channel_event_from_row(row: Row) -> ChannelEvent:
    target_platform = row.get("native_target_platform_id")
    target_id = row.get("native_target_id")
    native_target = (
        NativeReference(str(target_platform), str(target_id))
        if target_platform is not None and target_id is not None
        else None
    )
    return ChannelEvent(
        id=EventId.parse(row["id"]),
        workspace_id=WorkspaceId.parse(row["workspace_id"]),
        connection_id=ConnectionId.parse(row["connection_id"]),
        platform_event_id=str(row["platform_event_id"]),
        kind=ChannelEventKind(str(row["kind"])),
        occurred_at=require_utc(row["occurred_at"], field="channel event occurred_at"),
        native_target=native_target,
        raw_payload_ref=(
            str(row["raw_payload_ref"])
            if row.get("raw_payload_ref") is not None
            else None
        ),
    )


def workspace_event_from_row(row: Row) -> WorkspaceEvent:
    payload = row["payload"]
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise TypeError("workspace event payload must be valid JSON") from exc
    if not isinstance(payload, Mapping):
        raise TypeError("workspace event payload must be a mapping")
    return WorkspaceEvent.create(
        workspace_id=WorkspaceId.parse(row["workspace_id"]),
        cursor=EventCursor.parse(row["cursor"]),
        event_id=EventId.parse(row["event_id"]),
        aggregate_type=str(row["aggregate_type"]),
        aggregate_id=str(row["aggregate_id"]),
        event_type=str(row["event_type"]),
        payload=payload,
        occurred_at=require_utc(row["occurred_at"], field="workspace event occurred_at"),
    )
