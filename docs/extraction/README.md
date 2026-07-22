# Extraction Review Index

## Phase 2 canonical review order

1. `07-phase-2-mechanical-projection-design.md`
2. `../superpowers/specs/2026-07-22-hermes-connect-phase2-projection-design.md`
3. `../superpowers/plans/2026-07-22-hermes-connect-phase2-mechanical-projection.md`
4. `../superpowers/plans/2026-07-22-hermes-connect-phase2-execution-corrections.md`
5. `PHASE_2_REVIEW_CHECKLIST.md`
6. `06-phase-1-final-self-review.md`
7. `generated/phase-1-inventory.md`
8. `generated/phase-1-test-matrix.md`
9. `../../extracted/hermes-connect-kit/extraction-manifest.yaml`
10. `../../tests/extraction/snapshots/registry-snapshot.json`

The execution-corrections document is normative. It overrides conflicting Task 5–9 sequencing in the main implementation plan. In particular, drift is generated before the new lock is installed, interrupted swap state requires explicit recovery, and projected tests use a dependency-only virtual environment with no editable/source fallback.

The Phase 1 generated evidence still records baseline `18bb6f1aeaa334badee6271fc3337f39ca6bfcfb`. Checkpoint A must regenerate it against Phase 2 baseline `269eb7b30e0bc3666c377e0325263e7b5bcf49b4` before any source projection.

The canonical Phase 2 architecture uses one exact source-relative tree:

```text
extracted/hermes-connect-kit/upstream/<original repository-relative path>
```

Classification, subsystem ownership, and planned Phase 3 layer remain metadata. They do not create separate Python import roots.

The earlier split-root `vendor/compatibility/reference` runtime plan is superseded. The corrected implementation path uses a complete staged projection, deterministic proposed and installed locks, pre-write drift review, explicit transaction recovery, clean-environment projected tests, and five review checkpoints.

## Current execution state

- Latest upstream is merged into the isolated Phase 2 planning lineage.
- Design, implementation-plan, and execution-correction changes are documentation-only.
- Fork `main` remains unchanged.
- Checkpoint A requires a clean connected local worktree to run the registry probe, inventory generation, Ruff, pytest, and selected Hermes regressions.
- The current ChatGPT container cannot resolve GitHub, so no test or evidence-refresh success is claimed here.
- No temporary or expanded GitHub Actions workflow will be introduced to bypass this gate.

## Phase 1 archive order

1. `PHASE_1_STATUS.md`
2. `PHASE_1_REVIEW_GATE.md`
3. `06-phase-1-final-self-review.md`
4. `generated/phase-1-inventory.md`
5. `generated/phase-1-test-matrix.md`
6. `../../extracted/hermes-connect-kit/extraction-manifest.yaml`
7. `../../tests/extraction/snapshots/registry-snapshot.json`

The YAML inventory remains the machine-readable source for generated Markdown reports.