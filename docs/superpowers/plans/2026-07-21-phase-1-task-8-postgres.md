# Phase 1 Task 8 PostgreSQL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans and superpowers:test-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reversible PostgreSQL migrations and asyncpg-backed repository/unit-of-work adapters that preserve the existing workspace, idempotency, pagination, and transactional-outbox contracts.

**Architecture:** PostgreSQL becomes the durable source of truth. Versioned plain SQL migrations are discovered deterministically, checksum-verified, and applied under a transaction-scoped advisory lock. Product repositories use the existing `agentic_platform.ports.repositories` interfaces; the asyncpg dependency remains isolated inside `storage/postgres/` and is imported lazily so infrastructure-independent tests continue to run without the optional driver.

**Tech Stack:** Python 3.11–3.13, PostgreSQL 16+, existing exact pin `asyncpg==0.31.0`, pytest, GitHub Actions PostgreSQL service container. No SQLAlchemy or Alembic dependency is introduced.

## Global Constraints

- Continue on `worktree/agentic-platform-phase-1-closure` from Task 7 CI-green head `b2f1f19ee01ac9dc7c653bbd476309261b0b1940`.
- Every tenant row and every repository query is workspace-scoped.
- Native uniqueness includes workspace and connection/conversation identity as applicable.
- Channel-event ingestion and workspace-outbox append commit in the same PostgreSQL transaction.
- Migration history is immutable: an applied checksum mismatch blocks startup.
- Migration discovery rejects missing pairs, duplicate versions, version gaps, blank SQL, and unsafe filenames.
- PostgreSQL driver imports remain inside `agentic_platform.storage.postgres`.
- The memory and PostgreSQL adapters must satisfy the same repository behavior tests.
- No production code is written before a focused failing test.

---

### Task 8.1: Deterministic Reversible Migration Runner

**Files:**
- Create: `platform/backend/src/agentic_platform/storage/postgres/__init__.py`
- Create: `platform/backend/src/agentic_platform/storage/postgres/protocols.py`
- Create: `platform/backend/src/agentic_platform/storage/postgres/migrations.py`
- Create: `platform/backend/migrations/0001_workspace_inbox_core.up.sql`
- Create: `platform/backend/migrations/0001_workspace_inbox_core.down.sql`
- Create: `platform/backend/migrations/0002_outbox_audit_indexes.up.sql`
- Create: `platform/backend/migrations/0002_outbox_audit_indexes.down.sql`
- Test: `platform/backend/tests/storage/postgres/test_migration_catalog.py`
- Test: `platform/backend/tests/storage/postgres/test_migration_runner.py`
- Test: `platform/backend/tests/storage/postgres/test_schema_contract.py`

**Interfaces:**
- Produces `Migration(version: int, name: str, up_sql: str, down_sql: str, checksum: str)`.
- Produces `discover_migrations(root: Path) -> tuple[Migration, ...]`.
- Produces `MigrationRunner(connection: PostgresConnection, migrations: Sequence[Migration])`.
- Produces `MigrationRunner.up(target: int | None = None) -> tuple[int, ...]`.
- Produces `MigrationRunner.down(target: int = 0) -> tuple[int, ...]`.
- `PostgresConnection` structurally supports `execute`, `fetch`, and `transaction()`; no runtime import of asyncpg is required by this slice.

- [ ] **Step 1: Write migration-catalog RED tests**

```python
def test_discover_migrations_pairs_orders_and_hashes_sql(tmp_path: Path) -> None:
    write_pair(tmp_path, 2, "outbox", "SELECT 2;", "SELECT -2;")
    write_pair(tmp_path, 1, "core", "SELECT 1;", "SELECT -1;")

    migrations = discover_migrations(tmp_path)

    assert [item.version for item in migrations] == [1, 2]
    assert [item.name for item in migrations] == ["core", "outbox"]
    assert all(len(item.checksum) == 64 for item in migrations)
```

```python
@pytest.mark.parametrize(
    "filenames",
    [
        ("0001_core.up.sql",),
        ("0001_core.up.sql", "0002_next.up.sql", "0002_next.down.sql"),
        ("0001_core.up.sql", "0001_other.down.sql"),
    ],
)
def test_discover_migrations_rejects_incomplete_or_gapped_catalog(
    tmp_path: Path,
    filenames: tuple[str, ...],
) -> None:
    for filename in filenames:
        (tmp_path / filename).write_text("SELECT 1;", encoding="utf-8")
    with pytest.raises(MigrationCatalogError):
        discover_migrations(tmp_path)
```

- [ ] **Step 2: Verify RED**

Run:
```bash
python -m pytest platform/backend/tests/storage/postgres/test_migration_catalog.py -q
```
Expected: import failure because `storage.postgres.migrations` does not exist.

- [ ] **Step 3: Implement immutable migration discovery**

Implementation requirements:
- Accept only `NNNN_lower_snake_name.up.sql` and matching `.down.sql`.
- Require versions to start at 1 and remain contiguous.
- Require exact name match for each up/down pair.
- Strip UTF-8 BOM and surrounding whitespace; reject empty SQL.
- Compute SHA-256 over `version`, `name`, normalized up SQL, and normalized down SQL separated by NUL bytes.
- Return a tuple sorted by version.

- [ ] **Step 4: Verify GREEN**

Run:
```bash
python -m pytest platform/backend/tests/storage/postgres/test_migration_catalog.py -q
```
Expected: catalog tests pass.

- [ ] **Step 5: Write migration-runner RED tests**

```python
@pytest.mark.asyncio
async def test_up_uses_one_transaction_lock_and_records_each_checksum() -> None:
    connection = FakeConnection(applied=())
    runner = MigrationRunner(connection, sample_migrations())

    applied = await runner.up()

    assert applied == (1, 2)
    assert connection.transaction_entries == 1
    assert connection.advisory_lock_calls == 1
    assert connection.recorded_versions == [(1, CHECKSUM_1), (2, CHECKSUM_2)]
```

```python
@pytest.mark.asyncio
async def test_up_blocks_applied_checksum_drift() -> None:
    connection = FakeConnection(applied=((1, "different-checksum"),))
    with pytest.raises(MigrationDriftError):
        await MigrationRunner(connection, sample_migrations()).up()
```

```python
@pytest.mark.asyncio
async def test_down_runs_reverse_sql_and_removes_history() -> None:
    connection = FakeConnection(applied=((1, CHECKSUM_1), (2, CHECKSUM_2)))
    reverted = await MigrationRunner(connection, sample_migrations()).down(target=0)
    assert reverted == (2, 1)
    assert connection.executed_migration_sql == [DOWN_SQL_2, DOWN_SQL_1]
```

- [ ] **Step 6: Verify runner RED**

Run:
```bash
python -m pytest platform/backend/tests/storage/postgres/test_migration_runner.py -q
```
Expected: `MigrationRunner` is missing.

- [ ] **Step 7: Implement runner minimally**

Implementation requirements:
- Create `agentic_platform_schema_migrations(version INTEGER PRIMARY KEY, name TEXT NOT NULL, checksum CHAR(64) NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())`.
- Start one connection transaction for each `up()` or `down()` call.
- Execute `SELECT pg_advisory_xact_lock($1)` with stable signed 64-bit key `0x41504C4154464F52`.
- Read applied versions ordered ascending.
- Reject unknown applied versions and checksum/name drift.
- Apply pending SQL in ascending order and insert history after each successful migration.
- Revert SQL in descending order and delete history after each successful downgrade.
- Reject targets outside `0..latest_version`.

- [ ] **Step 8: Add canonical schema SQL and static contract test**

`0001` must create:
- `workspaces`, `users`, `memberships`, `agents`, `channel_connections`
- `contacts`, `external_identities`, `conversations`, `participants`
- `messages`, `attachments`, `reactions`, `receipts`
- `channel_events`, `raw_event_objects`, `workspace_outbox`, `audit_records`

Required constraints include:
- workspace composite foreign keys or workspace equality checks for tenant relationships;
- `UNIQUE (workspace_id, connection_id, native_id)` on external identities and conversations;
- `UNIQUE (workspace_id, conversation_id, native_id)` on messages;
- `UNIQUE (workspace_id, connection_id, platform_event_id)` on channel events;
- `UNIQUE (workspace_id, cursor)` on workspace outbox;
- `payload_version INTEGER NOT NULL CHECK (payload_version > 0)` on JSON payload tables.

`0002` must create recent-conversation, conversation-message, event-idempotency, outbox-cursor, and audit-time indexes. Down migrations remove objects in reverse dependency order.

- [ ] **Step 9: Run Task 8.1 and full regression gates**

Run:
```bash
python -m pytest platform/backend/tests/storage/postgres/test_migration_catalog.py platform/backend/tests/storage/postgres/test_migration_runner.py platform/backend/tests/storage/postgres/test_schema_contract.py -q
python -m pytest tests/scripts/platform_inventory platform/backend/tests -q
python -m compileall -q scripts/platform_inventory platform/backend/src/agentic_platform
git diff --check
```
Expected: all tests pass and no compile/diff errors.

- [ ] **Step 10: Commit migration slice**

```bash
git add platform/backend/migrations platform/backend/src/agentic_platform/storage/postgres platform/backend/tests/storage/postgres
git commit -m "feat(platform): add reversible postgres migrations"
```

Rollback boundary: revert this commit; Task 7 remains functional with the memory adapter.

---

### Task 8.2: Asyncpg Unit of Work and Repository Adapters

**Files:**
- Create: `platform/backend/src/agentic_platform/storage/postgres/codec.py`
- Create: `platform/backend/src/agentic_platform/storage/postgres/repositories.py`
- Create: `platform/backend/src/agentic_platform/storage/postgres/unit_of_work.py`
- Create: `platform/backend/src/agentic_platform/storage/postgres/pool.py`
- Modify: `pyproject.toml` to add exact optional extra `platform-postgres = ["asyncpg==0.31.0"]`.
- Test: `platform/backend/tests/storage/postgres/test_codec.py`
- Test: `platform/backend/tests/storage/postgres/test_unit_of_work.py`
- Test: `platform/backend/tests/storage/postgres/test_repository_sql_contract.py`

**Interfaces:**
- Consumes all repository protocols from `ports/repositories.py`.
- Produces `create_postgres_pool(dsn: str, *, min_size: int = 1, max_size: int = 10)` with lazy `asyncpg` import.
- Produces `PostgresUnitOfWork(pool: PostgresPool)` implementing `UnitOfWork`.
- Produces workspace-scoped repository implementations for workspace, contact, external identity, conversation, message, channel event, and outbox.

- [ ] **Step 1: Write codec and UoW RED tests**
- Serialize UUID-backed IDs as UUID/text values and enums as `.value`.
- Reconstruct every current aggregate with UTC-aware timestamps and native references.
- Assert UoW acquires one connection, starts one transaction, commits only when requested and no exception occurred, otherwise rolls back, and always releases the connection.

- [ ] **Step 2: Verify RED**

Run:
```bash
python -m pytest platform/backend/tests/storage/postgres/test_codec.py platform/backend/tests/storage/postgres/test_unit_of_work.py -q
```
Expected: postgres codec/UoW imports are missing.

- [ ] **Step 3: Implement codec and UoW minimally**
- Never place secret values into serialized rows; only opaque `secret_ref` is persisted.
- Repository properties are unavailable before `__aenter__` and after `__aexit__`.
- An exception after `commit()` still rolls back.

- [ ] **Step 4: Write repository SQL-contract RED tests**
- Assert every query contains `workspace_id` in lookup predicates.
- Assert all save statements use conflict targets matching canonical uniqueness constraints.
- Assert cursor pagination is exclusive and deterministic.
- Assert `next_cursor` locks the workspace cursor range or equivalent workspace row to prevent duplicate cursors.

- [ ] **Step 5: Implement repository adapters**
- Use positional asyncpg parameters only; never format user/native IDs into SQL strings.
- Enforce domain workspace equality before executing writes.
- Use `ON CONFLICT ... DO UPDATE` for aggregates and `DO NOTHING` for immutable channel-event idempotency.
- Use `FOR UPDATE` when allocating the next workspace outbox cursor.

- [ ] **Step 6: Run focused and full gates**

Run:
```bash
python -m pytest platform/backend/tests/storage/postgres/test_codec.py platform/backend/tests/storage/postgres/test_unit_of_work.py platform/backend/tests/storage/postgres/test_repository_sql_contract.py -q
python -m pytest tests/scripts/platform_inventory platform/backend/tests -q
python -m compileall -q scripts/platform_inventory platform/backend/src/agentic_platform
git diff --check
```
Expected: all tests pass.

- [ ] **Step 7: Commit adapter slice**

```bash
git add pyproject.toml platform/backend/src/agentic_platform/storage/postgres platform/backend/tests/storage/postgres
git commit -m "feat(platform): add asyncpg repository adapters"
```

Rollback boundary: revert this commit; migrations remain reviewable and runnable independently.

---

### Task 8.3: Live PostgreSQL Contract and Concurrent Idempotency CI

**Files:**
- Create: `platform/backend/tests/storage/postgres/test_live_repository_contract.py`
- Create: `platform/backend/tests/storage/postgres/test_live_ingestion.py`
- Modify: `.github/workflows/tests.yml` to add a PostgreSQL 16 service-backed Phase 1 job.

**Interfaces:**
- Consumes `POSTGRES_TEST_DSN` only in explicitly marked integration tests.
- Reuses the same behavioral fixtures for `MemoryUnitOfWork` and `PostgresUnitOfWork`.

- [ ] **Step 1: Write opt-in live tests**
- Upgrade an empty database to latest migration and downgrade to zero.
- Run repository save/get/native lookup/list pagination contracts.
- Start two concurrent normalized ingestions with the same `(workspace_id, connection_id, platform_event_id)` and assert one canonical message, one channel event, and one outbox event.
- Assert a forced exception after `commit()` leaves no partial aggregate/outbox data.

- [ ] **Step 2: Run locally without DSN**

Run:
```bash
python -m pytest platform/backend/tests/storage/postgres/test_live_repository_contract.py platform/backend/tests/storage/postgres/test_live_ingestion.py -q
```
Expected: tests skip with explicit `POSTGRES_TEST_DSN is required` reason.

- [ ] **Step 3: Add permanent PostgreSQL CI job**
- Use `postgres:16-alpine` with health checks.
- Install the locked `platform-postgres` and `dev` extras.
- Set a non-production DSN through job environment.
- Run migrations and only the PostgreSQL integration tests first, then the complete Phase 1 backend suite.

- [ ] **Step 4: Verify exact remote head**
- Blocking Ruff, ty diff, lockfile, security, Python matrix, Desktop E2E, and PostgreSQL contract job all succeed.
- Download or inspect PostgreSQL job logs to confirm migration upgrade/downgrade and concurrent idempotency tests executed rather than skipped.

- [ ] **Step 5: Commit CI slice**

```bash
git add .github/workflows/tests.yml platform/backend/tests/storage/postgres
git commit -m "test(platform): verify postgres contracts in CI"
```

Rollback boundary: revert the CI commit without changing production adapters; Task 8 cannot be marked complete until an equivalent live gate is restored.

---

## Task 8 Acceptance Gate

- [ ] Migration catalog is deterministic, paired, contiguous, checksummed, and reversible.
- [ ] Applied migration drift blocks startup.
- [ ] Canonical tenant tables and uniqueness constraints exist.
- [ ] Memory and PostgreSQL adapters satisfy the same repository behavior.
- [ ] Every durable query is workspace-scoped and parameterized.
- [ ] Concurrent duplicate ingestion produces one message, one channel event, and one outbox event.
- [ ] Transaction rollback prevents partial aggregate/outbox writes.
- [ ] Upgrade/downgrade and live repository contracts run against PostgreSQL 16 in GitHub CI.
- [ ] Full repository CI passes on the exact Task 8 head.
