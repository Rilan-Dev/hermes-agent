# Phase 2 Mechanical Source Projection Review

**Status:** Consolidated design — ready for human review  
**Repository:** `Rilan-Dev/hermes-agent`  
**Combined baseline:** `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`  
**Included upstream:** `NousResearch/hermes-agent@7de554277de632364c74fcf8641daa58a9a977d9`  
**Planning branch:** `planning/channels-providers-phase2-2026-07-22`  
**Work branch:** `worktree/channels-providers-phase2-2026-07-22`  
**Fork `main`:** unchanged at `d5a67ad32522273115d887560ca1c08a02bc7873`

The canonical detailed specification is:

`docs/superpowers/specs/2026-07-22-hermes-connect-phase2-projection-design.md`

This document presents the same decision in extraction-review order and records the evidence gates that must be satisfied before source movement.

## 1. Goal

Phase 2 mechanically projects the reviewed Hermes channel, provider, onboarding, host-port, optional-UI, and selected upstream-test files without changing source bytes or behavior.

Phase 2 does not introduce the stable `hermes_connect.*` facade. Public services and dependency inversion remain Phase 3 work.

## 2. Upstream refresh impact

The previous executable inventory was generated from combined baseline `18bb6f1aeaa334badee6271fc3337f39ca6bfcfb`.

The current isolated baseline is 252 commits ahead and includes 303 changed files relative to that evidence. Load-bearing scoped changes include:

- `gateway/run.py`;
- `gateway/status.py`;
- `gateway/authz_mixin.py`;
- `gateway/platforms/base.py`;
- `gateway/platforms/api_server.py`;
- direct and plugin platform adapters;
- `hermes_cli/config.py`;
- `hermes_cli/gateway.py`;
- `hermes_cli/main.py`;
- `hermes_cli/model_switch.py`;
- `hermes_cli/commands.py`;
- `agent/agent_init.py`;
- `agent/turn_context.py`;
- `run_agent.py`;
- `hermes_state.py`;
- `cli.py`;
- desktop onboarding and platform presentation tests.

Possible new or changed transitive boundaries include route identity, subprocess compatibility, context switching, process/service helpers, Windows SSH support, billing/subscription presentation, and bootstrap behavior.

The Phase 1 manifest source SHA, generated inventory, import graph, registry snapshot, and test matrix are therefore stale for source movement. Gate A must regenerate them before projection.

## 3. Final architecture decision

### Selected: one exact source-relative tree

Every selected source and selected upstream test is projected to:

```text
extracted/hermes-connect-kit/upstream/<original-repository-path>
```

Examples:

```text
source: gateway/session.py
projected: extracted/hermes-connect-kit/upstream/gateway/session.py

source: tests/gateway/test_session.py
projected: extracted/hermes-connect-kit/upstream/tests/gateway/test_session.py
```

This preserves normal Python package boundaries and unchanged absolute imports.

### Metadata retained for review

Each record retains:

- subsystem owner: `shared`, `providers`, `channels`, or `onboarding`;
- classification: `core`, `host_port`, `optional_ui`, `test`, or `exclude_by_default`;
- reason;
- optional planned Phase 3 layer;
- source and projected hashes;
- Git blob, mode, object type, and symlink target.

Subsystem and classification values are review metadata. They do not create separate Phase 2 import roots.

### Rejected: split runtime roots

The earlier proposal to project files into `vendor/`, `compatibility/`, and `reference/` runtime roots is rejected for Phase 2.

That layout can split regular packages such as `agent`, `gateway`, and `hermes_cli`, making behavior depend on shims, namespace-package rules, or `PYTHONPATH` ordering. It also weakens the promise that the mechanically projected tree behaves like the source.

Those names may remain planned Phase 3 layers in reports only.

## 4. Manifest version 2

Required lineage:

```yaml
version: 2
source_repository: Rilan-Dev/hermes-agent
source_sha: 269eb7b30e0bc3666c377e0325263e7b5bcf49b4
upstream_repository: NousResearch/hermes-agent
upstream_sha: 7de554277de632364c74fcf8641daa58a9a977d9
fork_main_sha: d5a67ad32522273115d887560ca1c08a02bc7873
projection_root: upstream
```

Every dynamic root, explicit file, and test rule receives one subsystem owner. A source path has one projected path and is never duplicated across subsystems.

The projected path is always derived as:

```text
<projection_root>/<source path>
```

## 5. Correct source guard

The implementation worktree contains extraction tooling and documentation commits after `source_sha`, so requiring `HEAD == source_sha` would make legitimate implementation impossible.

The guard must instead prove:

1. `source_sha` is an ancestor of `HEAD`.
2. The worktree is clean before projection.
3. Every scoped source/test path exists at `source_sha`.
4. Every scoped path's current committed Git blob, mode, and symlink target equal the object at `source_sha`.
5. No scoped production source changed after `source_sha`.
6. Extraction-only files may change after `source_sha`.

This is the same safety principle as the Phase 1 production-source drift guard, strengthened with Git-object provenance.

## 6. Generated ownership

The projector owns only:

```text
extracted/hermes-connect-kit/upstream/
extracted/hermes-connect-kit/projection-lock.json
```

It must never delete or overwrite handwritten package metadata, docs, scripts, tests, or future `src/hermes_connect/` code.

A stale path may be removed only when the previous lock records it as generated and the reviewed drift report lists it as removed or renamed.

## 7. Projection transaction

Projection uses a rollback-safe staged swap:

1. Build the complete sorted plan.
2. Write files and safe relative symlinks into a sibling staging directory.
3. Verify bytes, hashes, Git modes, targets, and expected paths.
4. Generate the deterministic staged lock.
5. Rename the old generated tree to a backup.
6. Rename staging to `upstream/`.
7. Restore the backup if the second rename fails.
8. Remove the backup only after final verification.

This is not described as universally atomic because directory replacement differs across operating systems and filesystems.

## 8. Projection lock

`projection-lock.json` contains sorted deterministic records and no timestamps, usernames, hostnames, or local absolute paths.

Each record contains:

- source repository and source SHA;
- upstream and fork-main lineage;
- source and projected paths;
- subsystem;
- classification;
- planned layer when present;
- Git object type, mode, and blob SHA;
- SHA-256;
- byte size;
- safe relative symlink target when applicable.

Normal projected files must be byte-identical to their source blobs. Absolute or escaping symlinks are rejected.

## 9. Identity invariants

The following remain distinct:

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

## 10. Channel and onboarding invariants

Projection must preserve current behavior for platform discovery, enablement, authorization, pairing, gateway locking, sessions, threads, chunking, media, explicit/home/cron delivery, hooks, mirroring, relay, streaming, reconnect, and startup failure.

`gateway/run.py` remains mechanically projected even though it is a Phase 3 host-port boundary.

Contextual, CLI, desktop, and web onboarding remain separate presentation surfaces over shared backend provider/platform truth. No new static membership list is allowed.

## 11. Test execution

Phase 2 adds no import rewriting or runtime shims.

Projected tests execute from the projected root so the original repository cannot shadow projected modules:

```bash
cd extracted/hermes-connect-kit/upstream
PYTHONPATH="$PWD" python -m pytest tests/<selected-path> ...
```

Use the repository's canonical isolated per-file runner or equivalent subprocess isolation when shared global state makes one combined pytest process unreliable.

Required coverage includes:

- manifest-v2 validation;
- source ancestry and scoped blob parity;
- dynamic-root recursion;
- deterministic ordering and lock output;
- cache/bytecode exclusion;
- path traversal and unsafe symlink rejection;
- collision and duplicate-rule rejection;
- byte/mode/target preservation;
- staged-swap rollback;
- handwritten-file preservation;
- stale generated-file deletion limited to `upstream/`;
- registry identity characterization;
- zero unresolved in-scope internal imports;
- selected changed gateway, provider, config, runtime, state, channel, and onboarding regressions.

## 12. Review reports

The complete projection tree is generated together. Review slicing is performed through metadata reports, not partial runtime trees.

Required reports:

1. shared infrastructure;
2. provider runtime and provider plugins;
3. channels, gateway, and platform plugins;
4. onboarding and optional reference surfaces;
5. added/removed/changed scoped paths;
6. identity and registry changes;
7. selected-test changes;
8. unresolved dependency changes.

## 13. Windows and process boundary

Gate A must explicitly classify:

- `hermes_cli/windows_ssh_runtime.py`;
- `hermes_cli/_subprocess_compat.py`;
- bootstrap dependencies;
- process title and hard-exit helpers;
- service/process management imports;
- route/context identity helpers.

Required files may be projected unchanged. Their behavior must not become part of the stable public API until Phase 3.

## 14. Git and CI policy

- Fork `main` remains unchanged.
- Work remains on isolated Phase 2 branches/worktrees.
- No unrelated cleanup is allowed.
- No GitHub Actions workflow is added, enabled, or expanded while Actions spending is disabled.
- Verification is local and recorded in committed notes.
- When a runtime cannot create a real local worktree or run tests, work stops at the review gate rather than claiming success.
- The implementation PR targets the Phase 2 planning branch and remains draft/unmerged until explicit review.

## 15. Execution gates

### Gate A — Refresh evidence

- regenerate manifest lineage, inventory, import graph, registry snapshot, and selected tests;
- classify new transitive dependencies;
- verify zero unresolved in-scope internal imports;
- record exact added, removed, and changed scoped paths.

### Gate B — Manifest and provenance

- implement manifest version 2;
- add subsystem and planned-layer metadata;
- derive projected paths from original source paths;
- capture Git blob, mode, object type, and safe symlink targets.

### Gate C — Projection engine

- implement deterministic planning;
- implement staging, verification, rollback-safe swap, `--write`, and `--check`;
- ensure generated ownership is limited to `upstream/` and the lock.

### Gate D — Generate and verify

- generate the complete projected source/test tree;
- verify every record against source;
- run characterization and selected upstream regressions from the projected root;
- produce subsystem and drift reports.

### Gate E — Human review

Review the projection tree, lock, drift reports, classifications, identities, dependency changes, test results, and self-critique.

Only Gate E approval authorizes Phase 3.

## 16. Acceptance criteria

Phase 2 is complete only when:

1. refreshed evidence uses combined baseline `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`;
2. every projected path is `upstream/<original source path>`;
3. every normal file is byte-identical to its source blob;
4. modes and safe symlinks are preserved;
5. the lock is deterministic;
6. dynamic plugin children are detected automatically;
7. removed/renamed scoped paths are reported before generated deletion;
8. no handwritten or production file is removed;
9. identity layers remain distinct;
10. unresolved in-scope internal imports are zero;
11. selected upstream tests pass from the projected root;
12. no behavior refactor or public facade is mixed into projection;
13. no GitHub Actions spending is introduced;
14. fork `main` remains unchanged;
15. the review PR remains unmerged until explicit approval.

## 17. Self-review corrections

The consolidated design corrects:

- split Python packages across classification roots;
- hidden import shims and path-order behavior;
- an impossible exact-HEAD requirement on the implementation branch;
- overstated cross-platform atomic replacement;
- partial subsystem trees being treated as independently runnable;
- dependence on paid GitHub Actions;
- provider/platform identity collapse;
- source adaptations being mixed into mechanical projection.

The next step after approval is to execute the detailed plan in `docs/superpowers/plans/2026-07-22-hermes-connect-phase2-mechanical-projection.md` inside a real local worktree.