# Hermes Connect Phase 2 Mechanical Projection Design

**Status:** Approved design refinement for Phase 2 planning
**Repository:** `Rilan-Dev/hermes-agent`
**Planning branch:** `planning/channels-providers-phase2-2026-07-22`
**Combined baseline:** `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`
**Upstream baseline:** `NousResearch/hermes-agent@7de554277de632364c74fcf8641daa58a9a977d9`
**Fork main preserved:** `Rilan-Dev/hermes-agent@d5a67ad32522273115d887560ca1c08a02bc7873`

## 1. Purpose

Phase 2 mechanically projects the approved channel, provider, onboarding, host-port, optional-UI, and selected upstream-test files into `extracted/hermes-connect-kit/` without changing their behavior. The generated tree remains replaceable from a later source baseline, while hand-written package metadata and later public facades stay outside generated directories.

This refines the already approved two-layer extraction design. It does not change the public-boundary decisions made in `docs/extraction/01-channels-providers-extraction-design.md`.

## 2. Latest-source impact

Upstream advanced by 172 commits after the previous Phase 1 baseline. Relevant changes include gateway orchestration and status, platform base/auth behavior, Telegram and other adapter behavior, provider/model switching, runtime route identity, desktop onboarding tests, and web/desktop integration files.

Therefore Phase 2 must begin by regenerating the scoped inventory and registry evidence against `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`. No projected source may be committed from the older `18bb6f1aeaa334badee6271fc3337f39ca6bfcfb` inventory.

## 3. Approaches considered

### A. Subsystem-sliced deterministic projection — recommended

Add explicit subsystem ownership to the manifest, generate a projection plan from the refreshed inventory, and write generated directories in reviewable slices: shared/provider, channel, then onboarding/reference/host-port.

Advantages:

- every projected byte is tied to a source path, source SHA, Git blob SHA, mode, and content hash;
- provider and channel changes can be reviewed independently;
- future upstream refreshes produce deterministic drift reports;
- failed generation cannot leave a partially updated tree;
- no hand-maintained second plugin membership list is introduced.

Trade-off: the manifest schema and inventory records must be strengthened before the first projection.

### B. One-shot projection of all scoped files

Generate all scoped files in a single commit.

This is mechanically simple but rejected because a several-hundred-file review would hide destination mistakes, host-port misclassifications, and upstream-test failures.

### C. Manual copying and import cleanup

Copy files manually and fix imports while moving them.

This is rejected because it mixes projection with behavior refactoring, loses deterministic provenance, and makes later upstream synchronization unreliable.

## 4. Generated and hand-written boundaries

The projection command owns only these generated paths:

```text
extracted/hermes-connect-kit/
├── vendor/                      # Core synchronized source
├── compatibility/               # Host-port source preserved unchanged
├── reference/                   # Optional CLI/desktop/web reference source
├── tests/upstream/              # Selected upstream tests, unchanged
└── projection-manifest.json     # Exact provenance and hashes
```

The command must never delete or overwrite hand-written paths such as:

```text
extracted/hermes-connect-kit/
├── README.md
├── pyproject.toml
├── extraction-manifest.yaml
├── src/hermes_connect/
└── tests/contracts/
```

## 5. Manifest ownership

Manifest schema version 2 adds a required `subsystem` value to every dynamic root, explicit file, and test rule:

- `shared`
- `providers`
- `channels`
- `onboarding`

Cross-cutting host dependencies use `shared`. A source path has exactly one subsystem owner even if it serves multiple consumers. The generated inventory may report cross-subsystem imports but must not duplicate a file into multiple destinations.

## 6. Provenance contract

Every projected record contains:

- source repository;
- combined source SHA;
- upstream SHA;
- fork-main SHA;
- source path;
- destination path;
- subsystem;
- classification;
- Git object type;
- Git mode;
- Git blob SHA;
- SHA-256;
- byte size;
- symlink target when applicable.

Projection reads the refreshed inventory, verifies the source guard, stages output in a temporary directory, verifies every staged record, and only then replaces the generated roots. `--check` regenerates the expected plan in memory and fails on missing, extra, changed, mis-moded, or mislinked projected entries.

## 7. Projection slices

### Slice 1 — Shared and provider runtime

Project shared infrastructure required by provider discovery plus provider profiles, auth/catalog/runtime/model selection, transports, and model-provider plugins. Run provider/plugin/transport characterization tests first.

### Slice 2 — Channels

Project gateway shared code, relay code, platform plugins/adapters, delivery/session/auth/pairing/stream behavior, and channel-facing tools. Run gateway and platform characterization tests.

### Slice 3 — Onboarding, host ports, and reference surfaces

Project contextual onboarding, CLI setup, optional desktop/web references, and host-port source. These files remain unchanged reference/compatibility material; public dependency inversion is deferred to Phase 3.

## 8. Import compatibility

Phase 2 may add package markers and import-path shims only when necessary to execute unchanged projected tests. Shims must forward to projected modules without changing behavior. New service abstractions, provider normalization changes, or adapter refactors belong to Phase 3.

No consumer may treat `vendor`, `compatibility`, or `reference` modules as stable public API.

## 9. Verification gates

Each slice must pass:

1. manifest validation;
2. refreshed inventory with zero unresolved internal imports;
3. projection `--check` immediately after `--write`;
4. unchanged selected upstream tests for the slice where feasible;
5. extraction characterization tests;
6. Ruff and repository policy checks;
7. a diff guard allowing changes only under extraction tooling, extraction docs/tests, and `extracted/hermes-connect-kit/`;
8. a self-review of additions, deletions, destination collisions, host-port changes, and unexpected source growth.

## 10. Failure behavior

Projection fails before replacing generated roots when:

- the manifest source SHA is not an ancestor of `HEAD`;
- scoped source differs from the approved source SHA;
- a manifest source is missing;
- two sources map to one destination;
- a Git tree entry cannot be resolved;
- staged content, mode, link target, or hash differs from inventory;
- an undeclared file exists in a generated root during `--check`;
- a selected upstream test resolves outside declared test rules.

A failed command leaves the previously generated tree intact and retains the staging directory path in the error message for inspection.

## 11. Phase boundary

Phase 2 ends when all approved source and selected test files are mechanically projected with deterministic provenance and unchanged characterization behavior. Stable channel/provider/onboarding services and host-port refactoring remain Phase 3 work.

## 12. Self-review

- No placeholders or unresolved design decisions remain.
- The design does not add a second platform/provider membership list.
- Generated and hand-written ownership is explicit.
- Projection and behavior refactoring are separated.
- The plan is decomposed by independently reviewable subsystem slices.
- The latest upstream baseline is recorded explicitly.
- Local worktree creation remains mandatory before executing source projection in a developer checkout.
