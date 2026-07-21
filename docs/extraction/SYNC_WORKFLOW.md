# Upstream Sync Workflow

1. Keep the fork's `main` unchanged during extraction planning.
2. Merge `sync/upstream-main-2026-07-21` into `planning/channels-providers-extraction-latest`.
3. Create `worktree/channels-providers-extraction-latest` from the refreshed planning branch.
4. Replay the extraction-only commits onto that work branch.
5. Run the Phase 1 evidence and characterization gates before Phase 2.
