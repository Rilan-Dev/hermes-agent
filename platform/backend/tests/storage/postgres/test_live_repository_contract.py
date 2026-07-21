from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import pytest

from agentic_platform.domain.channels import (
    ChannelConnection,
    Contact,
    ExternalIdentity,
    NativeReference,
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
from agentic_platform.domain.workspaces import Workspace
from agentic_platform.ports.event_bus import WorkspaceEvent
from agentic_platform.storage.postgres.migrations import (
    MigrationRunner,
    discover_migrations,
)
from agentic_platform.storage.postgres.pool import create_postgres_pool
from agentic_platform.storage.postgres.protocols import PostgresPool
from agentic_platform.storage.postgres.unit_of_work import PostgresUnitOfWork

NOW = datetime(2026, 7, 21, 15, 0, tzinfo=timezone.utc)
MIGRATIONS = Path("platform/backend/migrations")


async def _with_connection(
    pool: PostgresPool,
    operation: Callable[[Any], Awaitable[None]],
) -> None:
    connection = await pool.acquire()
    try:
        await operation(connection)
    finally:
        await pool.release(connection)


async def _reset_database(connection: Any) -> None:
    runner = MigrationRunner(connection, discover_migrations(MIGRATIONS))
    await runner.down(target=0)
    await runner.up()


async def _close_pool(pool: PostgresPool) -> None:
    await cast(Any, pool).close()


def _connection(workspace: Workspace) -> ChannelConnection:
    return ChannelConnection.create(
        workspace_id=workspace.id,
        platform_id="telegram",
        display_name="Support",
        created_at=NOW,
        secret_ref="vault://connections/support",
    )


async def _seed_connection(
    pool: PostgresPool,
    connection: ChannelConnection,
) -> None:
    async def insert(raw: Any) -> None:
        await raw.execute(
            """
INSERT INTO channel_connections(
    workspace_id, id, platform_id, display_name, secret_ref, created_at
)
VALUES ($1, $2, $3, $4, $5, $6)
""".strip(),
            connection.workspace_id.value,
            connection.id.value,
            connection.platform_id,
            connection.display_name,
            connection.secret_ref,
            connection.created_at,
        )

    await _with_connection(pool, insert)


@pytest.mark.asyncio
async def test_live_migrations_upgrade_and_downgrade_cleanly(
    postgres_test_dsn: str,
    asyncpg_module: Any,
) -> None:
    connection = await asyncpg_module.connect(postgres_test_dsn)
    migrations = discover_migrations(MIGRATIONS)
    runner = MigrationRunner(connection, migrations)
    try:
        await runner.down(target=0)
        assert await runner.up() == (1, 2)
        tables = {
            row["tablename"]
            for row in await connection.fetch(
                """
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
""".strip()
            )
        }
        assert {
            "workspaces",
            "channel_connections",
            "conversations",
            "messages",
            "channel_events",
            "workspace_outbox",
            "audit_records",
        } <= tables

        assert await runner.down(target=0) == (2, 1)
        remaining = {
            row["tablename"]
            for row in await connection.fetch(
                """
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
""".strip()
            )
        }
        assert "workspaces" not in remaining
        assert "workspace_outbox" not in remaining
    finally:
        await connection.close()


@pytest.mark.asyncio
async def test_live_repositories_preserve_workspace_scope_and_rollback(
    postgres_test_dsn: str,
    asyncpg_module: Any,
) -> None:
    del asyncpg_module
    pool = await create_postgres_pool(postgres_test_dsn, min_size=1, max_size=4)
    workspace = Workspace.create(name="Acme", created_at=NOW)
    connection = _connection(workspace)
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
    conversation = Conversation.create(
        workspace_id=workspace.id,
        connection=connection,
        native=NativeReference("telegram", "chat-1"),
        conversation_type=ConversationType.DIRECT,
        created_at=NOW,
    )
    message = Message.create(
        workspace_id=workspace.id,
        conversation=conversation,
        native=NativeReference("telegram", "message-1"),
        direction=MessageDirection.INBOUND,
        text="Hello",
        sent_at=NOW,
        delivery_state=DeliveryState.DELIVERED,
    )
    conversation = conversation.record_message(message)
    channel_event = ChannelEvent.create(
        workspace_id=workspace.id,
        connection=connection,
        platform_event_id="update-1",
        kind=ChannelEventKind.MESSAGE,
        occurred_at=NOW,
        native_target=message.native,
    )

    try:
        await _with_connection(pool, _reset_database)
        async with PostgresUnitOfWork(pool) as unit_of_work:
            await unit_of_work.workspaces.save(workspace.id, workspace)
            await unit_of_work.commit()
        await _seed_connection(pool, connection)

        async with PostgresUnitOfWork(pool) as unit_of_work:
            await unit_of_work.contacts.save(workspace.id, contact)
            await unit_of_work.external_identities.save(workspace.id, identity)
            await unit_of_work.conversations.save(workspace.id, conversation)
            await unit_of_work.messages.save(workspace.id, message)
            await unit_of_work.channel_events.save(workspace.id, channel_event)
            cursor = await unit_of_work.outbox.next_cursor(workspace.id)
            await unit_of_work.outbox.append(
                workspace.id,
                WorkspaceEvent.create(
                    workspace_id=workspace.id,
                    cursor=cursor,
                    event_id=EventId.new(),
                    aggregate_type="conversation",
                    aggregate_id=str(conversation.id),
                    event_type="conversation.message.created",
                    payload={"message_id": str(message.id)},
                    occurred_at=NOW,
                ),
            )
            await unit_of_work.commit()

        async with PostgresUnitOfWork(pool) as verification:
            assert await verification.workspaces.get(workspace.id) == workspace
            assert await verification.contacts.get(workspace.id, contact.id) == contact
            assert (
                await verification.external_identities.get_by_native_id(
                    workspace.id,
                    connection.id,
                    "user-1",
                )
                == identity
            )
            assert (
                await verification.conversations.get_by_native_id(
                    workspace.id,
                    connection.id,
                    "chat-1",
                )
                == conversation
            )
            assert (
                await verification.messages.get_by_native_id(
                    workspace.id,
                    conversation.id,
                    "message-1",
                )
                == message
            )
            assert len(
                await verification.outbox.read(workspace.id, after=None, limit=10)
            ) == 1
            other_workspace = WorkspaceId.new()
            assert await verification.contacts.get(other_workspace, contact.id) is None
            assert (
                await verification.conversations.list_recent(
                    other_workspace,
                    limit=10,
                )
                == ()
            )

        rolled_back = Contact.create(
            workspace_id=workspace.id,
            display_name="Rollback",
            created_at=NOW,
        )
        with pytest.raises(RuntimeError, match="abort"):
            async with PostgresUnitOfWork(pool) as unit_of_work:
                await unit_of_work.contacts.save(workspace.id, rolled_back)
                await unit_of_work.commit()
                raise RuntimeError("abort")

        async with PostgresUnitOfWork(pool) as verification:
            assert (
                await verification.contacts.get(workspace.id, rolled_back.id) is None
            )
    finally:
        async def downgrade(raw: Any) -> None:
            await MigrationRunner(
                raw,
                discover_migrations(MIGRATIONS),
            ).down(target=0)

        await _with_connection(pool, downgrade)
        await _close_pool(pool)
