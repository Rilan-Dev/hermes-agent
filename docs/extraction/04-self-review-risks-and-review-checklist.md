# Self-Review, Risks, and Review Checklist

**Status:** Planning self-critique  
**Scope:** Documents committed to `planning/channels-providers-extraction`

## 1. What was verified

The planning work verified the following directly against the fork at `main@d7b36070ef807841699ad32c5b6af547fee3ff64`:

- repository and branch access;
- gateway base adapter and platform registry;
- gateway architecture, message flow, authorization, sessions, and delivery documentation;
- provider profile base and lazy provider registry;
- provider plugin contract and automatic wiring behavior;
- provider authentication registry and automatic registry extension;
- unified provider catalog and parity contract;
- shared provider/model inventory;
- shared runtime provider resolution;
- transport registry and protocol transports;
- contextual onboarding;
- Desktop provider onboarding presentation;
- dashboard auth registry;
- plugin discovery/enablement architecture;
- current fork and upstream head equivalence at the inspected SHA.

The plan intentionally treats recursive plugin roots and runtime registries as authoritative rather than claiming a fixed list of platform/provider names is permanently complete.

## 2. Self-critique: important limitations

### 2.1 No executable filesystem walk has been committed yet

The current environment could inspect GitHub files and code search results, but the planning phase has not run a local repository-wide import graph, manifest walk, or test collection. Therefore:

- the named-file inventory is strong but not yet machine-proven;
- dynamically imported route handlers, auth implementations, optional helpers, packaging metadata, and platform-specific dependencies may add files;
- the exact selected test count is not yet known.

**Mitigation:** Phase 1 begins with a generated inventory and unresolved-import report before any source projection.

### 2.2 `gateway/run.py` is a major coupling risk

`gateway/run.py` owns orchestration, agent creation, commands, config reads, lifecycle tasks, and platform dispatch. Copying it wholesale would pull much of Hermes into the package; rewriting it immediately would risk behavioral regressions.

**Mitigation:** characterize existing behavior first, then place agent execution and host services behind ports. Keep the synchronized source version during the transition.

### 2.3 Provider truth is unified, but source data remains distributed

`provider_catalog.py` solves membership parity, but its descriptors still join:

- canonical provider definitions;
- auth registry entries;
- provider profiles;
- optional environment metadata;
- Hermes overlays.

A naive extraction of only provider plugins or only `PROVIDER_REGISTRY` would be incomplete.

**Mitigation:** preserve `provider_catalog()` parity tests and generate all provider sets in the inventory report.

### 2.4 UI ordering is still presentation-specific

Desktop onboarding maintains highlighted provider ordering and copy. That is acceptable for presentation, but it can be mistaken for provider membership.

**Mitigation:** define UI metadata as an overlay keyed by backend provider slug. Tests must verify that every backend descriptor remains reachable even if not featured.

### 2.5 Channel/plugin enablement has two generations

The repository has both plugin platform adapters and direct/legacy adapters. The platform registry also supports deferred imports and falls back to legacy creation paths.

**Mitigation:** preserve both paths during mechanical extraction. Consolidation is a later refactor with adapter parity tests, not a Phase 2 cleanup.

### 2.6 Optional dependency extras are not fully enumerated in this draft

Each platform may require a different SDK, system binary, webhook server, or external process. Provider auth may also require browser callbacks or external CLIs.

**Mitigation:** Phase 1 parses `pyproject.toml`, plugin manifests, import guards, install hints, and platform/provider documentation into a dependency matrix. The standalone package should use optional extras rather than installing every SDK by default.

### 2.7 Backend API route ownership needs an executable search

Desktop and web onboarding consume REST/JSON-RPC APIs. The client paths are identified, but every server route, request schema, middleware, and profile-routing dependency has not yet been individually listed.

**Mitigation:** trace endpoint strings from client to route registration and tests in Phase 1. Include only the endpoints required by the chosen reference UI.

### 2.8 Security-sensitive behavior must not be simplified during extraction

Authentication and messaging include:

- OAuth/device flows and token refresh;
- secret scopes and profile isolation;
- credential pools;
- URL/hostname trust checks;
- pairing and default-deny authorization;
- allowlists and allow-all overrides;
- token locks and scoped process state;
- webhook/API exposure.

**Mitigation:** security behavior is characterized before refactoring. No extraction shortcut may log secrets, relax default-deny behavior, forward credentials across origins, or collapse profile-scoped storage into globals.

### 2.9 License and attribution must follow copied source

The source repository is MIT-licensed, but the extracted application must retain the repository license, copyright notices, and provenance for synchronized files. Third-party optional SDKs keep their own licenses.

**Mitigation:** include license/notice generation in Phase 2 packaging checks.

### 2.10 A GitHub branch is not itself a local worktree

The planning branch has been created remotely. A linked local worktree is intentionally deferred until the documents are approved.

**Mitigation:** create and verify the local worktree from the planning branch at the start of Phase 1. Do not claim a worktree exists before that command is run in the developer environment.

## 3. Risks ranked by impact

| Risk | Impact | Likelihood | Required control |
|---|---:|---:|---|
| Missing dynamic dependency | High | Medium | Manifest/registry/import walk and unresolved-import gate |
| Provider auth/runtime regression | High | Medium | Characterization tests by auth type and API mode |
| Channel authorization regression | High | Medium | Default-deny, allowlist, pairing, and token-lock tests |
| Upstream sync overwrites local fix | High | Medium | Hash-based vendor protection and separate compatibility patches |
| Package pulls most of Hermes | High | Medium | Explicit host ports and no-undeclared-import CI |
| UI and backend provider sets diverge | Medium | Medium | Provider catalog parity test |
| Platform optional dependencies become mandatory | Medium | Medium | Per-platform extras and lazy loading |
| Direct and plugin adapters behave differently | Medium | High | Shared adapter contract suite plus platform characterization |
| Upstream removes/renames scoped file | Medium | Medium | Drift report and blocked provenance update |
| Excessive first extraction refactor | High | Medium | Mechanical projection before interface refactor |
| Prune branch creates recurring conflicts | High | High | Reject destructive prune strategy |

## 4. Scope decisions that need user review

Please review these decisions before implementation:

1. **Recommended approach:** keep an upstream-synchronized source layer plus a stable reusable facade.
2. **Repository placement:** first build under `extracted/hermes-connect-kit/` in this fork; split to a standalone repository only after stabilization.
3. **UI scope:** keep Desktop/web code as optional reference consumers, not mandatory runtime dependencies.
4. **Agent boundary:** channels call a host-supplied agent executor instead of owning the entire Hermes AIAgent.
5. **Cron boundary:** retain delivery contracts but treat the full cron scheduler as a host integration unless standalone scheduling is explicitly required.
6. **MoA:** retain it only if the extracted provider universe must match Hermes exactly; otherwise make it an optional virtual-provider plugin after parity is established.
7. **Legacy adapters:** preserve them initially; consolidate only after parity tests.
8. **Naming:** `hermes-connect-kit` is a working name, not a final branding decision.

## 5. Review checklist for the documents

### Architecture

- [ ] Channel, provider, and onboarding boundaries match the desired reusable product.
- [ ] Two-layer extraction is acceptable.
- [ ] Public consumers are prohibited from importing synchronized/vendor internals.
- [ ] Host ports cover agent execution, storage, config, secrets, logging, cron, and process management.

### Inventory

- [ ] Recursive roots are correct.
- [ ] Any known channel/provider/setup file missing from the named inventory is added.
- [ ] Optional Desktop/web scope is correctly classified.
- [ ] Excluded areas match the requested product.

### Workflow

- [ ] Planning branch remains documentation-only.
- [ ] Implementation worktree is created only after approval.
- [ ] No deletion occurs in fork `main`.
- [ ] Upstream source refresh and local compatibility changes use separate commits.
- [ ] Standalone repository split is deferred.

### Quality gates

- [ ] Exact generated inventory is reviewed before projection.
- [ ] Characterization tests run before refactoring.
- [ ] Security-sensitive tests are mandatory.
- [ ] Clean consumer-project integration is mandatory.
- [ ] Sync drift and modified-vendor conflicts block automatic updates.

## 6. Proposed next action after approval

Invoke the Superpowers implementation-planning workflow to create a task-by-task Phase 1 plan. That plan should cover only:

- isolated worktree setup;
- executable inventory generator;
- manifest schema;
- registry/plugin enumeration;
- import and dependency graph;
- selected test matrix;
- generated review report.

It must not copy, move, delete, or refactor production source until the generated Phase 1 report is reviewed.