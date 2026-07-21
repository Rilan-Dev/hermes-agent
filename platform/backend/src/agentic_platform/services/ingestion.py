from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from agentic_platform.domain.channels import (
    ChannelConnection,
    Contact,
    ExternalIdentity,
    NativeReference,
)
from agentic_platform.domain.errors import (
    CrossWorkspaceError,
    DomainValidationError,
)
from agentic_platform.domain.events import ChannelEvent, ChannelEventKind
from agentic_platform.domain.ids import EventId, WorkspaceId
from agentic_platform.domain.inbox import (
    Conversation,
    ConversationType,
    DeliveryState,
    Message,
    MessageDirection,
)
from agentic_platform.domain.time import require_utc
from agentic_platform.ports.event_bus import WorkspaceEvent
from agentic_platform.ports.repositories import UnitOfWork


class IngestionDisposition(StrEnum):
    CREATED = "created"
    APPLIED = "applied"
    DUPLICATE = "duplicate"
    DEFERRED = "deferred"


def _optional_text(value: str | None) -> str | None:
    return value.strip() or None if isinstance(value, str) else None


def _validate_connection_workspace(
    workspace_id: WorkspaceId,
    connection: ChannelConnection,
) -> None:
    if workspace_id != connection.workspace_id:
        raise CrossWorkspaceError(
            "normalized event must match the connection workspace"
        )


def _validate_platform(
    connection: ChannelConnection,
    *references: NativeReference,
) -> None:
    for reference in references:
        if reference.platform_id != connection.platform_id:
            raise DomainValidationError(
                "normalized native references must match the connection platform"
            )


@dataclass(frozen=True, slots=True)
class NormalizedMessageEvent:
    workspace_id: WorkspaceId
    connection: ChannelConnection
    platform_event_id: str
    conversation_native: NativeReference
    conversation_type: ConversationType
    sender_native: NativeReference
    sender_display_name: str | None
    message_native: NativeReference
    text: str | None
    occurred_at: datetime
    raw_payload_ref: str | None = None
    reply_to_native_id: str | None = None
    thread_native_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        workspace_id: WorkspaceId,
        connection: ChannelConnection,
        platform_event_id: str,
        conversation_native: NativeReference,
        conversation_type: ConversationType,
        sender_native: NativeReference,
        sender_display_name: str | None,
        message_native: NativeReference,
        text: str | None,
        occurred_at: datetime,
        raw_payload_ref: str | None = None,
        reply_to_native_id: str | None = None,
        thread_native_id: str | None = None,
    ) -> NormalizedMessageEvent:
        _validate_connection_workspace(workspace_id, connection)
        _validate_platform(
            connection,
            conversation_native,
            sender_native,
            message_native,
        )
        normalized_event_id = platform_event_id.strip()
        if not normalized_event_id:
            raise DomainValidationError("platform event ID must not be blank")
        if not isinstance(conversation_type, ConversationType):
            raise DomainValidationError("conversation type is invalid")
        return cls(
            workspace_id=workspace_id,
            connection=connection,
            platform_event_id=normalized_event_id,
            conversation_native=conversation_native,
            conversation_type=conversation_type,
            sender_native=sender_native,
            sender_display_name=_optional_text(sender_display_name),
            message_native=message_native,
            text=_optional_text(text),
            occurred_at=require_utc(occurred_at, field="message event occurred_at"),
            raw_payload_ref=_optional_text(raw_payload_ref),
            reply_to_native_id=_optional_text(reply_to_native_id),
            thread_native_id=_optional_text(thread_native_id),
        )


_TARGETED_KINDS = frozenset(
    {
        ChannelEventKind.MESSAGE_EDIT,
        ChannelEventKind.MESSAGE_DELETE,
        ChannelEventKind.REACTION,
        ChannelEventKind.RECEIPT,
    }
)


@dataclass(frozen=True, slots=True)
class NormalizedTargetedEvent:
    workspace_id: WorkspaceId
    connection: ChannelConnection
    platform_event_id: str
    kind: ChannelEventKind
    conversation_native: NativeReference
    target_message_native: NativeReference
    occurred_at: datetime
    raw_payload_ref: str | None = None

    @classmethod
    def create(
        cls,
        *,
        workspace_id: WorkspaceId,
        connection: ChannelConnection,
        platform_event_id: str,
        kind: ChannelEventKind,
        conversation_native: NativeReference,
        target_message_native: NativeReference,
        occurred_at: datetime,
        raw_payload_ref: str | None = None,
    ) -> NormalizedTargetedEvent:
        _validate_connection_workspace(workspace_id, connection)
        _validate_platform(connection, conversation_native, target_message_native)
        normalized_event_id = platform_event_id.strip()
        if not normalized_event_id:
            raise DomainValidationError("platform event ID must not be blank")
        if kind not in _TARGETED_KINDS:
            raise DomainValidationError("targeted event kind is invalid")
        return cls(
            workspace_id=workspace_id,
            connection=connection,
            platform_event_id=normalized_event_id,
            kind=kind,
            conversation_native=conversation_native,
            target_message_native=target_message_native,
            occurred_at=require_utc(occurred_at, field="targeted event occurred_at"),
            raw_payload_ref=_optional_text(raw_payload_ref),
        )


@dataclass(frozen=True, slots=True)
class IngestionResult:
    disposition: IngestionDisposition
    channel_event: ChannelEvent | None = None
    contact: Contact | None = None
    external_identity: ExternalIdentity | None = None
    conversation: Conversation | None = None
    message: Message | None = None
    deferred_reason: str | None = None


class IngestionService:
    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    async def ingest_message(self, event: NormalizedMessageEvent) -> IngestionResult:
        async with self._unit_of_work_factory() as uow:
            duplicate = await uow.channel_events.get_by_idempotency_key(
                event.workspace_id,
                event.connection.id,
                event.platform_event_id,
            )
            if duplicate is not None:
                return await self._duplicate_message_result(uow, event, duplicate)

            identity = await uow.external_identities.get_by_native_id(
                event.workspace_id,
                event.connection.id,
                event.sender_native.native_id,
            )
            if identity is None:
                contact = Contact.create(
                    workspace_id=event.workspace_id,
                    display_name=event.sender_display_name
                    or event.sender_native.native_id,
                    created_at=event.occurred_at,
                )
                identity = ExternalIdentity.create(
                    workspace_id=event.workspace_id,
                    connection=event.connection,
                    contact_id=contact.id,
                    native=event.sender_native,
                    display_name=event.sender_display_name,
                    created_at=event.occurred_at,
                )
                await uow.contacts.save(event.workspace_id, contact)
                await uow.external_identities.save(event.workspace_id, identity)
            else:
                contact = await uow.contacts.get(
                    event.workspace_id, identity.contact_id
                )
                if contact is None:
                    raise DomainValidationError(
                        "external identity references a missing contact"
                    )

            conversation = await uow.conversations.get_by_native_id(
                event.workspace_id,
                event.connection.id,
                event.conversation_native.native_id,
            )
            if conversation is None:
                conversation = Conversation.create(
                    workspace_id=event.workspace_id,
                    connection=event.connection,
                    native=event.conversation_native,
                    conversation_type=event.conversation_type,
                    created_at=event.occurred_at,
                )

            existing_message = await uow.messages.get_by_native_id(
                event.workspace_id,
                conversation.id,
                event.message_native.native_id,
            )
            if existing_message is not None:
                return IngestionResult(
                    disposition=IngestionDisposition.DUPLICATE,
                    contact=contact,
                    external_identity=identity,
                    conversation=conversation,
                    message=existing_message,
                )

            message = Message.create(
                workspace_id=event.workspace_id,
                conversation=conversation,
                native=event.message_native,
                direction=MessageDirection.INBOUND,
                text=event.text,
                sent_at=event.occurred_at,
                delivery_state=DeliveryState.DELIVERED,
                reply_to_native_id=event.reply_to_native_id,
                thread_native_id=event.thread_native_id,
            )
            conversation = conversation.record_message(message)
            channel_event = ChannelEvent.create(
                workspace_id=event.workspace_id,
                connection=event.connection,
                platform_event_id=event.platform_event_id,
                kind=ChannelEventKind.MESSAGE,
                occurred_at=event.occurred_at,
                native_target=event.message_native,
                raw_payload_ref=event.raw_payload_ref,
            )

            await uow.conversations.save(event.workspace_id, conversation)
            await uow.messages.save(event.workspace_id, message)
            await uow.channel_events.save(event.workspace_id, channel_event)
            cursor = await uow.outbox.next_cursor(event.workspace_id)
            await uow.outbox.append(
                event.workspace_id,
                WorkspaceEvent.create(
                    workspace_id=event.workspace_id,
                    cursor=cursor,
                    event_id=EventId.new(),
                    aggregate_type="conversation",
                    aggregate_id=str(conversation.id),
                    event_type="conversation.message.created",
                    payload={
                        "conversation_id": str(conversation.id),
                        "message_id": str(message.id),
                        "contact_id": str(contact.id),
                        "connection_id": str(event.connection.id),
                    },
                    occurred_at=event.occurred_at,
                ),
            )
            await uow.commit()
            return IngestionResult(
                disposition=IngestionDisposition.CREATED,
                channel_event=channel_event,
                contact=contact,
                external_identity=identity,
                conversation=conversation,
                message=message,
            )

    async def ingest_targeted(
        self,
        event: NormalizedTargetedEvent,
    ) -> IngestionResult:
        async with self._unit_of_work_factory() as uow:
            duplicate = await uow.channel_events.get_by_idempotency_key(
                event.workspace_id,
                event.connection.id,
                event.platform_event_id,
            )
            if duplicate is not None:
                return IngestionResult(
                    disposition=IngestionDisposition.DUPLICATE,
                    channel_event=duplicate,
                )

            conversation = await uow.conversations.get_by_native_id(
                event.workspace_id,
                event.connection.id,
                event.conversation_native.native_id,
            )
            if conversation is None:
                return IngestionResult(
                    disposition=IngestionDisposition.DEFERRED,
                    deferred_reason="conversation_not_found",
                )
            message = await uow.messages.get_by_native_id(
                event.workspace_id,
                conversation.id,
                event.target_message_native.native_id,
            )
            if message is None:
                return IngestionResult(
                    disposition=IngestionDisposition.DEFERRED,
                    conversation=conversation,
                    deferred_reason="message_not_found",
                )

            channel_event = ChannelEvent.create(
                workspace_id=event.workspace_id,
                connection=event.connection,
                platform_event_id=event.platform_event_id,
                kind=event.kind,
                occurred_at=event.occurred_at,
                native_target=event.target_message_native,
                raw_payload_ref=event.raw_payload_ref,
            )
            await uow.channel_events.save(event.workspace_id, channel_event)
            cursor = await uow.outbox.next_cursor(event.workspace_id)
            await uow.outbox.append(
                event.workspace_id,
                WorkspaceEvent.create(
                    workspace_id=event.workspace_id,
                    cursor=cursor,
                    event_id=EventId.new(),
                    aggregate_type="message",
                    aggregate_id=str(message.id),
                    event_type=f"channel.{event.kind.value}",
                    payload={
                        "conversation_id": str(conversation.id),
                        "message_id": str(message.id),
                    },
                    occurred_at=event.occurred_at,
                ),
            )
            await uow.commit()
            return IngestionResult(
                disposition=IngestionDisposition.APPLIED,
                channel_event=channel_event,
                conversation=conversation,
                message=message,
            )

    async def _duplicate_message_result(
        self,
        uow: UnitOfWork,
        event: NormalizedMessageEvent,
        duplicate: ChannelEvent,
    ) -> IngestionResult:
        identity = await uow.external_identities.get_by_native_id(
            event.workspace_id,
            event.connection.id,
            event.sender_native.native_id,
        )
        contact = (
            await uow.contacts.get(event.workspace_id, identity.contact_id)
            if identity is not None
            else None
        )
        conversation = await uow.conversations.get_by_native_id(
            event.workspace_id,
            event.connection.id,
            event.conversation_native.native_id,
        )
        message = (
            await uow.messages.get_by_native_id(
                event.workspace_id,
                conversation.id,
                event.message_native.native_id,
            )
            if conversation is not None
            else None
        )
        return IngestionResult(
            disposition=IngestionDisposition.DUPLICATE,
            channel_event=duplicate,
            contact=contact,
            external_identity=identity,
            conversation=conversation,
            message=message,
        )
