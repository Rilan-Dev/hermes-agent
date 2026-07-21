from __future__ import annotations

import asyncio
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Mapping, Sequence

import pytest

from agentic_platform.storage.postgres.protocols import PostgresConnection
from agentic_platform.storage.postgres.unit_of_work import PostgresUnitOfWork


@dataclass
class FakeTransaction:
    starts: int = 0
    commits: int = 0
    rollbacks: int = 0

    async def start(self) -> None:
        self.starts += 1

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def __aenter__(self) -> FakeTransaction:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        del exc_type, exc, traceback
        return None


class FakeConnection:
    def __init__(self) -> None:
        self.tx = FakeTransaction()

    def transaction(self) -> FakeTransaction:
        return self.tx

    async def execute(self, query: str, *args: Any) -> str:
        del query, args
        return "OK"

    async def fetch(
        self,
        query: str,
        *args: Any,
    ) -> Sequence[Mapping[str, Any]]:
        del query, args
        return ()

    async def fetchrow(
        self,
        query: str,
        *args: Any,
    ) -> Mapping[str, Any] | None:
        del query, args
        return None

    async def fetchval(self, query: str, *args: Any) -> Any:
        del query, args
        return None


class FakePool:
    def __init__(self) -> None:
        self.connection = FakeConnection()
        self.acquires = 0
        self.releases = 0

    async def acquire(self) -> PostgresConnection:
        self.acquires += 1
        return self.connection

    async def release(self, connection: PostgresConnection) -> None:
        assert connection is self.connection
        self.releases += 1


def test_unit_of_work_commits_only_after_clean_requested_exit() -> None:
    async def scenario() -> None:
        pool = FakePool()
        async with PostgresUnitOfWork(pool) as unit_of_work:
            assert unit_of_work.workspaces is unit_of_work.workspaces
            assert unit_of_work.outbox is unit_of_work.outbox
            await unit_of_work.commit()

        assert pool.acquires == 1
        assert pool.releases == 1
        assert pool.connection.tx.starts == 1
        assert pool.connection.tx.commits == 1
        assert pool.connection.tx.rollbacks == 0

    asyncio.run(scenario())


def test_unit_of_work_rolls_back_without_commit_request() -> None:
    async def scenario() -> None:
        pool = FakePool()
        async with PostgresUnitOfWork(pool):
            pass

        assert pool.connection.tx.commits == 0
        assert pool.connection.tx.rollbacks == 1
        assert pool.releases == 1

    asyncio.run(scenario())


def test_unit_of_work_rolls_back_exception_after_commit_request() -> None:
    async def scenario() -> None:
        pool = FakePool()
        with pytest.raises(RuntimeError, match="abort"):
            async with PostgresUnitOfWork(pool) as unit_of_work:
                await unit_of_work.commit()
                raise RuntimeError("abort")

        assert pool.connection.tx.commits == 0
        assert pool.connection.tx.rollbacks == 1
        assert pool.releases == 1

    asyncio.run(scenario())


def test_unit_of_work_repositories_require_active_context() -> None:
    unit_of_work = PostgresUnitOfWork(FakePool())

    with pytest.raises(RuntimeError, match="must be entered"):
        _ = unit_of_work.messages
