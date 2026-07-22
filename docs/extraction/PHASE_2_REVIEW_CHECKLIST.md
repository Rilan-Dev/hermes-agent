# Phase 2 Mechanical Projection Review Checklist

**Review branch:** `worktree/channels-providers-phase2-2026-07-22`  
**Planning base:** `planning/channels-providers-phase2-2026-07-22`  
**Canonical design:** `docs/superpowers/specs/2026-07-22-hermes-connect-phase2-projection-design.md`  
**Implementation plan:** `docs/superpowers/plans/2026-07-22-hermes-connect-phase2-mechanical-projection.md`

Approve **Checkpoint A execution** only after confirming:

- [ ] The source baseline is `269eb7b30e0bc3666c377e0325263e7b5bcf49b4` and includes upstream `7de554277de632364c74fcf8641daa58a9a977d9`.
- [ ] Fork `main` remains unchanged at `d5a67ad32522273115d887560ca1c08a02bc7873`.
- [ ] Phase 1 evidence will be regenerated before any source projection.
- [ ] The projection uses one exact source-relative `upstream/` tree.
- [ ] Classification and planned Phase 3 layer remain metadata and do not split Python packages across import roots.
- [ ] Phase 2 performs no import rewriting, compatibility wrapping, provider normalization, or behavior refactor.
- [ ] Projected files must be byte-identical to the reviewed source objects.
- [ ] The projection lock is deterministic and contains no local or time-dependent data.
- [ ] The projector may remove stale generated files only inside its recorded `upstream/` root.
- [ ] Provider manifest, profile, auth, runtime, model-catalog, and transport identities remain distinct.
- [ ] Platform manifest identities and runtime plugin keys remain characterized.
- [ ] Desktop and web onboarding remain consumers of backend provider/platform truth.
- [ ] `gateway/run.py` remains a Phase 3 host-port boundary rather than being refactored during projection.
- [ ] Windows/process helpers, including `windows_ssh_runtime.py`, `_subprocess_compat.py`, bootstrap, route identity, and service management, are explicitly classified during the evidence refresh.
- [ ] The refreshed selected test matrix covers changed gateway, provider, config, runtime, state, onboarding, and platform paths.
- [ ] The source guard permits extraction-only commits after `source_sha` but rejects any scoped source/blob/mode/target drift.
- [ ] The staged directory replacement is described and tested as rollback-safe, not universally atomic.
- [ ] GitHub Actions workflows are not added, enabled, or expanded while Actions spending is disabled.
- [ ] The implementation PR targets the isolated Phase 2 planning branch, not `main`.
- [ ] The implementation PR remains draft and unmerged until projection output, lock, drift report, and test evidence receive explicit review.

Approval of this checklist authorizes **Checkpoint A evidence refresh only**. Later checkpoints remain separately review-gated. It does not authorize merging into `main` or beginning Phase 3 refactoring.
