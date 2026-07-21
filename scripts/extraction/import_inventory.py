from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path

from scripts.extraction.filesystem_inventory import FileRecord

_EXCLUDED_INDEX_DIRS = frozenset(
    {".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", ".worktrees", "__pycache__", "node_modules", "venv"}
)


class ImportInventoryError(ValueError):
    pass


@dataclass(frozen=True)
class ImportRecord:
    source: str
    imports_in_scope: tuple[str, ...]
    imports_out_of_scope: tuple[str, ...]
    external_imports: tuple[str, ...]
    unresolved_internal: tuple[str, ...]


def _module_name(path: Path, repo_root: Path) -> str:
    relative = path.relative_to(repo_root)
    parts = list(relative.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _module_index(repo_root: Path) -> dict[str, str]:
    index: dict[str, str] = {}
    for directory, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = sorted(
            name for name in dirnames if name not in _EXCLUDED_INDEX_DIRS
        )
        base = Path(directory)
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            path = base / filename
            module = _module_name(path, repo_root)
            if not module:
                continue
            relative = path.relative_to(repo_root).as_posix()
            existing = index.get(module)
            if existing is not None and existing != relative:
                raise ImportInventoryError(
                    f"module {module} resolves to both {existing} and {relative}"
                )
            index[module] = relative
    return index


def _current_package(source: str, module_index: dict[str, str]) -> str:
    reverse_index = {path: module for module, path in module_index.items()}
    module = reverse_index.get(source, "")
    if source.endswith("/__init__.py") or source == "__init__.py":
        return module
    return module.rpartition(".")[0]


def _absolute_from_module(
    current_package: str, module: str | None, level: int
) -> str | None:
    if level == 0:
        return module or None

    package_parts = current_package.split(".") if current_package else []
    ascend = level - 1
    if ascend > len(package_parts):
        return None
    if ascend:
        package_parts = package_parts[:-ascend]
    if module:
        package_parts.extend(module.split("."))
    return ".".join(package_parts) or None


def _classify_module(
    module: str,
    *,
    module_index: dict[str, str],
    scoped_sources: set[str],
    internal_roots: set[str],
    in_scope: set[str],
    out_of_scope: set[str],
    external: set[str],
    unresolved: set[str],
) -> bool:
    resolved = module_index.get(module)
    if resolved is not None:
        if resolved in scoped_sources:
            in_scope.add(resolved)
        else:
            out_of_scope.add(resolved)
        return True

    root = module.split(".", 1)[0]
    if root in internal_roots:
        unresolved.add(module)
    else:
        external.add(root)
    return False


def _record_import_from(
    node: ast.ImportFrom,
    *,
    current_package: str,
    module_index: dict[str, str],
    scoped_sources: set[str],
    internal_roots: set[str],
    in_scope: set[str],
    out_of_scope: set[str],
    external: set[str],
    unresolved: set[str],
) -> None:
    base = _absolute_from_module(current_package, node.module, node.level)
    if base is None:
        unresolved.add(node.module or "." * node.level)
        return

    base_resolved = module_index.get(base)
    recorded_base = False
    for alias in node.names:
        if alias.name == "*":
            if not recorded_base:
                _classify_module(
                    base,
                    module_index=module_index,
                    scoped_sources=scoped_sources,
                    internal_roots=internal_roots,
                    in_scope=in_scope,
                    out_of_scope=out_of_scope,
                    external=external,
                    unresolved=unresolved,
                )
                recorded_base = True
            continue

        submodule = f"{base}.{alias.name}"
        if submodule in module_index:
            _classify_module(
                submodule,
                module_index=module_index,
                scoped_sources=scoped_sources,
                internal_roots=internal_roots,
                in_scope=in_scope,
                out_of_scope=out_of_scope,
                external=external,
                unresolved=unresolved,
            )
            continue

        if base_resolved is not None:
            if not recorded_base:
                _classify_module(
                    base,
                    module_index=module_index,
                    scoped_sources=scoped_sources,
                    internal_roots=internal_roots,
                    in_scope=in_scope,
                    out_of_scope=out_of_scope,
                    external=external,
                    unresolved=unresolved,
                )
                recorded_base = True
            continue

        _classify_module(
            base,
            module_index=module_index,
            scoped_sources=scoped_sources,
            internal_roots=internal_roots,
            in_scope=in_scope,
            out_of_scope=out_of_scope,
            external=external,
            unresolved=unresolved,
        )


def inventory_imports(
    repo_root: Path,
    files: tuple[FileRecord, ...],
    internal_roots: tuple[str, ...],
) -> tuple[ImportRecord, ...]:
    repository = repo_root.resolve()
    module_index = _module_index(repository)
    scoped_sources = {item.source for item in files}
    internal_root_set = set(internal_roots)
    records: list[ImportRecord] = []

    for item in sorted(files, key=lambda value: value.source):
        in_scope: set[str] = set()
        out_of_scope: set[str] = set()
        external: set[str] = set()
        unresolved: set[str] = set()

        if item.source.endswith(".py"):
            path = repository / item.source
            try:
                tree = ast.parse(
                    path.read_text(encoding="utf-8"), filename=item.source
                )
            except OSError as exc:
                raise ImportInventoryError(
                    f"unable to read Python source {item.source}: {exc}"
                ) from exc
            except SyntaxError as exc:
                raise ImportInventoryError(
                    f"unable to parse Python source {item.source}: {exc}"
                ) from exc

            current_package = _current_package(item.source, module_index)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        _classify_module(
                            alias.name,
                            module_index=module_index,
                            scoped_sources=scoped_sources,
                            internal_roots=internal_root_set,
                            in_scope=in_scope,
                            out_of_scope=out_of_scope,
                            external=external,
                            unresolved=unresolved,
                        )
                elif isinstance(node, ast.ImportFrom):
                    _record_import_from(
                        node,
                        current_package=current_package,
                        module_index=module_index,
                        scoped_sources=scoped_sources,
                        internal_roots=internal_root_set,
                        in_scope=in_scope,
                        out_of_scope=out_of_scope,
                        external=external,
                        unresolved=unresolved,
                    )

        in_scope.discard(item.source)
        out_of_scope.discard(item.source)
        records.append(
            ImportRecord(
                source=item.source,
                imports_in_scope=tuple(sorted(in_scope)),
                imports_out_of_scope=tuple(sorted(out_of_scope)),
                external_imports=tuple(sorted(external)),
                unresolved_internal=tuple(sorted(unresolved)),
            )
        )

    return tuple(records)
