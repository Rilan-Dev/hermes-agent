# Source-Derived Capability Catalogue and Web Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, provenance-complete catalogue from the exact reviewed Hermes projection, expose it through read-only workspace-safe APIs, and render it through an independent generic browser application without recreating Hermes business behavior.

**Architecture:** Extend the existing `scripts/platform_inventory` package and combine it with the approved Phase 2 projection lock. The generated catalogue is an immutable, content-addressed read model; the platform backend reads it through a stable repository port; `apps/platform-web` renders source-derived namespaces, descriptors, relationships, provenance, health, and the already-existing inbox list through generic projection classes.

**Tech Stack:** Python 3.11, dataclasses, pathlib, AST, subprocess, JSON/YAML, FastAPI, Pydantic, pytest, Ruff, React 19, TypeScript 6, Vite 8, Tailwind 4, React Router 7, Vitest 4, and `@nous-research/ui`.

## Global Constraints

- Execution is blocked until Phase 2 Checkpoint E approves the complete exact projection on `planning/channels-providers-phase2-2026-07-22`.
- Do not execute this plan from fork `main` at `d5a67ad32522273115d887560ca1c08a02bc7873`; it does not contain the projected source.
- The current reviewed combined source baseline is `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`; use the final Checkpoint E lineage if that value changes through approved review.
- Every displayed capability must originate from a projected source object, isolated runtime registry, manifest, source-owned command definition, or source-owned UI surface.
- Do not manually maintain provider, model, authentication, channel, tool, toolset, workflow, command, onboarding, agent, or chat-capability identity lists.
- Product code imports only `agentic_platform.*` contracts. It must not import arbitrary projected `agent.*`, `gateway.*`, `hermes_cli.*`, `providers.*`, `tools.*`, or plugin-manager internals.
- The exact projected tree under `extracted/hermes-connect-kit/upstream/` is read-only.
- Isolated probes set `HERMES_ENABLE_PROJECT_PLUGINS=0`, `PYTHONNOUSERSITE=1`, `PYTHONHASHSEED=0`, blank credential variables, and block network connections.
- OpenAI API-key, OpenAI Codex OAuth/runtime, native model identities, and OpenAI-compatible endpoint identities remain distinct.
- Catalogue output contains no timestamps, credential values, authorization headers, environment-variable values, or arbitrary tracebacks.
- No GitHub Actions workflow is added, enabled, or expanded.
- Each task uses RED → GREEN → focused regression → commit.
- Do not claim a command passed unless its output and exit status were observed.

## Required Execution Worktree

Run only after Checkpoint E has merged the reviewed projection into `planning/channels-providers-phase2-2026-07-22`:

```bash
git fetch origin

git switch planning/channels-providers-phase2-2026-07-22
git pull --ff-only

git worktree add \
  .worktrees/source-derived-capability-catalog \
  -b worktree/source-derived-capability-catalog \
  HEAD

cd .worktrees/source-derived-capability-catalog

git status --short
test -f extracted/hermes-connect-kit/projection-lock.json
test -d extracted/hermes-connect-kit/upstream
uv run python -m scripts.extraction.project_sources --check
```

Expected:

- `git status --short` prints nothing.
- Both path checks exit 0.
- Projection verification exits 0.
- Stop immediately when any precondition fails.

## Target Files

```text
scripts/platform_inventory/
├── models.py
├── source_view.py
├── provenance.py
├── capability_catalog.py
├── command_projection.py
├── ui_reuse.py
├── catalog_reports.py
├── probe_entrypoint.py
├── runtime_probe.py
└── cli.py

tests/scripts/platform_inventory/
├── test_source_view.py
├── test_provenance.py
├── test_capability_catalog.py
├── test_runtime_capability_metadata.py
├── test_command_projection.py
├── test_ui_reuse.py
├── test_catalog_reports.py
└── test_catalog_cli.py

extracted/hermes-connect-kit/catalog/
├── capability-catalog.json
└── capability-catalog-lock.json

docs/platform/generated/
├── capability-coverage.md
├── cli-tui-browser-projection.md
└── source-ui-reuse.md

platform/backend/src/agentic_platform/
├── domain/capabilities.py
├── ports/capabilities.py
├── storage/catalog_json.py
├── services/capabilities.py
└── api/capabilities.py

platform/backend/tests/
├── domain/test_capabilities.py
├── storage/test_catalog_json.py
├── services/test_capabilities.py
└── api/test_capabilities.py

apps/platform-web/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── vite.config.ts
└── src/
    ├── main.tsx
    ├── styles.css
    ├── app/App.tsx
    ├── app/router.tsx
    ├── app/workspace.ts
    ├── api/contracts.ts
    ├── api/errors.ts
    ├── api/client.ts
    ├── renderers/contracts.ts
    ├── renderers/registry.tsx
    ├── renderers/GenericDescriptorList.tsx
    ├── renderers/GenericDescriptorDetail.tsx
    ├── features/health/HealthPage.tsx
    ├── features/catalog/CatalogPage.tsx
    ├── features/catalog/DescriptorPage.tsx
    ├── features/catalog/ProvenancePanel.tsx
    ├── features/inbox/InboxPage.tsx
    └── test/
        ├── package-boundary.test.ts
        ├── api-client.test.ts
        ├── renderer-registry.test.tsx
        └── routes.test.tsx
```

---

### Task 1: Load and Verify the Exact Projected Source

**Files:**
- Modify: `scripts/platform_inventory/models.py`
- Create: `scripts/platform_inventory/source_view.py`
- Create: `tests/scripts/platform_inventory/test_source_view.py`

**Interfaces:**
- Consumes `extracted/hermes-connect-kit/projection-lock.json` schema version 1.
- Produces `ProjectionLineage`, `ProjectionRecord`, and `ProjectedSourceView`.
- Public function: `load_projected_source_view(repo_root: Path, kit_root: Path) -> ProjectedSourceView`.

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.platform_inventory.models import InventoryError
from scripts.platform_inventory.source_view import load_projected_source_view


def write_projection(
    root: Path,
    *,
    projected_path: str = "upstream/providers/example.py",
    projected_bytes: bytes = b"VALUE = 1\n",
    locked_bytes: bytes = b"VALUE = 1\n",
) -> Path:
    kit = root / "extracted/hermes-connect-kit"
    path = kit / projected_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(projected_bytes)
    lock = {
        "schema_version": 1,
        "generator_version": 1,
        "source_repository": "Rilan-Dev/hermes-agent",
        "source_sha": "a" * 40,
        "upstream_repository": "NousResearch/hermes-agent",
        "upstream_sha": "b" * 40,
        "fork_main_sha": "c" * 40,
        "projection_root": "upstream",
        "manifest_sha256": "d" * 64,
        "records": [
            {
                "source": "providers/example.py",
                "projected_path": projected_path,
                "subsystem": "providers",
                "classification": "core",
                "planned_layer": "vendor",
                "reason": "Provider source.",
                "sha256": hashlib.sha256(locked_bytes).hexdigest(),
                "size_bytes": len(locked_bytes),
                "git_mode": "100644",
                "git_object_type": "blob",
                "git_blob_sha": "e" * 40,
                "kind": "file",
                "link_target": None,
                "behavior": None,
            }
        ],
    }
    (kit / "projection-lock.json").write_text(
        json.dumps(lock), encoding="utf-8"
    )
    return kit


def test_source_view_accepts_exact_projected_bytes(tmp_path: Path) -> None:
    kit = write_projection(tmp_path)
    view = load_projected_source_view(tmp_path, kit)
    assert view.records[0].source == "providers/example.py"
    assert view.records[0].projected_path == "upstream/providers/example.py"


def test_source_view_rejects_projected_byte_drift(tmp_path: Path) -> None:
    kit = write_projection(tmp_path, projected_bytes=b"VALUE = 2\n")
    with pytest.raises(InventoryError, match="byte drift"):
        load_projected_source_view(tmp_path, kit)


@pytest.mark.parametrize(
    "projected_path",
    ["providers/example.py", "upstream/../escape.py", "/upstream/example.py"],
)
def test_source_view_rejects_noncanonical_projected_path(
    tmp_path: Path, projected_path: str
) -> None:
    kit = write_projection(tmp_path, projected_path=projected_path)
    with pytest.raises(InventoryError, match="projected path"):
        load_projected_source_view(tmp_path, kit)
```

- [ ] **Step 2: Run tests and verify RED**

```bash
uv run pytest tests/scripts/platform_inventory/test_source_view.py -q
```

Expected: import failure for the missing source-view models/module.

- [ ] **Step 3: Add immutable projection models**

Append to `scripts/platform_inventory/models.py`:

```python
@dataclass(frozen=True, slots=True)
class ProjectionLineage:
    source_repository: str
    source_sha: str
    upstream_repository: str
    upstream_sha: str
    fork_main_sha: str
    projection_root: str
    manifest_sha256: str
    lock_sha256: str


@dataclass(frozen=True, slots=True)
class ProjectionRecord:
    source: str
    projected_path: str
    subsystem: str
    classification: str
    planned_layer: str | None
    reason: str
    sha256: str
    size_bytes: int
    git_mode: str
    git_object_type: str
    git_blob_sha: str
    kind: str
    link_target: str | None
    behavior: str | None


@dataclass(frozen=True, slots=True)
class ProjectedSourceView:
    repository_root: Path
    kit_root: Path
    projection_root: Path
    lineage: ProjectionLineage
    records: tuple[ProjectionRecord, ...]

    def by_source(self) -> dict[str, ProjectionRecord]:
        return {record.source: record for record in self.records}
```

- [ ] **Step 4: Implement strict loading**

Create `scripts/platform_inventory/source_view.py`:

```python
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from .models import (
    InventoryError,
    ProjectedSourceView,
    ProjectionLineage,
    ProjectionRecord,
)


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_projected_source_view(
    repo_root: Path,
    kit_root: Path,
) -> ProjectedSourceView:
    repository = repo_root.resolve()
    kit = kit_root.resolve()
    lock_path = kit / "projection-lock.json"
    try:
        raw_lock = lock_path.read_bytes()
        data = json.loads(raw_lock)
        if data.get("schema_version") != 1:
            raise InventoryError("projection lock schema_version must be 1")
        if data.get("projection_root") != "upstream":
            raise InventoryError("projection root must be upstream")

        records: list[ProjectionRecord] = []
        sources: set[str] = set()
        destinations: set[str] = set()
        for raw_record in data.get("records", []):
            record = ProjectionRecord(**raw_record)
            expected = PurePosixPath("upstream", record.source).as_posix()
            if record.projected_path != expected:
                raise InventoryError(
                    f"invalid projected path {record.projected_path}; expected {expected}"
                )
            if record.source in sources or record.projected_path in destinations:
                raise InventoryError("duplicate projected source or destination")
            sources.add(record.source)
            destinations.add(record.projected_path)
            path = kit / record.projected_path
            if record.kind == "file":
                content = path.read_bytes()
                if len(content) != record.size_bytes or _digest(content) != record.sha256:
                    raise InventoryError(f"projected byte drift: {record.projected_path}")
            elif record.kind == "symlink":
                if not path.is_symlink() or path.readlink().as_posix() != record.link_target:
                    raise InventoryError(f"projected symlink drift: {record.projected_path}")
            else:
                raise InventoryError(f"unsupported projected object kind: {record.kind}")
            records.append(record)

        lineage = ProjectionLineage(
            source_repository=data["source_repository"],
            source_sha=data["source_sha"],
            upstream_repository=data["upstream_repository"],
            upstream_sha=data["upstream_sha"],
            fork_main_sha=data["fork_main_sha"],
            projection_root=data["projection_root"],
            manifest_sha256=data["manifest_sha256"],
            lock_sha256=_digest(raw_lock),
        )
    except InventoryError:
        raise
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise InventoryError(f"invalid projection lock {lock_path}: {exc}") from exc

    return ProjectedSourceView(
        repository_root=repository,
        kit_root=kit,
        projection_root=kit / "upstream",
        lineage=lineage,
        records=tuple(sorted(records, key=lambda item: item.source)),
    )
```

Call the Phase 2 `verify_tree()` implementation before returning so extra files and mode drift are checked by the canonical projector verifier rather than a duplicate traversal.

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest tests/scripts/platform_inventory/test_source_view.py -q
uv run pytest tests/scripts/platform_inventory -q
uv run ruff check scripts/platform_inventory tests/scripts/platform_inventory

git add scripts/platform_inventory/models.py \
  scripts/platform_inventory/source_view.py \
  tests/scripts/platform_inventory/test_source_view.py
git commit -m "feat(inventory): validate exact projected source"
```

---

### Task 2: Define Catalogue, Relationship, and Provenance Types

**Files:**
- Modify: `scripts/platform_inventory/models.py`
- Create: `scripts/platform_inventory/provenance.py`
- Create: `scripts/platform_inventory/capability_catalog.py`
- Create: `tests/scripts/platform_inventory/test_provenance.py`
- Create: `tests/scripts/platform_inventory/test_capability_catalog.py`

**Interfaces:**
- Public functions: `provenance_from_projection(...)`, `canonical_catalog_bytes(catalog)`, `catalog_digest(catalog)`, and `validate_catalog(catalog)`.

- [ ] **Step 1: Write failing deterministic-schema tests**

```python
from scripts.platform_inventory.capability_catalog import (
    canonical_catalog_bytes,
    catalog_digest,
)
from scripts.platform_inventory.models import (
    BrowserProjection,
    CapabilityCatalog,
    CapabilityDescriptor,
    CapabilityNamespace,
    HostBoundary,
    ProjectionLineage,
)


def make_catalog(identities: tuple[str, ...]) -> CapabilityCatalog:
    lineage = ProjectionLineage(
        source_repository="Rilan-Dev/hermes-agent",
        source_sha="a" * 40,
        upstream_repository="NousResearch/hermes-agent",
        upstream_sha="b" * 40,
        fork_main_sha="c" * 40,
        projection_root="upstream",
        manifest_sha256="d" * 64,
        lock_sha256="e" * 64,
    )
    descriptors = tuple(
        CapabilityDescriptor(
            namespace=CapabilityNamespace.PROVIDERS,
            identity=identity,
            label=identity,
            source_kind="runtime_registry",
            browser_projection=BrowserProjection.GENERATED_TABLE,
            host_boundary=HostBoundary.SERVER_MEDIATED,
            attributes=(),
            provenance_ids=(f"p-{identity}",),
        )
        for identity in identities
    )
    return CapabilityCatalog(
        schema_version=1,
        generator_version=1,
        lineage=lineage,
        descriptors=descriptors,
        relationships=(),
        provenance=(),
    )


def test_catalog_serialization_is_order_independent() -> None:
    first = make_catalog(("z", "a"))
    second = make_catalog(("a", "z"))
    assert canonical_catalog_bytes(first) == canonical_catalog_bytes(second)
    assert catalog_digest(first) == catalog_digest(second)
```

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_provenance.py \
  tests/scripts/platform_inventory/test_capability_catalog.py -q
```

- [ ] **Step 3: Add exact enums and dataclasses**

Add these values to `models.py`:

```python
class CapabilityNamespace(StrEnum):
    PROVIDERS = "providers"
    PROVIDER_PROFILES = "provider_profiles"
    AUTHENTICATION_PROVIDERS = "authentication_providers"
    MODEL_PROVIDERS = "model_providers"
    MODELS = "models"
    PLATFORMS = "platforms"
    CHANNELS = "channels"
    CHANNEL_CONNECTIONS = "channel_connections"
    ONBOARDING_FLOWS = "onboarding_flows"
    AGENTS = "agents"
    TOOLS = "tools"
    TOOLSETS = "toolsets"
    COMMANDS = "commands"
    WORKFLOWS = "workflows"
    CHAT_CAPABILITIES = "chat_capabilities"
    RUNTIME_EVENTS = "runtime_events"
    RUNTIME_LOGS = "runtime_logs"
    EXISTING_UI_SURFACES = "existing_ui_surfaces"


class BrowserProjection(StrEnum):
    EXISTING_WEB_UI = "existing_web_ui"
    REUSED_BROWSER_COMPONENT = "reused_browser_component"
    GENERATED_FORM = "generated_form"
    GENERATED_WIZARD = "generated_wizard"
    GENERATED_TABLE = "generated_table"
    GENERATED_LOG_VIEW = "generated_log_view"
    GENERATED_CHAT_VIEW = "generated_chat_view"
    SERVER_COMMAND_ACTION = "server_command_action"
    LOCAL_AGENT_ACTION = "local_agent_action"
    EMBEDDED_TERMINAL_ONLY = "embedded_terminal_only"
    HOST_ADMINISTRATION_ONLY = "host_administration_only"
    UNSUPPORTED_IN_BROWSER = "unsupported_in_browser"


class HostBoundary(StrEnum):
    BROWSER_DIRECT = "browser_direct"
    SERVER_MEDIATED = "server_mediated"
    LOCAL_AGENT_MEDIATED = "local_agent_mediated"
    EMBEDDED_TERMINAL_ONLY = "embedded_terminal_only"
    HOST_ADMINISTRATION_ONLY = "host_administration_only"
    UNSUPPORTED_IN_BROWSER = "unsupported_in_browser"
```

Add frozen dataclasses `ProvenanceRecord`, `CapabilityDescriptor`, `CapabilityRelationship`, and `CapabilityCatalog` with the exact fields defined by the approved design specification.

- [ ] **Step 4: Implement provenance IDs**

Create `provenance.py`:

```python
from __future__ import annotations

import hashlib
import json

from .models import HostBoundary, ProjectionRecord, ProvenanceRecord


def provenance_from_projection(
    *,
    repository: str,
    source_commit: str,
    record: ProjectionRecord,
    host_boundary: HostBoundary,
    runtime_registry_identity: str | None = None,
    manifest_identity: str | None = None,
    generator_version: int = 1,
) -> ProvenanceRecord:
    identity = {
        "source_repository": repository,
        "source_commit": source_commit,
        "source_path": record.source,
        "source_blob_sha": record.git_blob_sha,
        "source_object_mode": record.git_mode,
        "runtime_registry_identity": runtime_registry_identity,
        "manifest_identity": manifest_identity,
    }
    provenance_id = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return ProvenanceRecord(
        provenance_id=provenance_id,
        source_repository=repository,
        source_commit=source_commit,
        source_path=record.source,
        projected_path=record.projected_path,
        source_blob_sha=record.git_blob_sha,
        source_object_mode=record.git_mode,
        subsystem=record.subsystem,
        classification=record.classification,
        host_boundary=host_boundary,
        runtime_registry_identity=runtime_registry_identity,
        manifest_identity=manifest_identity,
        generator_version=generator_version,
    )
```

- [ ] **Step 5: Implement canonical JSON and validation**

`capability_catalog.py` sorts descriptors by `(namespace, identity)`, relationships by their complete source/kind/target tuple, and provenance by `provenance_id`. It rejects duplicate identities, dangling relationship endpoints, missing provenance IDs, non-scalar attributes, unknown projection/boundary values, and non-empty values under attribute keys containing `secret`, `token`, `password`, `authorization`, `credential`, or `api_key`.

```python
def canonical_catalog_bytes(catalog: CapabilityCatalog) -> bytes:
    validate_catalog(catalog)
    payload = canonical_catalog_data(catalog)
    return (
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def catalog_digest(catalog: CapabilityCatalog) -> str:
    return hashlib.sha256(canonical_catalog_bytes(catalog)).hexdigest()
```

- [ ] **Step 6: Verify and commit**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_provenance.py \
  tests/scripts/platform_inventory/test_capability_catalog.py -q
uv run ruff check scripts/platform_inventory tests/scripts/platform_inventory

git add scripts/platform_inventory/models.py \
  scripts/platform_inventory/provenance.py \
  scripts/platform_inventory/capability_catalog.py \
  tests/scripts/platform_inventory/test_provenance.py \
  tests/scripts/platform_inventory/test_capability_catalog.py
git commit -m "feat(inventory): define source capability catalogue"
```

---

### Task 3: Extend the Existing Isolated Runtime Probe

**Files:**
- Modify: `scripts/platform_inventory/models.py`
- Modify: `scripts/platform_inventory/probe_entrypoint.py`
- Modify: `scripts/platform_inventory/runtime_probe.py`
- Modify: `tests/scripts/platform_inventory/test_runtime_probe.py`
- Create: `tests/scripts/platform_inventory/test_runtime_capability_metadata.py`

**Interfaces:**
- Extends the existing `RegistrySnapshot`; it does not create alternate registries.
- Probe root is the exact projected `upstream/` directory.

- [ ] **Step 1: Write failing metadata parsing tests**

```python
import json

from scripts.platform_inventory.runtime_probe import parse_probe_output


def test_probe_preserves_provider_identity_layers() -> None:
    payload = {
        "platforms": [],
        "platform_concrete": [],
        "platform_deferred": [],
        "provider_profiles": ["openai"],
        "provider_aliases": {},
        "auth_providers": ["openai-codex"],
        "canonical_providers": ["openai"],
        "model_catalog_providers": ["openai"],
        "transports": [],
        "service_providers": {},
        "service_provider_builtins": {},
        "service_provider_plugins": {},
        "toolsets": {},
        "toolset_includes": {},
        "tools": [],
        "tool_to_toolset": {},
        "imported_tool_modules": [],
        "probe_errors": [],
        "platform_metadata": [],
        "provider_profile_metadata": [
            {
                "name": "openai",
                "aliases": [],
                "auth_type": "api_key",
                "env_vars": ["OPENAI_API_KEY"],
                "api_mode": "responses",
                "base_url": "",
                "supports_health_check": True,
                "supports_vision": True,
            }
        ],
        "auth_provider_metadata": [
            {
                "id": "openai-codex",
                "name": "OpenAI Codex",
                "auth_type": "oauth",
                "api_key_env_vars": [],
                "base_url_env_var": "",
                "inference_base_url": "",
            }
        ],
        "provider_catalog": [],
        "provider_catalog_slugs": [],
    }
    snapshot = parse_probe_output(json.dumps(payload))
    assert snapshot.provider_profile_metadata[0]["name"] == "openai"
    assert snapshot.auth_provider_metadata[0]["id"] == "openai-codex"
```

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_runtime_probe.py \
  tests/scripts/platform_inventory/test_runtime_capability_metadata.py -q
```

- [ ] **Step 3: Reuse extraction probe metadata behavior**

Move the source-neutral metadata extraction behavior already present in `scripts/extraction/registry_probe.py` into `scripts/platform_inventory/probe_entrypoint.py`. Extend the payload with:

```python
"platform_metadata": [],
"provider_profile_metadata": [],
"auth_provider_metadata": [],
"provider_catalog": [],
"provider_catalog_slugs": [],
```

Populate those fields from the same platform registry, provider profiles, authentication registry, canonical provider catalogue, model catalogue, transports, service-provider registries, tool registry, and toolset registry already used by the existing probe.

- [ ] **Step 4: Harden the launcher**

Use this exact environment in `probe_runtime()`:

```python
env.update(
    {
        "HERMES_HOME": home,
        "HERMES_PROFILE": "inventory",
        "HERMES_INVENTORY_MODE": "1",
        "HERMES_ENABLE_PROJECT_PLUGINS": "0",
        "HERMES_SAFE_MODE": "0",
        "HERMES_PLUGINS_DEBUG": "0",
        "PYTHONNOUSERSITE": "1",
        "PYTHONHASHSEED": "0",
        "OPENROUTER_API_KEY": "",
        "OPENAI_API_KEY": "",
        "NOUS_API_KEY": "",
        "PYTHONPATH": str(repository),
    }
)
```

Block `socket.create_connection`, `socket.getaddrinfo`, `socket.socket.connect`, and `socket.socket.connect_ex` before importing runtime registries. Run with `cwd=view.projection_root`; do not include the original checkout root in `PYTHONPATH`.

- [ ] **Step 5: Parse exact metadata keys**

Add immutable metadata fields to `RegistrySnapshot`. Validate required key sets and scalar/list value types. Sort platform records by `name`, profile records by `name`, authentication records by `id`, and provider-catalog records by `slug`. Reject missing or unknown metadata keys.

- [ ] **Step 6: Verify and commit**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_runtime_probe.py \
  tests/scripts/platform_inventory/test_runtime_capability_metadata.py -q
uv run pytest tests/scripts/platform_inventory -q
uv run ruff check scripts/platform_inventory tests/scripts/platform_inventory

git add scripts/platform_inventory/models.py \
  scripts/platform_inventory/probe_entrypoint.py \
  scripts/platform_inventory/runtime_probe.py \
  tests/scripts/platform_inventory/test_runtime_probe.py \
  tests/scripts/platform_inventory/test_runtime_capability_metadata.py
git commit -m "feat(inventory): enrich isolated runtime probe"
```

---

### Task 4: Derive Provider, Channel, Tool, and Identity Relationships

**Files:**
- Modify: `scripts/platform_inventory/capability_catalog.py`
- Modify: `scripts/platform_inventory/manifests.py`
- Create: `tests/scripts/platform_inventory/test_capability_relationships.py`
- Modify: `tests/scripts/platform_inventory/test_manifests.py`

**Interfaces:**
- `build_source_capabilities(view, plugins, registries) -> CapabilityCatalog`.

- [ ] **Step 1: Write failing relationship tests**

```python
from scripts.platform_inventory.models import CapabilityNamespace


def test_alias_is_relationship_not_identity_merge() -> None:
    catalog = build_catalog_for_test(
        provider_profiles=("openai",),
        provider_aliases={"gpt": "openai"},
    )
    identities = {
        item.identity
        for item in catalog.descriptors
        if item.namespace is CapabilityNamespace.PROVIDER_PROFILES
    }
    assert identities == {"gpt", "openai"}
    assert any(
        relation.kind == "alias_of"
        and relation.source_identity == "gpt"
        and relation.target_identity == "openai"
        for relation in catalog.relationships
    )
```

Define `build_catalog_for_test()` in the same test module using direct `ProjectedSourceView`, `PluginRecord`, and `RegistrySnapshot` constructors, with empty tuples/maps for unrelated fields.

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_capability_relationships.py \
  tests/scripts/platform_inventory/test_manifests.py -q
```

- [ ] **Step 3: Make manifest discovery projection-root aware**

`discover_plugins(view.projection_root, (Path("plugins"),))` must return paths relative to the projection root. For every returned manifest and entrypoint, require a matching `ProjectionRecord`; fail with `InventoryError` when provenance is absent.

- [ ] **Step 4: Build descriptors from existing source identities**

Create descriptors for every identity in the existing registries and manifests:

```text
platforms and platform manifests
provider profiles and aliases
authentication providers
canonical provider catalogue
model-provider catalogue
transports
service-provider families
tools
toolsets and toolset includes
```

Projection decisions are generic and source-derived:

```python
def projection_for_auth(auth_type: str) -> tuple[BrowserProjection, HostBoundary]:
    if auth_type == "oauth":
        return BrowserProjection.GENERATED_WIZARD, HostBoundary.SERVER_MEDIATED
    if auth_type == "api_key":
        return BrowserProjection.GENERATED_FORM, HostBoundary.SERVER_MEDIATED
    return BrowserProjection.UNSUPPORTED_IN_BROWSER, HostBoundary.UNSUPPORTED_IN_BROWSER
```

Do not branch on provider/channel identity.

- [ ] **Step 5: Add explicit source relationships**

Supported relationship kinds in this cycle are exactly:

```text
alias_of
manifest_runtime_identity
canonical_provider_profile
profile_authentication
profile_model_catalog
profile_transport
service_provider_family
tool_in_toolset
toolset_includes_toolset
```

Reject a relationship whose source or target descriptor does not exist.

- [ ] **Step 6: Verify and commit**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_capability_catalog.py \
  tests/scripts/platform_inventory/test_capability_relationships.py \
  tests/scripts/platform_inventory/test_manifests.py -q
uv run ruff check scripts/platform_inventory tests/scripts/platform_inventory

git add scripts/platform_inventory/capability_catalog.py \
  scripts/platform_inventory/manifests.py \
  tests/scripts/platform_inventory/test_capability_relationships.py \
  tests/scripts/platform_inventory/test_manifests.py
git commit -m "feat(inventory): derive source capability relationships"
```

---

### Task 5: Classify CLI, TUI, and Existing UI Coverage

**Files:**
- Create: `scripts/platform_inventory/command_projection.py`
- Create: `scripts/platform_inventory/ui_reuse.py`
- Modify: `scripts/platform_inventory/frontend_map.py`
- Create: `tests/scripts/platform_inventory/test_command_projection.py`
- Create: `tests/scripts/platform_inventory/test_ui_reuse.py`
- Modify: `tests/scripts/platform_inventory/test_frontend_map.py`

**Interfaces:**
- `scan_command_projection(view) -> tuple[CapabilityDescriptor, ...]`.
- `scan_ui_reuse(view) -> tuple[CapabilityDescriptor, ...]`.
- Every discovered item receives exactly one projection class.

- [ ] **Step 1: Write failing discovery tests**

```python
def test_fire_command_receives_generated_form_classification(tmp_path: Path) -> None:
    view = write_single_file_view(
        tmp_path,
        "hermes_cli/main.py",
        """
import fire

def configure(provider: str):
    return provider

fire.Fire({'configure': configure})
""",
    )
    descriptors = scan_command_projection(view)
    configure = next(item for item in descriptors if item.identity == "configure")
    assert configure.browser_projection.value == "generated_form"


def test_electron_bound_component_is_not_browser_reusable(tmp_path: Path) -> None:
    view = write_single_file_view(
        tmp_path,
        "apps/desktop/src/Terminal.tsx",
        "export const Terminal = () => window.hermesDesktop.openTerminal();",
    )
    descriptor = scan_ui_reuse(view)[0]
    assert descriptor.browser_projection.value == "local_agent_action"
```

Define `write_single_file_view()` in the same test module. It writes one projected file plus one exact lock record, then calls `load_projected_source_view()`.

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_command_projection.py \
  tests/scripts/platform_inventory/test_ui_reuse.py \
  tests/scripts/platform_inventory/test_frontend_map.py -q
```

- [ ] **Step 3: Implement AST command discovery**

Discover literal command registrations from:

- dictionaries passed to `fire.Fire()`;
- `argparse.add_parser()` and `argparse.add_argument()` calls;
- literal Click/Typer decorators when present in source;
- referenced handler functions.

Extract only source-declared command name, handler path, scalar annotations, literal defaults, required flags, and literal choices. Never execute handlers during scanning.

Use this ordered classifier:

```python
def classify_command(command: CommandRecord):
    if command.uses_pty_or_interactive_terminal:
        return BrowserProjection.EMBEDDED_TERMINAL_ONLY, HostBoundary.EMBEDDED_TERMINAL_ONLY
    if command.uses_host_administration_or_process_control:
        return BrowserProjection.HOST_ADMINISTRATION_ONLY, HostBoundary.HOST_ADMINISTRATION_ONLY
    if command.uses_local_filesystem_or_ssh:
        return BrowserProjection.LOCAL_AGENT_ACTION, HostBoundary.LOCAL_AGENT_MEDIATED
    if command.arguments_are_finite_scalars:
        return BrowserProjection.GENERATED_FORM, HostBoundary.SERVER_MEDIATED
    return BrowserProjection.UNSUPPORTED_IN_BROWSER, HostBoundary.UNSUPPORTED_IN_BROWSER
```

- [ ] **Step 4: Implement UI reuse scanning**

Scan projected JavaScript/TypeScript source records. Classify:

- browser component without native globals as `reused_browser_component`;
- existing dashboard route as `existing_web_ui`;
- Electron IPC, `window.hermesDesktop`, PTY, SSH, process, or host-filesystem use as the matching local/terminal/host class;
- TUI table/log/chat renderer semantics as generated table/log/chat views;
- unknown semantics as `unsupported_in_browser`.

Extend `FrontendMap` with source surface records containing source path, exported identity, routes, API paths, WebSocket paths, and native-global references.

- [ ] **Step 5: Prove no omissions**

Tests assert all discovered descriptors have non-empty provenance and a projection class. Parse failures remain visible as `unsupported_in_browser`; they are not silently skipped.

- [ ] **Step 6: Verify and commit**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_command_projection.py \
  tests/scripts/platform_inventory/test_ui_reuse.py \
  tests/scripts/platform_inventory/test_frontend_map.py -q
uv run pytest tests/scripts/platform_inventory -q
uv run ruff check scripts/platform_inventory tests/scripts/platform_inventory

git add scripts/platform_inventory/command_projection.py \
  scripts/platform_inventory/ui_reuse.py \
  scripts/platform_inventory/frontend_map.py \
  tests/scripts/platform_inventory/test_command_projection.py \
  tests/scripts/platform_inventory/test_ui_reuse.py \
  tests/scripts/platform_inventory/test_frontend_map.py
git commit -m "feat(inventory): classify CLI TUI and source UI"
```

---

### Task 6: Generate Catalogue, Lock, and Review Reports

**Files:**
- Modify: `scripts/platform_inventory/cli.py`
- Create: `scripts/platform_inventory/catalog_reports.py`
- Create: `tests/scripts/platform_inventory/test_catalog_reports.py`
- Create: `tests/scripts/platform_inventory/test_catalog_cli.py`
- Generate: `extracted/hermes-connect-kit/catalog/capability-catalog.json`
- Generate: `extracted/hermes-connect-kit/catalog/capability-catalog-lock.json`
- Generate: `docs/platform/generated/capability-coverage.md`
- Generate: `docs/platform/generated/cli-tui-browser-projection.md`
- Generate: `docs/platform/generated/source-ui-reuse.md`

**Interfaces:**
- CLI: `uv run python -m scripts.platform_inventory catalog`.
- Check mode: `uv run python -m scripts.platform_inventory catalog --check`.

- [ ] **Step 1: Write failing CLI tests**

```python
def test_catalog_command_writes_deterministic_artifacts(tmp_path: Path) -> None:
    repository = write_complete_projected_repository(tmp_path)
    first = run_catalog_command(repository)
    assert first.returncode == 0
    catalog_path = repository / "extracted/hermes-connect-kit/catalog/capability-catalog.json"
    lock_path = repository / "extracted/hermes-connect-kit/catalog/capability-catalog-lock.json"
    first_catalog = catalog_path.read_bytes()
    first_lock = lock_path.read_bytes()
    second = run_catalog_command(repository)
    assert second.returncode == 0
    assert catalog_path.read_bytes() == first_catalog
    assert lock_path.read_bytes() == first_lock
    assert b"generated_at" not in first_lock
```

Define both helpers in the same test module: `write_complete_projected_repository()` creates the minimum valid lock/tree/registry fixture, and `run_catalog_command()` invokes `cli.main(["--root", str(root), "catalog"])` while capturing the exit value.

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_catalog_reports.py \
  tests/scripts/platform_inventory/test_catalog_cli.py -q
```

- [ ] **Step 3: Add the catalogue command**

Extend the parser:

```python
catalog = subparsers.add_parser("catalog")
catalog.add_argument(
    "--kit-root",
    type=Path,
    default=Path("extracted/hermes-connect-kit"),
)
catalog.add_argument("--check", action="store_true")
```

Execution order is fixed: validate projection, run isolated probe, discover manifests, scan commands/UI, build and validate catalogue, serialize canonical bytes, build reports and lock, then either compare in `--check` mode or write via temporary file plus `os.replace()`.

- [ ] **Step 4: Write exact lock data**

```python
lock_data = {
    "schema_version": 1,
    "generator_version": catalog.generator_version,
    "source_repository": view.lineage.source_repository,
    "source_sha": view.lineage.source_sha,
    "upstream_repository": view.lineage.upstream_repository,
    "upstream_sha": view.lineage.upstream_sha,
    "fork_main_sha": view.lineage.fork_main_sha,
    "projection_lock_sha256": view.lineage.lock_sha256,
    "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(),
    "artifacts": {
        path: hashlib.sha256(content).hexdigest()
        for path, content in sorted(generated_artifacts.items())
    },
}
```

- [ ] **Step 5: Render complete reports**

Coverage report includes counts by namespace, source kind, subsystem, classification, boundary, and projection class. CLI/TUI report lists every discovered identity. UI reuse report lists every source surface and native binding decision. Every report ends with:

```markdown
No capability is browser-exposed without reviewed source provenance.
```

- [ ] **Step 6: Generate twice and verify**

```bash
uv run python -m scripts.platform_inventory catalog
cp extracted/hermes-connect-kit/catalog/capability-catalog.json /tmp/catalog.json
cp extracted/hermes-connect-kit/catalog/capability-catalog-lock.json /tmp/catalog-lock.json
cp -R docs/platform/generated /tmp/platform-generated

uv run python -m scripts.platform_inventory catalog

diff -u /tmp/catalog.json extracted/hermes-connect-kit/catalog/capability-catalog.json
diff -u /tmp/catalog-lock.json extracted/hermes-connect-kit/catalog/capability-catalog-lock.json
diff -ru /tmp/platform-generated docs/platform/generated
uv run python -m scripts.platform_inventory catalog --check
```

- [ ] **Step 7: Verify and commit**

```bash
uv run pytest tests/scripts/platform_inventory -q
uv run ruff check scripts/platform_inventory tests/scripts/platform_inventory
git diff --check

git add scripts/platform_inventory/cli.py \
  scripts/platform_inventory/catalog_reports.py \
  tests/scripts/platform_inventory/test_catalog_reports.py \
  tests/scripts/platform_inventory/test_catalog_cli.py \
  extracted/hermes-connect-kit/catalog \
  docs/platform/generated
git commit -m "feat(inventory): generate capability catalogue"
```

**Checkpoint 1:** Stop for catalogue/provenance/coverage review before backend APIs.

---

### Task 7: Add Capability Domain, Permission, Port, and JSON Adapter

**Files:**
- Create: `platform/backend/src/agentic_platform/domain/capabilities.py`
- Create: `platform/backend/src/agentic_platform/ports/capabilities.py`
- Create: `platform/backend/src/agentic_platform/storage/catalog_json.py`
- Modify: `platform/backend/src/agentic_platform/auth/contracts.py`
- Modify: `platform/backend/src/agentic_platform/auth/policies.py`
- Create: `platform/backend/tests/domain/test_capabilities.py`
- Create: `platform/backend/tests/storage/test_catalog_json.py`
- Modify: `platform/backend/tests/auth/test_policies.py`

**Interfaces:**
- `CapabilityRepository.list_namespaces()`.
- `CapabilityRepository.list_descriptors(namespace, limit, after)`.
- `CapabilityRepository.get_descriptor(namespace, identity)`.
- `CapabilityRepository.get_provenance(provenance_id)`.

- [ ] **Step 1: Write failing adapter tests**

```python
import hashlib
import json
from pathlib import Path

import pytest

from agentic_platform.storage.catalog_json import (
    CatalogIntegrityError,
    JsonCapabilityRepository,
)


def write_catalog_files(tmp_path: Path) -> tuple[Path, Path]:
    catalog = {
        "schema_version": 1,
        "generator_version": 1,
        "lineage": {},
        "descriptors": [
            {
                "namespace": "providers",
                "identity": "openai",
                "label": "OpenAI",
                "source_kind": "runtime_registry",
                "browser_projection": "generated_table",
                "host_boundary": "server_mediated",
                "attributes": {},
                "provenance_ids": ["p1"],
            }
        ],
        "relationships": [],
        "provenance": [
            {
                "provenance_id": "p1",
                "source_repository": "Rilan-Dev/hermes-agent",
                "source_commit": "a" * 40,
                "source_path": "providers/__init__.py",
                "projected_path": "upstream/providers/__init__.py",
                "source_blob_sha": "b" * 40,
                "source_object_mode": "100644",
                "subsystem": "providers",
                "classification": "core",
                "host_boundary": "server_mediated",
                "runtime_registry_identity": "openai",
                "manifest_identity": None,
            }
        ],
    }
    catalog_bytes = (json.dumps(catalog, sort_keys=True) + "\n").encode()
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_bytes(catalog_bytes)
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(
        json.dumps({"schema_version": 1, "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest()}),
        encoding="utf-8",
    )
    return catalog_path, lock_path


def test_adapter_rejects_digest_mismatch(tmp_path: Path) -> None:
    catalog_path, lock_path = write_catalog_files(tmp_path)
    lock_path.write_text(
        json.dumps({"schema_version": 1, "catalog_sha256": "0" * 64}),
        encoding="utf-8",
    )
    with pytest.raises(CatalogIntegrityError, match="digest"):
        JsonCapabilityRepository(catalog_path, lock_path)
```

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  platform/backend/tests/domain/test_capabilities.py \
  platform/backend/tests/storage/test_catalog_json.py \
  platform/backend/tests/auth/test_policies.py -q
```

- [ ] **Step 3: Add immutable domain views**

Create frozen dataclasses:

```python
CapabilityNamespaceSummary(namespace: str, count: int)
CapabilityDescriptorView(namespace, identity, label, source_kind, browser_projection, host_boundary, attributes, provenance_ids)
CapabilityPage(items, next_cursor)
ProvenanceView(provenance_id, source_repository, source_commit, source_path, projected_path, source_blob_sha, source_object_mode, subsystem, classification, host_boundary, runtime_registry_identity, manifest_identity)
```

Use `tuple[tuple[str, JsonScalar], ...]` for attributes inside the domain.

- [ ] **Step 4: Implement port and adapter**

The adapter verifies the catalogue digest, schema version, descriptor uniqueness, and provenance references at construction. It sorts by `(namespace, identity)` and uses URL-safe base64 of `namespace + "\0" + identity` for cursors. It never returns generated dictionaries directly.

- [ ] **Step 5: Add permission**

Add:

```python
CAPABILITY_READ = "capability.read"
```

Grant it to owner, admin, operator, developer, and viewer. Do not change mutation permissions.

- [ ] **Step 6: Verify and commit**

```bash
uv run pytest \
  platform/backend/tests/domain/test_capabilities.py \
  platform/backend/tests/storage/test_catalog_json.py \
  platform/backend/tests/auth/test_policies.py -q
uv run pytest platform/backend/tests -q
uv run ruff check platform/backend/src platform/backend/tests

git add platform/backend/src/agentic_platform/domain/capabilities.py \
  platform/backend/src/agentic_platform/ports/capabilities.py \
  platform/backend/src/agentic_platform/storage/catalog_json.py \
  platform/backend/src/agentic_platform/auth/contracts.py \
  platform/backend/src/agentic_platform/auth/policies.py \
  platform/backend/tests/domain/test_capabilities.py \
  platform/backend/tests/storage/test_catalog_json.py \
  platform/backend/tests/auth/test_policies.py
git commit -m "feat(platform): load immutable capability catalogue"
```

---

### Task 8: Expose Read-Only Capability APIs

**Files:**
- Create: `platform/backend/src/agentic_platform/services/capabilities.py`
- Create: `platform/backend/src/agentic_platform/api/capabilities.py`
- Modify: `platform/backend/src/agentic_platform/api/app.py`
- Create: `platform/backend/tests/services/test_capabilities.py`
- Create: `platform/backend/tests/api/test_capabilities.py`
- Modify: `platform/backend/tests/api/test_app.py`

**Interfaces:**
- `GET /api/workspaces/{workspace_id}/capabilities`.
- `GET /api/workspaces/{workspace_id}/capabilities/{namespace}`.
- `GET /api/workspaces/{workspace_id}/capabilities/{namespace}/{identity}`.
- `GET /api/workspaces/{workspace_id}/capability-provenance/{provenance_id}`.

- [ ] **Step 1: Write failing API tests**

```python
def test_viewer_can_read_capability_catalogue() -> None:
    workspace_id = WorkspaceId.new()
    client = make_capability_client()
    response = client.get(
        f"/api/workspaces/{workspace_id}/capabilities/providers",
        headers=principal_headers(workspace_id, MembershipRole.VIEWER),
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["identity"] == "openai"


def test_cross_workspace_capability_access_is_not_found_safe() -> None:
    requested = WorkspaceId.new()
    principal = WorkspaceId.new()
    response = make_capability_client().get(
        f"/api/workspaces/{requested}/capabilities",
        headers=principal_headers(principal, MembershipRole.ADMIN),
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource_not_found"
```

Define `principal_headers()` and `make_capability_client()` in the same test module. The fake repository returns one `openai` descriptor and one provenance record.

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  platform/backend/tests/services/test_capabilities.py \
  platform/backend/tests/api/test_capabilities.py -q
```

- [ ] **Step 3: Implement service**

`CapabilityService` accepts `CapabilityRepository`, validates namespace/identity text, delegates pagination, and raises the existing not-found-safe domain error for missing descriptors/provenance. It imports no Hermes runtime module.

- [ ] **Step 4: Implement frozen API DTOs and routes**

Every route enforces:

```python
dependencies.authorization.require(
    principal,
    Permission.CAPABILITY_READ,
    resource_workspace_id=WorkspaceId.parse(workspace_id),
)
```

List endpoints accept `limit: Query(ge=1, le=100)` and an opaque `after` cursor. Attributes are returned as JSON objects after safe scalar validation.

- [ ] **Step 5: Inject repository dependency**

Extend `ApplicationDependencies`:

```python
capability_repository: CapabilityRepository
```

Register the capabilities router. Update every existing app fixture with a deterministic empty repository implementation rather than `None`.

- [ ] **Step 6: Verify and commit**

```bash
uv run pytest \
  platform/backend/tests/services/test_capabilities.py \
  platform/backend/tests/api/test_capabilities.py \
  platform/backend/tests/api/test_app.py -q
uv run pytest platform/backend/tests -q
uv run ruff check platform/backend/src platform/backend/tests

git add platform/backend/src/agentic_platform/services/capabilities.py \
  platform/backend/src/agentic_platform/api/capabilities.py \
  platform/backend/src/agentic_platform/api/app.py \
  platform/backend/tests/services/test_capabilities.py \
  platform/backend/tests/api/test_capabilities.py \
  platform/backend/tests/api/test_app.py
git commit -m "feat(platform): expose read-only capability APIs"
```

**Checkpoint 2:** Stop for API/security review before browser implementation.

---

### Task 9: Create the Independent Browser Package

**Files:**
- Create: `apps/platform-web/package.json`
- Create: `apps/platform-web/index.html`
- Create: `apps/platform-web/tsconfig.json`
- Create: `apps/platform-web/tsconfig.app.json`
- Create: `apps/platform-web/vite.config.ts`
- Create: `apps/platform-web/src/main.tsx`
- Create: `apps/platform-web/src/styles.css`
- Create: `apps/platform-web/src/test/package-boundary.test.ts`
- Modify: `package.json`
- Modify: `package-lock.json`

**Interfaces:**
- Existing root `apps/*` workspace discovers the package automatically.
- Backend URL is `VITE_PLATFORM_API_URL`, default `http://127.0.0.1:8000`.

- [ ] **Step 1: Write package-boundary test**

```typescript
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const root = resolve(import.meta.dirname, "../..");

describe("platform web boundary", () => {
  it("does not depend on Electron or desktop globals", () => {
    const packageJson = readFileSync(resolve(root, "package.json"), "utf8");
    const viteConfig = readFileSync(resolve(root, "vite.config.ts"), "utf8");
    expect(packageJson).not.toContain("electron");
    expect(viteConfig).not.toContain("hermesDesktop");
    expect(viteConfig).not.toContain("__HERMES_SESSION_TOKEN__");
  });
});
```

- [ ] **Step 2: Copy repository stack versions**

Use the exact dependency versions already declared by `web/package.json` for React, React DOM, React Router, Vite, TypeScript, Tailwind, Vitest, Lucide, and `@nous-research/ui`. Required scripts are:

```json
{
  "dev": "vite",
  "build": "tsc -b && vite build",
  "typecheck": "tsc -p . --noEmit",
  "test": "vitest run",
  "check": "npm run typecheck && npm run test && npm run build"
}
```

- [ ] **Step 3: Create browser-safe Vite config**

```typescript
import path from "node:path";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

const backend = process.env.VITE_PLATFORM_API_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@hermes/shared": path.resolve(__dirname, "../shared/src"),
    },
    dedupe: ["react", "react-dom"],
  },
  server: {
    proxy: {
      "/api": { target: backend, ws: true },
      "/health": { target: backend },
    },
  },
});
```

- [ ] **Step 4: Add root helper scripts**

Do not change the workspace array. Add:

```json
"install:platform-web": "npm install --workspace apps/platform-web",
"check:platform-web": "npm run check --workspace apps/platform-web"
```

- [ ] **Step 5: Install, verify, and commit**

```bash
npm install
npm run test --workspace apps/platform-web
npm run typecheck --workspace apps/platform-web
npm run build --workspace apps/platform-web

git add package.json package-lock.json apps/platform-web
git commit -m "feat(platform-web): add independent browser package"
```

---

### Task 10: Add Typed API Client and Generic Renderer Registry

**Files:**
- Create: `apps/platform-web/src/api/contracts.ts`
- Create: `apps/platform-web/src/api/errors.ts`
- Create: `apps/platform-web/src/api/client.ts`
- Create: `apps/platform-web/src/app/workspace.ts`
- Create: `apps/platform-web/src/renderers/contracts.ts`
- Create: `apps/platform-web/src/renderers/registry.tsx`
- Create: `apps/platform-web/src/renderers/GenericDescriptorList.tsx`
- Create: `apps/platform-web/src/renderers/GenericDescriptorDetail.tsx`
- Create: `apps/platform-web/src/test/api-client.test.ts`
- Create: `apps/platform-web/src/test/renderer-registry.test.tsx`

**Interfaces:**
- `PlatformApiClient` maps exactly to Task 8 routes.
- Renderer selection uses only `browser_projection`, never source identity.

- [ ] **Step 1: Write failing client/renderer tests**

```typescript
it("adds workspace principal headers", async () => {
  const requests: Request[] = [];
  const fetcher: typeof fetch = async (input, init) => {
    requests.push(new Request(input, init));
    return Response.json({ items: [], next_cursor: null });
  };
  const client = new PlatformApiClient({
    baseUrl: "http://platform.test",
    workspaceId: "11111111-1111-4111-8111-111111111111",
    userId: "22222222-2222-4222-8222-222222222222",
    role: "viewer",
    fetcher,
  });
  await client.listDescriptors("providers");
  expect(requests[0].headers.get("X-Workspace-ID")).toBe(
    "11111111-1111-4111-8111-111111111111",
  );
});

it("selects renderer from projection class", () => {
  const renderer = resolveDescriptorRenderer({
    namespace: "tools",
    identity: "example",
    label: "Example",
    source_kind: "runtime_registry",
    browser_projection: "generated_table",
    host_boundary: "server_mediated",
    attributes: {},
    provenance_ids: ["p1"],
  });
  expect(renderer.kind).toBe("table");
});
```

- [ ] **Step 2: Verify RED**

```bash
npm run test --workspace apps/platform-web -- \
  src/test/api-client.test.ts \
  src/test/renderer-registry.test.tsx
```

- [ ] **Step 3: Define exact JSON contracts**

```typescript
export type JsonScalar = string | number | boolean | null;

export interface CapabilityDescriptor {
  namespace: string;
  identity: string;
  label: string;
  source_kind: string;
  browser_projection: string;
  host_boundary: string;
  attributes: Record<string, JsonScalar>;
  provenance_ids: string[];
}

export interface CapabilityPage {
  items: CapabilityDescriptor[];
  next_cursor: string | null;
}
```

- [ ] **Step 4: Implement safe API errors and development principal**

`PlatformApiClient` throws `PlatformApiError(status, code, safeMessage)` for non-2xx responses and rejects non-JSON responses. It never returns raw error bodies to components.

```typescript
export function developmentPrincipal() {
  return {
    userId: import.meta.env.VITE_PLATFORM_USER_ID ?? "",
    role: import.meta.env.VITE_PLATFORM_ROLE ?? "viewer",
  } as const;
}
```

Display a configuration error when `userId` is blank; do not invent a production identity.

- [ ] **Step 5: Implement projection-class registry**

```typescript
const registry: Record<string, DescriptorRenderer> = {
  generated_form: { kind: "detail", component: GenericDescriptorDetail },
  generated_wizard: { kind: "detail", component: GenericDescriptorDetail },
  generated_table: { kind: "table", component: GenericDescriptorList },
  generated_log_view: { kind: "detail", component: GenericDescriptorDetail },
  generated_chat_view: { kind: "detail", component: GenericDescriptorDetail },
  existing_web_ui: { kind: "detail", component: GenericDescriptorDetail },
  reused_browser_component: { kind: "detail", component: GenericDescriptorDetail },
  server_command_action: { kind: "detail", component: GenericDescriptorDetail },
  local_agent_action: { kind: "detail", component: GenericDescriptorDetail },
  embedded_terminal_only: { kind: "detail", component: GenericDescriptorDetail },
  host_administration_only: { kind: "detail", component: GenericDescriptorDetail },
  unsupported_in_browser: { kind: "detail", component: GenericDescriptorDetail },
};
```

This cycle remains read-only; form/wizard/action classes show metadata and provenance without mutation buttons.

- [ ] **Step 6: Verify and commit**

```bash
npm run test --workspace apps/platform-web
npm run typecheck --workspace apps/platform-web
npm run build --workspace apps/platform-web

git add apps/platform-web/src/api \
  apps/platform-web/src/app/workspace.ts \
  apps/platform-web/src/renderers \
  apps/platform-web/src/test/api-client.test.ts \
  apps/platform-web/src/test/renderer-registry.test.tsx
git commit -m "feat(platform-web): add generic capability renderer"
```

---

### Task 11: Build Health, Catalogue, Provenance, and Inbox Pages

**Files:**
- Create: `apps/platform-web/src/app/App.tsx`
- Create: `apps/platform-web/src/app/router.tsx`
- Create: `apps/platform-web/src/features/health/HealthPage.tsx`
- Create: `apps/platform-web/src/features/catalog/CatalogPage.tsx`
- Create: `apps/platform-web/src/features/catalog/DescriptorPage.tsx`
- Create: `apps/platform-web/src/features/catalog/ProvenancePanel.tsx`
- Create: `apps/platform-web/src/features/inbox/InboxPage.tsx`
- Modify: `apps/platform-web/src/main.tsx`
- Modify: `apps/platform-web/src/styles.css`
- Create: `apps/platform-web/src/test/routes.test.tsx`

**Interfaces:**
- `/w/:workspaceId/health`.
- `/w/:workspaceId/catalog`.
- `/w/:workspaceId/catalog/:namespace`.
- `/w/:workspaceId/catalog/:namespace/:identity`.
- `/w/:workspaceId/inbox`.

- [ ] **Step 1: Write failing source-driven route tests**

```typescript
it("uses API namespaces instead of static source identities", () => {
  const html = renderCatalogForTest([
    { namespace: "channels", count: 20 },
    { namespace: "tools", count: 79 },
  ]);
  expect(html).toContain("channels");
  expect(html).toContain("tools");
  expect(html).not.toContain("OpenAI");
  expect(html).not.toContain("Telegram");
});

it("shows host boundary from descriptor data", () => {
  const html = renderDescriptorForTest({
    namespace: "commands",
    identity: "interactive-shell",
    label: "Interactive shell",
    source_kind: "source_command",
    browser_projection: "embedded_terminal_only",
    host_boundary: "embedded_terminal_only",
    attributes: {},
    provenance_ids: ["p1"],
  });
  expect(html).toContain("embedded_terminal_only");
});
```

Define both render helpers in the same test module using `renderToStaticMarkup()` from `react-dom/server`.

- [ ] **Step 2: Verify RED**

```bash
npm run test --workspace apps/platform-web -- src/test/routes.test.tsx
```

- [ ] **Step 3: Build the generic shell**

Use existing `@nous-research/ui` primitives. Permanent navigation contains only product routes: Health, Catalogue, and Inbox. Namespace navigation is fetched from the API; no namespace or source identity array is committed in the browser.

- [ ] **Step 4: Implement page states**

Each page handles exactly:

```text
loading
empty
offline
permission_denied
source_drift
runtime_error
ready
```

`CatalogPage` paginates using `next_cursor`. `DescriptorPage` shows source attributes, projection class, boundary, relationships, and provenance references. It contains no authentication/setup/execute controls.

- [ ] **Step 5: Implement provenance panel**

Display source repository, commit, source path, projected path, blob SHA, object mode, subsystem, classification, runtime identity, manifest identity, and host boundary. Do not display source contents or secret values.

- [ ] **Step 6: Integrate existing inbox list**

Call only `GET /api/workspaces/{workspace_id}/inbox/conversations`. Render platform ID, type, status, unread count, last-message text, and time. Do not add message sending or channel-specific controls.

- [ ] **Step 7: Verify and commit**

```bash
npm run test --workspace apps/platform-web
npm run typecheck --workspace apps/platform-web
npm run build --workspace apps/platform-web
npm run check:platform-web

git add apps/platform-web/src
git commit -m "feat(platform-web): render source capability explorer"
```

---

### Task 12: Full Verification and Human Review Gate

**Files:**
- Create: `docs/platform/01-source-derived-capability-catalog-review.md`
- Create: `docs/platform/SOURCE_DERIVED_CATALOG_REVIEW_GATE.md`

**Interfaces:**
- Produces exact command evidence and blocks all mutation slices.

- [ ] **Step 1: Verify projection and generated catalogue**

```bash
uv run python -m scripts.extraction.project_sources --check
uv run python -m scripts.platform_inventory catalog --check
```

- [ ] **Step 2: Run Python verification**

```bash
uv run ruff check \
  scripts/platform_inventory \
  tests/scripts/platform_inventory \
  platform/backend/src \
  platform/backend/tests

uv run pytest tests/scripts/platform_inventory -q
uv run pytest platform/backend/tests -q
uv run pytest tests/integration/platform_inventory -q
```

Record exact exits and pass/fail counts.

- [ ] **Step 3: Run browser verification**

```bash
npm run test --workspace apps/platform-web
npm run typecheck --workspace apps/platform-web
npm run build --workspace apps/platform-web
```

Record exact Vitest count and command exits.

- [ ] **Step 4: Run source-only and secret guards**

```bash
! grep -RInE \
  '(Authorization: Bearer|api[_-]?key["'"']?\s*[:=]\s*["'"'][^"'"']+)' \
  extracted/hermes-connect-kit/catalog \
  docs/platform/generated \
  apps/platform-web/src

! grep -RInE \
  '(window\.hermesDesktop|electron|ipcRenderer)' \
  apps/platform-web/src apps/platform-web/vite.config.ts

! grep -RInE \
  '(const|let|var)\s+(PROVIDERS|CHANNELS|TOOLS|MODELS)\s*=' \
  apps/platform-web/src
```

- [ ] **Step 5: Run diff guards**

```bash
IMPLEMENTATION_BASE="$(git merge-base HEAD origin/planning/channels-providers-phase2-2026-07-22)"

git diff --check

test -z "$(git diff --name-only "$IMPLEMENTATION_BASE"...HEAD -- .github)"
test -z "$(git diff --name-only "$IMPLEMENTATION_BASE"...HEAD -- extracted/hermes-connect-kit/upstream)"
```

- [ ] **Step 6: Write exact review evidence**

The review document records implementation base/head SHAs, projection/catalogue digests, counts by namespace/boundary/projection, relationship and provenance counts, CLI/TUI coverage, UI reuse decisions, API/browser routes, exact command outputs, secret/source-only guards, known unsupported boundaries, and self-critique.

Its final line is exactly:

```markdown
Provider, channel, agent, tool, workflow, command, and chat mutations remain blocked until their source-backed vertical slice is separately designed and approved.
```

- [ ] **Step 7: Write gate checklist and commit**

The gate requires confirmation of catalogue determinism, complete provenance, zero browser identity registries, zero CLI/TUI omissions, explicit host boundaries, no projected-source/workflow changes, correct authorization, and no Electron dependency.

```bash
git add docs/platform/01-source-derived-capability-catalog-review.md \
  docs/platform/SOURCE_DERIVED_CATALOG_REVIEW_GATE.md
git commit -m "docs(platform): record source catalogue review gate"
```

**Checkpoint 3:** Stop for human review. Do not begin provider authentication, channel onboarding, agent/tool execution, workflows, command execution, or chat sending.

## Plan Self-Review

Before execution, verify all twelve statements:

1. Phase 2 Checkpoints A–E are complete.
2. The implementation branch starts from the exact reviewed projection integration branch.
3. Existing `scripts/platform_inventory` code is extended rather than duplicated.
4. Projected source remains read-only.
5. Every descriptor originates from source, registry, manifest, command, or source UI.
6. Every descriptor/relationship has provenance.
7. Unsupported CLI/TUI/UI items remain visible in reports.
8. Backend product code imports only stable platform contracts.
9. Browser rendering switches only on generic projection classes.
10. No mutation feature is included.
11. No GitHub Actions workflow changes.
12. Every success claim is backed by observed command output.
