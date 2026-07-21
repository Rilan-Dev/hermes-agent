from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from agentic_platform.storage.postgres.migrations import (
    Migration,
    MigrationDriftError,
    MigrationRunner,
)


UP_SQL_1 = "CREATE TABLE first_table(id integer);"
DOWN_SQL_1 = "DROP TABLE first_table;"
UP_SQL_2 = "CREATE TABLE second_table(id integer);"
DOWN_SQL_2 = "DROP TABLE second_table;"
CHECKSUM_1 = "1" * 64
CHECKSUM_2 = "2" * 64


def _migrations() -> tuple[Migration, ...]:
    return (
        Migration(1, "first", UP_SQL_1, DOWN_SQL_1, CHECKSUM_1),
        Migration(2, "second", UP_SQL_2, DOWN_SQL_2, CHECKSUM_2),
    )


@dataclass
class _Transaction:
    connection: FakeConnection

    async def __aenter__(self) -> _Transaction:
        self.connection.transaction_entries += 1
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        del exc_type, exc, traceback


class FakeConnection:
    def __init__(
        self,
        *,
        applied: tuple[tuple[int, str, str], ...] = (),
    ) -> None:
        self.applied = list(applied)
        self.transaction_entries = 0
        self.advisory_lock_calls = 0
        self.executed_migration_sql: list[str] = []
        self.recorded_versions: list[tuple[int, str, str]] = []
        self.deleted_versions: list[int] = []

    def transaction(self) -> _Transaction:
        return _Transaction(self)

    async def execute(self, query: str, *args: Any) -> str:
        if "pg_advisory_xact_lock" in query:
            self.advisory_lock_calls += 1
        elif query in {UP_SQL_1, UP_SQL_2, DOWN_SQL_1, DOWN_SQL_2}:
            self.executed_migration_sql.append(query)
        elif "INSERT INTO agentic_platform_schema_migrations" in query:
            version, name, checksum = args
            self.recorded_versions.append((version, name, checksum))
            self.applied.append((version, name, checksum))
        elif "DELETE FROM agentic_platform_schema_migrations" in query:
            (version,) = args
            self.deleted_versions.append(version)
            self.applied = [item for item in self.applied if item[0] != version]
        return "OK"

    async def fetch(self, query: str, *args: Any):
        del args
        if "FROM agentic_platform_schema_migrations" in query:
            return [
                {"version": version, "name": name, "checksum": checksum}
                for version, name, checksum in sorted(self.applied)
            ]
        raise AssertionError(f"unexpected fetch query: {query}")


@pytest.mark.asyncio
async def test_up_uses_one_transaction_lock_and_records_each_checksum() -> None:
    connection = FakeConnection()
    runner = MigrationRunner(connection, _migrations())

    applied = await runner.up()

    assert applied == (1, 2)
    assert connection.transaction_entries == 1
    assert connection.advisory_lock_calls == 1
    assert connection.executed_migration_sql == [UP_SQL_1, UP_SQL_2]
    assert connection.recorded_versions == [
        (1, "first", CHECKSUM_1),
        (2, "second", CHECKSUM_2),
    ]


@pytest.mark.asyncio
async def test_up_skips_verified_applied_migrations() -> None:
    connection = FakeConnection(applied=((1, "first", CHECKSUM_1),))

    applied = await MigrationRunner(connection, _migrations()).up()

    assert applied == (2,)
    assert connection.executed_migration_sql == [UP_SQL_2]


@pytest.mark.asyncio
async def test_up_blocks_applied_checksum_drift() -> None:
    connection = FakeConnection(applied=((1, "first", "different-checksum"),))

    with pytest.raises(MigrationDriftError, match="checksum drift"):
        await MigrationRunner(connection, _migrations()).up()

    assert connection.executed_migration_sql == []


@pytest.mark.asyncio
async def test_up_blocks_unknown_applied_version() -> None:
    connection = FakeConnection(applied=((3, "future", "3" * 64),))

    with pytest.raises(MigrationDriftError, match="unknown applied migration"):
        await MigrationRunner(connection, _migrations()).up()


@pytest.mark.asyncio
async def test_up_blocks_noncontiguous_applied_history() -> None:
    connection = FakeConnection(applied=((2, "second", CHECKSUM_2),))

    with pytest.raises(MigrationDriftError, match="contiguous prefix"):
        await MigrationRunner(connection, _migrations()).up()


@pytest.mark.asyncio
async def test_down_runs_reverse_sql_and_removes_history() -> None:
    connection = FakeConnection(
        applied=((1, "first", CHECKSUM_1), (2, "second", CHECKSUM_2))
    )

    reverted = await MigrationRunner(connection, _migrations()).down(target=0)

    assert reverted == (2, 1)
    assert connection.transaction_entries == 1
    assert connection.advisory_lock_calls == 1
    assert connection.executed_migration_sql == [DOWN_SQL_2, DOWN_SQL_1]
    assert connection.deleted_versions == [2, 1]


@pytest.mark.asyncio
@pytest.mark.parametrize("target", [-1, 3])
async def test_runner_rejects_target_outside_catalog(target: int) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="migration target"):
        await MigrationRunner(connection, _migrations()).up(target=target)
