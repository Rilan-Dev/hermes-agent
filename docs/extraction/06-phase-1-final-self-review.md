# Phase 1 Final Self-Review

## Scope reviewed

This review covers the refreshed Phase 1 inventory and characterization evidence for channels, onboarding, and AI providers after combining the fork and latest upstream histories.

## What is verified

- The approved source baseline is `18bb6f1aeaa334badee6271fc3337f39ca6bfcfb` and includes upstream `a88512b114059fff642d60d54cbf30d5793c6c37`.
- Runtime platform, plugin, provider-profile, canonical-provider, authentication-provider, and transport registries were captured in an isolated environment.
- The filesystem inventory, registry snapshot, Markdown report, YAML report, and test matrix are deterministic.
- Ruff and all extraction tests passed in the evidence workflow.
- The selected existing provider, gateway, model-provider, transport, and provider-parity tests passed through the repository's canonical per-file runner.
- The production source-drift guard passed against the latest combined baseline.
- The final evidence staging diff contains no production source changes.
- Temporary evidence workflows and trigger files are removed in the cleaned review result.

## Corrections made during review

1. Platform parity now compares manifest names with runtime plugin keys instead of comparing directory names to plugin keys.
2. Model-provider parity now compares provider plugin directories with the dedicated provider-profile registry and permits intentional multi-profile registrations.
3. The legacy regression baseline uses `scripts/run_tests.sh` rather than a shared multi-root pytest process.
4. Evidence publication no longer depends on Git transport write-back from GitHub Actions; the verified output was applied to a dedicated staging branch through the GitHub Contents API.
5. The repository's original `tests.yml` was restored byte-for-byte from the refreshed baseline, and temporary evidence workflows are removed from the review result.
6. A test-first correction excludes generated `__pycache__`, `.pyc`, and `.pyo` artifacts from dynamic-root inventory walks. The clean inventory contains 285 scoped source files instead of the earlier noisy count of 322.
7. Upstream freshness was rechecked after the first review run. When upstream advanced, the planning/work branches and all evidence were refreshed again rather than presenting stale results as current.

## Remaining risks before Phase 2

- Phase 1 classifies dependencies but does not yet copy or move production source.
- `gateway/run.py` and host integrations remain highly coupled and require adapter boundaries before extraction.
- Provider identity aliases must remain distinct across user-facing IDs, auth IDs, runtime IDs, and model-catalog IDs.
- Desktop and web onboarding surfaces must continue to consume the backend provider catalog rather than becoming independent sources of truth.
- The latest upstream introduced `hermes_cli/windows_ssh_runtime.py` as a new out-of-scope dependency of `hermes_cli/main.py`; its host-port treatment must be reviewed before copying CLI integration code.
- A real local worktree should still be created in the development environment before Phase 2 source movement begins.

## Gate decision

Phase 1 is ready for human review after final CI. Phase 2 must not begin until the generated inventory, manifest classifications, registry identities, host-port boundaries, selected test matrix, and the new Windows SSH runtime dependency are reviewed and approved.
