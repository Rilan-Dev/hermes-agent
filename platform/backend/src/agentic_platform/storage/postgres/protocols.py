from __future__ import annotations

from types import TracebackType
from typing import Any, Mapping, Protocol, Sequence


class MigrationTransaction(Protocol):
    async def __aenter__(self) -> MigrationTransaction: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class MigrationConnection(Protocol):
    def transaction(self) -> MigrationTransaction: ...

    async def execute(self, query: str, *args: Any) -> str: ...

    async def fetch(
        self,
        query: str,
        *args: Any,
    ) -> Sequence[Mapping[str, Any]]: ...


class RepositoryConnection(Protocol):
    async def execute(self, query: str, *args: Any) -> str: ...

    async def fetch(
        self,
        query: str,
        *args: Any,
    ) -> Sequence[Mapping[str, Any]]: ...

    async def fetchrow(
        self,
        query: str,
        *args: Any,
    ) -> Mapping[str, Any] | None: ...

    async def fetchval(self, query: str, *args: Any) -> Any: ...


class PostgresTransaction(MigrationTransaction, Protocol):
    async def start(self) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


class PostgresConnection(RepositoryConnection, Protocol):
    def transaction(self) -> PostgresTransaction: ...


class PostgresPool(Protocol):
    async def acquire(self) -> PostgresConnection: ...

    async def release(self, connection: PostgresConnection) -> None: ...
