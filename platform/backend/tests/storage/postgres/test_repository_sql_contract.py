from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest

from agentic_platform.domain.channels import (
    ChannelConnection,
    Contact,
    ExternalIdentity,
    NativeReference,
)
from agentic_platform.domain.errors import CrossWorkspaceError
from agentic_platform.domain.events import ChannelEvent, ChannelEventKind
from agentic_platform.domain.ids import EventId, WorkspaceId
from agentic_platform.domain.inbox import (
    Conversation,
    ConversationType,
    DeliveryState,
    Message,
    MessageDirection,
)
from agentic_platform.domain.workspaces import Workspace
from agentic_platform.ports.event_bus import EventCursor, WorkspaceEvent
from agentic_platform.storage.postgres.repositories import (
    PostgresChannelEventRepository,
    PostgresContactRepository,
    PostgresConversationRepository,
    PostgresExternalIdentityRepository,
    PostgresMessageRepository,
    PostgresOutboxRepository,
    PostgresWorkspaceRepository,
)


NOW = datetime(2026, 7, 21, 14, 0, tzinfo=timezone.utc)


class FakeConnection:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, tuple[Any, ...]]] = []
        self.fetchrow_results: list[dict[str, Any] | None] = []
        self.fetch_results: list[list[dict[str, Any]]] = []
        self.fetchval_results: list[Any] = []

    async def execute(self, query: str, *args: Any) -> str:
        self.calls.append(("execute", query, args))
        return "OK"

    async def fetchrow(self, query: str, *args: Any):
        self.calls.append(("fetchrow", query, args))
        return self.fetchrow_results.pop(0) if self.fetchrow_results else None

    async def fetch(self, query: str, *args: Any):
        self.calls.append(("fetch", query, args))
        return self.fetch_results.pop(0) if self.fetch_results else []

    async def fetchval(self, query: str, *args: Any):
        self.calls.append(("fetchval", query, args))
        return self.fetchval_results.pop(0) if self.fetchval_results else None


def _workspace() -> Workspace:
    return Workspace.create(name="Acme", created_at=NOW)


def _connection(workspace_id: WorkspaceId) -> ChannelConnection:
    return ChannelConnection.create(
        workspace_id=workspace_id,
        platform_id="telegram",
        display_name="Support",
        created_at=NOW,
        secret_ref="vault://connections/support",
    )


def _conversation(
    workspace_id: WorkspaceId,
    connection: ChannelConnection,
) -> Conversation:
    return Conversation.create(
        workspace_id=workspace_id,
        connection=connection,
        native=NativeReference("telegram", "chat-1"),
        conversation_type=ConversationType.DIRECT,
        created_at=NOW,
    )


@pytest.mark.asyncio
async def test_workspace_contact_and_identity_writes_are_scoped_and_parameterized() -> None:
    db = FakeConnection()
    workspace = _workspace()
    connection = _connection(workspace.id)
    contact = Contact.create(
        workspace_id=workspace.id,
        display_name="Asha",
        created_at=NOW,
    )
    identity = ExternalIdentity.create(
        workspace_id=workspace.id,
        connection=connection,
        contact_id=contact.id,
        native=NativeReference("telegram", "user-1"),
        display_name="Asha",
        created_at=NOW,
    )

    await PostgresWorkspaceRepository(db).save(workspace.id, workspace)
    await PostgresContactRepository(db).save(workspace.id, contact)
    await PostgresExternalIdentityRepository(db).save(workspace.id, identity)

    assert len(db.calls) == 3
    for method, query, args in db.calls:
        assert method == "execute"
        assert "$1" in query
        assert "Asha" not in query
        assert args
    assert "ON CONFLICT (workspace_id, connection_id, native_id)" in db.calls[2][1]
    assert "secret" not in db.calls[2][1].lower()


@pytest.mark.asyncio
async def test_cross_workspace_writes_fail_before_sql() -> None:
    db = FakeConnection()
    workspace = _workspace()
    contact = Contact.create(
        workspace_id=workspace.id,
        display_name="Asha",
        created_at=NOW,
    )

    with pytest.raises(CrossWorkspaceError):
        await PostgresContactRepository(db).save(WorkspaceId.new(), contact)

    assert db.calls == []


@pytest.mark.asyncio
async def test_conversation_and_message_pagination_is_exclusive_and_deterministic() -> None:
    db = FakeConnection()
    workspace = _workspace()
    connection = _connection(workspace.id)
    conversation = _conversation(workspace.id, connection)
    message = Message.create(
        workspace_id=workspace.id,
        conversation=conversation,
        native=NativeReference("telegram", "message-1"),
        direction=MessageDirection.INBOUND,
        text="Hello",
        sent_at=NOW,
        delivery_state=DeliveryState.DELIVERED,
    )

    await PostgresConversationRepository(db).save(workspace.id, conversation)
    await PostgresMessageRepository(db).save(workspace.id, message)
    await PostgresConversationRepository(db).list_recent(
        workspace.id,
        limit=20,
        after=str(conversation.id),
    )
    await PostgresMessageRepository(db).list_for_conversation(
        workspace.id,
        conversation.id,
        limit=20,
        after=str(message.id),
    )

    conversation_query = db.calls[2][1]
    message_query = db.calls[3][1]
    assert "WHERE workspace_id = $1" in conversation_query
    assert "ORDER BY updated_at DESC, id DESC" in conversation_query
    assert "(updated_at, id) <" in conversation_query
    assert "WHERE workspace_id = $1" in message_query
    assert "conversation_id = $2" in message_query
    assert "ORDER BY sent_at ASC, id ASC" in message_query
    assert "(sent_at, id) >" in message_query


@pytest.mark.asyncio
async def test_channel_event_lookup_serializes_duplicate_ingestion() -> None:
    db = FakeConnection()
    workspace = _workspace()
    connection = _connection(workspace.id)
    event = ChannelEvent.create(
        workspace_id=workspace.id,
        connection=connection,
        platform_event_id="update-1",
        kind=ChannelEventKind.MESSAGE,
        occurred_at=NOW,
    )
    repository = PostgresChannelEventRepository(db)

    await repository.get_by_idempotency_key(
        workspace.id,
        connection.id,
        "update-1",
    )
    await repository.save(workspace.id, event)

    assert "pg_advisory_xact_lock" in db.calls[0][1]
    assert db.calls[0][2] == (
        f"{workspace.id}:{connection.id}:update-1",
    )
    assert "WHERE workspace_id = $1" in db.calls[1][1]
    assert (
        "ON CONFLICT (workspace_id, connection_id, platform_event_id) DO NOTHING"
        in db.calls[2][1]
    )


@pytest.mark.asyncio
async def test_outbox_allocates_cursor_under_workspace_lock_and_serializes_json() -> None:
    db = FakeConnection()
    workspace = _workspace()
    db.fetchval_results = [workspace.id.value, 8]
    repository = PostgresOutboxRepository(db)
    event = WorkspaceEvent.create(
        workspace_id=workspace.id,
        cursor=EventCursor(8),
        event_id=EventId.new(),
        aggregate_type="message",
        aggregate_id="message-8",
        event_type="message.created",
        payload={"message_id": "message-8"},
        occurred_at=NOW,
    )

    cursor = await repository.next_cursor(workspace.id)
    await repository.append(workspace.id, event)
    await repository.read(workspace.id, after=EventCursor(7), limit=10)

    assert cursor == EventCursor(8)
    assert "FOR UPDATE" in db.calls[0][1]
    assert "MAX(cursor)" in db.calls[1][1]
    assert json.loads(db.calls[2][2][6]) == {"message_id": "message-8"}
    assert "cursor > $2" in db.calls[3][1]
    assert "ORDER BY cursor ASC" in db.calls[3][1]
