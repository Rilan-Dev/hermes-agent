# Source-Derived Capability Catalogue and Web Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a deterministic, provenance-complete capability catalogue from the reviewed Hermes projection, expose it through read-only workspace-safe APIs, and render it in an independent generic browser application without recreating provider, channel, tool, workflow, command, agent, onboarding, or chat business logic.

**Architecture:** Extend the existing `scripts/platform_inventory` package rather than creating a parallel inventory system. The catalogue builder consumes only the reviewed Phase 2 `projection-lock.json`, exact projected tree, refreshed registry snapshots, and existing source scanners; the platform backend loads the generated immutable catalogue through a stable port; `apps/platform-web` renders namespaces, descriptors, relationships, provenance, health, and the existing inbox list through generic source-derived contracts.

**Tech Stack:** Python 3.11, dataclasses, pathlib, AST, subprocess/Git plumbing, JSON/YAML, FastAPI, Pydantic, pytest, Ruff, React 19, TypeScript 6, Vite 8, Tailwind 4, React Router 7, Vitest 4, `@nous-research/ui`, and the repository's existing npm workspace.

## Global Constraints

- The execution branch must be created only after Phase 2 Checkpoint E has approved the exact projection and its integration base contains `extracted/hermes-connect-kit/upstream/` plus `extracted/hermes-connect-kit/projection-lock.json`.
- Do not execute this plan from current fork `main` at `d5a67ad32522273115d887560ca1c08a02bc7873`; that commit does not contain the approved projection.
- The reviewed combined source baseline is `269eb7b30e0bc3666c377e0325263e7b5bcf49b4` until Checkpoint A produces and approves a replacement.
- Every exposed capability must originate from a reviewed projected source object, isolated runtime registry record, manifest, source-owned command definition, or existing source UI surface.
- New code is limited to deterministic inspection, provenance, stable workspace-safe adapters, generic rendering, authorization, persistence boundaries, realtime-safe DTOs, and audit-safe diagnostics.
- Do not manually maintain provider, model, authentication, channel, tool, toolset, workflow, command, onboarding, agent, chat-capability, or source-UI identity lists.
- Do not import arbitrary `agent.*`, `gateway.*`, `hermes_cli.*`, `providers.*`, `tools.*`, plugin-manager internals, or projected modules from platform product code.
- Runtime inspection runs in an isolated `HERMES_HOME`, with project plugins disabled, user-site loading disabled, credentials blank, deterministic hash seed, and network access blocked.
- OpenAI API-key, OpenAI Codex OAuth/runtime, native model identifiers, and OpenAI-compatible endpoints remain separate identities.
- The exact projected tree is read-only input. Catalogue generation must never modify files under `extracted/hermes-connect-kit/upstream/`.
- Catalogue artifacts contain no timestamps, secret values, authorization headers, environment-variable values, tokens, or arbitrary tracebacks.
- No GitHub Actions workflow is added, enabled, or expanded by this plan.
- Every task follows RED → GREEN → focused regression → commit.
- Every checkpoint ends with a written self-review and an explicit diff guard.

## Required Execution Worktree

After Phase 2 Checkpoint E is approved, create an isolated implementation branch from the approved integration commit:

```bash
git fetch origin

git switch <approved-phase2-integration-branch>
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
- Both `test` commands exit 0.
- Projection verification exits 0.
- No implementation begins when any precondition fails.

## Target File Structure

```text
scripts/platform_inventory/
├── models.py                         # Extend existing inventory types
├── source_view.py                    # Validate projection lock and projected objects
├── provenance.py                     # Content-addressed provenance records
├── capability_catalog.py             # Descriptor/relationship builder
├── command_projection.py             # CLI/TUI discovery and classification
├── ui_reuse.py                       # Existing browser component reuse inventory
├── catalog_reports.py                # Deterministic Markdown reports
├── runtime_probe.py                  # Reuse isolated probe launcher
├── probe_entrypoint.py               # Extend source-owned runtime metadata capture
└── cli.py                            # Add `catalog` command

tests/scripts/platform_inventory/
├── test_source_view.py
├── test_provenance.py
├── test_capability_catalog.py
├── test_command_projection.py
├── test_ui_reuse.py
├── test_catalog_reports.py
└── test_catalog_cli.py

extracted/hermes-connect-kit/catalog/
├── capability-catalog.json           # Generated, immutable read model
└── capability-catalog-lock.json      # Generated content digests and lineage

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
    ├── app/App.tsx
    ├── app/router.tsx
    ├── app/workspace.ts
    ├── api/client.ts
    ├── api/contracts.ts
    ├── api/errors.ts
    ├── features/health/HealthPage.tsx
    ├── features/catalog/CatalogPage.tsx
    ├── features/catalog/DescriptorPage.tsx
    ├── features/catalog/ProvenancePanel.tsx
    ├── features/inbox/InboxPage.tsx
    ├── renderers/contracts.ts
    ├── renderers/registry.tsx
    ├── renderers/GenericDescriptorList.tsx
    ├── renderers/GenericDescriptorDetail.tsx
    ├── styles.css
    └── test/
        ├── api-client.test.ts
        ├── renderer-registry.test.tsx
        └── routes.test.tsx
```

---

### Task 1: Validate the Exact Projected Source View

**Files:**
- Create: `scripts/platform_inventory/source_view.py`
- Modify: `scripts/platform_inventory/models.py`
- Create: `tests/scripts/platform_inventory/test_source_view.py`

**Interfaces:**
- Consumes: `extracted/hermes-connect-kit/projection-lock.json` schema version 1 produced by Phase 2.
- Produces: `ProjectionRecord`, `ProjectionLineage`, and `ProjectedSourceView`.
- Public function: `load_projected_source_view(repo_root: Path, kit_root: Path) -> ProjectedSourceView`.

- [ ] **Step 1: Write failing lock and byte-parity tests**

```python
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.platform_inventory.models import InventoryError
from scripts.platform_inventory.source_view import load_projected_source_view


def test_source_view_rejects_projected_byte_drift(tmp_path: Path) -> None:
    kit = tmp_path / "extracted/hermes-connect-kit"
    projected = kit / "upstream/providers/example.py"
    projected.parent.mkdir(parents=True)
    projected.write_bytes(b"VALUE = 2\n")
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
                "projected_path": "upstream/providers/example.py",
                "subsystem": "providers",
                "classification": "core",
                "planned_layer": "vendor",
                "reason": "Provider source.",
                "sha256": hashlib.sha256(b"VALUE = 1\n").hexdigest(),
                "size_bytes": len(b"VALUE = 1\n"),
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

    with pytest.raises(InventoryError, match="byte drift"):
        load_projected_source_view(tmp_path, kit)
```

Also add tests proving rejection of:

```python
@pytest.mark.parametrize(
    "projected_path",
    ["providers/example.py", "upstream/../escape.py", "/upstream/example.py"],
)
def test_source_view_rejects_noncanonical_projected_paths(
    tmp_path: Path, projected_path: str
) -> None:
    # Build the same minimal lock fixture with `projected_path`.
    # The helper returns a complete valid fixture except for this field.
    write_projection_fixture(tmp_path, projected_path=projected_path)
    with pytest.raises(InventoryError, match="projected path"):
        load_projected_source_view(
            tmp_path, tmp_path / "extracted/hermes-connect-kit"
        )
```

- [ ] **Step 2: Run tests and verify RED**

```bash
uv run pytest tests/scripts/platform_inventory/test_source_view.py -q
```

Expected: collection fails because `source_view` and the new models do not exist.

- [ ] **Step 3: Add immutable projection models**

Add to `scripts/platform_inventory/models.py`:

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

- [ ] **Step 4: Implement strict lock loading and object verification**

Create `scripts/platform_inventory/source_view.py` with:

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


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_projected_path(source: str) -> str:
    return PurePosixPath("upstream", source).as_posix()


def load_projected_source_view(
    repo_root: Path,
    kit_root: Path,
) -> ProjectedSourceView:
    repository = repo_root.resolve()
    kit = kit_root.resolve()
    lock_path = kit / "projection-lock.json"
    raw_bytes = lock_path.read_bytes()
    payload = json.loads(raw_bytes)
    if payload.get("schema_version") != 1:
        raise InventoryError("projection lock schema_version must be 1")
    if payload.get("projection_root") != "upstream":
        raise InventoryError("projection root must be upstream")

    records: list[ProjectionRecord] = []
    seen_sources: set[str] = set()
    seen_projected: set[str] = set()
    for row in payload.get("records", []):
        record = ProjectionRecord(**row)
        expected = _canonical_projected_path(record.source)
        if record.projected_path != expected:
            raise InventoryError(
                f"invalid projected path {record.projected_path}; expected {expected}"
            )
        if record.source in seen_sources or record.projected_path in seen_projected:
            raise InventoryError("projection lock contains duplicate source or path")
        seen_sources.add(record.source)
        seen_projected.add(record.projected_path)
        path = kit / record.projected_path
        if record.kind == "file":
            data = path.read_bytes()
            if len(data) != record.size_bytes or _sha256_bytes(data) != record.sha256:
                raise InventoryError(f"projected byte drift: {record.projected_path}")
        elif record.kind == "symlink":
            if not path.is_symlink() or path.readlink().as_posix() != record.link_target:
                raise InventoryError(f"projected symlink drift: {record.projected_path}")
        else:
            raise InventoryError(f"unsupported projected object kind: {record.kind}")
        records.append(record)

    lineage = ProjectionLineage(
        source_repository=payload["source_repository"],
        source_sha=payload["source_sha"],
        upstream_repository=payload["upstream_repository"],
        upstream_sha=payload["upstream_sha"],
        fork_main_sha=payload["fork_main_sha"],
        projection_root=payload["projection_root"],
        manifest_sha256=payload["manifest_sha256"],
        lock_sha256=_sha256_bytes(raw_bytes),
    )
    return ProjectedSourceView(
        repository_root=repository,
        kit_root=kit,
        projection_root=kit / "upstream",
        lineage=lineage,
        records=tuple(sorted(records, key=lambda item: item.source)),
    )
```

Wrap `OSError`, `json.JSONDecodeError`, `KeyError`, and `TypeError` in `InventoryError` with the lock path and safe detail. Reject extra files by invoking the Phase 2 `verify_tree()` interface when available rather than duplicating its traversal logic.

- [ ] **Step 5: Verify GREEN and regressions**

```bash
uv run pytest tests/scripts/platform_inventory/test_source_view.py -q
uv run pytest tests/scripts/platform_inventory -q
uv run ruff check scripts/platform_inventory tests/scripts/platform_inventory
```

Expected: all commands exit 0.

- [ ] **Step 6: Commit**

```bash
git add scripts/platform_inventory/models.py \
  scripts/platform_inventory/source_view.py \
  tests/scripts/platform_inventory/test_source_view.py
git commit -m "feat(inventory): validate projected source view"
```

---

### Task 2: Define the Deterministic Capability Catalogue Schema

**Files:**
- Modify: `scripts/platform_inventory/models.py`
- Create: `scripts/platform_inventory/provenance.py`
- Create: `scripts/platform_inventory/capability_catalog.py`
- Create: `tests/scripts/platform_inventory/test_provenance.py`
- Create: `tests/scripts/platform_inventory/test_capability_catalog.py`

**Interfaces:**
- Produces: `CapabilityNamespace`, `BrowserProjection`, `HostBoundary`, `ProvenanceRecord`, `CapabilityDescriptor`, `CapabilityRelationship`, and `CapabilityCatalog`.
- Public functions: `canonical_catalog_bytes(catalog) -> bytes` and `catalog_digest(catalog) -> str`.

- [ ] **Step 1: Write failing identity and determinism tests**

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
)


def test_catalog_serialization_is_order_independent() -> None:
    first = catalog_fixture(
        descriptors=(descriptor_fixture("providers", "z"), descriptor_fixture("providers", "a"))
    )
    second = catalog_fixture(
        descriptors=(descriptor_fixture("providers", "a"), descriptor_fixture("providers", "z"))
    )
    assert canonical_catalog_bytes(first) == canonical_catalog_bytes(second)
    assert catalog_digest(first) == catalog_digest(second)


def test_descriptor_keeps_native_identity_distinctions() -> None:
    api = CapabilityDescriptor(
        namespace=CapabilityNamespace.AUTHENTICATION_PROVIDERS,
        identity="openai-api-key",
        label="OpenAI API key",
        source_kind="runtime_registry",
        browser_projection=BrowserProjection.GENERATED_FORM,
        host_boundary=HostBoundary.SERVER_MEDIATED,
        attributes=(("auth_type", "api_key"),),
        provenance_ids=("p-api",),
    )
    codex = CapabilityDescriptor(
        namespace=CapabilityNamespace.AUTHENTICATION_PROVIDERS,
        identity="openai-codex",
        label="OpenAI Codex",
        source_kind="runtime_registry",
        browser_projection=BrowserProjection.GENERATED_WIZARD,
        host_boundary=HostBoundary.LOCAL_AGENT_MEDIATED,
        attributes=(("auth_type", "oauth"),),
        provenance_ids=("p-codex",),
    )
    assert api.identity != codex.identity
```

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_provenance.py \
  tests/scripts/platform_inventory/test_capability_catalog.py -q
```

Expected: missing schema types and serializer.

- [ ] **Step 3: Add exact enums and immutable records**

Add to `scripts/platform_inventory/models.py`:

```python
from enum import StrEnum


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


JsonScalar = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    provenance_id: str
    source_repository: str
    source_commit: str
    source_path: str
    projected_path: str
    source_blob_sha: str
    source_object_mode: str
    subsystem: str
    classification: str
    host_boundary: HostBoundary
    runtime_registry_identity: str | None
    manifest_identity: str | None
    generator_version: int


@dataclass(frozen=True, slots=True)
class CapabilityDescriptor:
    namespace: CapabilityNamespace
    identity: str
    label: str
    source_kind: str
    browser_projection: BrowserProjection
    host_boundary: HostBoundary
    attributes: tuple[tuple[str, JsonScalar], ...]
    provenance_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CapabilityRelationship:
    kind: str
    source_namespace: CapabilityNamespace
    source_identity: str
    target_namespace: CapabilityNamespace
    target_identity: str
    provenance_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CapabilityCatalog:
    schema_version: int
    generator_version: int
    lineage: ProjectionLineage
    descriptors: tuple[CapabilityDescriptor, ...]
    relationships: tuple[CapabilityRelationship, ...]
    provenance: tuple[ProvenanceRecord, ...]
```

- [ ] **Step 4: Implement content-addressed provenance**

Create `scripts/platform_inventory/provenance.py`:

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
    identity_payload = {
        "source_repository": repository,
        "source_commit": source_commit,
        "source_path": record.source,
        "source_blob_sha": record.git_blob_sha,
        "source_object_mode": record.git_mode,
        "runtime_registry_identity": runtime_registry_identity,
        "manifest_identity": manifest_identity,
    }
    provenance_id = hashlib.sha256(
        json.dumps(identity_payload, sort_keys=True, separators=(",", ":")).encode()
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

- [ ] **Step 5: Implement canonical serialization and validation**

Create `scripts/platform_inventory/capability_catalog.py` with validation that:

```python
_REQUIRED_NAMESPACES = frozenset(CapabilityNamespace)


def canonical_catalog_data(catalog: CapabilityCatalog) -> dict[str, object]:
    descriptors = sorted(
        catalog.descriptors,
        key=lambda item: (item.namespace.value, item.identity),
    )
    relationships = sorted(
        catalog.relationships,
        key=lambda item: (
            item.source_namespace.value,
            item.source_identity,
            item.kind,
            item.target_namespace.value,
            item.target_identity,
        ),
    )
    provenance = sorted(catalog.provenance, key=lambda item: item.provenance_id)
    return {
        "schema_version": catalog.schema_version,
        "generator_version": catalog.generator_version,
        "lineage": asdict(catalog.lineage),
        "descriptors": [asdict(item) for item in descriptors],
        "relationships": [asdict(item) for item in relationships],
        "provenance": [asdict(item) for item in provenance],
    }


def canonical_catalog_bytes(catalog: CapabilityCatalog) -> bytes:
    validate_catalog(catalog)
    return (
        json.dumps(
            canonical_catalog_data(catalog),
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")


def catalog_digest(catalog: CapabilityCatalog) -> str:
    return hashlib.sha256(canonical_catalog_bytes(catalog)).hexdigest()
```

`validate_catalog()` rejects duplicate `(namespace, identity)` pairs, dangling relationship endpoints, duplicate provenance IDs with different content, blank labels/identities, unknown projection values, non-scalar attributes, empty provenance references, and attribute keys matching `key`, `token`, `secret`, `password`, `authorization`, or `credential` when their values are non-empty.

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
git commit -m "feat(inventory): define capability catalogue schema"
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
- Consumes: exact projected Python source through a dependency-only interpreter environment.
- Produces: enriched `RegistrySnapshot` with platform metadata, provider-profile metadata, authentication metadata, provider-catalog metadata, tool/toolset identities, transport identities, and service-provider identities.

- [ ] **Step 1: Write failing enriched-probe tests**

```python
from scripts.platform_inventory.runtime_probe import parse_probe_output


def test_runtime_probe_preserves_provider_identity_layers() -> None:
    payload = complete_probe_payload(
        provider_profile_metadata=[
            {
                "name": "openai",
                "aliases": ["gpt"],
                "auth_type": "api_key",
                "env_vars": ["OPENAI_API_KEY"],
                "api_mode": "responses",
                "base_url": "",
                "supports_health_check": True,
                "supports_vision": True,
            }
        ],
        auth_provider_metadata=[
            {
                "id": "openai-codex",
                "name": "OpenAI Codex",
                "auth_type": "oauth",
                "api_key_env_vars": [],
                "base_url_env_var": "",
                "inference_base_url": "",
            }
        ],
    )
    snapshot = parse_probe_output(json.dumps(payload))
    assert snapshot.provider_profile_metadata[0]["name"] == "openai"
    assert snapshot.auth_provider_metadata[0]["id"] == "openai-codex"
```

Add a subprocess-environment test asserting:

```python
assert env["HERMES_ENABLE_PROJECT_PLUGINS"] == "0"
assert env["PYTHONNOUSERSITE"] == "1"
assert env["PYTHONHASHSEED"] == "0"
assert env["OPENAI_API_KEY"] == ""
```

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_runtime_probe.py \
  tests/scripts/platform_inventory/test_runtime_capability_metadata.py -q
```

Expected: metadata fields are missing.

- [ ] **Step 3: Reuse the existing extraction metadata functions**

Move the reusable `_platform_metadata`, `_profile_metadata`, `_auth_metadata`, and `_catalog_metadata` behavior from `scripts/extraction/registry_probe.py` into source-neutral helpers inside `scripts/platform_inventory/probe_entrypoint.py`. Extend the initial payload with:

```python
"platform_metadata": [],
"provider_profile_metadata": [],
"auth_provider_metadata": [],
"provider_catalog": [],
"provider_catalog_slugs": [],
```

Populate them from the same runtime registries already used by the existing probe. Do not add alternate provider/channel lists.

- [ ] **Step 4: Harden the isolated launcher**

Update `probe_runtime()` environment:

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

Block socket connection functions at the start of `collect_snapshot()` using the existing extraction probe behavior. The projected runtime probe must execute with `cwd=view.projection_root` and must not include the original checkout path in `PYTHONPATH`.

- [ ] **Step 5: Parse and freeze metadata deterministically**

Add tuple-of-read-only-mapping fields to `RegistrySnapshot` and parse each metadata list after validating its exact required key set. Sort by native identity (`name`, `id`, or `slug`). Reject unknown or missing keys rather than silently discarding them.

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
git commit -m "feat(inventory): enrich isolated runtime capability probe"
```

---

### Task 4: Build Source-Derived Provider, Channel, Tool, and Relationship Records

**Files:**
- Modify: `scripts/platform_inventory/capability_catalog.py`
- Modify: `scripts/platform_inventory/manifests.py`
- Create: `tests/scripts/platform_inventory/test_capability_relationships.py`
- Modify: `tests/scripts/platform_inventory/test_manifests.py`

**Interfaces:**
- Consumes: `ProjectedSourceView`, existing `discover_plugins()`, and enriched `RegistrySnapshot`.
- Produces: `build_source_capabilities(view, plugins, registries) -> tuple[descriptors, relationships, provenance]`.

- [ ] **Step 1: Write failing relationship tests**

```python
def test_catalog_keeps_platform_manifest_and_runtime_identity_linked() -> None:
    view = projected_view_fixture("plugins/platforms/telegram/plugin.yaml")
    plugins = (plugin_fixture(kind="platform", plugin_key="telegram"),)
    registries = registry_fixture(platforms=("telegram",))

    catalog = build_catalog_from_sources(view, plugins, registries)

    channel = descriptor(catalog, "channels", "telegram")
    assert channel.source_kind == "plugin_manifest"
    assert relationship_exists(
        catalog,
        kind="manifest_runtime_identity",
        source=("channels", "telegram"),
        target=("platforms", "telegram"),
    )


def test_provider_alias_is_relationship_not_identity_merge() -> None:
    registries = registry_fixture(
        provider_profiles=("openai",),
        provider_aliases={"gpt": "openai"},
    )
    catalog = build_catalog_from_sources(empty_view(), (), registries)
    assert descriptor(catalog, "provider_profiles", "openai")
    assert relationship_exists(
        catalog,
        kind="alias_of",
        source=("provider_profiles", "gpt"),
        target=("provider_profiles", "openai"),
    )
```

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_capability_relationships.py \
  tests/scripts/platform_inventory/test_manifests.py -q
```

- [ ] **Step 3: Make manifest discovery projection-root aware**

Change `discover_plugins(root, roots)` only by making all returned `manifest_path`, `directory`, and `files` values repository-relative to the passed `root`. When `root` is `view.projection_root`, paths therefore correspond to original source paths. Match each plugin record to `view.by_source()` and fail when its manifest or declared entrypoint lacks projection provenance.

- [ ] **Step 4: Build descriptors from existing identities**

Implement descriptor builders with no static identity arrays:

```python
def _runtime_descriptor(
    namespace: CapabilityNamespace,
    identity: str,
    label: str,
    *,
    projection: BrowserProjection,
    boundary: HostBoundary,
    attributes: Mapping[str, JsonScalar],
    provenance_ids: tuple[str, ...],
) -> CapabilityDescriptor:
    return CapabilityDescriptor(
        namespace=namespace,
        identity=identity,
        label=label or identity,
        source_kind="runtime_registry",
        browser_projection=projection,
        host_boundary=boundary,
        attributes=tuple(sorted(attributes.items())),
        provenance_ids=tuple(sorted(set(provenance_ids))),
    )
```

Generate descriptors for every identity already present in:

- `platforms`, `platform_metadata`, and platform plugin manifests;
- `provider_profiles` and provider-profile metadata;
- `auth_providers` and authentication metadata;
- `canonical_providers` and provider catalogue records;
- `model_catalog_providers`;
- `transports`;
- service-provider families;
- `tools`, `tool_to_toolset`, `toolsets`, and `toolset_includes`.

Projection and boundary are derived from source declarations and generic rules only:

- finite credential schema → `generated_form` / `server_mediated`;
- OAuth/browser callback declaration → `generated_wizard` / `server_mediated`;
- manifest channel configuration → `generated_wizard` / declared host boundary;
- tools/toolsets in this read-only cycle → `generated_table` / `server_mediated`;
- no safe source declaration → `unsupported_in_browser`.

- [ ] **Step 5: Build explicit relationship records**

Create only relationships supported by source evidence:

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

Reject a relationship when either endpoint descriptor is absent. Do not synthesize a missing endpoint merely to satisfy a relationship.

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

### Task 5: Classify CLI, TUI, and Existing UI Coverage Without Omissions

**Files:**
- Create: `scripts/platform_inventory/command_projection.py`
- Create: `scripts/platform_inventory/ui_reuse.py`
- Modify: `scripts/platform_inventory/frontend_map.py`
- Create: `tests/scripts/platform_inventory/test_command_projection.py`
- Create: `tests/scripts/platform_inventory/test_ui_reuse.py`
- Modify: `tests/scripts/platform_inventory/test_frontend_map.py`

**Interfaces:**
- `scan_command_projection(view: ProjectedSourceView) -> tuple[CapabilityDescriptor, ...]`.
- `scan_ui_reuse(view: ProjectedSourceView) -> tuple[CapabilityDescriptor, ...]`.
- Every discovered command/TUI action receives exactly one `BrowserProjection` classification.

- [ ] **Step 1: Write failing complete-coverage tests**

```python
def test_every_discovered_command_has_one_projection_class() -> None:
    view = view_with_files(
        {
            "hermes_cli/main.py": """
import fire

def configure(provider: str):
    return provider

if __name__ == '__main__':
    fire.Fire({'configure': configure})
""",
        }
    )
    descriptors = scan_command_projection(view)
    configure = next(item for item in descriptors if item.identity == "configure")
    assert configure.browser_projection is BrowserProjection.GENERATED_FORM


def test_desktop_global_marks_component_not_browser_reusable() -> None:
    view = view_with_files(
        {
            "apps/desktop/src/Terminal.tsx":
                "export const Terminal = () => window.hermesDesktop.openTerminal();",
        }
    )
    descriptor = scan_ui_reuse(view)[0]
    assert descriptor.browser_projection is BrowserProjection.LOCAL_AGENT_ACTION
```

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_command_projection.py \
  tests/scripts/platform_inventory/test_ui_reuse.py \
  tests/scripts/platform_inventory/test_frontend_map.py -q
```

- [ ] **Step 3: Implement deterministic Python command discovery**

Use `ast.parse()` over projected `.py` files selected from source-owned CLI roots already present in projection records. Discover:

- dictionary entries passed to `fire.Fire(...)`;
- `argparse` calls to `add_parser()` and `add_argument()` with literal names;
- functions decorated by literal Click/Typer command decorators when those decorators exist in source;
- command handler functions referenced by discovered registrations.

Store source-derived argument metadata only: name, required/default declaration, annotation text, choices, and handler source path. Do not execute command handlers.

Classify with ordered generic rules:

```python
def classify_command(command: CommandRecord) -> tuple[BrowserProjection, HostBoundary]:
    if command.imports_pty_or_interactive_terminal:
        return (
            BrowserProjection.EMBEDDED_TERMINAL_ONLY,
            HostBoundary.EMBEDDED_TERMINAL_ONLY,
        )
    if command.imports_host_admin_or_process_control:
        return (
            BrowserProjection.HOST_ADMINISTRATION_ONLY,
            HostBoundary.HOST_ADMINISTRATION_ONLY,
        )
    if command.requires_local_filesystem_or_ssh:
        return (
            BrowserProjection.LOCAL_AGENT_ACTION,
            HostBoundary.LOCAL_AGENT_MEDIATED,
        )
    if command.arguments_are_finite_scalars:
        return (
            BrowserProjection.GENERATED_FORM,
            HostBoundary.SERVER_MEDIATED,
        )
    return (
        BrowserProjection.UNSUPPORTED_IN_BROWSER,
        HostBoundary.UNSUPPORTED_IN_BROWSER,
    )
```

No discovered command is dropped when the final rule applies.

- [ ] **Step 4: Implement TUI and source-UI reuse inventory**

Scan projected files under source-owned UI roots found in lock records, not a manually maintained identity list. Use file paths and import references to classify:

- browser React component with no Electron/native global → `reused_browser_component`;
- existing dashboard route → `existing_web_ui`;
- `window.hermesDesktop`, Electron IPC, PTY, native process, SSH, or local filesystem binding → matching local/terminal/host projection;
- TUI chat/log/table semantics detected from source component base classes or renderer names → generated chat/log/table view;
- unknown UI semantics → `unsupported_in_browser`.

Extend `FrontendMap` with `source_surfaces`, each containing source path, exported component/page identity, route references, Electron reference flag, API references, and WebSocket references.

- [ ] **Step 5: Prove complete coverage**

Add assertions that:

```python
assert all(item.provenance_ids for item in descriptors)
assert len({item.identity for item in descriptors}) == len(descriptors)
assert not any(item.browser_projection is None for item in descriptors)
```

A parser error produces a visible `unsupported_in_browser` descriptor with safe error classification in the review report; it does not silently skip the file.

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
git commit -m "feat(inventory): classify CLI TUI and source UI surfaces"
```

---

### Task 6: Generate Catalogue Artifacts, Lock, and Review Reports

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
- CLI: `python -m scripts.platform_inventory --root . --output generated/platform_inventory catalog`.
- Lock contains catalogue digest, projection-lock digest, schema versions, source lineage, and generated artifact digests; no timestamps.

- [ ] **Step 1: Write failing CLI and determinism tests**

```python
def test_catalog_command_writes_expected_artifacts(projected_repo: Path) -> None:
    result = run_inventory(projected_repo, "catalog")
    assert result.returncode == 0
    assert (
        projected_repo
        / "extracted/hermes-connect-kit/catalog/capability-catalog.json"
    ).is_file()
    lock = json.loads(
        (
            projected_repo
            / "extracted/hermes-connect-kit/catalog/capability-catalog-lock.json"
        ).read_text(encoding="utf-8")
    )
    assert "generated_at" not in lock
    assert lock["catalog_sha256"]


def test_catalog_generation_is_byte_identical_twice(projected_repo: Path) -> None:
    run_inventory(projected_repo, "catalog", check=True)
    first = generated_catalog_bytes(projected_repo)
    run_inventory(projected_repo, "catalog", check=True)
    assert generated_catalog_bytes(projected_repo) == first
```

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  tests/scripts/platform_inventory/test_catalog_reports.py \
  tests/scripts/platform_inventory/test_catalog_cli.py -q
```

- [ ] **Step 3: Add the `catalog` command**

Extend `build_parser()`:

```python
catalog = subparsers.add_parser("catalog")
catalog.add_argument(
    "--kit-root",
    type=Path,
    default=Path("extracted/hermes-connect-kit"),
)
catalog.add_argument("--check", action="store_true")
```

The command sequence is fixed:

1. load and verify projected source view;
2. run isolated runtime probe against projection root;
3. discover manifests from projection root;
4. scan commands/TUI/source UI;
5. build and validate catalogue;
6. serialize canonical bytes;
7. build reports and lock;
8. in `--check`, compare committed bytes and exit 1 on any drift;
9. otherwise write with newline-stable UTF-8 and `os.replace()` temporary files.

- [ ] **Step 4: Build exact lock data**

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
        relative_path: hashlib.sha256(content).hexdigest()
        for relative_path, content in sorted(generated_artifacts.items())
    },
}
```

- [ ] **Step 5: Render complete review reports**

`capability-coverage.md` contains counts by namespace, source kind, subsystem, classification, host boundary, and browser projection. Empty groups print `0`.

`cli-tui-browser-projection.md` contains every discovered command/TUI identity, source path, projection class, boundary, and provenance ID.

`source-ui-reuse.md` contains every source UI surface with route/API/WebSocket references and browser-reuse decision.

All reports end with:

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

diff -u /tmp/catalog.json \
  extracted/hermes-connect-kit/catalog/capability-catalog.json
diff -u /tmp/catalog-lock.json \
  extracted/hermes-connect-kit/catalog/capability-catalog-lock.json
diff -ru /tmp/platform-generated docs/platform/generated
uv run python -m scripts.platform_inventory catalog --check
```

Expected: all diffs are empty and check exits 0.

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
git commit -m "feat(inventory): generate source capability catalogue"
```

**Checkpoint 1:** Stop for catalogue, provenance, CLI/TUI coverage, and source-UI reuse review before adding platform APIs.

---

### Task 7: Add Workspace-Safe Capability Domain and JSON Catalogue Adapter

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
- `CapabilityRepository.list_namespaces() -> tuple[CapabilityNamespaceSummary, ...]`.
- `CapabilityRepository.list_descriptors(namespace, limit, after) -> CapabilityPage`.
- `CapabilityRepository.get_descriptor(namespace, identity) -> CapabilityDescriptorView | None`.
- `CapabilityRepository.get_provenance(provenance_id) -> ProvenanceView | None`.

- [ ] **Step 1: Write failing domain and adapter tests**

```python
def test_catalog_adapter_rejects_digest_mismatch(tmp_path: Path) -> None:
    catalog, lock = write_catalog_fixture(tmp_path)
    lock_payload = json.loads(lock.read_text(encoding="utf-8"))
    lock_payload["catalog_sha256"] = "0" * 64
    lock.write_text(json.dumps(lock_payload), encoding="utf-8")

    with pytest.raises(CatalogIntegrityError, match="digest"):
        JsonCapabilityRepository(catalog, lock)


def test_capability_page_uses_stable_cursor(tmp_path: Path) -> None:
    repository = repository_fixture(tmp_path, identities=("a", "b", "c"))
    page = repository.list_descriptors("providers", limit=2, after=None)
    assert [item.identity for item in page.items] == ["a", "b"]
    assert page.next_cursor is not None
```

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  platform/backend/tests/domain/test_capabilities.py \
  platform/backend/tests/storage/test_catalog_json.py \
  platform/backend/tests/auth/test_policies.py -q
```

- [ ] **Step 3: Add browser-facing immutable domain views**

Create `domain/capabilities.py` with frozen dataclasses for:

```python
@dataclass(frozen=True, slots=True)
class CapabilityNamespaceSummary:
    namespace: str
    count: int


@dataclass(frozen=True, slots=True)
class CapabilityDescriptorView:
    namespace: str
    identity: str
    label: str
    source_kind: str
    browser_projection: str
    host_boundary: str
    attributes: tuple[tuple[str, JsonScalar], ...]
    provenance_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CapabilityPage:
    items: tuple[CapabilityDescriptorView, ...]
    next_cursor: str | None


@dataclass(frozen=True, slots=True)
class ProvenanceView:
    provenance_id: str
    source_repository: str
    source_commit: str
    source_path: str
    projected_path: str
    source_blob_sha: str
    source_object_mode: str
    subsystem: str
    classification: str
    host_boundary: str
    runtime_registry_identity: str | None
    manifest_identity: str | None
```

- [ ] **Step 4: Add the port and integrity-checked JSON adapter**

`ports/capabilities.py` defines the synchronous read-only protocol. `storage/catalog_json.py`:

- reads both files once at construction;
- verifies catalogue SHA-256 against lock;
- validates schema version 1;
- rejects duplicate descriptors/provenance;
- sorts descriptors by `(namespace, identity)`;
- encodes cursors as URL-safe base64 of `namespace\0identity`;
- does not expose raw generated dictionaries outside the adapter.

- [ ] **Step 5: Add read permission**

Add:

```python
CAPABILITY_READ = "capability.read"
```

Include it for owner, admin, operator, developer, and viewer. Keep all mutation permissions unchanged.

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

### Task 8: Expose Read-Only Capability and Provenance APIs

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
def test_capability_api_is_workspace_scoped_and_read_only() -> None:
    workspace_id = WorkspaceId.new()
    client = capability_client()
    response = client.get(
        f"/api/workspaces/{workspace_id}/capabilities/providers?limit=1",
        headers=_headers(workspace_id, MembershipRole.VIEWER),
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["identity"] == "openai"
    assert "secret" not in json.dumps(response.json()).lower()


def test_cross_workspace_capability_access_is_not_found_safe() -> None:
    response = capability_client().get(
        f"/api/workspaces/{WorkspaceId.new()}/capabilities",
        headers=_headers(WorkspaceId.new(), MembershipRole.ADMIN),
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "resource_not_found"
```

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  platform/backend/tests/services/test_capabilities.py \
  platform/backend/tests/api/test_capabilities.py -q
```

- [ ] **Step 3: Add service boundary**

Create `CapabilityService` that accepts `CapabilityRepository` and performs no Hermes imports. It validates namespace/identity input, delegates pagination, and converts missing records into the existing not-found-safe domain error.

- [ ] **Step 4: Add API DTOs and routes**

Use frozen Pydantic models. Convert tuple attributes into JSON objects only after checking keys against the generated schema. Apply:

```python
dependencies.authorization.require(
    principal,
    Permission.CAPABILITY_READ,
    resource_workspace_id=WorkspaceId.parse(workspace_id),
)
```

Every list endpoint uses `limit: Query(ge=1, le=100)` and an opaque `after` cursor.

- [ ] **Step 5: Inject repository dependency**

Extend `ApplicationDependencies`:

```python
capability_repository: CapabilityRepository
```

Include the new router in `create_app()`. Update every existing test fixture with a deterministic empty capability repository, not `None`.

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

**Checkpoint 2:** Stop for stable API and security review before creating the independent browser package.

---

### Task 9: Create the Independent Browser Package from Existing Source Stack

**Files:**
- Create: `apps/platform-web/package.json`
- Create: `apps/platform-web/index.html`
- Create: `apps/platform-web/tsconfig.json`
- Create: `apps/platform-web/tsconfig.app.json`
- Create: `apps/platform-web/vite.config.ts`
- Create: `apps/platform-web/src/main.tsx`
- Create: `apps/platform-web/src/styles.css`
- Modify: `package.json`

**Interfaces:**
- Browser package is an existing `apps/*` npm workspace.
- Development backend URL: `VITE_PLATFORM_API_URL`, default `http://127.0.0.1:8000`.
- No Electron global or dashboard session-token injection.

- [ ] **Step 1: Write the package boundary verification test**

Create `apps/platform-web/src/test/package-boundary.test.ts`:

```typescript
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const root = resolve(import.meta.dirname, "../..");

describe("platform web package boundary", () => {
  it("does not depend on Electron or the Hermes desktop global", () => {
    const packageJson = readFileSync(resolve(root, "package.json"), "utf8");
    const viteConfig = readFileSync(resolve(root, "vite.config.ts"), "utf8");
    expect(packageJson).not.toContain("electron");
    expect(viteConfig).not.toContain("hermesDesktop");
    expect(viteConfig).not.toContain("__HERMES_SESSION_TOKEN__");
  });
});
```

- [ ] **Step 2: Create package metadata by reusing repository versions**

Use the same React, Vite, TypeScript, Tailwind, React Router, Vitest, Lucide, and `@nous-research/ui` versions already present in `web/package.json`. Do not introduce a second UI framework. Required scripts:

```json
{
  "dev": "vite",
  "build": "tsc -b && vite build",
  "typecheck": "tsc -p . --noEmit",
  "test": "vitest run",
  "check": "npm run typecheck && npm run test && npm run build"
}
```

- [ ] **Step 3: Create browser-safe Vite configuration**

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

- [ ] **Step 4: Add the workspace helper script without changing workspace roots**

The root already includes `apps/*`; add only:

```json
"install:platform-web": "npm install --workspace apps/platform-web",
"check:platform-web": "npm run check --workspace apps/platform-web"
```

Do not change the `workspaces` array.

- [ ] **Step 5: Install, verify, and commit**

```bash
npm install
npm run test --workspace apps/platform-web
npm run typecheck --workspace apps/platform-web
npm run build --workspace apps/platform-web

git add package.json package-lock.json apps/platform-web
git commit -m "feat(platform-web): add independent browser package"
```

Expected: all commands exit 0 and the build writes only inside `apps/platform-web/dist/`.

---

### Task 10: Add Typed API Client and Descriptor Renderer Contracts

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
- `PlatformApiClient` methods map exactly to Task 8 routes.
- `resolveDescriptorRenderer(descriptor) -> DescriptorRenderer` uses source-derived `browser_projection`, never provider/channel identity switches.

- [ ] **Step 1: Write failing client and renderer tests**

```typescript
it("adds workspace principal headers to every request", async () => {
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

it("selects renderers by source projection class", () => {
  const renderer = resolveDescriptorRenderer(
    descriptorFixture({ browser_projection: "generated_table" }),
  );
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

export interface ApiErrorEnvelope {
  error: { code: string; message: string };
}
```

No provider/channel/tool union hard-codes source identities.

- [ ] **Step 4: Implement strict client errors**

`PlatformApiClient.request()` throws `PlatformApiError` containing HTTP status, stable code, and safe message. It rejects non-JSON responses and does not expose raw response bodies in rendered errors.

Workspace configuration is read from URL path plus environment-provided development principal values:

```typescript
export function developmentPrincipal() {
  return {
    userId: import.meta.env.VITE_PLATFORM_USER_ID ?? "",
    role: import.meta.env.VITE_PLATFORM_ROLE ?? "viewer",
  } as const;
}
```

The application displays a configuration error when the user ID is blank; it does not invent a production identity.

- [ ] **Step 5: Implement generic renderer registry**

Map only projection classes:

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

This cycle is read-only, so form/wizard/action classifications render metadata and provenance but no mutation controls.

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
git commit -m "feat(platform-web): add typed capability renderer"
```

---

### Task 11: Build Health, Catalogue, Provenance, and Existing Inbox Pages

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

- [ ] **Step 1: Write failing route and source-driven navigation tests**

```typescript
it("builds catalogue navigation from API namespaces", async () => {
  const html = await renderRoute("/w/ws/catalog", {
    namespaces: [
      { namespace: "channels", count: 20 },
      { namespace: "tools", count: 79 },
    ],
  });
  expect(html).toContain("channels");
  expect(html).toContain("tools");
  expect(html).not.toContain("OpenAI");
  expect(html).not.toContain("Telegram");
});

it("shows unsupported browser boundary from descriptor data", async () => {
  const html = await renderDescriptor(
    descriptorFixture({
      browser_projection: "embedded_terminal_only",
      host_boundary: "embedded_terminal_only",
    }),
  );
  expect(html).toContain("embedded_terminal_only");
});
```

- [ ] **Step 2: Verify RED**

```bash
npm run test --workspace apps/platform-web -- src/test/routes.test.tsx
```

- [ ] **Step 3: Build the source-derived application shell**

Use existing `@nous-research/ui` primitives for buttons, typography, spinners, and dialog/surface components. The permanent navigation contains only product-level routes (`Health`, `Catalogue`, `Inbox`). Catalogue namespace links are fetched from the API and are not committed as constants.

- [ ] **Step 4: Implement health and catalogue pages**

Every page implements exact states:

```text
loading
empty
offline
permission_denied
source_drift
runtime_error
ready
```

`CatalogPage` paginates with `next_cursor`. `DescriptorPage` displays all scalar attributes, relationship links returned by the API, browser boundary, and provenance IDs. It renders no setup/login/execute buttons in this cycle.

- [ ] **Step 5: Implement provenance panel**

Display source repository, source commit, source path, projected path, blob SHA, object mode, subsystem, classification, runtime identity, manifest identity, and host boundary. Do not display source file contents or secret values.

- [ ] **Step 6: Integrate the existing inbox list endpoint**

`InboxPage` calls only:

```text
GET /api/workspaces/{workspace_id}/inbox/conversations
```

Render platform ID, conversation type, status, unread count, last message text, and last-message time from the existing DTO. Do not add message sending or channel-specific controls.

- [ ] **Step 7: Verify accessibility, responsiveness, and commit**

```bash
npm run test --workspace apps/platform-web
npm run typecheck --workspace apps/platform-web
npm run build --workspace apps/platform-web
npm run check:platform-web

git add apps/platform-web/src
git commit -m "feat(platform-web): render source capability explorer"
```

Expected: all commands exit 0, routes build without Electron globals, and no source identity appears in a committed frontend constant.

---

### Task 12: Run Full Verification and Write the First-Cycle Review Gate

**Files:**
- Create: `docs/platform/01-source-derived-capability-catalog-review.md`
- Create: `docs/platform/SOURCE_DERIVED_CATALOG_REVIEW_GATE.md`
- Modify only if generated output changes: catalogue and generated reports from Task 6.

**Interfaces:**
- Produces complete command evidence and an explicit gate before provider/authentication mutation work.

- [ ] **Step 1: Verify exact projection and catalogue drift**

```bash
uv run python -m scripts.extraction.project_sources --check
uv run python -m scripts.platform_inventory catalog --check
```

Expected: both exit 0.

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

Record exact pass/fail counts and exit codes. Do not summarize an unexecuted command as passing.

- [ ] **Step 3: Run browser verification**

```bash
npm run test --workspace apps/platform-web
npm run typecheck --workspace apps/platform-web
npm run build --workspace apps/platform-web
```

Record exact Vitest count and build/typecheck exits.

- [ ] **Step 4: Run source-only guards**

```bash
! grep -RInE \
  '(OPENAI_API_KEY=.+|Authorization: Bearer|api[_-]?key["'"']?\s*[:=]\s*["'"'][^"'"']+)' \
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

Expected: each negated grep exits 0.

- [ ] **Step 5: Run diff guards**

```bash
git diff --check

UNEXPECTED_WORKFLOWS="$(git diff --name-only <implementation-base>...HEAD -- .github || true)"
test -z "$UNEXPECTED_WORKFLOWS"

PROJECTED_CHANGES="$(git diff --name-only <implementation-base>...HEAD -- \
  extracted/hermes-connect-kit/upstream || true)"
test -z "$PROJECTED_CHANGES"
```

Expected: no workflow or projected-source changes.

- [ ] **Step 6: Write exact review evidence**

`docs/platform/01-source-derived-capability-catalog-review.md` records:

- implementation base and head SHAs;
- projection-lock and catalogue-lock digests;
- descriptor counts by namespace;
- relationship and provenance counts;
- CLI/TUI classification counts with zero omissions;
- source UI reuse decisions;
- API routes added;
- browser routes added;
- exact commands, exits, and test counts;
- source-only and secret guards;
- known unsupported/host-bound capabilities;
- self-critique.

The final line is exactly:

```markdown
Provider, channel, agent, tool, workflow, command, and chat mutations remain blocked until their source-backed vertical slice is separately designed and approved.
```

- [ ] **Step 7: Create the review gate**

`SOURCE_DERIVED_CATALOG_REVIEW_GATE.md` requires human confirmation that:

```text
catalogue determinism is proven
all descriptors have provenance
no source identity list is manually maintained in the browser
CLI/TUI coverage has no omissions
host boundaries are explicit
no projected source changed
no workflow changed
read-only API authorization is correct
browser package has no Electron dependency
```

- [ ] **Step 8: Commit and stop**

```bash
git add docs/platform/01-source-derived-capability-catalog-review.md \
  docs/platform/SOURCE_DERIVED_CATALOG_REVIEW_GATE.md \
  extracted/hermes-connect-kit/catalog \
  docs/platform/generated

git commit -m "docs(platform): record source catalogue review gate"
```

**Checkpoint 3:** Stop for human review. Do not begin provider authentication, model selection, channel onboarding, agent execution, tool execution, workflow actions, CLI command execution, or chat sending.

## Plan Self-Review Checklist

Before publishing the implementation branch:

1. Every task traces to the approved source-derived design.
2. No task bypasses Phase 2 Checkpoints A–E.
3. Existing `scripts/platform_inventory` code is extended rather than duplicated.
4. The exact projected tree remains read-only.
5. Catalogue identities originate only from source, manifests, registries, commands, or source UI.
6. Every descriptor and relationship has provenance.
7. CLI/TUI and source UI scans retain unsupported entries rather than dropping them.
8. The backend imports only stable platform contracts.
9. The browser switches only on generic projection classes, never provider/channel/tool identities.
10. No mutation feature is included in this first cycle.
11. No GitHub Actions workflow is changed.
12. Every claimed pass is backed by observed command output.
