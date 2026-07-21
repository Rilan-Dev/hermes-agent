# Channels, Providers, and Onboarding Phase 1 Inventory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic executable inventory and characterization baseline for every Hermes messaging-channel, onboarding, and AI-provider dependency before any production source is copied, moved, deleted, or refactored.

**Architecture:** Add a manifest-driven analysis package under `scripts/extraction/`. It scans selected roots, parses plugin manifests without executing them, resolves Python imports statically, and runs existing Hermes registries inside an isolated subprocess. The generated YAML, Markdown, registry snapshot, and test matrix form the Phase 1 review gate.

**Tech Stack:** Python 3.11–3.13, `dataclasses`, `ast`, `hashlib`, `json`, `pathlib`, `subprocess`, PyYAML 6.0.3, pytest 9.0.2, Ruff 0.15.10, uv.

## Global Constraints

- Work only on `worktree/channels-providers-extraction-latest`, based on `planning/channels-providers-extraction-latest`.
- Source baseline is `main@e3ce380c068f532fcceb2c087310fcc98da4ee38`.
- Do not modify `main`.
- Do not move, copy, delete, rename, or rewrite existing production source in Phase 1.
- Do not create the final `hermes_connect.*` facade in Phase 1.
- Preserve recursive discovery for `plugins/platforms/**`, `plugins/model-providers/**`, `providers/**`, `gateway/relay/**`, and `gateway/platforms/**`.
- Keep `openai-api`, `openai-codex`, and the native runtime/catalog identifier `openai` distinct unless executable evidence maps them.
- Registry discovery must use a temporary `HERMES_HOME`, project plugins disabled, and no network calls.
- Generated data must be deterministic: sorted paths and identifiers, UTF-8, Unix newlines, and no timestamps.
- Phase 2 is blocked until the user reviews the generated inventory, registry snapshot, test matrix, and host-port dependency list.

---

## Planned File Structure

```text
extracted/hermes-connect-kit/
└── extraction-manifest.yaml

scripts/extraction/
├── __init__.py
├── schema.py
├── manifest.py
├── filesystem_inventory.py
├── plugin_inventory.py
├── import_inventory.py
├── registry_probe.py
├── render_report.py
└── build_inventory.py

tests/extraction/
├── __init__.py
├── snapshots/registry-snapshot.json
├── test_manifest.py
├── test_filesystem_inventory.py
├── test_plugin_inventory.py
├── test_import_inventory.py
├── test_registry_probe.py
├── test_build_inventory.py
└── test_characterization.py

docs/extraction/generated/
├── phase-1-inventory.yaml
├── phase-1-inventory.md
└── phase-1-test-matrix.md
```

## Core Interfaces

```python
@dataclass(frozen=True)
class RootRule:
    path: str
    classification: Classification
    destination: str
    reason: str


@dataclass(frozen=True)
class FileRule:
    path: str
    classification: Classification
    destination: str
    reason: str


@dataclass(frozen=True)
class ExtractionManifest:
    version: int
    source_repository: str
    source_sha: str
    dynamic_roots: tuple[RootRule, ...]
    explicit_files: tuple[FileRule, ...]
    test_rules: tuple[TestRule, ...]
    internal_module_roots: tuple[str, ...]


def load_manifest(path: Path) -> ExtractionManifest: ...
def inventory_files(repo_root: Path, manifest: ExtractionManifest) -> tuple[FileRecord, ...]: ...
def inventory_plugins(repo_root: Path, roots: tuple[str, ...]) -> tuple[PluginRecord, ...]: ...
def inventory_imports(repo_root: Path, files: tuple[FileRecord, ...], internal_roots: tuple[str, ...]) -> tuple[ImportRecord, ...]: ...
def build_registry_snapshot() -> dict[str, object]: ...
def build_inventory(repo_root: Path, manifest_path: Path, registry_snapshot_path: Path) -> dict[str, object]: ...
```

---

### Task 1: Create the isolated local worktree and verify the baseline

**Files:**
- Modify only when required by the ignore check: `.gitignore`
- No production files

**Interfaces:**
- Consumes: remote branch `worktree/channels-providers-extraction-latest`
- Produces: isolated checkout with a clean baseline

- [ ] **Step 1: Detect existing isolation**

```bash
GIT_DIR="$(cd "$(git rev-parse --git-dir)" && pwd -P)"
GIT_COMMON="$(cd "$(git rev-parse --git-common-dir)" && pwd -P)"
SUPERPROJECT="$(git rev-parse --show-superproject-working-tree 2>/dev/null || true)"
BRANCH="$(git branch --show-current)"
printf 'git_dir=%s\ngit_common=%s\nsuperproject=%s\nbranch=%s\n' \
  "$GIT_DIR" "$GIT_COMMON" "$SUPERPROJECT" "$BRANCH"
```

When `GIT_DIR != GIT_COMMON` and `SUPERPROJECT` is empty, continue in the existing worktree. Otherwise execute Step 2.

- [ ] **Step 2: Create the worktree safely**

```bash
git fetch origin
mkdir -p .worktrees
if ! git check-ignore -q .worktrees; then
  printf '\n# Local linked worktrees\n.worktrees/\n' >> .gitignore
  git add .gitignore
  git commit -m "chore: ignore local worktrees"
fi
git worktree add .worktrees/channels-providers-extraction \
  worktree/channels-providers-extraction-latest
cd .worktrees/channels-providers-extraction
```

Expected: HEAD is on `worktree/channels-providers-extraction-latest`.

- [ ] **Step 3: Verify ancestry and unchanged scoped production files**

```bash
test "$(git branch --show-current)" = "worktree/channels-providers-extraction-latest"
git merge-base --is-ancestor \
  e3ce380c068f532fcceb2c087310fcc98da4ee38 HEAD
git diff --exit-code \
  e3ce380c068f532fcceb2c087310fcc98da4ee38..HEAD -- \
  gateway providers plugins/model-providers plugins/platforms \
  hermes_cli agent cron tools/send_message_tool.py run_agent.py
```

Expected: status `0` and no scoped diff.

- [ ] **Step 4: Install and test the baseline**

```bash
uv sync --extra dev
uv run pytest \
  tests/providers \
  tests/gateway \
  tests/plugins/model_providers \
  tests/agent/transports \
  tests/hermes_cli/test_provider_parity.py \
  -q
git status --short
```

Expected: all collected non-integration tests pass and the worktree is clean. Do not continue when the baseline fails.

---

### Task 2: Add the validated extraction manifest

**Files:**
- Create: `scripts/extraction/__init__.py`
- Create: `scripts/extraction/schema.py`
- Create: `scripts/extraction/manifest.py`
- Create: `extracted/hermes-connect-kit/extraction-manifest.yaml`
- Create: `tests/extraction/__init__.py`
- Create: `tests/extraction/test_manifest.py`

**Interfaces:**
- Produces the immutable schema types and `load_manifest()` used by all later tasks.

- [ ] **Step 1: Write failing manifest tests**

```python
from pathlib import Path

import pytest

from scripts.extraction.manifest import ManifestError, load_manifest
from scripts.extraction.schema import Classification


def test_repository_manifest_loads() -> None:
    manifest = load_manifest(
        Path("extracted/hermes-connect-kit/extraction-manifest.yaml")
    )
    assert manifest.version == 1
    assert manifest.source_sha == "e3ce380c068f532fcceb2c087310fcc98da4ee38"
    assert {rule.path for rule in manifest.dynamic_roots} >= {
        "plugins/platforms",
        "plugins/model-providers",
        "providers",
        "gateway/relay",
        "gateway/platforms",
    }
    assert manifest.dynamic_roots[0].classification is Classification.CORE


@pytest.mark.parametrize("value", ["", "/absolute", "../escape", "a/../../escape"])
def test_manifest_rejects_unsafe_paths(tmp_path: Path, value: str) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text(
        f"""version: 1
source_repository: Rilan-Dev/hermes-agent
source_sha: e3ce380c068f532fcceb2c087310fcc98da4ee38
dynamic_roots:
  - path: {value!r}
    classification: core
    destination: vendor/root
    reason: invalid
explicit_files: []
test_rules: []
internal_module_roots: []
""",
        encoding="utf-8",
    )
    with pytest.raises(ManifestError):
        load_manifest(path)
```

- [ ] **Step 2: Run the test to confirm it fails**

```bash
uv run pytest tests/extraction/test_manifest.py -q
```

Expected: collection fails because the extraction modules do not exist.

- [ ] **Step 3: Implement `schema.py`**

```python
from dataclasses import dataclass
from enum import Enum


class Classification(str, Enum):
    CORE = "core"
    HOST_PORT = "host_port"
    OPTIONAL_UI = "optional_ui"
    TEST = "test"
    EXCLUDE_BY_DEFAULT = "exclude_by_default"


@dataclass(frozen=True)
class RootRule:
    path: str
    classification: Classification
    destination: str
    reason: str


@dataclass(frozen=True)
class FileRule:
    path: str
    classification: Classification
    destination: str
    reason: str


@dataclass(frozen=True)
class TestRule:
    path: str
    kind: str
    behavior: str


@dataclass(frozen=True)
class ExtractionManifest:
    version: int
    source_repository: str
    source_sha: str
    dynamic_roots: tuple[RootRule, ...]
    explicit_files: tuple[FileRule, ...]
    test_rules: tuple[TestRule, ...]
    internal_module_roots: tuple[str, ...]
```

- [ ] **Step 4: Implement strict YAML loading in `manifest.py`**

The loader must:

1. use `yaml.safe_load()`;
2. require `version == 1`;
3. require a lowercase 40-character Git SHA;
4. reject absolute paths, empty paths, backtracking `..`, and Windows separators after normalization;
5. accept only `core`, `host_port`, `optional_ui`, `test`, and `exclude_by_default` classifications;
6. accept only `root`, `file`, and `glob` test-rule kinds;
7. return tuples so downstream ordering cannot be mutated accidentally.

Use these exact helpers and exception type:

```python
class ManifestError(ValueError):
    pass


def _safe_repo_path(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field} must be a non-empty string")
    text = value.strip().replace("\\", "/")
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or text == ".":
        raise ManifestError(f"{field} must be repository-relative")
    return path.as_posix()
```

- [ ] **Step 5: Create the authoritative YAML manifest**

The manifest must contain the five recursive roots from the design, every named load-bearing file in `docs/extraction/02-source-and-test-inventory.md`, the required test roots/globs, and these internal roots:

```yaml
internal_module_roots:
  - agent
  - cron
  - gateway
  - hermes_cli
  - plugins
  - providers
  - tools
  - acp_adapter
  - tui_gateway
  - cli
  - hermes_constants
  - hermes_logging
  - hermes_state
  - model_tools
  - run_agent
  - toolsets
  - utils
```

Each dynamic root and explicit file must include `path`, `classification`, `destination`, and a concrete `reason`. The manifest is the machine-readable translation of the reviewed inventory; it must not invent additional product scope.

- [ ] **Step 6: Run and commit**

```bash
uv run pytest tests/extraction/test_manifest.py -q
git add scripts/extraction extracted/hermes-connect-kit/extraction-manifest.yaml tests/extraction
git commit -m "feat(extraction): add validated phase one manifest"
```

---

### Task 3: Inventory files and plugin manifests deterministically

**Files:**
- Create: `scripts/extraction/filesystem_inventory.py`
- Create: `scripts/extraction/plugin_inventory.py`
- Create: `tests/extraction/test_filesystem_inventory.py`
- Create: `tests/extraction/test_plugin_inventory.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class FileRecord:
    source: str
    destination: str
    classification: str
    reason: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class PluginRecord:
    key: str
    name: str
    kind: str
    version: str
    description: str
    manifest_path: str
    module_path: str
```

- [ ] **Step 1: Write failing recursive inventory tests**

```python
def test_inventory_is_recursive_sorted_and_hashed(tmp_path: Path) -> None:
    (tmp_path / "plugins/platforms/chat").mkdir(parents=True)
    (tmp_path / "plugins/platforms/chat/__init__.py").write_text(
        "VALUE = 1\n", encoding="utf-8"
    )
    (tmp_path / "plugins/platforms/chat/plugin.yaml").write_text(
        "name: chat\nkind: platform\n", encoding="utf-8"
    )
    records = inventory_files(tmp_path, manifest_for_tmp_tree())
    assert [item.source for item in records] == sorted(item.source for item in records)
    assert all(len(item.sha256) == 64 for item in records)


def test_plugin_inventory_never_imports_plugin_module(tmp_path: Path) -> None:
    plugin = tmp_path / "plugins/platforms/example"
    plugin.mkdir(parents=True)
    (plugin / "plugin.yaml").write_text(
        "name: example\nkind: platform\nversion: 1.0.0\n",
        encoding="utf-8",
    )
    (plugin / "__init__.py").write_text(
        "raise RuntimeError('must not import')\n", encoding="utf-8"
    )
    records = inventory_plugins(tmp_path, ("plugins/platforms",))
    assert records[0].name == "example"
```

- [ ] **Step 2: Implement file inventory**

`inventory_files()` must recursively walk each dynamic root, include every file type, hash bytes in 1 MiB chunks, map destinations by relative path, add explicit files, reject missing explicit files, reject conflicting rules, and return records sorted by `source`.

Use this hashing implementation:

```python
def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
```

- [ ] **Step 3: Implement non-executing plugin inventory**

`inventory_plugins()` must search `plugin.yaml` and `plugin.yml`, parse with `yaml.safe_load()`, require non-empty `name` and `kind`, derive `key` from the path relative to its root, record `__init__.py` as `module_path`, and sort by `(kind, key, name)`.

- [ ] **Step 4: Run and commit**

```bash
uv run pytest \
  tests/extraction/test_filesystem_inventory.py \
  tests/extraction/test_plugin_inventory.py -q
git add scripts/extraction tests/extraction
git commit -m "feat(extraction): inventory scoped files and plugins"
```

---

### Task 4: Classify Python imports and reveal host dependencies

**Files:**
- Create: `scripts/extraction/import_inventory.py`
- Create: `tests/extraction/test_import_inventory.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ImportRecord:
    source: str
    imports_in_scope: tuple[str, ...]
    imports_out_of_scope: tuple[str, ...]
    external_imports: tuple[str, ...]
    unresolved_internal: tuple[str, ...]
```

- [ ] **Step 1: Write failing tests for absolute and relative imports**

```python
def test_imports_are_classified(tmp_path: Path) -> None:
    (tmp_path / "gateway").mkdir()
    (tmp_path / "gateway/__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "gateway/session.py").write_text(
        "from gateway.delivery import deliver\n"
        "from hermes_state import SessionDB\n"
        "import json\n",
        encoding="utf-8",
    )
    (tmp_path / "gateway/delivery.py").write_text("def deliver(): pass\n", encoding="utf-8")
    (tmp_path / "hermes_state.py").write_text("class SessionDB: pass\n", encoding="utf-8")
    result = inventory_imports(
        tmp_path,
        (record("gateway/session.py"), record("gateway/delivery.py")),
        ("gateway", "hermes_state"),
    )[0]
    assert result.imports_in_scope == ("gateway/delivery.py",)
    assert result.imports_out_of_scope == ("hermes_state.py",)
    assert result.external_imports == ("json",)
```

- [ ] **Step 2: Implement AST resolution**

The implementation must build a repository module index for packages and top-level modules, parse `ast.Import` and `ast.ImportFrom`, resolve relative imports using the current package, classify resolved paths against the scoped `FileRecord` set, treat standard/third-party roots as external, and record unresolved names only when their root is listed in `internal_module_roots`.

Do not import production modules during this task.

- [ ] **Step 3: Run and commit**

```bash
uv run pytest tests/extraction/test_import_inventory.py -q
git add scripts/extraction/import_inventory.py tests/extraction/test_import_inventory.py
git commit -m "feat(extraction): classify scoped python imports"
```

---

### Task 5: Capture runtime registries in an isolated subprocess

**Files:**
- Create: `scripts/extraction/registry_probe.py`
- Create: `tests/extraction/test_registry_probe.py`
- Create: `tests/extraction/snapshots/registry-snapshot.json`

**Interfaces:**
- Command: `python -m scripts.extraction.registry_probe`
- Output: one deterministic JSON object on stdout

- [ ] **Step 1: Write the failing subprocess contract test**

```python
def test_registry_probe_is_deterministic_and_isolated(tmp_path: Path) -> None:
    env = os.environ.copy()
    env.update({
        "HERMES_HOME": str(tmp_path / "home"),
        "HERMES_ENABLE_PROJECT_PLUGINS": "0",
        "HERMES_SAFE_MODE": "0",
        "HERMES_PLUGINS_DEBUG": "0",
        "PYTHONHASHSEED": "0",
    })
    command = [sys.executable, "-m", "scripts.extraction.registry_probe"]
    first = subprocess.run(command, check=True, env=env, text=True, capture_output=True)
    second = subprocess.run(command, check=True, env=env, text=True, capture_output=True)
    assert first.stdout == second.stdout
    data = json.loads(first.stdout)
    assert data["provider_catalog_slugs"] == data["canonical_providers"]
    assert "openai-api" in data["canonical_providers"]
    assert "openai-codex" in data["canonical_providers"]
    assert set(data["platform_registry"]) == (
        set(data["platform_concrete"]) | set(data["platform_deferred"])
    )
```

- [ ] **Step 2: Implement the probe using the real APIs**

Use these calls exactly:

```python
from gateway.platform_registry import platform_registry
from hermes_cli.auth import PROVIDER_REGISTRY
from hermes_cli.models import CANONICAL_PROVIDERS
from hermes_cli.plugins import discover_plugins, get_plugin_manager
from hermes_cli.provider_catalog import provider_catalog
from providers import list_providers

discover_plugins(force=True)
plugins = get_plugin_manager().list_plugins()
profiles = list_providers()
catalog = provider_catalog()
```

Record:

- plugin rows sorted by `(kind, key)`;
- `platform_registry` as the sorted union of `platform_registry._entries` and `platform_registry._deferred`;
- concrete platform metadata without forcing deferred adapters to import;
- provider profile names, aliases, auth type, env vars, and API mode;
- canonical provider slugs in canonical order;
- sorted auth-provider IDs;
- provider catalog descriptors and catalog slugs.

The private `_entries` and `_deferred` access is intentional characterization of the current internal lazy-loading contract. Do not call `all_entries()` because that would import optional platform SDKs and make membership depend on installed extras.

- [ ] **Step 3: Generate the committed snapshot**

```bash
mkdir -p tests/extraction/snapshots
HERMES_HOME="$(mktemp -d)" \
HERMES_ENABLE_PROJECT_PLUGINS=0 \
HERMES_SAFE_MODE=0 \
HERMES_PLUGINS_DEBUG=0 \
PYTHONHASHSEED=0 \
uv run python -m scripts.extraction.registry_probe \
  > tests/extraction/snapshots/registry-snapshot.json
uv run python -m json.tool tests/extraction/snapshots/registry-snapshot.json >/dev/null
```

- [ ] **Step 4: Run and commit**

```bash
uv run pytest tests/extraction/test_registry_probe.py -q
git add scripts/extraction/registry_probe.py tests/extraction
git commit -m "test(extraction): snapshot channel and provider registries"
```

---

### Task 6: Generate the machine-readable and human review reports

**Files:**
- Create: `scripts/extraction/render_report.py`
- Create: `scripts/extraction/build_inventory.py`
- Create: `tests/extraction/test_build_inventory.py`
- Generate: `docs/extraction/generated/phase-1-inventory.yaml`
- Generate: `docs/extraction/generated/phase-1-inventory.md`
- Generate: `docs/extraction/generated/phase-1-test-matrix.md`

**Interfaces:**

```bash
python -m scripts.extraction.build_inventory \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --registry-snapshot tests/extraction/snapshots/registry-snapshot.json \
  --yaml docs/extraction/generated/phase-1-inventory.yaml \
  --markdown docs/extraction/generated/phase-1-inventory.md \
  --test-matrix docs/extraction/generated/phase-1-test-matrix.md
```

- [ ] **Step 1: Write deterministic build tests**

```python
def test_build_inventory_is_deterministic() -> None:
    kwargs = {
        "repo_root": Path.cwd(),
        "manifest_path": Path("extracted/hermes-connect-kit/extraction-manifest.yaml"),
        "registry_snapshot_path": Path("tests/extraction/snapshots/registry-snapshot.json"),
    }
    first = build_inventory(**kwargs)
    second = build_inventory(**kwargs)
    assert first == second
    assert first["source_sha"] == "e3ce380c068f532fcceb2c087310fcc98da4ee38"
    assert first["files"]
    assert first["plugins"]["platforms"]
    assert first["plugins"]["model_providers"]
```

- [ ] **Step 2: Add source guards**

Before scanning, run:

```bash
git merge-base --is-ancestor <source_sha> HEAD
git diff --name-only <source_sha>..HEAD -- <all manifest source paths>
```

`build_inventory()` must raise when the source SHA is not an ancestor or when any scoped production source differs from the baseline. Planning documents, generated reports, tests, and extraction scripts are outside this guard.

- [ ] **Step 3: Assemble the YAML data**

The report must contain:

```yaml
schema_version: 1
source_repository: Rilan-Dev/hermes-agent
source_sha: e3ce380c068f532fcceb2c087310fcc98da4ee38
inventory_head: <current commit SHA>
files: []
plugins:
  platforms: []
  model_providers: []
registries:
  platform_entries: []
  platform_concrete: []
  platform_deferred: []
  provider_profiles: []
  canonical_providers: []
  auth_providers: []
  provider_catalog: []
out_of_scope_imports: []
unresolved_imports: []
test_rules: []
```

Each file row must include source, destination, classification, reason, SHA-256, byte size, in-scope imports, out-of-scope internal imports, and external import roots.

- [ ] **Step 4: Render Markdown summaries**

`phase-1-inventory.md` must show counts by classification, plugin type, registry type, unresolved imports, and a table of out-of-scope dependencies. `phase-1-test-matrix.md` must list each test path/pattern, its rule kind, and protected behavior.

- [ ] **Step 5: Generate twice and verify idempotence**

```bash
uv run python -m scripts.extraction.build_inventory \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --registry-snapshot tests/extraction/snapshots/registry-snapshot.json \
  --yaml docs/extraction/generated/phase-1-inventory.yaml \
  --markdown docs/extraction/generated/phase-1-inventory.md \
  --test-matrix docs/extraction/generated/phase-1-test-matrix.md
git add docs/extraction/generated
uv run python -m scripts.extraction.build_inventory \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --registry-snapshot tests/extraction/snapshots/registry-snapshot.json \
  --yaml docs/extraction/generated/phase-1-inventory.yaml \
  --markdown docs/extraction/generated/phase-1-inventory.md \
  --test-matrix docs/extraction/generated/phase-1-test-matrix.md
git diff --exit-code -- docs/extraction/generated
```

Expected: the second generation produces no diff.

- [ ] **Step 6: Run and commit**

```bash
uv run pytest tests/extraction/test_build_inventory.py -q
git add scripts/extraction tests/extraction docs/extraction/generated
git commit -m "feat(extraction): generate phase one inventory reports"
```

---

### Task 7: Lock characterization contracts

**Files:**
- Create: `tests/extraction/test_characterization.py`
- Modify only when evidence requires a correction: manifest, snapshot, generated reports

- [ ] **Step 1: Add exact parity and scope assertions**

```python
def test_platform_manifests_match_discovered_platform_plugins() -> None:
    assert {item["key"] for item in inventory()["plugins"]["platforms"]} == {
        item["key"] for item in registry()["plugins"] if item["kind"] == "platform"
    }


def test_model_provider_manifests_match_discovered_plugins() -> None:
    assert {item["key"] for item in inventory()["plugins"]["model_providers"]} == {
        item["key"] for item in registry()["plugins"] if item["kind"] == "model-provider"
    }


def test_provider_catalog_preserves_canonical_order() -> None:
    data = registry()
    assert data["provider_catalog_slugs"] == data["canonical_providers"]
    assert "openai-api" in data["canonical_providers"]
    assert "openai-codex" in data["canonical_providers"]


def test_required_onboarding_surfaces_are_scoped() -> None:
    sources = {item["source"] for item in inventory()["files"]}
    assert {
        "agent/onboarding.py",
        "hermes_cli/setup.py",
        "hermes_cli/model_setup_flows.py",
        "hermes_cli/gateway.py",
        "apps/desktop/src/components/onboarding/index.tsx",
        "apps/desktop/src/store/onboarding.ts",
        "web/src/components/OAuthProvidersCard.tsx",
        "web/src/lib/api.ts",
    } <= sources


def test_no_unresolved_internal_imports() -> None:
    assert inventory()["unresolved_imports"] == []
```

- [ ] **Step 2: Run all Phase 1 tests**

```bash
uv run pytest tests/extraction -q
```

A parity failure is a review signal. Do not weaken an invariant merely to make the test green; correct the manifest or document a proven exception with a focused assertion.

- [ ] **Step 3: Commit**

```bash
git add tests/extraction extracted/hermes-connect-kit/extraction-manifest.yaml \
  docs/extraction/generated
git commit -m "test(extraction): lock phase one characterization"
```

---

### Task 8: Final verification and review handoff

**Files:**
- No new production files

- [ ] **Step 1: Run lint and Phase 1 tests**

```bash
uv run ruff check scripts/extraction tests/extraction
uv run pytest tests/extraction -q
```

- [ ] **Step 2: Re-run the selected existing test baseline**

```bash
uv run pytest \
  tests/providers \
  tests/gateway \
  tests/plugins/model_providers \
  tests/agent/transports \
  tests/hermes_cli/test_provider_parity.py \
  -q
```

- [ ] **Step 3: Regenerate and prove a clean tree**

```bash
uv run python -m scripts.extraction.build_inventory \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --registry-snapshot tests/extraction/snapshots/registry-snapshot.json \
  --yaml docs/extraction/generated/phase-1-inventory.yaml \
  --markdown docs/extraction/generated/phase-1-inventory.md \
  --test-matrix docs/extraction/generated/phase-1-test-matrix.md
git diff --exit-code
git status --short
```

Expected: no output.

- [ ] **Step 4: Prove no existing production path changed**

```bash
UNEXPECTED="$(git diff --name-only \
  planning/channels-providers-extraction-latest...HEAD \
  | grep -Ev '^(docs/extraction/generated/|docs/superpowers/plans/|extracted/hermes-connect-kit/extraction-manifest.yaml$|scripts/extraction/|tests/extraction/|\.gitignore$)' || true)"
test -z "$UNEXPECTED" || { printf '%s\n' "$UNEXPECTED"; exit 1; }
```

- [ ] **Step 5: Prepare the review summary**

Report:

- source SHA and implementation HEAD;
- scoped file count by classification;
- platform-plugin and model-provider-plugin counts;
- concrete and deferred platform counts;
- canonical-provider, auth-provider, and provider-profile counts;
- out-of-scope internal dependency count;
- unresolved internal import count;
- Phase 1 test count and existing selected test count;
- every host-port candidate revealed by import analysis;
- optional dependencies required by selected adapters/transports;
- backend API routes still requiring proof for optional desktop/web onboarding.

Explicitly state that Phase 1 performed no production source projection, deletion, import rewriting, public-facade implementation, pull-request merge, or change to `main`.

Stop at this gate. Phase 2 begins only after the user reviews and approves the generated evidence.

---

## Self-Review Results

### Spec coverage

- Isolated worktree and clean baseline: Task 1.
- Executable manifest: Task 2.
- Recursive channel/provider roots and file hashes: Task 3.
- Static dependency and host-port evidence: Task 4.
- Real plugin/platform/provider registry enumeration: Task 5.
- Deterministic machine and human reports: Task 6.
- Provider identity, plugin parity, and onboarding coverage: Task 7.
- No production movement and final review gate: Task 8.

### Placeholder scan

Every planned file has an exact path, interface, test command, implementation rule, expected result, and commit boundary. No deferred implementation markers are present.

### Type consistency

`ExtractionManifest` feeds the file, plugin, import, and report builders. `FileRecord` feeds import analysis and report generation. Registry snapshot keys used by characterization tests match the probe contract. CLI argument names are identical in Tasks 6 and 8.
