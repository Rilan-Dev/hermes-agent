from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from scripts.extraction.filesystem_inventory import inventory_files
from scripts.extraction.import_inventory import inventory_imports
from scripts.extraction.manifest import load_manifest
from scripts.extraction.plugin_inventory import inventory_plugins
from scripts.extraction.render_report import (
    render_inventory_markdown,
    render_test_matrix,
)


class SourceGuardError(RuntimeError):
    pass


def _git(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        stderr = getattr(exc, "stderr", "") or ""
        raise SourceGuardError(
            f"git {' '.join(args)} failed: {stderr.strip() or exc}"
        ) from exc


def _scoped_paths(manifest: object) -> list[str]:
    dynamic_roots = getattr(manifest, "dynamic_roots", ())
    explicit_files = getattr(manifest, "explicit_files", ())
    return sorted(
        {rule.path for rule in dynamic_roots}
        | {rule.path for rule in explicit_files}
    )


def verify_source_guard(repo_root: Path, manifest_path: Path) -> None:
    repository = repo_root.resolve()
    manifest = load_manifest(manifest_path)
    source_sha = manifest.source_sha

    _git(repository, "cat-file", "-e", f"{source_sha}^{{commit}}")
    try:
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", source_sha, "HEAD"],
            cwd=repository,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SourceGuardError(
            f"source SHA {source_sha} is not an ancestor of HEAD"
        ) from exc

    scoped_paths = _scoped_paths(manifest)
    if not scoped_paths:
        raise SourceGuardError("manifest contains no scoped source paths")
    changed = _git(
        repository,
        "diff",
        "--name-only",
        source_sha,
        "--",
        *scoped_paths,
    )
    if changed:
        raise SourceGuardError(
            "scoped production source differs from the approved baseline:\n"
            + changed
        )


def _read_registry_snapshot(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"unable to read registry snapshot {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid registry snapshot {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("registry snapshot must contain a JSON object")
    return value


def _registry_section(snapshot: dict[str, Any]) -> dict[str, object]:
    return {
        "platform_entries": list(snapshot.get("platform_registry", [])),
        "platform_concrete": list(snapshot.get("platform_concrete", [])),
        "platform_deferred": list(snapshot.get("platform_deferred", [])),
        "platform_concrete_metadata": list(
            snapshot.get("platform_concrete_metadata", [])
        ),
        "provider_profiles": list(snapshot.get("provider_profiles", [])),
        "canonical_providers": list(snapshot.get("canonical_providers", [])),
        "auth_providers": list(snapshot.get("auth_providers", [])),
        "auth_provider_metadata": list(
            snapshot.get("auth_provider_metadata", [])
        ),
        "provider_catalog": list(snapshot.get("provider_catalog", [])),
    }


def build_inventory(
    repo_root: Path,
    manifest_path: Path,
    registry_snapshot_path: Path,
    *,
    verify_source: bool = True,
) -> dict[str, object]:
    repository = repo_root.resolve()
    manifest_file = manifest_path.resolve()
    snapshot_file = registry_snapshot_path.resolve()
    manifest = load_manifest(manifest_file)

    if verify_source:
        verify_source_guard(repository, manifest_file)

    files = inventory_files(repository, manifest)
    imports = inventory_imports(
        repository, files, manifest.internal_module_roots
    )
    imports_by_source = {item.source: item for item in imports}

    plugin_roots = tuple(
        rule.path
        for rule in manifest.dynamic_roots
        if rule.path in {"plugins/platforms", "plugins/model-providers"}
    )
    plugins = inventory_plugins(repository, plugin_roots)
    snapshot = _read_registry_snapshot(snapshot_file)

    file_rows: list[dict[str, object]] = []
    out_of_scope_imports: list[dict[str, str]] = []
    unresolved_imports: list[dict[str, str]] = []
    for file_record in files:
        import_record = imports_by_source[file_record.source]
        row = asdict(file_record)
        row.update(
            {
                "imports_in_scope": list(import_record.imports_in_scope),
                "imports_out_of_scope": list(
                    import_record.imports_out_of_scope
                ),
                "external_imports": list(import_record.external_imports),
            }
        )
        file_rows.append(row)
        out_of_scope_imports.extend(
            {
                "source": file_record.source,
                "dependency": dependency,
            }
            for dependency in import_record.imports_out_of_scope
        )
        unresolved_imports.extend(
            {"source": file_record.source, "import": name}
            for name in import_record.unresolved_internal
        )

    platform_plugins = [
        asdict(item) for item in plugins if item.kind == "platform"
    ]
    provider_plugins = [
        asdict(item) for item in plugins if item.kind == "model-provider"
    ]

    return {
        "schema_version": 1,
        "source_repository": manifest.source_repository,
        "source_sha": manifest.source_sha,
        "inventory_head": _git(repository, "rev-parse", "HEAD"),
        "files": file_rows,
        "plugins": {
            "platforms": platform_plugins,
            "model_providers": provider_plugins,
        },
        "registries": _registry_section(snapshot),
        "out_of_scope_imports": sorted(
            out_of_scope_imports,
            key=lambda row: (row["source"], row["dependency"]),
        ),
        "unresolved_imports": sorted(
            unresolved_imports,
            key=lambda row: (row["source"], row["import"]),
        ),
        "test_rules": [asdict(rule) for rule in manifest.test_rules],
    }


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_inventory_outputs(
    data: dict[str, object],
    *,
    yaml_path: Path,
    markdown_path: Path,
    test_matrix_path: Path,
) -> None:
    _write_text(
        yaml_path,
        yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=True,
            width=120,
        ),
    )
    _write_text(markdown_path, render_inventory_markdown(data))
    _write_text(test_matrix_path, render_test_matrix(data["test_rules"]))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build deterministic Phase 1 extraction inventory reports."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("extracted/hermes-connect-kit/extraction-manifest.yaml"),
    )
    parser.add_argument(
        "--registry-snapshot",
        type=Path,
        default=Path("tests/extraction/snapshots/registry-snapshot.json"),
    )
    parser.add_argument(
        "--yaml",
        dest="yaml_path",
        type=Path,
        default=Path("docs/extraction/generated/phase-1-inventory.yaml"),
    )
    parser.add_argument(
        "--markdown",
        dest="markdown_path",
        type=Path,
        default=Path("docs/extraction/generated/phase-1-inventory.md"),
    )
    parser.add_argument(
        "--test-matrix",
        type=Path,
        default=Path("docs/extraction/generated/phase-1-test-matrix.md"),
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    data = build_inventory(
        Path.cwd(),
        args.manifest,
        args.registry_snapshot,
    )
    write_inventory_outputs(
        data,
        yaml_path=args.yaml_path,
        markdown_path=args.markdown_path,
        test_matrix_path=args.test_matrix,
    )


if __name__ == "__main__":
    main()
