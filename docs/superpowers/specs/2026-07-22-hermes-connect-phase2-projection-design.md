# Hermes Connect Phase 2 Mechanical Projection Design

**Status:** Consolidated design — ready for human review  
**Repository:** `Rilan-Dev/hermes-agent`  
**Planning branch:** `planning/channels-providers-phase2-2026-07-22`  
**Work branch:** `worktree/channels-providers-phase2-2026-07-22`  
**Combined baseline:** `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`  
**Upstream baseline:** `NousResearch/hermes-agent@7de554277de632364c74fcf8641daa58a9a977d9`  
**Fork main preserved:** `Rilan-Dev/hermes-agent@d5a67ad32522273115d887560ca1c08a02bc7873`

## 1. Purpose

Phase 2 mechanically projects the approved channel, provider, onboarding, host-port, optional-UI, and selected upstream-test files into `extracted/hermes-connect-kit/` without changing source behavior or source bytes.

The projection must remain replaceable from a later Hermes source baseline and must preserve original repository-relative paths so unchanged absolute imports continue to work.

Stable `hermes_connect.*` services, dependency inversion, and host-port adapters remain Phase 3 work.

The detailed companion design is `docs/extraction/07-phase-2-mechanical-projection-design.md`. This specification is the canonical Superpowers design summary and must remain consistent with that document.

## 2. Latest-source impact

The Phase 2 branch includes 252 commits and 303 changed files after the previous executable evidence baseline `18bb6f1aeaa334badee6271fc3337f39ca6bfcfb`.

Relevant changes include:

- gateway orchestration, status, authorization, startup, reconnect, and API behavior;
- platform base behavior and several direct/plugin adapters;
- CLI configuration, gateway setup, top-level dispatch, and model switching;
- agent initialization, turn context, runtime construction, and session state;
- route/process identity and subprocess compatibility helpers;
- desktop onboarding tests and platform presentation.

Therefore Phase 2 must begin by regenerating the scoped inventory, import graph, registry snapshot, and selected regression matrix against combined baseline `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`.

No source projection may be produced from the older Phase 1 evidence.

## 3. Approaches considered

### A. One exact source-relative projection tree — selected

Project every selected source and selected upstream test to:

```text
extracted/hermes-connect-kit/upstream/<original-repository-path>
```

Store subsystem ownership, classification, planned Phase 3 layer, Git provenance, and hashes in the manifest, generated inventory, and projection lock.

Advantages:

- unchanged absolute imports resolve exactly as they do in Hermes;
- regular packages such as `agent`, `gateway`, and `hermes_cli` are not split across import roots;
- every projected path is mechanically derived from its source path;
- future synchronization and byte verification remain straightforward;
- subsystem review is still available through metadata and generated reports.

Trade-off: Phase 2 does not yet produce an ideal public package layout. That is intentional and deferred to Phase 3.

### B. Classification-specific roots — rejected for runtime projection

Project core files to `vendor/`, host-port files to `compatibility/`, and optional UI files to `reference/`.

This is rejected as the Phase 2 runtime layout because it can split ordinary Python packages across multiple roots. Import shims or `PYTHONPATH` ordering would become hidden behavior and would weaken the claim that projected source is unchanged.

The values `vendor`, `compatibility`, and `reference` may remain as **planned Phase 3 layers** in metadata and reports only.

### C. Manual copying with import cleanup — rejected

Manual copying and import rewriting mix projection with behavior refactoring, lose deterministic provenance, and make later upstream synchronization unreliable.

## 4. Generated and hand-written boundaries

The projection command owns only:

```text
extracted/hermes-connect-kit/
├── upstream/                    # Generated exact source-relative tree
└── projection-lock.json         # Generated deterministic provenance
```

Selected tests are projected under their original paths, for example:

```text
extracted/hermes-connect-kit/upstream/tests/gateway/test_session.py
```

The projector must never delete or overwrite hand-written paths such as:

```text
extracted/hermes-connect-kit/
├── README.md
├── pyproject.toml
├── extraction-manifest.yaml
├── src/hermes_connect/
├── scripts/
└── tests/
```

The `src/hermes_connect/` public facade is not implemented during Phase 2 except for pre-existing package markers or documentation-only placeholders already approved by the branch.

## 5. Manifest version 2

Manifest version 2 records source lineage and review metadata:

```yaml
version: 2
source_repository: Rilan-Dev/hermes-agent
source_sha: 269eb7b30e0bc3666c377e0325263e7b5bcf49b4
upstream_repository: NousResearch/hermes-agent
upstream_sha: 7de554277de632364c74fcf8641daa58a9a977d9
fork_main_sha: d5a67ad32522273115d887560ca1c08a02bc7873
projection_root: upstream
```

Every dynamic root, explicit file, and test rule receives one subsystem owner:

- `shared`
- `providers`
- `channels`
- `onboarding`

Every source rule also keeps:

- classification;
- reason;
- optional `planned_layer` for Phase 3 review.

The projected path is always derived as:

```text
<projection_root>/<source path>
```

A source path has one owner and one projected path. Files are never duplicated across subsystems or planned layers.

## 6. Source guard

The implementation worktree necessarily contains extraction docs, tests, and tooling commits after `source_sha`. Therefore Phase 2 must **not** require `HEAD == source_sha`.

The source guard requires all of the following:

1. `source_sha` is an ancestor of `HEAD`.
2. The worktree is clean before projection.
3. Every scoped source/test path resolves at `source_sha`.
4. The current committed Git blob, mode, and symlink target for every scoped path equal the corresponding object at `source_sha`.
5. No scoped production source has changed after `source_sha`.
6. Extraction-only files may change after `source_sha`.

This preserves an isolated implementation branch while proving the projected source still represents the approved baseline.

## 7. Provenance contract

Every projection-lock record contains:

- source repository;
- combined source SHA;
- upstream SHA;
- fork-main SHA;
- source path;
- projected path;
- subsystem;
- classification;
- planned Phase 3 layer when present;
- Git object type;
- Git mode;
- Git blob SHA;
- SHA-256;
- byte size;
- symlink target when applicable.

The lock is deterministic. It contains no timestamps, usernames, hostnames, local absolute paths, or environment-dependent ordering.

Projected normal files must be byte-identical to their source blobs. Safe relative symlinks may be recreated exactly; absolute or escaping symlink targets are rejected.

## 8. Projection transaction

Projection proceeds through a staging directory beside `upstream/`:

1. Build the complete deterministic projection plan.
2. Write every file/symlink into staging.
3. Verify hashes, modes, targets, and expected paths.
4. Write the staged lock.
5. Rename the current generated tree to a backup when it exists.
6. Rename staging to `upstream/`.
7. Restore the backup if the second rename fails.
8. Remove the backup only after the new tree and lock pass verification.

This is a rollback-safe staged swap. It must not be described as universally atomic because directory-replacement semantics differ across filesystems and operating systems.

A failed projection leaves the prior generated tree recoverable and never modifies files outside generated ownership.

## 9. Drift and deletion policy

The drift report classifies:

- added scoped paths;
- removed scoped paths;
- changed hashes;
- changed Git modes;
- changed symlink targets;
- classification changes;
- subsystem changes;
- planned-layer changes;
- registry identity changes;
- newly unresolved internal imports;
- selected-test changes.

A stale generated path may be removed only when:

- it is inside `extracted/hermes-connect-kit/upstream/`;
- the previous lock records it as generated;
- the new reviewed plan no longer contains it;
- the drift report lists it as removed or renamed.

Locally patched files inside `upstream/` are prohibited. Adaptations belong outside the generated tree in Phase 3.

## 10. Import and test execution

Phase 2 performs no import rewriting and adds no runtime import shims.

Projected tests run from the projected root so repository-root modules cannot shadow projected modules:

```bash
cd extracted/hermes-connect-kit/upstream
PYTHONPATH="$PWD" python -m pytest tests/<selected-path> ...
```

The implementation plan must use the repository's canonical isolated per-file runner or equivalent subprocess isolation when shared global state makes one combined pytest process unreliable.

Characterization tests outside the projected tree compare source and projected registries, paths, and hashes.

## 11. Identity invariants

The following remain separate and unchanged:

- platform manifest name;
- runtime plugin key;
- provider plugin directory key;
- provider profile ID;
- canonical provider ID;
- authentication provider ID;
- runtime provider ID;
- model-catalog/provider-picker ID;
- transport/protocol family.

OpenAI API-key authentication, OpenAI Codex OAuth/runtime, native OpenAI model identifiers, and generic OpenAI-compatible endpoints must not be collapsed.

Intentional regional, OAuth, and multi-profile aliases remain explicit.

## 12. Phase 2 review units

Subsystem metadata supports four review reports:

1. shared infrastructure;
2. provider runtime and provider plugins;
3. channels, gateway, and platform plugins;
4. onboarding and optional reference surfaces.

The projector still writes one complete exact tree. Review slicing is performed through lock/report filters, not separate import roots and not partially functional runtime trees.

## 13. Verification gates

Before the projection review PR is ready:

1. refreshed evidence uses combined baseline `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`;
2. unresolved in-scope internal imports are zero;
3. manifest-v2 tests pass;
4. source-guard tests pass;
5. projection safety and rollback tests pass;
6. `--write` followed by `--check` passes;
7. every projected hash/blob/mode/target matches source;
8. platform and provider registry characterization passes;
9. selected changed upstream tests pass from the projected root;
10. diff guards show no production-source or workflow changes;
11. a written self-review covers unexpected growth, deletions, boundary changes, and test gaps.

## 14. Git and CI policy

- Fork `main` remains unchanged.
- Work stays on isolated Phase 2 planning/work branches.
- No GitHub Actions workflow is added, enabled, or expanded while Actions spending is disabled.
- The implementation plan must rely on local commands and committed verification notes.
- If the executing environment cannot create a real local worktree or run the tests, implementation stops at the review gate rather than claiming success.
- The projection PR targets the Phase 2 planning branch and remains draft/unmerged until explicit review.

## 15. Phase boundary

Phase 2 ends when the complete reviewed source/test set is projected under `upstream/` with deterministic provenance and unchanged behavior.

Phase 3 begins only after human approval and introduces stable `hermes_connect.*` channel, provider, and onboarding services plus explicit host ports.

## 16. Self-review

The consolidated design corrects these risks from the concurrent drafts:

- split regular Python packages across `vendor`, `compatibility`, and `reference` roots;
- hidden import behavior through shims or path ordering;
- impossible `HEAD == source_sha` requirements on an implementation branch;
- overstated cross-platform atomic directory replacement;
- dependency on paid GitHub Actions while Actions spending is disabled;
- partially projected subsystem trees being treated as independently runnable;
- duplicated provider/platform membership;
- source adaptations being mixed into mechanical projection.

No unresolved architectural decision remains inside Phase 2. Human approval is still required before executing the implementation plan.