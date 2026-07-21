from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from scripts.extraction.schema import ExtractionManifest


class InventoryError(ValueError):
    pass


@dataclass(frozen=True)
class FileRecord:
    source: str
    destination: str
    classification: str
    reason: str
    sha256: str
    size_bytes: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_generated_python_cache(path: Path, source_root: Path) -> bool:
    relative = path.relative_to(source_root)
    return "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}


def _file_record(
    *,
    repo_root: Path,
    path: Path,
    destination: str,
    classification: str,
    reason: str,
) -> FileRecord:
    return FileRecord(
        source=path.relative_to(repo_root).as_posix(),
        destination=destination,
        classification=classification,
        reason=reason,
        sha256=_sha256(path),
        size_bytes=path.stat().st_size,
    )


def _add_record(
    records_by_source: dict[str, FileRecord],
    sources_by_destination: dict[str, str],
    record: FileRecord,
) -> None:
    existing = records_by_source.get(record.source)
    if existing is not None:
        if existing != record:
            raise InventoryError(
                f"conflicting rules for {record.source}: "
                f"{existing.destination} and {record.destination}"
            )
        return

    destination_source = sources_by_destination.get(record.destination)
    if destination_source is not None and destination_source != record.source:
        raise InventoryError(
            f"destination collision for {record.destination}: "
            f"{destination_source} and {record.source}"
        )

    records_by_source[record.source] = record
    sources_by_destination[record.destination] = record.source


def inventory_files(
    repo_root: Path, manifest: ExtractionManifest
) -> tuple[FileRecord, ...]:
    root = repo_root.resolve()
    records_by_source: dict[str, FileRecord] = {}
    sources_by_destination: dict[str, str] = {}

    for rule in manifest.dynamic_roots:
        source_root = root / rule.path
        if not source_root.is_dir():
            raise InventoryError(f"missing dynamic root: {rule.path}")

        for path in sorted(
            candidate
            for candidate in source_root.rglob("*")
            if candidate.is_file()
            and not _is_generated_python_cache(candidate, source_root)
        ):
            relative = path.relative_to(source_root).as_posix()
            destination = PurePosixPath(rule.destination, relative).as_posix()
            _add_record(
                records_by_source,
                sources_by_destination,
                _file_record(
                    repo_root=root,
                    path=path,
                    destination=destination,
                    classification=rule.classification.value,
                    reason=rule.reason,
                ),
            )

    for rule in manifest.explicit_files:
        path = root / rule.path
        if not path.is_file():
            raise InventoryError(f"missing explicit file: {rule.path}")
        _add_record(
            records_by_source,
            sources_by_destination,
            _file_record(
                repo_root=root,
                path=path,
                destination=rule.destination,
                classification=rule.classification.value,
                reason=rule.reason,
            ),
        )

    return tuple(
        records_by_source[source] for source in sorted(records_by_source)
    )
