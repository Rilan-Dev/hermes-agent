from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class PluginInventoryError(ValueError):
    pass


@dataclass(frozen=True)
class PluginRecord:
    key: str
    name: str
    kind: str
    version: str
    description: str
    manifest_path: str
    module_path: str


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PluginInventoryError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_text(value: object, field: str) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    raise PluginInventoryError(f"{field} must be a scalar value")


def _load_manifest(path: Path) -> Mapping[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PluginInventoryError(f"unable to read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise PluginInventoryError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise PluginInventoryError(f"plugin manifest must be a mapping: {path}")
    return raw


def _manifest_paths(root: Path) -> tuple[Path, ...]:
    by_directory: dict[Path, Path] = {}
    for pattern in ("plugin.yaml", "plugin.yml"):
        for path in root.rglob(pattern):
            existing = by_directory.get(path.parent)
            if existing is not None and existing != path:
                raise PluginInventoryError(
                    f"multiple plugin manifests in {path.parent}"
                )
            by_directory[path.parent] = path
    return tuple(sorted(by_directory.values()))


def inventory_plugins(
    repo_root: Path, roots: tuple[str, ...]
) -> tuple[PluginRecord, ...]:
    repository = repo_root.resolve()
    records: list[PluginRecord] = []
    seen_manifest_paths: set[str] = set()

    for root_text in roots:
        root = repository / root_text
        if not root.is_dir():
            raise PluginInventoryError(f"missing plugin root: {root_text}")

        for manifest_path in _manifest_paths(root):
            relative_manifest = manifest_path.relative_to(repository).as_posix()
            if relative_manifest in seen_manifest_paths:
                continue
            seen_manifest_paths.add(relative_manifest)

            data = _load_manifest(manifest_path)
            plugin_dir = manifest_path.parent
            module_path = (plugin_dir / "__init__.py").relative_to(
                repository
            ).as_posix()
            records.append(
                PluginRecord(
                    key=plugin_dir.relative_to(root).as_posix(),
                    name=_required_text(data.get("name"), f"{relative_manifest}.name"),
                    kind=_required_text(data.get("kind"), f"{relative_manifest}.kind"),
                    version=_optional_text(
                        data.get("version"), f"{relative_manifest}.version"
                    ),
                    description=_optional_text(
                        data.get("description"), f"{relative_manifest}.description"
                    ),
                    manifest_path=relative_manifest,
                    module_path=module_path,
                )
            )

    return tuple(sorted(records, key=lambda item: (item.kind, item.key, item.name)))
