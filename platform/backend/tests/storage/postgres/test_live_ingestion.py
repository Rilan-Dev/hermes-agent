from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import pytest

from agentic_platform.domain.channels import ChannelConnection, NativeReference
from agentic_platform.domain.inbox import ConversationType
from agentic_platform.domain.workspaces import Workspace
from agentic_platform.services.ingestion import (
    IngestionDisposition,
    IngestionService,
    NormalizedMessageEvent,
)
from agentic_platform.storage.postgres.migrations import (
    MigrationRunner,
    discover_migrations,
)
from agentic_platform.storage.postgres.pool import create_postgres_pool
from agentic_platform.storage.postgres.protocols import PostgresPool
from agentic_platform.storage.postgres.unit_of_work import PostgresUnitOfWork

NOW = datetime(2026, 7, 21, 15, 30, tzinfo=timezone.utc)
MIGRATIONS = Path("platform/backend/migrations")


async def _close_pool(pool: PostgresPool) -> None:
    await cast(Any, pool).close()


async def _reset_and_seed(
    pool: PostgresPool,
    workspace: Workspace,
    connection: ChannelConnection,
) -> None:
    raw = await pool.acquire()
    try:
        runner = MigrationRunner(raw, discover_migrations(MIGRATIONS))
        await runner.down(target=0)
        await runner.up()
        async with raw.transaction():
            await raw.execute(
                "INSERT INTO workspaces(id, name, created_at) VALUES ($1, $2, $3)",
                workspace.id.value,
                workspace.name,
                workspace.created_at,
            )
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
    finally:
        await pool.release(raw)


@pytest.mark.asyncio
async def test_live_concurrent_duplicate_ingestion_is_atomic_and_idempotent(
    postgres_test_dsn: str,
    asyncpg_module: Any,
) -> None:
    del asyncpg_module
    pool = await create_postgres_pool(postgres_test_dsn, min_size=2, max_size=4)
    workspace = Workspace.create(name="Acme", created_at=NOW)
    connection = ChannelConnection.create(
        workspace_id=workspace.id,
        platform_id="telegram",
        display_name="Support",
        created_at=NOW,
        secret_ref="vault://connections/support",
    )
    event = NormalizedMessageEvent.create(
        workspace_id=workspace.id,
        connection=connection,
        platform_event_id="update-100",
        conversation_native=NativeReference("telegram", "chat-1"),
        conversation_type=ConversationType.DIRECT,
        sender_native=NativeReference("telegram", "user-1"),
        sender_display_name="Asha",
        message_native=NativeReference("telegram", "message-1"),
        text="Hello",
        occurred_at=NOW,
        raw_payload_ref="objects/raw/update-100",
    )

    try:
        await _reset_and_seed(pool, workspace, connection)
        service = IngestionService(lambda: PostgresUnitOfWork(pool))

        results = await asyncio.gather(
            service.ingest_message(event),
            service.ingest_message(event),
        )

        assert {result.disposition for result in results} == {
            IngestionDisposition.CREATED,
            IngestionDisposition.DUPLICATE,
        }
        raw = await pool.acquire()
        try:
            queries = {
                "contacts": "SELECT COUNT(*) FROM contacts WHERE workspace_id = $1",
                "external_identities": (
                    "SELECT COUNT(*) FROM external_identities WHERE workspace_id = $1"
                ),
                "conversations": (
                    "SELECT COUNT(*) FROM conversations WHERE workspace_id = $1"
                ),
                "messages": "SELECT COUNT(*) FROM messages WHERE workspace_id = $1",
                "channel_events": (
                    "SELECT COUNT(*) FROM channel_events WHERE workspace_id = $1"
                ),
                "workspace_outbox": (
                    "SELECT COUNT(*) FROM workspace_outbox WHERE workspace_id = $1"
                ),
            }
            counts = {
                table: await raw.fetchval(query, workspace.id.value)
                for table, query in queries.items()
            }
        finally:
            await pool.release(raw)
        assert counts == {
            "contacts": 1,
            "external_identities": 1,
            "conversations": 1,
            "messages": 1,
            "channel_events": 1,
            "workspace_outbox": 1,
        }
    finally:
        raw = await pool.acquire()
        try:
            await MigrationRunner(
                raw,
                discover_migrations(MIGRATIONS),
            ).down(target=0)
        finally:
            await pool.release(raw)
        await _close_pool(pool)
