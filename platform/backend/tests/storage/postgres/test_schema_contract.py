from __future__ import annotations

import re
from pathlib import Path


MIGRATIONS = Path("platform/backend/migrations")
CANONICAL_TABLES = {
    "workspaces",
    "users",
    "memberships",
    "agents",
    "channel_connections",
    "contacts",
    "external_identities",
    "conversations",
    "participants",
    "messages",
    "attachments",
    "reactions",
    "receipts",
    "channel_events",
    "raw_event_objects",
    "workspace_outbox",
    "audit_records",
}


def _sql(filename: str) -> str:
    return (MIGRATIONS / filename).read_text(encoding="utf-8").lower()


def test_core_migration_creates_every_canonical_table() -> None:
    sql = _sql("0001_workspace_inbox_core.up.sql")

    created = set(re.findall(r"create\s+table\s+([a-z_]+)", sql))

    assert created == CANONICAL_TABLES


def test_core_migration_enforces_workspace_native_and_payload_constraints() -> None:
    sql = re.sub(r"\s+", " ", _sql("0001_workspace_inbox_core.up.sql"))

    required_fragments = {
        "unique (workspace_id, connection_id, native_id)",
        "unique (workspace_id, conversation_id, native_id)",
        "unique (workspace_id, connection_id, platform_event_id)",
        "primary key (workspace_id, cursor)",
        "check (payload_version > 0)",
        "check (unread_count >= 0)",
        "foreign key (workspace_id, connection_id, platform_id)",
        "foreign key (workspace_id, conversation_id, platform_id)",
    }
    for fragment in required_fragments:
        assert fragment in sql

    assert sql.count("payload_version integer not null") >= 5
    assert "secret_ref text" in sql
    assert "secret_value" not in sql
    assert "api_key" not in sql


def test_index_migration_covers_inbox_event_and_audit_access_paths() -> None:
    sql = _sql("0002_outbox_audit_indexes.up.sql")

    expected_indexes = {
        "idx_conversations_workspace_recent",
        "idx_messages_workspace_conversation_sent",
        "idx_channel_events_idempotency",
        "idx_workspace_outbox_cursor",
        "idx_audit_records_workspace_occurred",
    }
    created = set(re.findall(r"create\s+index\s+([a-z_]+)", sql))

    assert created == expected_indexes


def test_down_migrations_drop_indexes_and_tables_in_reverse_order() -> None:
    indexes_down = _sql("0002_outbox_audit_indexes.down.sql")
    core_down = _sql("0001_workspace_inbox_core.down.sql")

    assert indexes_down.index("idx_audit_records_workspace_occurred") < indexes_down.index(
        "idx_conversations_workspace_recent"
    )
    assert core_down.index("drop table audit_records") < core_down.index(
        "drop table workspaces"
    )
    assert all(f"drop table {table}" in core_down for table in CANONICAL_TABLES)
