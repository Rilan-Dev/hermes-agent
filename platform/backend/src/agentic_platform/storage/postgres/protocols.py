from __future__ import annotations

from types import TracebackType
from typing import Any, Mapping, Protocol, Sequence


class PostgresTransaction(Protocol):
    async def __aenter__(self) -> PostgresTransaction: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...


class PostgresConnection(Protocol):
    def transaction(self) -> PostgresTransaction: ...

    async def execute(self, query: str, *args: Any) -> str: ...

    async def fetch(
        self,
        query: str,
        *args: Any,
    ) -> Sequence[Mapping[str, Any]]: ...
