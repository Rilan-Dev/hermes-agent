from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace

import pytest

from agentic_platform.domain.errors import DomainValidationError
from agentic_platform.storage.postgres.pool import create_postgres_pool


def test_pool_factory_lazily_calls_asyncpg_with_bounded_sizes(monkeypatch) -> None:
    calls: list[tuple[str, int, int]] = []
    pool = object()

    async def create_pool(dsn: str, *, min_size: int, max_size: int):
        calls.append((dsn, min_size, max_size))
        return pool

    monkeypatch.setitem(sys.modules, "asyncpg", SimpleNamespace(create_pool=create_pool))

    result = asyncio.run(
        create_postgres_pool(
            "postgresql://platform@example/platform",
            min_size=2,
            max_size=8,
        )
    )

    assert result is pool
    assert calls == [("postgresql://platform@example/platform", 2, 8)]


@pytest.mark.parametrize(
    ("dsn", "min_size", "max_size"),
    [
        ("", 1, 10),
        ("postgresql://example/db", 0, 10),
        ("postgresql://example/db", 5, 4),
    ],
)
def test_pool_factory_rejects_invalid_configuration(
    dsn: str,
    min_size: int,
    max_size: int,
) -> None:
    with pytest.raises(DomainValidationError):
        asyncio.run(
            create_postgres_pool(dsn, min_size=min_size, max_size=max_size)
        )
