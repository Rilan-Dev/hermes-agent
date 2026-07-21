# Agentic Platform Phase 0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, machine-generated inventory of Hermes channels, AI providers, tools, frontend/API surfaces, dependencies, tests, and source provenance so Phase 1 can be designed and implemented without guessing.

**Architecture:** Add a standalone, standard-library-first inventory package under `scripts/platform_inventory/`. It scans the checked-out repository, parses manifests and source files, probes dynamic registries in an isolated subprocess, and emits JSON, YAML, and Markdown review artifacts under `generated/platform_inventory/`. It does not move, delete, or refactor production code.

**Tech Stack:** Python 3.11–3.13, dataclasses, pathlib, ast, subprocess, hashlib, json, PyYAML 6.0.3, pytest 9.0.2.

## Global Constraints

- Work only on `worktree/agentic-platform-phase-0` or its verified local worktree.
- Do not delete, move, or modify existing production runtime files in Phase 0.
- Do not add runtime dependencies; use Python standard library plus existing `pyyaml`.
- Discover plugin membership from manifests/directories and runtime registries, never a fixed channel/provider list.
- Treat provider profile IDs, auth IDs, model-catalog IDs, aliases, runtime IDs, and transport families as distinct sets.
- Treat built-in, plugin, dynamic toolset, and MCP registration paths as distinct sets.
- Record exact source commit, branch, dirty state, file hash, and origin path.
- Run runtime probes in an isolated subprocess with a temporary `HERMES_HOME`.
- Fail closed on malformed manifests, unresolved local imports, registry-probe failures, or output-schema violations.
- Generated output must be deterministic: sorted keys, sorted records, UTF-8, and no timestamps except an explicitly supplied `--generated-at` value.
- Phase 0 must not require configured provider credentials or live messaging connections.
- Every task follows test-driven development and ends in a focused commit.

---

## File structure

```text
scripts/platform_inventory/
├── __init__.py                 # Package exports and schema version
├── __main__.py                 # `python -m scripts.platform_inventory`
├── cli.py                      # Command-line orchestration
├── models.py                   # Typed inventory records
├── source_state.py             # Git provenance and repository validation
├── manifests.py                # Plugin manifest discovery and parsing
├── python_graph.py             # Python import graph and dynamic import hints
├── runtime_probe.py            # Isolated registry probe launcher
├── probe_entrypoint.py         # Subprocess-side registry inspection
├── frontend_map.py             # React routes, API calls, Electron bridge mapping
├── dependencies.py             # Python/JS dependencies and test selection mapping
├── classify.py                 # Scope classification rules
└── reports.py                  # JSON/YAML/Markdown generation

tests/scripts/platform_inventory/
├── __init__.py
├── test_source_state.py
├── test_manifests.py
├── test_python_graph.py
├── test_runtime_probe.py
├── test_frontend_map.py
├── test_dependencies.py
├── test_reports.py
└── test_cli.py

tests/fixtures/platform_inventory/
├── plugins/
├── python_graph/
├── frontend/
└── pyproject.toml

generated/platform_inventory/
├── source-state.json
├── inventory.json
├── extraction-manifest.yaml
├── channel-capabilities.md
├── provider-capabilities.md
├── tool-capabilities.md
├── frontend-api-map.md
├── dependency-test-map.md
└── phase-0-review.md
```

---

### Task 1: Source provenance and CLI skeleton

**Files:**
- Create: `scripts/platform_inventory/__init__.py`
- Create: `scripts/platform_inventory/__main__.py`
- Create: `scripts/platform_inventory/models.py`
- Create: `scripts/platform_inventory/source_state.py`
- Create: `scripts/platform_inventory/cli.py`
- Create: `tests/scripts/platform_inventory/__init__.py`
- Create: `tests/scripts/platform_inventory/test_source_state.py`
- Create: `tests/scripts/platform_inventory/test_cli.py`

**Interfaces:**
- Produces: `SourceState`, `InventoryError`, `read_source_state(root: Path) -> SourceState`, and `main(argv: Sequence[str] | None = None) -> int`.
- Later tasks consume `SourceState.root`, `SourceState.head_sha`, and the CLI output directory.

- [ ] **Step 1: Write failing source-state tests**

```python
from pathlib import Path

import pytest

from scripts.platform_inventory.source_state import InventoryError, read_source_state


def _git(repo: Path, *args: str) -> None:
    import subprocess

    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def test_read_source_state_reports_branch_head_and_clean_status(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "inventory@example.test")
    _git(repo, "config", "user.name", "Inventory Test")
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "initial")

    state = read_source_state(repo)

    assert state.branch == "main"
    assert len(state.head_sha) == 40
    assert state.dirty is False
    assert state.root == repo.resolve()


def test_read_source_state_marks_untracked_files_dirty(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "inventory@example.test")
    _git(repo, "config", "user.name", "Inventory Test")
    (repo / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "initial")
    (repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")

    assert read_source_state(repo).dirty is True


def test_read_source_state_rejects_non_repository(tmp_path: Path) -> None:
    with pytest.raises(InventoryError, match="not a Git repository"):
        read_source_state(tmp_path)
```

- [ ] **Step 2: Run tests and verify collection/import failure**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_source_state.py -v
```

Expected: `ERROR` because `scripts.platform_inventory.source_state` does not exist.

- [ ] **Step 3: Implement typed models and Git provenance**

```python
# scripts/platform_inventory/models.py
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


class InventoryError(RuntimeError):
    """Raised when Phase 0 cannot produce a trustworthy inventory."""


@dataclass(frozen=True, slots=True)
class SourceState:
    root: Path
    branch: str
    head_sha: str
    dirty: bool
    remotes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["root"] = str(self.root)
        return data
```

```python
# scripts/platform_inventory/source_state.py
from __future__ import annotations

import subprocess
from pathlib import Path

from .models import InventoryError, SourceState


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise InventoryError(detail)
    return result.stdout.strip()


def read_source_state(root: Path) -> SourceState:
    root = root.resolve()
    try:
        repository_root = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
    except InventoryError as exc:
        raise InventoryError(f"{root} is not a Git repository") from exc

    branch = _git(repository_root, "branch", "--show-current") or "DETACHED"
    head_sha = _git(repository_root, "rev-parse", "HEAD")
    dirty = bool(_git(repository_root, "status", "--porcelain=v1", "--untracked-files=all"))
    remotes: dict[str, str] = {}
    for name in filter(None, _git(repository_root, "remote").splitlines()):
        remotes[name] = _git(repository_root, "remote", "get-url", name)
    return SourceState(repository_root, branch, head_sha, dirty, dict(sorted(remotes.items())))
```

- [ ] **Step 4: Add CLI parse and source-state output test**

```python
# tests/scripts/platform_inventory/test_cli.py
import json
from pathlib import Path

from scripts.platform_inventory.cli import main


def test_cli_writes_source_state_json(monkeypatch, tmp_path: Path) -> None:
    from scripts.platform_inventory.models import SourceState

    monkeypatch.setattr(
        "scripts.platform_inventory.cli.read_source_state",
        lambda root: SourceState(root.resolve(), "test", "a" * 40, False, {"origin": "example"}),
    )
    output = tmp_path / "generated"

    assert main(["--root", str(tmp_path), "--output", str(output), "source-state"]) == 0
    payload = json.loads((output / "source-state.json").read_text(encoding="utf-8"))
    assert payload["head_sha"] == "a" * 40
    assert payload["branch"] == "test"
```

```python
# scripts/platform_inventory/cli.py
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .source_state import read_source_state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="platform-inventory")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("generated/platform_inventory"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("source-state")
    subparsers.add_parser("generate")
    return parser


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    state = read_source_state(args.root)
    if args.command == "source-state":
        _write_json(args.output / "source-state.json", state.to_dict())
        return 0
    raise SystemExit("generate is added in Task 7")
```

```python
# scripts/platform_inventory/__init__.py
SCHEMA_VERSION = 1
```

```python
# scripts/platform_inventory/__main__.py
from .cli import main

raise SystemExit(main())
```

- [ ] **Step 5: Run Task 1 tests**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_source_state.py tests/scripts/platform_inventory/test_cli.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add scripts/platform_inventory tests/scripts/platform_inventory
git commit -m "feat(inventory): add source provenance CLI"
```

---

### Task 2: Dynamic plugin manifest inventory

**Files:**
- Modify: `scripts/platform_inventory/models.py`
- Create: `scripts/platform_inventory/manifests.py`
- Create: `tests/scripts/platform_inventory/test_manifests.py`
- Create fixtures under: `tests/fixtures/platform_inventory/plugins/`

**Interfaces:**
- Produces: `PluginRecord` and `discover_plugins(root: Path, roots: Sequence[Path]) -> list[PluginRecord]`.
- Later runtime and report tasks consume plugin `kind`, `plugin_id`, `manifest_path`, `directory`, `entrypoints`, and `files`.

- [ ] **Step 1: Add fixture manifests and failing tests**

```yaml
# tests/fixtures/platform_inventory/plugins/platforms/telegram/plugin.yaml
kind: platform
name: telegram
entrypoint: adapter:register
optional_dependencies:
  - python-telegram-bot
```

```yaml
# tests/fixtures/platform_inventory/plugins/model-providers/example/plugin.yaml
kind: model-provider
name: example
entrypoint: provider:register
```

```python
# tests/scripts/platform_inventory/test_manifests.py
from pathlib import Path

import pytest

from scripts.platform_inventory.manifests import discover_plugins
from scripts.platform_inventory.models import InventoryError


FIXTURE = Path("tests/fixtures/platform_inventory/plugins")


def test_discover_plugins_finds_all_manifest_children() -> None:
    records = discover_plugins(
        FIXTURE,
        [Path("platforms"), Path("model-providers")],
    )
    assert [(r.kind, r.plugin_id) for r in records] == [
        ("model-provider", "example"),
        ("platform", "telegram"),
    ]
    telegram = next(r for r in records if r.plugin_id == "telegram")
    assert telegram.entrypoints == ("adapter:register",)
    assert "platforms/telegram/plugin.yaml" in telegram.files


def test_discover_plugins_rejects_missing_kind(tmp_path: Path) -> None:
    plugin = tmp_path / "platforms" / "broken"
    plugin.mkdir(parents=True)
    (plugin / "plugin.yaml").write_text("name: broken\n", encoding="utf-8")
    with pytest.raises(InventoryError, match="missing kind"):
        discover_plugins(tmp_path, [Path("platforms")])
```

- [ ] **Step 2: Run and verify failure**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_manifests.py -v
```

Expected: import failure for `manifests` or `PluginRecord`.

- [ ] **Step 3: Implement manifest discovery**

```python
# add to scripts/platform_inventory/models.py
@dataclass(frozen=True, slots=True)
class PluginRecord:
    kind: str
    plugin_id: str
    manifest_path: str
    directory: str
    entrypoints: tuple[str, ...]
    optional_dependencies: tuple[str, ...]
    files: tuple[str, ...]
```

```python
# scripts/platform_inventory/manifests.py
from __future__ import annotations

from pathlib import Path
from typing import Sequence

import yaml

from .models import InventoryError, PluginRecord


def _strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(value)
    raise InventoryError(f"expected string or string list, got {type(value).__name__}")


def discover_plugins(root: Path, roots: Sequence[Path]) -> list[PluginRecord]:
    repository = root.resolve()
    records: list[PluginRecord] = []
    for relative_root in roots:
        plugin_root = repository / relative_root
        if not plugin_root.exists():
            continue
        for manifest in sorted(plugin_root.glob("*/plugin.yaml")):
            payload = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
            if not isinstance(payload, dict):
                raise InventoryError(f"{manifest}: manifest must be a mapping")
            kind = str(payload.get("kind") or "").strip()
            if not kind:
                raise InventoryError(f"{manifest}: missing kind")
            plugin_id = str(payload.get("name") or payload.get("id") or manifest.parent.name).strip()
            if not plugin_id:
                raise InventoryError(f"{manifest}: missing plugin identifier")
            entrypoints = _strings(payload.get("entrypoints") or payload.get("entrypoint"))
            optional_dependencies = _strings(
                payload.get("optional_dependencies") or payload.get("dependencies")
            )
            files = tuple(
                sorted(
                    path.relative_to(repository).as_posix()
                    for path in manifest.parent.rglob("*")
                    if path.is_file()
                )
            )
            records.append(
                PluginRecord(
                    kind=kind,
                    plugin_id=plugin_id,
                    manifest_path=manifest.relative_to(repository).as_posix(),
                    directory=manifest.parent.relative_to(repository).as_posix(),
                    entrypoints=entrypoints,
                    optional_dependencies=optional_dependencies,
                    files=files,
                )
            )
    return sorted(records, key=lambda record: (record.kind, record.plugin_id, record.manifest_path))
```

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_manifests.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/platform_inventory/models.py scripts/platform_inventory/manifests.py tests/scripts/platform_inventory/test_manifests.py tests/fixtures/platform_inventory/plugins
git commit -m "feat(inventory): discover platform and provider plugins"
```

---

### Task 3: File classification, hashing, and Python dependency graph

**Files:**
- Modify: `scripts/platform_inventory/models.py`
- Create: `scripts/platform_inventory/classify.py`
- Create: `scripts/platform_inventory/python_graph.py`
- Create: `tests/scripts/platform_inventory/test_python_graph.py`
- Create fixtures under: `tests/fixtures/platform_inventory/python_graph/`

**Interfaces:**
- Produces: `FileRecord`, `ImportEdge`, `scan_python_graph(root: Path, include_paths: Sequence[Path]) -> PythonGraph`.
- Reports unresolved local imports and dynamic import hints separately.

- [ ] **Step 1: Write failing graph tests**

```python
# tests/scripts/platform_inventory/test_python_graph.py
from pathlib import Path

from scripts.platform_inventory.python_graph import scan_python_graph


def test_scan_python_graph_resolves_local_imports_and_hashes(tmp_path: Path) -> None:
    package = tmp_path / "gateway"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "base.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "run.py").write_text(
        "from gateway.base import VALUE\nimport importlib\nimportlib.import_module('gateway.base')\n",
        encoding="utf-8",
    )

    graph = scan_python_graph(tmp_path, [Path("gateway")])

    assert [record.path for record in graph.files] == [
        "gateway/__init__.py",
        "gateway/base.py",
        "gateway/run.py",
    ]
    assert any(edge.source == "gateway/run.py" and edge.target == "gateway/base.py" for edge in graph.imports)
    assert graph.dynamic_imports == ("gateway/run.py:gateway.base",)
    assert graph.unresolved_local_imports == ()
    assert all(len(record.sha256) == 64 for record in graph.files)


def test_scan_python_graph_reports_missing_local_module(tmp_path: Path) -> None:
    package = tmp_path / "gateway"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "run.py").write_text("from gateway.missing import value\n", encoding="utf-8")

    graph = scan_python_graph(tmp_path, [Path("gateway")])

    assert graph.unresolved_local_imports == ("gateway/run.py:gateway.missing",)
```

- [ ] **Step 2: Run and verify failure**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_python_graph.py -v
```

Expected: import failure.

- [ ] **Step 3: Implement models and scanner**

```python
# add to scripts/platform_inventory/models.py
@dataclass(frozen=True, slots=True)
class FileRecord:
    path: str
    sha256: str
    size_bytes: int
    classification: str


@dataclass(frozen=True, slots=True)
class ImportEdge:
    source: str
    module: str
    target: str | None


@dataclass(frozen=True, slots=True)
class PythonGraph:
    files: tuple[FileRecord, ...]
    imports: tuple[ImportEdge, ...]
    dynamic_imports: tuple[str, ...]
    unresolved_local_imports: tuple[str, ...]
```

```python
# scripts/platform_inventory/classify.py
from pathlib import PurePosixPath


def classify_path(path: str) -> str:
    p = PurePosixPath(path)
    if path.startswith("tests/"):
        return "test"
    if path.startswith("apps/desktop/") or path.startswith("web/"):
        return "frontend"
    if path.startswith("plugins/platforms/") or path.startswith("plugins/model-providers/"):
        return "core-plugin"
    if path.startswith("gateway/") or path.startswith("providers/"):
        return "core"
    if path.startswith("tools/") or p.name in {"toolsets.py", "toolset_distributions.py"}:
        return "tool-runtime"
    return "support"
```

```python
# scripts/platform_inventory/python_graph.py
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Sequence

from .classify import classify_path
from .models import FileRecord, ImportEdge, PythonGraph


def _module_index(root: Path) -> dict[str, str]:
    index: dict[str, str] = {}
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        parts = list(relative.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        if parts:
            index[".".join(parts)] = relative.as_posix()
    return index


def _resolve(module: str, index: dict[str, str]) -> str | None:
    candidate = module
    while candidate:
        if candidate in index:
            return index[candidate]
        candidate = candidate.rpartition(".")[0]
    return None


def scan_python_graph(root: Path, include_paths: Sequence[Path]) -> PythonGraph:
    repository = root.resolve()
    index = _module_index(repository)
    selected: set[Path] = set()
    for relative in include_paths:
        absolute = repository / relative
        if absolute.is_file() and absolute.suffix == ".py":
            selected.add(absolute)
        elif absolute.is_dir():
            selected.update(path for path in absolute.rglob("*.py") if path.is_file())

    files: list[FileRecord] = []
    imports: list[ImportEdge] = []
    dynamic: set[str] = set()
    unresolved: set[str] = set()
    local_prefixes = {module.split(".", 1)[0] for module in index}

    for path in sorted(selected):
        relative = path.relative_to(repository).as_posix()
        content = path.read_bytes()
        files.append(
            FileRecord(relative, hashlib.sha256(content).hexdigest(), len(content), classify_path(relative))
        )
        tree = ast.parse(content.decode("utf-8"), filename=relative)
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                dynamic.add(f"{relative}:{node.args[0].value}")
        for module in sorted(modules):
            target = _resolve(module, index)
            imports.append(ImportEdge(relative, module, target))
            if target is None and module.split(".", 1)[0] in local_prefixes:
                unresolved.add(f"{relative}:{module}")

    return PythonGraph(
        files=tuple(sorted(files, key=lambda record: record.path)),
        imports=tuple(sorted(imports, key=lambda edge: (edge.source, edge.module))),
        dynamic_imports=tuple(sorted(dynamic)),
        unresolved_local_imports=tuple(sorted(unresolved)),
    )
```

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_python_graph.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/platform_inventory tests/scripts/platform_inventory/test_python_graph.py tests/fixtures/platform_inventory/python_graph
git commit -m "feat(inventory): map scoped Python dependencies"
```

---

### Task 4: Isolated runtime registry probe

**Files:**
- Modify: `scripts/platform_inventory/models.py`
- Create: `scripts/platform_inventory/runtime_probe.py`
- Create: `scripts/platform_inventory/probe_entrypoint.py`
- Create: `tests/scripts/platform_inventory/test_runtime_probe.py`

**Interfaces:**
- Produces: `RegistrySnapshot` and `probe_runtime(root: Path, timeout_seconds: float = 30) -> RegistrySnapshot`.
- Snapshot fields keep separate `platforms`, `provider_profiles`, `provider_aliases`, `auth_providers`, `canonical_providers`, `model_catalog_providers`, `transports`, `toolsets`, `tools`, and `probe_errors`.

- [ ] **Step 1: Write failing subprocess parsing tests**

```python
# tests/scripts/platform_inventory/test_runtime_probe.py
import json
from pathlib import Path

import pytest

from scripts.platform_inventory.models import InventoryError
from scripts.platform_inventory.runtime_probe import parse_probe_output, probe_runtime


def test_parse_probe_output_keeps_provider_identifier_sets_separate() -> None:
    payload = {
        "platforms": ["telegram"],
        "provider_profiles": ["openai-api"],
        "provider_aliases": {"openai": "openai-api"},
        "auth_providers": ["openai-api", "openai-codex"],
        "canonical_providers": ["openai-api"],
        "model_catalog_providers": ["openai"],
        "transports": ["chat_completions", "codex"],
        "toolsets": {"web": ["web_search"]},
        "tools": ["web_search"],
        "probe_errors": [],
    }
    snapshot = parse_probe_output(json.dumps(payload))
    assert snapshot.auth_providers == ("openai-api", "openai-codex")
    assert snapshot.model_catalog_providers == ("openai",)
    assert snapshot.provider_aliases == {"openai": "openai-api"}


def test_parse_probe_output_rejects_invalid_json() -> None:
    with pytest.raises(InventoryError, match="invalid runtime probe JSON"):
        parse_probe_output("not-json")


def test_probe_runtime_uses_isolated_home(monkeypatch, tmp_path: Path) -> None:
    observed = {}

    class Result:
        returncode = 0
        stdout = json.dumps({
            "platforms": [], "provider_profiles": [], "provider_aliases": {},
            "auth_providers": [], "canonical_providers": [],
            "model_catalog_providers": [], "transports": [],
            "toolsets": {}, "tools": [], "probe_errors": [],
        })
        stderr = ""

    def fake_run(command, **kwargs):
        observed.update(kwargs["env"])
        return Result()

    monkeypatch.setattr("scripts.platform_inventory.runtime_probe.subprocess.run", fake_run)
    probe_runtime(tmp_path)
    assert observed["HERMES_HOME"]
    assert observed["HERMES_PROFILE"] == "inventory"
    assert observed["PYTHONPATH"].split(__import__("os").pathsep)[0] == str(tmp_path.resolve())
```

- [ ] **Step 2: Run and verify failure**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_runtime_probe.py -v
```

Expected: import failure.

- [ ] **Step 3: Implement snapshot and launcher**

```python
# add to scripts/platform_inventory/models.py
@dataclass(frozen=True, slots=True)
class RegistrySnapshot:
    platforms: tuple[str, ...]
    provider_profiles: tuple[str, ...]
    provider_aliases: dict[str, str]
    auth_providers: tuple[str, ...]
    canonical_providers: tuple[str, ...]
    model_catalog_providers: tuple[str, ...]
    transports: tuple[str, ...]
    toolsets: dict[str, tuple[str, ...]]
    tools: tuple[str, ...]
    probe_errors: tuple[str, ...]
```

```python
# scripts/platform_inventory/runtime_probe.py
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .models import InventoryError, RegistrySnapshot


def parse_probe_output(stdout: str) -> RegistrySnapshot:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise InventoryError("invalid runtime probe JSON") from exc
    required = {
        "platforms", "provider_profiles", "provider_aliases", "auth_providers",
        "canonical_providers", "model_catalog_providers", "transports",
        "toolsets", "tools", "probe_errors",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise InventoryError(f"runtime probe missing keys: {', '.join(missing)}")
    return RegistrySnapshot(
        platforms=tuple(sorted(map(str, payload["platforms"]))),
        provider_profiles=tuple(sorted(map(str, payload["provider_profiles"]))),
        provider_aliases=dict(sorted((str(k), str(v)) for k, v in payload["provider_aliases"].items())),
        auth_providers=tuple(sorted(map(str, payload["auth_providers"]))),
        canonical_providers=tuple(sorted(map(str, payload["canonical_providers"]))),
        model_catalog_providers=tuple(sorted(map(str, payload["model_catalog_providers"]))),
        transports=tuple(sorted(map(str, payload["transports"]))),
        toolsets={str(k): tuple(sorted(map(str, v))) for k, v in sorted(payload["toolsets"].items())},
        tools=tuple(sorted(map(str, payload["tools"]))),
        probe_errors=tuple(sorted(map(str, payload["probe_errors"]))),
    )


def probe_runtime(root: Path, timeout_seconds: float = 30) -> RegistrySnapshot:
    repository = root.resolve()
    with tempfile.TemporaryDirectory(prefix="hermes-inventory-") as home:
        env = os.environ.copy()
        env.update({
            "HERMES_HOME": home,
            "HERMES_PROFILE": "inventory",
            "PYTHONPATH": os.pathsep.join([str(repository), env.get("PYTHONPATH", "")]).rstrip(os.pathsep),
            "HERMES_INVENTORY_MODE": "1",
        })
        result = subprocess.run(
            [sys.executable, "-m", "scripts.platform_inventory.probe_entrypoint"],
            cwd=repository,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    if result.returncode != 0:
        raise InventoryError(f"runtime probe failed: {result.stderr.strip() or result.stdout.strip()}")
    return parse_probe_output(result.stdout)
```

- [ ] **Step 4: Implement probe entrypoint with defensive introspection**

The entrypoint must import known registry modules and use small helper functions so a missing optional registry produces a named error rather than deleting the entire snapshot.

```python
# scripts/platform_inventory/probe_entrypoint.py
from __future__ import annotations

import json
from collections.abc import Mapping


def _keys(value: object) -> list[str]:
    if isinstance(value, Mapping):
        return sorted(map(str, value.keys()))
    return []


def main() -> int:
    payload = {
        "platforms": [],
        "provider_profiles": [],
        "provider_aliases": {},
        "auth_providers": [],
        "canonical_providers": [],
        "model_catalog_providers": [],
        "transports": [],
        "toolsets": {},
        "tools": [],
        "probe_errors": [],
    }
    try:
        from gateway.platform_registry import platform_registry
        payload["platforms"] = _keys(platform_registry)
    except Exception as exc:
        payload["probe_errors"].append(f"platform_registry:{type(exc).__name__}:{exc}")
    try:
        import providers
        payload["provider_profiles"] = sorted(getattr(providers, "list_providers")())
        payload["provider_aliases"] = dict(sorted(getattr(providers, "PROVIDER_ALIASES", {}).items()))
    except Exception as exc:
        payload["probe_errors"].append(f"providers:{type(exc).__name__}:{exc}")
    try:
        from hermes_cli.auth import PROVIDER_REGISTRY
        payload["auth_providers"] = _keys(PROVIDER_REGISTRY)
    except Exception as exc:
        payload["probe_errors"].append(f"auth:{type(exc).__name__}:{exc}")
    try:
        from hermes_cli.provider_catalog import provider_catalog
        payload["canonical_providers"] = sorted(str(item.slug) for item in provider_catalog())
    except Exception as exc:
        payload["probe_errors"].append(f"provider_catalog:{type(exc).__name__}:{exc}")
    try:
        from hermes_cli.models import MODEL_CATALOG
        payload["model_catalog_providers"] = _keys(MODEL_CATALOG)
    except Exception as exc:
        payload["probe_errors"].append(f"model_catalog:{type(exc).__name__}:{exc}")
    try:
        from agent.transports import list_transports
        payload["transports"] = sorted(map(str, list_transports()))
    except Exception as exc:
        payload["probe_errors"].append(f"transports:{type(exc).__name__}:{exc}")
    try:
        from toolsets import TOOLSETS, get_all_tools
        payload["toolsets"] = {
            str(name): sorted(map(str, config.get("tools", [])))
            for name, config in sorted(TOOLSETS.items())
        }
        payload["tools"] = sorted(map(str, get_all_tools()))
    except Exception as exc:
        payload["probe_errors"].append(f"toolsets:{type(exc).__name__}:{exc}")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

During implementation, inspect the actual exported names and adjust only the adapter code above; retain the output schema and tests.

- [ ] **Step 5: Run unit tests and real probe**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_runtime_probe.py -v
python -m scripts.platform_inventory.probe_entrypoint | python -m json.tool >/dev/null
```

Expected: tests pass and the real probe emits valid JSON. Probe errors are allowed in this step only if they are explicitly listed; Task 8 decides which errors block completion.

- [ ] **Step 6: Commit**

```bash
git add scripts/platform_inventory tests/scripts/platform_inventory/test_runtime_probe.py
git commit -m "feat(inventory): probe dynamic Hermes registries"
```

---

### Task 5: Frontend routes, API calls, and Electron dependency map

**Files:**
- Modify: `scripts/platform_inventory/models.py`
- Create: `scripts/platform_inventory/frontend_map.py`
- Create: `tests/scripts/platform_inventory/test_frontend_map.py`
- Create fixtures under: `tests/fixtures/platform_inventory/frontend/`

**Interfaces:**
- Produces: `FrontendMap` with routes, API paths, WebSocket paths, Electron bridge references, platform source IDs, and static provider/channel/tool lists.

- [ ] **Step 1: Write failing frontend scanner test**

```python
# tests/scripts/platform_inventory/test_frontend_map.py
from pathlib import Path

from scripts.platform_inventory.frontend_map import scan_frontend


def test_scan_frontend_maps_routes_api_and_electron_bridge(tmp_path: Path) -> None:
    web = tmp_path / "web" / "src"
    desktop = tmp_path / "apps" / "desktop" / "src"
    web.mkdir(parents=True)
    desktop.mkdir(parents=True)
    (web / "App.tsx").write_text(
        'const routes = {"/channels": ChannelsPage}; fetch("/api/messaging/platforms");\n',
        encoding="utf-8",
    )
    (desktop / "hermes.ts").write_text(
        'window.hermesDesktop?.terminal; new WebSocket("/ws/chat");\n',
        encoding="utf-8",
    )

    result = scan_frontend(tmp_path)

    assert result.routes == ("/channels",)
    assert result.api_paths == ("/api/messaging/platforms",)
    assert result.websocket_paths == ("/ws/chat",)
    assert result.electron_bridge_references == ("apps/desktop/src/hermes.ts:hermesDesktop",)
```

- [ ] **Step 2: Run and verify failure**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_frontend_map.py -v
```

Expected: import failure.

- [ ] **Step 3: Implement deterministic text/AST-oriented scanner**

Use regex only for literal route/API strings and explicit bridge symbols; record the source path for static-list findings so humans can distinguish authoritative backend catalogs from presentation overlays.

```python
# add to models.py
@dataclass(frozen=True, slots=True)
class FrontendMap:
    routes: tuple[str, ...]
    api_paths: tuple[str, ...]
    websocket_paths: tuple[str, ...]
    electron_bridge_references: tuple[str, ...]
    static_catalog_references: tuple[str, ...]
```

```python
# scripts/platform_inventory/frontend_map.py
from __future__ import annotations

import re
from pathlib import Path

from .models import FrontendMap

_ROUTE = re.compile(r"[\"'](/(?:[a-zA-Z0-9:_-]+/?)+)[\"']")
_API = re.compile(r"[\"'](/api/[a-zA-Z0-9_./{}:-]+)[\"']")
_WS = re.compile(r"[\"'](/ws/[a-zA-Z0-9_./{}:-]+)[\"']")
_STATIC_MARKERS = (
    "MESSAGING_SESSION_SOURCE_IDS",
    "SOURCE_LABELS",
    "CANONICAL_PROVIDERS",
    "MODEL_CATALOG_TOOLSETS",
    "PLATFORM_ICONS",
)


def scan_frontend(root: Path) -> FrontendMap:
    repository = root.resolve()
    files: list[Path] = []
    for relative in (Path("web/src"), Path("apps/desktop/src"), Path("apps/shared")):
        base = repository / relative
        if base.exists():
            files.extend(path for path in base.rglob("*") if path.suffix in {".ts", ".tsx", ".js", ".jsx"})
    routes: set[str] = set()
    api_paths: set[str] = set()
    websocket_paths: set[str] = set()
    electron: set[str] = set()
    static: set[str] = set()
    for path in sorted(set(files)):
        relative = path.relative_to(repository).as_posix()
        text = path.read_text(encoding="utf-8")
        routes.update(match for match in _ROUTE.findall(text) if not match.startswith(("/api/", "/ws/")))
        api_paths.update(_API.findall(text))
        websocket_paths.update(_WS.findall(text))
        if "hermesDesktop" in text:
            electron.add(f"{relative}:hermesDesktop")
        for marker in _STATIC_MARKERS:
            if marker in text:
                static.add(f"{relative}:{marker}")
    return FrontendMap(
        routes=tuple(sorted(routes)),
        api_paths=tuple(sorted(api_paths)),
        websocket_paths=tuple(sorted(websocket_paths)),
        electron_bridge_references=tuple(sorted(electron)),
        static_catalog_references=tuple(sorted(static)),
    )
```

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_frontend_map.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/platform_inventory/models.py scripts/platform_inventory/frontend_map.py tests/scripts/platform_inventory/test_frontend_map.py tests/fixtures/platform_inventory/frontend
git commit -m "feat(inventory): map web APIs and Electron coupling"
```

---

### Task 6: Dependency and test inventory

**Files:**
- Modify: `scripts/platform_inventory/models.py`
- Create: `scripts/platform_inventory/dependencies.py`
- Create: `tests/scripts/platform_inventory/test_dependencies.py`
- Create: `tests/fixtures/platform_inventory/pyproject.toml`

**Interfaces:**
- Produces: `DependencyMap` with core Python requirements, optional extras, JS packages by application, test files by subsystem, and inferred external imports.

- [ ] **Step 1: Write failing dependency tests**

```python
# tests/scripts/platform_inventory/test_dependencies.py
from pathlib import Path

from scripts.platform_inventory.dependencies import scan_dependencies


def test_scan_dependencies_keeps_optional_extras_and_tests_separate(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = ["fastapi==1.0.0"]
[project.optional-dependencies]
messaging = ["discord.py==2.0.0"]
""".strip() + "\n",
        encoding="utf-8",
    )
    tests = tmp_path / "tests" / "gateway"
    tests.mkdir(parents=True)
    (tests / "test_delivery.py").write_text("def test_ok(): pass\n", encoding="utf-8")

    result = scan_dependencies(tmp_path)

    assert result.python_core == ("fastapi==1.0.0",)
    assert result.python_extras == {"messaging": ("discord.py==2.0.0",)}
    assert result.tests_by_area == {"gateway": ("tests/gateway/test_delivery.py",)}
```

- [ ] **Step 2: Run and verify failure**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_dependencies.py -v
```

Expected: import failure.

- [ ] **Step 3: Implement dependency scanner**

Use `tomllib` for Python metadata and `json` for JavaScript package files. Test areas are grouped by the first path below `tests/`, with special groups for `apps/desktop` and `web` tests.

```python
# add to models.py
@dataclass(frozen=True, slots=True)
class DependencyMap:
    python_core: tuple[str, ...]
    python_extras: dict[str, tuple[str, ...]]
    javascript_packages: dict[str, tuple[str, ...]]
    tests_by_area: dict[str, tuple[str, ...]]
```

```python
# scripts/platform_inventory/dependencies.py
from __future__ import annotations

import json
import tomllib
from pathlib import Path

from .models import DependencyMap


def scan_dependencies(root: Path) -> DependencyMap:
    repository = root.resolve()
    pyproject = tomllib.loads((repository / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject.get("project", {})
    core = tuple(sorted(map(str, project.get("dependencies", []))))
    extras = {
        str(name): tuple(sorted(map(str, values)))
        for name, values in sorted(project.get("optional-dependencies", {}).items())
    }
    javascript: dict[str, tuple[str, ...]] = {}
    for relative in (Path("web/package.json"), Path("apps/desktop/package.json"), Path("apps/shared/package.json")):
        path = repository / relative
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        names = set(payload.get("dependencies", {})) | set(payload.get("devDependencies", {}))
        javascript[relative.parent.as_posix()] = tuple(sorted(map(str, names)))
    tests: dict[str, list[str]] = {}
    test_root = repository / "tests"
    if test_root.exists():
        for path in sorted(test_root.rglob("test_*.py")):
            relative = path.relative_to(repository).as_posix()
            parts = path.relative_to(test_root).parts
            area = parts[0] if len(parts) > 1 else "root"
            tests.setdefault(area, []).append(relative)
    for base, area in ((repository / "apps/desktop", "desktop"), (repository / "web", "web")):
        if base.exists():
            for path in sorted(base.rglob("*.test.*")):
                tests.setdefault(area, []).append(path.relative_to(repository).as_posix())
            for path in sorted((base / "e2e").glob("*.spec.*")) if (base / "e2e").exists() else []:
                tests.setdefault(area, []).append(path.relative_to(repository).as_posix())
    return DependencyMap(
        python_core=core,
        python_extras=extras,
        javascript_packages=dict(sorted(javascript.items())),
        tests_by_area={name: tuple(sorted(paths)) for name, paths in sorted(tests.items())},
    )
```

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_dependencies.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/platform_inventory/models.py scripts/platform_inventory/dependencies.py tests/scripts/platform_inventory/test_dependencies.py tests/fixtures/platform_inventory/pyproject.toml
git commit -m "feat(inventory): map dependencies and subsystem tests"
```

---

### Task 7: Deterministic reports and complete generate command

**Files:**
- Modify: `scripts/platform_inventory/models.py`
- Modify: `scripts/platform_inventory/cli.py`
- Create: `scripts/platform_inventory/reports.py`
- Create: `tests/scripts/platform_inventory/test_reports.py`
- Modify: `tests/scripts/platform_inventory/test_cli.py`

**Interfaces:**
- Produces: `InventoryReport`, `build_inventory(root: Path) -> InventoryReport`, and `write_reports(report: InventoryReport, output: Path) -> tuple[Path, ...]`.
- CLI command: `python -m scripts.platform_inventory --root . --output generated/platform_inventory generate`.

- [ ] **Step 1: Write failing deterministic report test**

```python
# tests/scripts/platform_inventory/test_reports.py
import json
from pathlib import Path

from scripts.platform_inventory.models import (
    DependencyMap,
    FrontendMap,
    InventoryReport,
    PythonGraph,
    RegistrySnapshot,
    SourceState,
)
from scripts.platform_inventory.reports import write_reports


def test_write_reports_is_deterministic_and_creates_review_files(tmp_path: Path) -> None:
    report = InventoryReport(
        schema_version=1,
        source=SourceState(tmp_path, "main", "a" * 40, False, {}),
        plugins=(),
        python_graph=PythonGraph((), (), (), ()),
        registries=RegistrySnapshot((), (), {}, (), (), (), (), {}, (), ()),
        frontend=FrontendMap((), (), (), (), ()),
        dependencies=DependencyMap((), {}, {}, {}),
    )

    paths = write_reports(report, tmp_path / "out")

    assert {path.name for path in paths} == {
        "source-state.json",
        "inventory.json",
        "extraction-manifest.yaml",
        "channel-capabilities.md",
        "provider-capabilities.md",
        "tool-capabilities.md",
        "frontend-api-map.md",
        "dependency-test-map.md",
        "phase-0-review.md",
    }
    payload = json.loads((tmp_path / "out" / "inventory.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["source"]["head_sha"] == "a" * 40
```

- [ ] **Step 2: Run and verify failure**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_reports.py -v
```

Expected: `InventoryReport` or `reports` import failure.

- [ ] **Step 3: Add report aggregate and serializer**

```python
# add to models.py
@dataclass(frozen=True, slots=True)
class InventoryReport:
    schema_version: int
    source: SourceState
    plugins: tuple[PluginRecord, ...]
    python_graph: PythonGraph
    registries: RegistrySnapshot
    frontend: FrontendMap
    dependencies: DependencyMap
```

`reports.py` must:

1. Convert dataclasses, tuples, sets and paths into deterministic primitive values.
2. Write complete `inventory.json`.
3. Write a draft `extraction-manifest.yaml` with source SHA, recursive roots, explicit load-bearing files, discovered plugins, unresolved imports, and host-port candidates.
4. Render separate Markdown matrices for channels, providers, tools, frontend/API coupling and dependency/tests.
5. Render `phase-0-review.md` with blocking findings first.

Core serializer:

```python
# scripts/platform_inventory/reports.py
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import yaml

from .models import InventoryReport


def _primitive(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {field.name: _primitive(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _primitive(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_primitive(item) for item in value]
    return value


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path


def write_reports(report: InventoryReport, output: Path) -> tuple[Path, ...]:
    payload = _primitive(report)
    paths = [
        _write(output / "source-state.json", json.dumps(payload["source"], indent=2, sort_keys=True)),
        _write(output / "inventory.json", json.dumps(payload, indent=2, sort_keys=True)),
        _write(output / "extraction-manifest.yaml", yaml.safe_dump(_manifest(payload), sort_keys=True)),
        _write(output / "channel-capabilities.md", _channel_markdown(payload)),
        _write(output / "provider-capabilities.md", _provider_markdown(payload)),
        _write(output / "tool-capabilities.md", _tool_markdown(payload)),
        _write(output / "frontend-api-map.md", _frontend_markdown(payload)),
        _write(output / "dependency-test-map.md", _dependency_markdown(payload)),
        _write(output / "phase-0-review.md", _review_markdown(payload)),
    ]
    return tuple(paths)
```

Implement `_manifest` and Markdown functions with explicit headings and tables. Do not hide empty or failed sections; render `None discovered` or blocking errors.

- [ ] **Step 4: Wire complete inventory orchestration into CLI**

Add fixed initial include roots:

```python
PLUGIN_ROOTS = (Path("plugins/platforms"), Path("plugins/model-providers"))
PYTHON_ROOTS = (
    Path("gateway"),
    Path("providers"),
    Path("hermes_cli"),
    Path("agent/transports"),
    Path("tools"),
    Path("toolsets.py"),
    Path("toolset_distributions.py"),
    Path("cron"),
)
```

`build_inventory()` combines `read_source_state`, `discover_plugins`, `scan_python_graph`, `probe_runtime`, `scan_frontend`, and `scan_dependencies`. `main(... generate)` writes all reports and returns `2` when the source is dirty, runtime probe errors exist, or unresolved local imports exist; otherwise `0`.

- [ ] **Step 5: Add CLI integration test**

Mock each scanner and assert `generate` creates all nine files and returns `0`. Add a second test where `probe_errors=("provider_catalog:ImportError",)` and assert return code `2` while reports are still written.

- [ ] **Step 6: Run Task 7 tests**

Run:

```bash
python -m pytest tests/scripts/platform_inventory/test_reports.py tests/scripts/platform_inventory/test_cli.py -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add scripts/platform_inventory tests/scripts/platform_inventory
git commit -m "feat(inventory): generate Phase 0 review artifacts"
```

---

### Task 8: Execute against Hermes, resolve probe mismatches, and commit generated inventory

**Files:**
- Modify only if required by real findings: `scripts/platform_inventory/probe_entrypoint.py`
- Modify only if required by real findings: `scripts/platform_inventory/classify.py`
- Create/update: `generated/platform_inventory/*`
- Create: `docs/platform/phase-0-findings.md`
- Modify: `docs/extraction/02-source-and-test-inventory.md` only when generated evidence proves a correction is required.

**Interfaces:**
- Produces the reviewed source of truth for the Phase 1 plan.

- [ ] **Step 1: Run all inventory tests**

```bash
python -m pytest tests/scripts/platform_inventory -v
```

Expected: all tests pass.

- [ ] **Step 2: Run repository quality checks for new Python code**

```bash
python -m ruff check scripts/platform_inventory tests/scripts/platform_inventory
python -m ruff format --check scripts/platform_inventory tests/scripts/platform_inventory
```

Expected: both commands exit `0`.

- [ ] **Step 3: Verify clean worktree before generation**

```bash
git status --short
```

Expected: no output. If generated files are intentionally already tracked from a previous run, restore them before the authoritative run.

- [ ] **Step 4: Generate the real inventory**

```bash
python -m scripts.platform_inventory \
  --root . \
  --output generated/platform_inventory \
  generate
```

Expected: exit `0`. Exit `2` is a blocking finding, not a reason to suppress the error.

- [ ] **Step 5: Review blocking findings**

```bash
cat generated/platform_inventory/phase-0-review.md
python - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("generated/platform_inventory/inventory.json").read_text())
print("platforms", len(payload["registries"]["platforms"]))
print("provider profiles", len(payload["registries"]["provider_profiles"]))
print("auth providers", len(payload["registries"]["auth_providers"]))
print("tools", len(payload["registries"]["tools"]))
print("probe errors", payload["registries"]["probe_errors"])
print("unresolved", payload["python_graph"]["unresolved_local_imports"])
PY
```

Expected: no probe errors and no unresolved imports. Counts are recorded, not hard-coded in tests.

- [ ] **Step 6: Resolve actual registry export differences with focused tests**

If an inspected module exports a different registry name, first add a failing unit test around a helper that extracts that real shape, then change only `probe_entrypoint.py`. Do not modify Hermes production modules to make the inventory script easier.

- [ ] **Step 7: Re-run generation twice and prove determinism**

```bash
sha256sum generated/platform_inventory/* > /tmp/platform-inventory-first.sha
python -m scripts.platform_inventory --root . --output generated/platform_inventory generate
sha256sum generated/platform_inventory/* > /tmp/platform-inventory-second.sha
diff -u /tmp/platform-inventory-first.sha /tmp/platform-inventory-second.sha
```

Expected: `diff` prints nothing.

- [ ] **Step 8: Write the human findings summary**

`docs/platform/phase-0-findings.md` must include:

- exact branch and source SHA;
- current main/upstream divergence status;
- complete discovered channel families and packaging generations;
- provider identifier-set differences;
- tool/toolset/plugin/MCP registration paths;
- Web versus Desktop reusable surfaces;
- Electron-only dependencies;
- current API/WebSocket paths;
- security-critical compatibility behaviors;
- optional dependency matrix;
- selected test roots;
- recommended Phase 1 boundaries;
- explicit unresolved questions, if any.

Do not duplicate the generated tables; link to their repository paths and explain architectural consequences.

- [ ] **Step 9: Run final verification**

```bash
python -m pytest tests/scripts/platform_inventory -v
python -m ruff check scripts/platform_inventory tests/scripts/platform_inventory
python -m ruff format --check scripts/platform_inventory tests/scripts/platform_inventory
python -m scripts.platform_inventory --root . --output generated/platform_inventory generate
git diff --check
git status --short
```

Expected:

- tests pass;
- lint/format pass;
- generator exits `0`;
- `git diff --check` prints nothing;
- status contains only Phase 0 scripts, tests, generated reports and approved documentation.

- [ ] **Step 10: Commit generated Phase 0 result**

```bash
git add scripts/platform_inventory tests/scripts/platform_inventory tests/fixtures/platform_inventory generated/platform_inventory docs/platform/phase-0-findings.md
git commit -m "feat(platform): complete Phase 0 capability inventory"
```

---

## Completion gate

Phase 0 is complete only after all of the following evidence exists:

- clean, reproducible source state;
- passing inventory test suite;
- zero unresolved local imports in the approved scope;
- zero unexplained runtime-probe errors;
- deterministic generated artifacts;
- manifest-based channel/provider/plugin discovery;
- distinct provider identifier sets;
- dynamic tool/toolset/MCP registration map;
- frontend/API/Electron coupling map;
- dependency and test matrix;
- human-reviewed Phase 0 findings document;
- no production source moved, deleted or refactored.

After this gate, write a separate Phase 1 implementation plan for the platform foundation and omnichannel inbox core. Do not extend this Phase 0 branch directly into inbox schema or frontend renderer implementation without that reviewed plan.