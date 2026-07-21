from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from agentic_platform.domain.channels import ChannelConnection, NativeReference
from agentic_platform.domain.events import ChannelEventKind
from agentic_platform.domain.ids import WorkspaceId
from agentic_platform.domain.inbox import ConversationType
from agentic_platform.services.ingestion import (
    IngestionDisposition,
    IngestionService,
    NormalizedMessageEvent,
    NormalizedTargetedEvent,
)
from agentic_platform.storage.memory import MemoryDatabase, MemoryUnitOfWork


NOW = datetime(2026, 7, 21, 10, 0, tzinfo=timezone.utc)


def _connection() -> ChannelConnection:
    return ChannelConnection.create(
        workspace_id=WorkspaceId.new(),
        platform_id="telegram",
        display_name="Support Bot",
        created_at=NOW,
    )


def _message_event(connection: ChannelConnection) -> NormalizedMessageEvent:
    return NormalizedMessageEvent.create(
        workspace_id=connection.workspace_id,
        connection=connection,
        platform_event_id="update-100",
        conversation_native=NativeReference("telegram", "chat-1"),
        conversation_type=ConversationType.DIRECT,
        sender_native=NativeReference("telegram", "user-42"),
        sender_display_name="Asha",
        message_native=NativeReference("telegram", "message-500"),
        text="Hello from Telegram",
        occurred_at=NOW,
        raw_payload_ref="obj_raw_update_100",
    )


def test_message_ingestion_creates_canonical_records_and_outbox_atomically() -> None:
    async def scenario() -> None:
        database = MemoryDatabase()
        connection = _connection()
        service = IngestionService(lambda: MemoryUnitOfWork(database))

        result = await service.ingest_message(_message_event(connection))

        assert result.disposition is IngestionDisposition.CREATED
        assert result.contact is not None
        assert result.external_identity is not None
        assert result.conversation is not None
        assert result.message is not None
        assert result.channel_event is not None
        assert result.channel_event.raw_payload_ref == "obj_raw_update_100"
        assert result.conversation.unread_count == 1
        assert result.conversation.last_message_text == "Hello from Telegram"
        assert result.conversation.last_message_at == NOW

        async with MemoryUnitOfWork(database) as verification:
            assert (
                await verification.contacts.get(
                    connection.workspace_id,
                    result.contact.id,
                )
                == result.contact
            )
            assert (
                await verification.external_identities.get_by_native_id(
                    connection.workspace_id,
                    connection.id,
                    "user-42",
                )
                == result.external_identity
            )
            assert (
                await verification.conversations.get_by_native_id(
                    connection.workspace_id,
                    connection.id,
                    "chat-1",
                )
                == result.conversation
            )
            assert (
                await verification.messages.get_by_native_id(
                    connection.workspace_id,
                    result.conversation.id,
                    "message-500",
                )
                == result.message
            )
            assert (
                await verification.channel_events.get_by_idempotency_key(
                    connection.workspace_id,
                    connection.id,
                    "update-100",
                )
                == result.channel_event
            )
            outbox = await verification.outbox.read(
                connection.workspace_id,
                after=None,
                limit=10,
            )
            assert len(outbox) == 1
            assert outbox[0].event_type == "conversation.message.created"

    asyncio.run(scenario())


def test_concurrent_duplicate_ingestion_returns_original_without_duplicate_writes(
) -> None:
    async def scenario() -> None:
        database = MemoryDatabase()
        connection = _connection()
        service = IngestionService(lambda: MemoryUnitOfWork(database))
        event = _message_event(connection)

        results = await asyncio.gather(
            service.ingest_message(event),
            service.ingest_message(event),
        )

        assert {result.disposition for result in results} == {
            IngestionDisposition.CREATED,
            IngestionDisposition.DUPLICATE,
        }

        async with MemoryUnitOfWork(database) as verification:
            conversation = await verification.conversations.get_by_native_id(
                connection.workspace_id,
                connection.id,
                "chat-1",
            )
            assert conversation is not None
            messages = await verification.messages.list_for_conversation(
                connection.workspace_id,
                conversation.id,
                limit=10,
            )
            outbox = await verification.outbox.read(
                connection.workspace_id,
                after=None,
                limit=10,
            )
            assert len(messages) == 1
            assert len(outbox) == 1

    asyncio.run(scenario())


def test_targeted_event_without_native_target_is_deferred_without_writes() -> None:
    async def scenario() -> None:
        database = MemoryDatabase()
        connection = _connection()
        service = IngestionService(lambda: MemoryUnitOfWork(database))
        targeted = NormalizedTargetedEvent.create(
            workspace_id=connection.workspace_id,
            connection=connection,
            platform_event_id="update-101",
            kind=ChannelEventKind.MESSAGE_EDIT,
            conversation_native=NativeReference("telegram", "chat-missing"),
            target_message_native=NativeReference("telegram", "message-missing"),
            occurred_at=NOW,
        )

        result = await service.ingest_targeted(targeted)

        assert result.disposition is IngestionDisposition.DEFERRED
        assert result.deferred_reason == "conversation_not_found"

        async with MemoryUnitOfWork(database) as verification:
            assert (
                await verification.channel_events.get_by_idempotency_key(
                    connection.workspace_id,
                    connection.id,
                    "update-101",
                )
                is None
            )
            assert await verification.outbox.read(
                connection.workspace_id,
                after=None,
                limit=10,
            ) == ()

    asyncio.run(scenario())
