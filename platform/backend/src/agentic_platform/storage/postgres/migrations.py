from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from agentic_platform.storage.postgres.protocols import PostgresConnection


_MIGRATION_FILE = re.compile(
    r"^(?P<version>[0-9]{4})_(?P<name>[a-z][a-z0-9]*(?:_[a-z0-9]+)*)"
    r"\.(?P<direction>up|down)\.sql$"
)


class MigrationError(RuntimeError):
    """Base class for deterministic migration failures."""


class MigrationCatalogError(MigrationError):
    """Raised when migration files are incomplete or unsafe."""


class MigrationDriftError(MigrationError):
    """Raised when applied migration metadata differs from source files."""


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    name: str
    up_sql: str
    down_sql: str
    checksum: str


def _normalized_sql(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise MigrationCatalogError(f"migration must be UTF-8: {path.name}") from exc
    normalized = text.lstrip("\ufeff").strip()
    if not normalized:
        raise MigrationCatalogError(f"migration SQL must not be blank: {path.name}")
    return normalized


def _checksum(version: int, name: str, up_sql: str, down_sql: str) -> str:
    digest = hashlib.sha256()
    for value in (str(version), name, up_sql, down_sql):
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def discover_migrations(root: Path) -> tuple[Migration, ...]:
    directory = root.resolve()
    if not directory.is_dir():
        raise MigrationCatalogError(f"migration directory does not exist: {root}")

    entries: dict[int, dict[str, Path | str]] = {}
    sql_files = sorted(path for path in directory.iterdir() if path.suffix == ".sql")
    for path in sql_files:
        match = _MIGRATION_FILE.fullmatch(path.name)
        if match is None:
            raise MigrationCatalogError(f"invalid migration filename: {path.name}")
        version = int(match.group("version"))
        if version < 1:
            raise MigrationCatalogError("migration versions must start at 1")
        name = match.group("name")
        direction = match.group("direction")
        entry = entries.setdefault(version, {"name": name})
        if entry["name"] != name:
            raise MigrationCatalogError(
                f"migration version {version:04d} has conflicting names"
            )
        if direction in entry:
            raise MigrationCatalogError(
                f"duplicate {direction} migration for version {version:04d}"
            )
        entry[direction] = path

    if not entries:
        return ()

    versions = sorted(entries)
    expected = list(range(1, versions[-1] + 1))
    if versions != expected:
        raise MigrationCatalogError("migration versions must be contiguous from 1")

    migrations: list[Migration] = []
    for version in versions:
        entry = entries[version]
        if "up" not in entry or "down" not in entry:
            raise MigrationCatalogError(
                f"migration {version:04d}_{entry['name']} requires up and down SQL"
            )
        name = str(entry["name"])
        up_path = entry["up"]
        down_path = entry["down"]
        assert isinstance(up_path, Path)
        assert isinstance(down_path, Path)
        up_sql = _normalized_sql(up_path)
        down_sql = _normalized_sql(down_path)
        migrations.append(
            Migration(
                version=version,
                name=name,
                up_sql=up_sql,
                down_sql=down_sql,
                checksum=_checksum(version, name, up_sql, down_sql),
            )
        )
    return tuple(migrations)


_MIGRATION_LOCK_KEY = 0x41504C4154464F52
_CREATE_HISTORY_SQL = """
CREATE TABLE IF NOT EXISTS agentic_platform_schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    checksum CHAR(64) NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
""".strip()
_LOCK_SQL = "SELECT pg_advisory_xact_lock($1)"
_READ_HISTORY_SQL = """
SELECT version, name, checksum
FROM agentic_platform_schema_migrations
ORDER BY version ASC
""".strip()
_INSERT_HISTORY_SQL = """
INSERT INTO agentic_platform_schema_migrations(version, name, checksum)
VALUES ($1, $2, $3)
""".strip()
_DELETE_HISTORY_SQL = (
    "DELETE FROM agentic_platform_schema_migrations WHERE version = $1"
)


class MigrationRunner:
    def __init__(
        self,
        connection: PostgresConnection,
        migrations: Sequence[Migration],
    ) -> None:
        self._connection = connection
        self._migrations = tuple(migrations)
        versions = [migration.version for migration in self._migrations]
        if versions != list(range(1, len(versions) + 1)):
            raise MigrationCatalogError(
                "migration runner requires contiguous versions starting at 1"
            )

    def _validated_target(self, target: int | None, *, default: int) -> int:
        selected = default if target is None else target
        if (
            not isinstance(selected, int)
            or isinstance(selected, bool)
            or selected < 0
            or selected > len(self._migrations)
        ):
            raise ValueError(
                f"migration target must be between 0 and {len(self._migrations)}"
            )
        return selected

    async def _read_verified_history(self) -> dict[int, Migration]:
        rows = await self._connection.fetch(_READ_HISTORY_SQL)
        catalog = {migration.version: migration for migration in self._migrations}
        applied: dict[int, Migration] = {}
        for row in rows:
            version = int(row["version"])
            migration = catalog.get(version)
            if migration is None:
                raise MigrationDriftError(
                    f"unknown applied migration version {version:04d}"
                )
            name = str(row["name"])
            checksum = str(row["checksum"])
            if name != migration.name:
                raise MigrationDriftError(
                    f"migration name drift for version {version:04d}"
                )
            if checksum != migration.checksum:
                raise MigrationDriftError(
                    f"migration checksum drift for version {version:04d}"
                )
            applied[version] = migration
        applied_versions = sorted(applied)
        if applied_versions:
            expected_versions = list(range(1, applied_versions[-1] + 1))
            if applied_versions != expected_versions:
                raise MigrationDriftError(
                    "applied migration history must be a contiguous prefix"
                )
        return applied

    async def _prepare(self) -> dict[int, Migration]:
        await self._connection.execute(_LOCK_SQL, _MIGRATION_LOCK_KEY)
        await self._connection.execute(_CREATE_HISTORY_SQL)
        return await self._read_verified_history()

    async def up(self, target: int | None = None) -> tuple[int, ...]:
        selected_target = self._validated_target(
            target,
            default=len(self._migrations),
        )
        applied_versions: list[int] = []
        async with self._connection.transaction():
            applied = await self._prepare()
            if any(version > selected_target for version in applied):
                raise ValueError("migration target precedes the current database version")
            for migration in self._migrations:
                if migration.version > selected_target:
                    break
                if migration.version in applied:
                    continue
                await self._connection.execute(migration.up_sql)
                await self._connection.execute(
                    _INSERT_HISTORY_SQL,
                    migration.version,
                    migration.name,
                    migration.checksum,
                )
                applied_versions.append(migration.version)
        return tuple(applied_versions)

    async def down(self, target: int = 0) -> tuple[int, ...]:
        selected_target = self._validated_target(target, default=0)
        reverted_versions: list[int] = []
        async with self._connection.transaction():
            applied = await self._prepare()
            for version in sorted(applied, reverse=True):
                if version <= selected_target:
                    continue
                migration = applied[version]
                await self._connection.execute(migration.down_sql)
                await self._connection.execute(_DELETE_HISTORY_SQL, version)
                reverted_versions.append(version)
        return tuple(reverted_versions)
