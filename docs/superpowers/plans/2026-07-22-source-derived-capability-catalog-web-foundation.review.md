# Source-Derived Capability Catalogue Plan Self-Review

**Date:** 2026-07-22  
**Design approval:** Confirmed by the user in conversation  
**Reviewed plan:** `docs/superpowers/plans/2026-07-22-source-derived-capability-catalog-web-foundation.md`  
**Planning branch:** `planning/agentic-platform-web-foundation-2026-07-22`

## Scope review

The plan implements only the first approved cycle:

1. exact projected-source validation;
2. deterministic catalogue and provenance schema;
3. enriched isolated registry capture;
4. source-derived provider/channel/tool relationships;
5. complete CLI/TUI/source-UI projection classification;
6. deterministic generated catalogue, lock, and reports;
7. read-only platform domain and JSON adapter;
8. workspace-safe read-only APIs;
9. independent browser package;
10. typed API client and generic renderer registry;
11. health, catalogue, provenance, and existing inbox pages;
12. full verification and human review gate.

It does not authorize provider login, model mutation, channel connection, channel onboarding execution, agent execution, tool execution, workflow mutation, CLI command execution, or chat sending.

## Source-only review

- Existing `scripts/platform_inventory` code is extended rather than replaced.
- The Phase 2 projection lock and exact `upstream/` tree are the only production-source inputs.
- Browser code selects generic projection classes, not provider/channel/tool identities.
- Provider, authentication, channel, model, tool, toolset, command, workflow, and UI identities remain source-derived.
- Unsupported or host-bound CLI/TUI/UI items remain visible in generated reports.
- No projected source modification is planned.
- No GitHub Actions workflow change is planned.

## Placeholder and ambiguity review

The first draft contained an unresolved integration-branch placeholder and undeclared fixture-helper references. That draft was removed.

The corrected plan:

- names `planning/channels-providers-phase2-2026-07-22` as the exact post-Checkpoint-E integration branch;
- computes the implementation diff base with `git merge-base`;
- requires test helpers to be defined in the same test modules that use them;
- defines all public production interfaces consumed by later tasks;
- fixes the first-cycle mutation boundary;
- identifies three explicit human review checkpoints.

No `TBD`, `TODO`, “implement later”, or unspecified branch/base placeholder remains in the corrected plan.

## Type and interface review

The interface flow is consistent:

```text
ProjectedSourceView
  → CapabilityCatalog
  → generated catalogue JSON and lock
  → CapabilityRepository
  → CapabilityService
  → read-only FastAPI routes
  → PlatformApiClient
  → generic descriptor renderers
```

Catalogue namespaces, browser projection classes, and host boundaries are shared by generated data, backend DTOs, and browser contracts without provider-specific switching.

## Execution gate

The plan is not currently executable because Checkpoint A evidence has not been generated and Phase 2 Checkpoints B–E have not completed.

Implementation must not start until:

```text
PR #30 blocker is resolved
Checkpoint A evidence is reviewed
manifest v2 and provenance pass Checkpoint B
projector safety passes Checkpoint C
the exact tree and isolated tests pass Checkpoint D
Checkpoint E human review approves the projection
```

## Integrity

This review records planning work only. It does not claim that catalogue, backend, browser, lint, test, build, projection, or runtime commands have been executed.
