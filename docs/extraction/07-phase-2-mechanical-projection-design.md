# Phase 2 Mechanical Source Projection Design

**Status:** Ready for human review — design only  
**Repository:** `Rilan-Dev/hermes-agent`  
**Isolated planning baseline:** `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`  
**Included upstream:** `NousResearch/hermes-agent@7de554277de632364c74fcf8641daa58a9a977d9`  
**Work branch:** `worktree/channels-providers-phase2-2026-07-22`  
**Fork `main`:** unchanged at `d5a67ad32522273115d887560ca1c08a02bc7873`

## 1. Goal

Phase 2 creates a mechanically synchronized source projection for the scoped Hermes channel, onboarding, and AI-provider subsystem. It must preserve source bytes, source-relative paths, plugin discovery, provider identities, and current import behavior before any architectural refactor begins.

Phase 2 is successful when the projected tree is reproducible from an exact Hermes commit, byte-verifiable against that commit, importable using the original module names, and covered by the Phase 1 characterization matrix.

Phase 2 does **not** create the stable public `hermes_connect.*` API. Public services, host ports, and dependency inversion belong to Phase 3 after mechanical parity is proven.

## 2. Upstream refresh findings

The previous executable inventory was generated from combined baseline `18bb6f1aeaa334badee6271fc3337f39ca6bfcfb`. The isolated Phase 2 branch now contains 252 later commits and 303 changed files relative to that baseline.

The refresh changes several load-bearing scoped files, including:

- `gateway/run.py`
- `gateway/status.py`
- `gateway/authz_mixin.py`
- `gateway/platforms/base.py`
- `gateway/platforms/api_server.py`
- direct and plugin platform adapters
- `hermes_cli/config.py`
- `hermes_cli/gateway.py`
- `hermes_cli/main.py`
- `hermes_cli/model_switch.py`
- `hermes_cli/commands.py`
- `agent/agent_init.py`
- `agent/turn_context.py`
- `run_agent.py`
- `hermes_state.py`
- `cli.py`
- desktop onboarding and platform presentation tests

The refresh also adds or changes possible transitive boundary files such as `hermes_cli/route_identity.py`, `_subprocess_compat.py`, context-switch support, billing/subscription presentation, and process/runtime helpers.

Therefore, the Phase 1 inventory, registry snapshot, manifest source SHA, and regression matrix are stale for source movement. They must be regenerated against `269eb7b30e0bc3666c377e0325263e7b5bcf49b4` before the first projection commit.

## 3. Corrected projection architecture

### 3.1 One exact upstream tree

All projected files must preserve their original repository-relative paths beneath a single tree:

```text
extracted/hermes-connect-kit/
├── README.md
├── extraction-manifest.yaml
├── projection-lock.json
├── upstream/
│   ├── agent/
│   ├── gateway/
│   ├── hermes_cli/
│   ├── plugins/
│   ├── providers/
│   ├── cron/
│   ├── tools/
│   └── <other explicitly scoped source paths>
├── scripts/
│   ├── project_sources.py
│   ├── verify_projection.py
│   └── report_upstream_drift.py
└── tests/
    ├── projection/
    ├── characterization/
    └── regression/
```

A source file such as `gateway/session.py` is projected to:

```text
extracted/hermes-connect-kit/upstream/gateway/session.py
```

No source file is moved into a classification-specific Python import root during Phase 2.

### 3.2 Classification is metadata, not an import location

The Phase 1 classes remain authoritative:

- `core`
- `host_port`
- `optional_ui`
- `test`
- `exclude_by_default`

These values are stored in the manifest, generated inventory, and projection lock. They determine later Phase 3 work, review ownership, and clean-room inclusion. They do not split Python packages in Phase 2.

This correction avoids a defect in the earlier target layout. Separating `agent`, `gateway`, or `hermes_cli` files across `vendor/`, `compatibility/`, and `reference/` roots would split regular Python packages and make unchanged absolute imports dependent on `PYTHONPATH` ordering and namespace-package behavior. A single exact tree avoids that ambiguity.

### 3.3 No import rewriting

Phase 2 must copy exact bytes. It must not rewrite imports, rename packages, wrap classes, change provider IDs, or change plugin manifests.

Selected upstream tests run with:

```bash
PYTHONPATH=extracted/hermes-connect-kit/upstream
```

The projected modules therefore keep their current names such as `gateway`, `providers`, `hermes_cli`, and `agent`.

Consumer projects must not depend on these upstream module names as the stable API. Phase 3 will introduce `hermes_connect.*` services that delegate into this tree.

## 4. Manifest and lock model

### 4.1 Manifest version 2

The Phase 2 manifest should separate source identity from future architectural placement.

Required top-level fields:

```yaml
version: 2
source_repository: Rilan-Dev/hermes-agent
source_sha: 269eb7b30e0bc3666c377e0325263e7b5bcf49b4
projection_root: upstream
```

Each dynamic-root or explicit-file rule keeps:

```yaml
path: gateway/platforms
classification: core
reason: Base adapter contract plus direct and legacy platform implementations.
```

The projected path is derived mechanically as:

```text
<projection_root>/<source path>
```

A rule may keep a `planned_layer` value for Phase 3 documentation, but `planned_layer` must not change the Phase 2 projected path.

### 4.2 Projection lock

`projection-lock.json` is deterministic and contains:

- schema version;
- source repository;
- source commit SHA;
- manifest SHA-256;
- generator version;
- sorted file records;
- source path;
- projected path;
- classification;
- reason;
- source SHA-256;
- projected SHA-256;
- byte size;
- executable-bit state where relevant.

The lock must not contain wall-clock timestamps, local absolute paths, hostnames, usernames, or environment-dependent ordering.

### 4.3 Source identity rules

The projector must reject:

- a source checkout whose `HEAD` is not the manifest `source_sha`;
- a dirty source checkout unless an explicit read-only override is used only for diagnostics;
- path traversal;
- symlinks that resolve outside the source repository;
- destination collisions;
- generated Python cache and bytecode files;
- duplicate source rules with conflicting metadata;
- source files absent from the generated Phase 1 inventory;
- projected files whose bytes differ from the source bytes.

## 5. Projection algorithm

The projection command is intentionally destructive only inside the generated `upstream/` tree.

1. Load and validate the version-2 manifest.
2. Verify the source repository and exact source SHA.
3. Regenerate the scoped filesystem inventory.
4. Compare runtime registries with the reviewed registry snapshot.
5. Build the complete sorted source-to-projected-path plan.
6. Write all projected files into a temporary sibling directory.
7. Preserve source bytes and executable-bit state.
8. Generate `projection-lock.json` from the temporary output.
9. Re-hash every temporary projected file and compare it with its source record.
10. Atomically replace the prior generated `upstream/` tree.
11. Leave every handwritten file outside `upstream/` unchanged.
12. Run projection, characterization, and selected upstream regression tests.

Stale generated files may be removed only when all of the following are true:

- the path is inside `extracted/hermes-connect-kit/upstream/`;
- the previous projection lock records the path as generated;
- the refreshed manifest/inventory no longer includes it;
- the drift report explicitly lists it as removed or renamed.

The projector must never delete repository files outside the generated projection root.

## 6. Drift handling

`report_upstream_drift.py` compares two reviewed source SHAs and reports:

- newly scoped files;
- removed scoped files;
- renamed scoped files when Git evidence is available;
- changed file hashes;
- classification changes;
- newly unresolved internal imports;
- registry membership changes;
- provider identity changes;
- platform identity changes;
- tests added, removed, or changed in the selected matrix.

A drift report is review evidence. It must not silently update classifications or provider aliases.

Locally patched projected files are prohibited in Phase 2. Any required adaptation must be recorded as a Phase 3 compatibility change outside `upstream/`. `verify_projection.py` fails when a projected file differs from its source hash.

## 7. Provider identity invariants

The following identity layers remain distinct:

- platform manifest name;
- runtime plugin key;
- provider plugin directory key;
- provider profile ID;
- canonical provider ID;
- authentication provider ID;
- runtime provider ID;
- model-catalog/provider-picker ID;
- transport/protocol family.

The projector copies these identities unchanged. It must not normalize aliases or collapse OpenAI-compatible providers.

In particular, the following remain separate concepts:

- OpenAI API authentication;
- OpenAI Codex OAuth/runtime;
- native OpenAI runtime/model-catalog identifiers;
- generic OpenAI-compatible endpoints;
- intentional multi-profile aliases such as regional or OAuth variants.

## 8. Channel invariants

The projected tree must preserve current behavior for:

- platform discovery and enablement;
- direct, legacy, and plugin-packaged adapters;
- source authorization and allowlists;
- pairing;
- profile/token-scoped gateway locking;
- session keys;
- thread and reply routing;
- message chunking and media delivery;
- home-channel and explicit-target delivery;
- standalone and cron delivery;
- hooks, mirroring, relay behavior, and stream events;
- reconnect and startup-failure behavior.

`gateway/run.py` remains mechanically projected in Phase 2 even though it is a host-port boundary. Phase 3 must replace its concrete agent construction and process-global dependencies behind explicit protocols.

## 9. Onboarding invariants

Contextual, CLI, desktop, and web onboarding remain separate presentation surfaces over shared backend truth.

Phase 2 preserves existing source and tests. It must not introduce a second static provider or platform membership list.

The backend provider catalog, provider profiles, auth registry, and platform registry remain the membership sources. Desktop/web files may retain ordering, icons, labels, and featured presentation only.

## 10. Required tests before projection review

### 10.1 Manifest and projector tests

- version-2 schema validation;
- exact source-SHA requirement;
- dynamic-root recursion;
- deterministic ordering;
- cache/bytecode exclusion;
- path traversal rejection;
- external symlink rejection;
- destination collision rejection;
- duplicate-rule conflict rejection;
- exact byte-copy verification;
- executable-bit preservation;
- deterministic lock generation;
- atomic replacement;
- handwritten-file preservation;
- stale generated-file removal limited to the projection root.

### 10.2 Characterization tests

- platform manifest names equal the expected runtime plugin-key set;
- provider plugin directories are represented in provider profiles;
- intentional additional provider profiles are characterized explicitly;
- canonical, auth, runtime, and picker provider sets remain compatible without being incorrectly equated;
- unresolved in-scope internal imports remain zero;
- every projected source is declared;
- every declared source is projected;
- every projected hash equals its source hash.

### 10.3 Selected upstream regressions

The refreshed matrix must include changed scoped tests for:

- gateway startup, reconnect, authorization, status, session, model commands, and API server behavior;
- platform base behavior and changed platform adapters;
- provider/model switching and runtime resolution;
- config persistence and migration;
- agent initialization, transport use, and credential rotation;
- session-state persistence;
- CLI and onboarding behavior relevant to provider/channel setup;
- desktop onboarding parity and platform presentation where retained as reference UI.

Tests should run through the repository's canonical isolated per-file runner when shared process state makes a combined pytest invocation unreliable.

## 11. Windows and process-runtime boundary

Before projecting optional CLI integration, the refreshed inventory must explicitly classify:

- `hermes_cli/windows_ssh_runtime.py`;
- `hermes_cli/_subprocess_compat.py`;
- `hermes_bootstrap` dependencies;
- process title and hard-exit helpers;
- service/process management imports;
- newly introduced route/context identity helpers.

These files may be mechanically projected when required for unchanged imports or selected tests. Their behavior remains a Phase 3 host-port concern and must not leak into the stable public service API.

## 12. Git and CI policy

- Fork `main` is not modified by Phase 2 planning or projection review.
- Work occurs only on the isolated Phase 2 branch/worktree lineage.
- No unrelated file cleanup is allowed.
- No GitHub Actions workflow is added, enabled, or expanded while Actions spending is disabled.
- Verification commands must be runnable locally.
- When local execution is unavailable in the current automation runtime, the branch must remain at the design/evidence gate rather than claiming unrun tests passed.
- A projection PR targets the Phase 2 planning branch, not `main`.
- The projection PR remains unmerged until its generated tree, lock, drift report, and test evidence are reviewed.

## 13. Implementation sequence

### Gate A — Refresh evidence

1. Regenerate the manifest source SHA, filesystem inventory, import graph, registry snapshot, and test matrix at `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`.
2. Review all added/changed/removed scoped paths.
3. Explicitly classify Windows/process helpers and new transitive dependencies.
4. Confirm unresolved in-scope internal imports are zero.

### Gate B — Manifest v2

1. Write failing schema and mapping tests.
2. Introduce `projection_root` and source-relative projected paths.
3. Preserve classification and planned-layer metadata.
4. Regenerate deterministic inventory reports.

### Gate C — Projector

1. Write failing exact-copy, safety, determinism, and atomicity tests.
2. Implement the minimal projector.
3. Generate the first `upstream/` tree and lock.
4. Verify byte parity for every file.

### Gate D — Regression parity

1. Run extraction tests.
2. Run changed scoped upstream tests through the canonical runner.
3. Run registry parity and unresolved-import checks.
4. Produce a review report containing exact commands and results.

### Gate E — Human review

Review the generated source tree, projection lock, drift report, classifications, provider identities, channel invariants, onboarding surfaces, and test evidence.

Only after Gate E approval may Phase 3 introduce `hermes_connect.*` public services and host ports.

## 14. Acceptance criteria

Phase 2 is complete only when:

1. The refreshed evidence is based on `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`.
2. Every projected file exists at `upstream/<original source path>`.
3. Every projected file is byte-identical to its source.
4. The projection lock is deterministic.
5. New children under dynamic platform/provider roots are detected automatically.
6. Removed or renamed scoped files are reported before deletion from the generated tree.
7. No file outside the generated projection root is removed by the projector.
8. Provider and platform identity layers remain distinct and characterized.
9. Unresolved in-scope internal imports are zero.
10. Selected unchanged upstream tests pass against the projected tree.
11. No public facade or behavior refactor is mixed into the mechanical projection.
12. Fork `main` remains unchanged.
13. The Phase 2 review PR remains unmerged until explicit human approval.

## 15. Self-review

The design was checked for the following failure modes:

- split regular Python packages across classification roots;
- hidden import rewriting;
- copied files drifting from source bytes;
- stale generated files being deleted without provenance;
- provider aliases being incorrectly collapsed;
- desktop/web presentation becoming a provider registry;
- host-specific process/runtime behavior entering the stable API too early;
- generated output touching files outside the projection root;
- claims of successful testing without an executable local environment;
- accidental changes to fork `main` or GitHub Actions spending.

The main correction from the earlier design is deliberate: Phase 2 uses one exact source-relative projection tree. Architectural separation follows in Phase 3, after mechanical parity is proven.