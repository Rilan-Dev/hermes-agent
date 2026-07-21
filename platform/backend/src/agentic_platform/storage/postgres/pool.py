from __future__ import annotations

import importlib
from typing import Any

from agentic_platform.domain.errors import DomainValidationError
from agentic_platform.storage.postgres.protocols import PostgresPool


async def create_postgres_pool(
    dsn: str,
    *,
    min_size: int = 1,
    max_size: int = 10,
) -> PostgresPool:
    normalized_dsn = dsn.strip() if isinstance(dsn, str) else ""
    if not normalized_dsn:
        raise DomainValidationError("PostgreSQL DSN must not be blank")
    if (
        not isinstance(min_size, int)
        or isinstance(min_size, bool)
        or min_size < 1
    ):
        raise DomainValidationError("PostgreSQL pool min_size must be positive")
    if (
        not isinstance(max_size, int)
        or isinstance(max_size, bool)
        or max_size < min_size
    ):
        raise DomainValidationError(
            "PostgreSQL pool max_size must be greater than or equal to min_size"
        )
    try:
        asyncpg: Any = importlib.import_module("asyncpg")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "asyncpg==0.31.0 is required for PostgreSQL storage"
        ) from exc
    return await asyncpg.create_pool(
        normalized_dsn,
        min_size=min_size,
        max_size=max_size,
    )
