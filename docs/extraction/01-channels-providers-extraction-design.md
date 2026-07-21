# Channels, Onboarding, and AI Providers Extraction Design

**Status:** Review draft — documentation only  
**Repository:** `Rilan-Dev/hermes-agent`  
**Verified source ref:** `main` at `18bb6f1aeaa334badee6271fc3337f39ca6bfcfb`  
**Planning branch:** `planning/channels-providers-extraction-latest`

## 1. Goal

Extract the messaging-channel system, onboarding surfaces, and AI-provider configuration/runtime into a reusable application/package that can be embedded in other projects while remaining straightforward to refresh from the fork's `main` branch.

The extraction must preserve these existing contracts:

1. Platform adapters are discovered through the platform registry and plugin system.
2. Provider profiles are discovered lazily from bundled and user plugin directories.
3. Provider membership is sourced from the canonical provider catalog rather than duplicated UI lists.
4. Authentication supports API keys, OAuth/device flows, external processes, AWS SDK credentials, credential pools, and provider-specific refresh behavior.
5. Provider runtime selection works consistently for CLI, gateway, cron, TUI, desktop, and helper processes.
6. Messaging preserves session keys, authorization, pairing, delivery, thread routing, platform limits, hooks, and standalone/cron delivery.
7. Upstream updates can be imported without repeatedly resolving a large delete-vs-add conflict set.

## 2. Non-goals for the planning branch

This branch must not:

- delete or move production code;
- create the extracted application;
- rewrite imports;
- change provider or platform behavior;
- change secrets, config files, CI, packaging, or dependencies;
- open or merge a pull request into `main`;
- prune unrelated repository content.

The only allowed changes in this branch are extraction documents and later review corrections to those documents.

## 3. Architectural findings

### 3.1 Channels are a distributed subsystem

The channel implementation is not limited to `gateway/platforms/` or `plugins/platforms/`. It spans:

- gateway orchestration and message dispatch;
- platform registry and lazy adapter loading;
- plugin discovery and enablement;
- platform configuration and environment bridges;
- authorization, allowlists, pairing, and token locks;
- session-key construction and persistence;
- outbound, cross-platform, home-channel, cron, and standalone delivery;
- slash-command routing and running-agent guards;
- platform adapters, relay connectors, hooks, mirroring, and stream events;
- CLI setup/status/service management;
- agent construction and runtime provider resolution;
- tests covering shared and platform-specific behavior.

Copying only adapter files would produce an incomplete and unsafe extraction.

### 3.2 Providers are registry-driven

Provider support is split into several layers:

- `providers/` defines the declarative `ProviderProfile` contract and lazy registry.
- `plugins/model-providers/` contains bundled provider profiles and manifests.
- `hermes_cli/auth.py` owns credential types, auth state, refresh behavior, and provider runtime credentials.
- `hermes_cli/provider_catalog.py` creates the unified provider descriptor set used across CLI and GUI surfaces.
- `hermes_cli/inventory.py`, `models.py`, `model_switch.py`, and `model_setup_flows.py` own model discovery, picker data, setup, and selection.
- `hermes_cli/runtime_provider.py` resolves effective provider, endpoint, API mode, key, and credential pool for CLI, gateway, cron, and helpers.
- `agent/transports/` handles protocol-specific request/response behavior.
- `run_agent.py` and agent runtime modules consume the resolved provider contract.

The provider plugin README explicitly states that auth, config, model listing, doctor checks, metadata, runtime resolution, and chat-completions transport auto-wire from the registry. The extraction must retain that property.

### 3.3 Onboarding has multiple surfaces

There are three distinct onboarding/configuration surfaces:

1. **Contextual onboarding** in `agent/onboarding.py` for first-touch hints and consent-gated profile building.
2. **CLI onboarding/setup** in `hermes_cli/`, including model/provider selection and channel setup.
3. **Desktop/web onboarding** that consumes backend API contracts and adds presentation, ordering, and provider-specific UX.

The backend catalog is the source of truth. Desktop and web components are optional presentation layers and must not become new provider registries.

## 4. Extraction approaches considered

### Approach A — Two-layer in-repository extraction (recommended)

Create a new application/package inside the fork with:

- an **upstream-compatible source layer** that preserves selected Hermes paths and behavior;
- a **stable public facade** with clean interfaces for use by other projects;
- an extraction manifest and sync tool that refresh the source layer from `main`;
- characterization and contract tests around the public facade.

Advantages:

- smallest upstream merge burden;
- selected upstream files can be refreshed mechanically;
- preserves original behavior before refactoring;
- allows gradual replacement of host-specific dependencies;
- the extracted directory can later be split into another repository with `git subtree split` while preserving its history.

Trade-off: the first extraction contains compatibility wrappers and selected original layout rather than an immediate idealized rewrite.

### Approach B — Separate repository immediately

Use `git filter-repo`, subtree, or a custom projection to create a separate repository at the beginning.

Advantages:

- clean standalone repository immediately;
- independent release lifecycle.

Risks:

- source updates and extraction refactors are mixed from day one;
- every missed transitive dependency becomes a cross-repository problem;
- upstream synchronization requires a maintained patch queue before the extraction boundary is proven.

This is suitable only after the in-repository package passes contract tests.

### Approach C — Destructive prune branch

Create a branch from `main` and delete every unrelated file, leaving only selected channel/provider/onboarding code.

Advantages:

- visually simple repository tree.

Risks:

- severe merge conflicts whenever `main` changes;
- rename and delete noise obscures real upstream changes;
- difficult to distinguish intentionally excluded files from newly required dependencies;
- encourages direct edits to copied upstream code;
- makes future automated synchronization fragile.

This approach is rejected.

## 5. Recommended target structure

Working name: `hermes-connect-kit`. The name is provisional; the boundary matters more than the name.

```text
extracted/hermes-connect-kit/
├── README.md
├── pyproject.toml
├── extraction-manifest.yaml
├── src/
│   └── hermes_connect/
│       ├── __init__.py
│       ├── api/                     # Public service contracts and DTOs
│       ├── channels/
│       │   ├── service.py           # Stable host-facing channel service
│       │   ├── contracts.py
│       │   ├── registry.py
│       │   ├── configuration.py
│       │   ├── authorization.py
│       │   ├── sessions.py
│       │   ├── delivery.py
│       │   ├── relay/
│       │   └── adapters/
│       ├── providers/
│       │   ├── service.py           # Stable host-facing provider service
│       │   ├── contracts.py
│       │   ├── registry.py
│       │   ├── catalog.py
│       │   ├── runtime.py
│       │   ├── auth/
│       │   ├── transports/
│       │   └── profiles/
│       ├── onboarding/
│       │   ├── service.py
│       │   ├── contracts.py
│       │   ├── contextual.py
│       │   └── cli/
│       ├── config/
│       ├── compatibility/           # Explicit adapters to Hermes host services
│       └── vendor/                  # Mechanically synchronized source layer
├── plugins/
│   ├── platforms/                   # Manifest-driven platform plugins
│   └── model-providers/             # Manifest-driven provider plugins
├── apps/
│   └── reference-onboarding/        # Optional UI/reference consumer
├── scripts/
│   ├── build_inventory.py
│   ├── sync_from_hermes_main.py
│   ├── verify_manifest.py
│   └── report_upstream_drift.py
└── tests/
    ├── contracts/
    ├── characterization/
    ├── channels/
    ├── providers/
    ├── onboarding/
    └── sync/
```

### Why keep a synchronized source layer

Reorganizing all selected files during the first extraction would make future upstream diffs difficult to apply. The synchronized layer should retain source identities and record their origin SHA. The public facade provides the reusable API, while upstream files remain replaceable or patchable by path.

No consumer project should import directly from the synchronized/vendor layer. Only `hermes_connect.*` public contracts may be treated as stable.

## 6. Public boundaries to introduce

### Channel service

The reusable channel surface should expose operations such as:

- discover/list platform descriptors;
- validate and configure a platform;
- connect/disconnect enabled adapters;
- normalize an inbound event;
- authorize/pair a source;
- resolve a session key;
- send/reply/deliver media;
- send to explicit or home-channel targets;
- register hooks and receive lifecycle events.

The host application supplies agent execution through a callback/protocol rather than importing a concrete `AIAgent` inside the channel package.

### Provider service

The reusable provider surface should expose:

- discover/list provider descriptors;
- inspect authentication type and required credentials;
- start/continue/logout auth flows;
- resolve runtime credentials and API mode;
- list models and capabilities;
- create/select protocol transport;
- validate provider configuration and health;
- read/write model choice through a host-provided config store.

### Onboarding service

Onboarding should consume the channel/provider descriptors rather than own provider or platform lists. UI adapters may add ordering, labels, icons, and featured-provider treatment without changing membership.

## 7. Dependency inversion requirements

The following Hermes-specific dependencies must become explicit host ports before the package is reusable:

- configuration and secret storage;
- profile-aware home paths;
- session persistence;
- logging;
- agent/conversation execution;
- cron scheduling;
- tool invocation and send-message integration;
- plugin enablement storage;
- process/service management;
- browser opening and interactive terminal prompts;
- desktop/web transport bridges.

During the mechanical extraction these may use compatibility adapters. They must not remain hidden global imports in the final public service layer.

## 8. Implementation phases and review gates

### Phase 0 — Planning and inventory (this branch)

Deliver documents only. User review is required before Phase 1.

### Phase 1 — Reproducible inventory and characterization

- create the isolated implementation worktree from this planning branch;
- add an executable extraction manifest;
- generate exact source/test inventories from the filesystem and registries;
- add characterization tests against the current Hermes implementation;
- do not move production code yet.

**Gate:** review generated inventory and test matrix.

### Phase 2 — Mechanical source projection

- populate the synchronized source layer using the manifest;
- preserve original file identity and provenance;
- add import-compatibility shims;
- run selected upstream tests unchanged where possible.

**Gate:** no behavior refactor until characterization tests pass.

### Phase 3 — Stable public services

- introduce channel, provider, and onboarding contracts;
- replace direct host imports with explicit ports;
- keep adapters/profiles plugin-driven;
- make CLI/reference UI consume the same catalog contracts.

**Gate:** public API and host integration review.

### Phase 4 — Remove non-scoped files from the extracted application only

- use dependency/test evidence to remove unnecessary projected files;
- never delete unrelated files from fork `main`;
- fail the build on undeclared imports from excluded source areas.

**Gate:** clean-room install and test in a temporary consumer project.

### Phase 5 — Upstream synchronization automation

- sync selected paths from a new `main` SHA;
- report added, removed, renamed, and changed files;
- block automatic overwrite of locally patched synchronized files;
- rerun characterization and contract tests;
- record source SHA and applied compatibility patches.

### Phase 6 — Optional standalone repository

After the in-repository extraction is stable, split `extracted/hermes-connect-kit/` into its own repository using subtree history. Continue producing it from the fork through the manifest/sync workflow.

## 9. Acceptance criteria

Extraction is complete only when:

1. All current platform and provider plugins are discovered without maintaining a second membership list.
2. Adding a new plugin under the recognized source roots is detected by inventory/sync tests.
3. CLI, gateway, and reference UI show the same provider universe, subject only to explicit filtering.
4. Provider runtime resolution preserves endpoint, API mode, credential, refresh, and transport behavior.
5. Channel behavior preserves authorization, pairing, session/thread routing, message limits, media delivery, cron targets, and hooks.
6. The package can be installed in a clean environment and integrated using only documented public contracts.
7. Updating from a newer fork `main` produces a deterministic drift report and test result.
8. No unrelated source files are deleted from `main` or from this planning branch.

## 10. Decision requested

Review and approve or revise:

- the recommended two-layer extraction approach;
- the proposed public boundaries;
- the target folder structure;
- the phased review gates.

No extraction work should begin until this design and the accompanying inventory are reviewed.