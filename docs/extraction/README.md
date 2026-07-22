# Extraction Review Index

## Phase 2 design review

Review the current Phase 2 design in this order:

1. `07-phase-2-mechanical-projection-design.md`
2. `PHASE_2_REVIEW_CHECKLIST.md`
3. `06-phase-1-final-self-review.md`
4. `generated/phase-1-inventory.md`
5. `generated/phase-1-test-matrix.md`
6. `../../extracted/hermes-connect-kit/extraction-manifest.yaml`
7. `../../tests/extraction/snapshots/registry-snapshot.json`

The Phase 1 generated evidence still records baseline `18bb6f1aeaa334badee6271fc3337f39ca6bfcfb`. It must be regenerated against Phase 2 baseline `269eb7b30e0bc3666c377e0325263e7b5bcf49b4` before source projection begins.

The Phase 2 design corrects the projection layout to use one exact source-relative `upstream/` tree. Classification remains metadata so regular Python packages are not split across incompatible import roots.

## Phase 1 archive order

1. `PHASE_1_STATUS.md`
2. `PHASE_1_REVIEW_GATE.md`
3. `06-phase-1-final-self-review.md`
4. `generated/phase-1-inventory.md`
5. `generated/phase-1-test-matrix.md`
6. `../../extracted/hermes-connect-kit/extraction-manifest.yaml`
7. `../../tests/extraction/snapshots/registry-snapshot.json`

The YAML inventory is the machine-readable source for the generated Markdown report. Phase 2 implementation planning remains blocked until the new design and checklist are approved.