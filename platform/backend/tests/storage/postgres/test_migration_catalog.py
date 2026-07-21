from __future__ import annotations

from pathlib import Path

import pytest

from agentic_platform.storage.postgres.migrations import (
    MigrationCatalogError,
    discover_migrations,
)


def _write_pair(
    root: Path,
    version: int,
    name: str,
    up_sql: str,
    down_sql: str,
) -> None:
    prefix = f"{version:04d}_{name}"
    (root / f"{prefix}.up.sql").write_text(up_sql, encoding="utf-8")
    (root / f"{prefix}.down.sql").write_text(down_sql, encoding="utf-8")


def test_discover_migrations_pairs_orders_and_hashes_sql(tmp_path: Path) -> None:
    _write_pair(tmp_path, 2, "outbox", "SELECT 2;", "SELECT -2;")
    _write_pair(tmp_path, 1, "core", "SELECT 1;", "SELECT -1;")

    migrations = discover_migrations(tmp_path)

    assert [item.version for item in migrations] == [1, 2]
    assert [item.name for item in migrations] == ["core", "outbox"]
    assert all(len(item.checksum) == 64 for item in migrations)
    assert migrations[0].checksum != migrations[1].checksum


def test_discover_migrations_normalizes_bom_and_surrounding_whitespace(
    tmp_path: Path,
) -> None:
    _write_pair(
        tmp_path,
        1,
        "core",
        "\ufeff\n SELECT 1; \n",
        "\n SELECT -1; \n",
    )

    migration = discover_migrations(tmp_path)[0]

    assert migration.up_sql == "SELECT 1;"
    assert migration.down_sql == "SELECT -1;"


@pytest.mark.parametrize(
    "filenames",
    [
        ("0001_core.up.sql",),
        (
            "0001_core.up.sql",
            "0001_core.down.sql",
            "0003_next.up.sql",
            "0003_next.down.sql",
        ),
        ("0001_core.up.sql", "0001_other.down.sql"),
        ("0000_core.up.sql", "0000_core.down.sql"),
        ("0001-Core.up.sql", "0001-Core.down.sql"),
    ],
)
def test_discover_migrations_rejects_incomplete_gapped_or_unsafe_catalog(
    tmp_path: Path,
    filenames: tuple[str, ...],
) -> None:
    for filename in filenames:
        (tmp_path / filename).write_text("SELECT 1;", encoding="utf-8")

    with pytest.raises(MigrationCatalogError):
        discover_migrations(tmp_path)


def test_discover_migrations_rejects_blank_sql(tmp_path: Path) -> None:
    _write_pair(tmp_path, 1, "core", "  \n", "SELECT -1;")

    with pytest.raises(MigrationCatalogError, match="must not be blank"):
        discover_migrations(tmp_path)


def test_repository_migration_catalog_is_complete() -> None:
    migrations = discover_migrations(Path("platform/backend/migrations"))

    assert [(item.version, item.name) for item in migrations] == [
        (1, "workspace_inbox_core"),
        (2, "outbox_audit_indexes"),
    ]
