from __future__ import annotations

import os
from typing import Any

import pytest


@pytest.fixture
def postgres_test_dsn() -> str:
    dsn = os.environ.get("POSTGRES_TEST_DSN", "").strip()
    if not dsn:
        pytest.skip("POSTGRES_TEST_DSN is required for live PostgreSQL tests")
    return dsn


@pytest.fixture
def asyncpg_module(postgres_test_dsn: str) -> Any:
    del postgres_test_dsn
    return pytest.importorskip(
        "asyncpg",
        reason="asyncpg==0.31.0 is required for live PostgreSQL tests",
    )
