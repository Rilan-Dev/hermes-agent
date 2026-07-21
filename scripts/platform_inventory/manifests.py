from __future__ import annotations

from pathlib import Path
from typing import Sequence

import yaml

from .models import InventoryError, PluginRecord


def _strings(value: object, *, field: str, manifest: Path) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(value)
    raise InventoryError(
        f"{manifest}: {field} must be a string or list of strings, "
        f"got {type(value).__name__}"
    )


def _env_names(value: object, *, field: str, manifest: Path) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise InventoryError(f"{manifest}: {field} must be a list")

    names: list[str] = []
    for item in value:
        if isinstance(item, str):
            name = item.strip()
        elif isinstance(item, dict):
            name = str(item.get("name") or "").strip()
        else:
            raise InventoryError(
                f"{manifest}: {field} entries must be strings or mappings"
            )
        if not name:
            raise InventoryError(f"{manifest}: {field} entry missing name")
        names.append(name)
    return tuple(sorted(set(names)))


def _plugin_key(repository: Path, scan_root: Path, directory: Path) -> str:
    relative_to_repository = directory.relative_to(repository)
    parts = relative_to_repository.parts
    if "plugins" in parts:
        index = parts.index("plugins")
        suffix = parts[index + 1 :]
        if suffix:
            return Path(*suffix).as_posix()
    return directory.relative_to(scan_root).as_posix()


def discover_plugins(root: Path, roots: Sequence[Path]) -> list[PluginRecord]:
    repository = root.resolve()
    records: list[PluginRecord] = []
    seen_manifests: set[Path] = set()

    for relative_root in roots:
        plugin_root = (repository / relative_root).resolve()
        if not plugin_root.exists():
            continue
        for manifest in sorted(plugin_root.rglob("plugin.yaml")):
            if manifest in seen_manifests:
                continue
            seen_manifests.add(manifest)
            try:
                payload = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError as exc:
                raise InventoryError(f"{manifest}: invalid YAML: {exc}") from exc
            if not isinstance(payload, dict):
                raise InventoryError(f"{manifest}: manifest must be a mapping")

            kind = str(payload.get("kind") or "").strip()
            if not kind:
                raise InventoryError(f"{manifest}: missing kind")

            plugin_id = manifest.parent.name
            plugin_key = _plugin_key(repository, plugin_root, manifest.parent)
            parent_key = plugin_key.rpartition("/")[0]
            category = parent_key or None
            manifest_name = str(payload.get("name") or plugin_id).strip()
            if not manifest_name:
                raise InventoryError(f"{manifest}: missing plugin name")

            label_value = payload.get("label")
            version_value = payload.get("version")
            description_value = payload.get("description")
            label = str(label_value).strip() if label_value is not None else None
            version = str(version_value).strip() if version_value is not None else None
            description = (
                str(description_value).strip() if description_value is not None else None
            )

            entrypoints = _strings(
                payload.get("entrypoints") or payload.get("entrypoint"),
                field="entrypoints",
                manifest=manifest,
            )
            optional_dependencies = _strings(
                payload.get("optional_dependencies") or payload.get("dependencies"),
                field="optional_dependencies",
                manifest=manifest,
            )
            provides_tools = _strings(
                payload.get("provides_tools"), field="provides_tools", manifest=manifest
            )
            provides_hooks = _strings(
                payload.get("provides_hooks"), field="provides_hooks", manifest=manifest
            )
            required_env = _env_names(
                payload.get("requires_env"), field="requires_env", manifest=manifest
            )
            optional_env = _env_names(
                payload.get("optional_env"), field="optional_env", manifest=manifest
            )
            files = tuple(
                sorted(
                    path.relative_to(repository).as_posix()
                    for path in manifest.parent.rglob("*")
                    if path.is_file() and "__pycache__" not in path.parts
                )
            )
            records.append(
                PluginRecord(
                    kind=kind,
                    plugin_id=plugin_id,
                    plugin_key=plugin_key,
                    category=category,
                    manifest_name=manifest_name,
                    label=label or None,
                    version=version or None,
                    description=description or None,
                    manifest_path=manifest.relative_to(repository).as_posix(),
                    directory=manifest.parent.relative_to(repository).as_posix(),
                    entrypoints=entrypoints,
                    required_env=required_env,
                    optional_env=optional_env,
                    optional_dependencies=optional_dependencies,
                    provides_tools=provides_tools,
                    provides_hooks=provides_hooks,
                    files=files,
                )
            )

    return sorted(
        records,
        key=lambda record: (record.kind, record.plugin_key, record.manifest_path),
    )
