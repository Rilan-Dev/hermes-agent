# Agentic Platform Phase 1 Foundation Implementation Plan

> **Execution rule:** Use test-driven development for every production behavior. Keep the Phase 1 branch based on the validated Phase 0 branch until Phase 0 is merged. Do not modify or delete Hermes runtime files unless a later bridge task explicitly requires a compatibility adapter.

**Goal:** Establish the browser-first platform backend, canonical omnichannel domain, durable event-ingestion boundary, realtime contract, and Hermes compatibility ports needed by later channel-specific interfaces.

**Architecture:** Add a modular-monolith source-layout package under `platform/backend/src/agentic_platform/`. The filesystem retains the `platform/` product boundary while avoiding collision with Python's standard-library `platform` module. Domain objects and service contracts remain independent of FastAPI, PostgreSQL, Redis, S3, and Hermes internals. Infrastructure adapters implement those contracts. The initial slice proves behavior with in-memory adapters; production adapters are added only after the domain and idempotency contracts are characterized.

**Phase 0 evidence used:** 93 plugin manifests, 20 runtime channels with zero manifest/runtime differences, 41 canonical providers, 79 registered tools, 222 frontend routes, 92 Electron bridge references, 775 scoped Python files, and one intentional optional local import.

## Global constraints

- Work on `worktree/agentic-platform-phase-1` in an isolated worktree/branch based on the final Phase 0 head.
- Keep PR #1 draft and unmerged while Phase 1 is developed on a dependent branch.
- New Python application code imports only `agentic_platform.*` contracts. The repository folder is named `platform/`, but it is never used as a Python package because it collides with the standard-library `platform` module.
- No new product code may import arbitrary `gateway.*`, `hermes_cli.*`, `agent.*`, or `tools.*` modules directly.
- Workspace ID is mandatory on every durable aggregate and repository query.
- External channel events are idempotent by `(workspace_id, connection_id, platform_event_id)`.
- Native platform IDs are preserved; canonical UUIDs do not replace them.
- Secrets are represented by opaque references. Domain objects and API responses never contain secret values.
- Public-channel agent bindings default to no terminal, filesystem, administrative, or external-write tools.
- Use UTC-aware datetimes only.
- Every task ends with focused tests and a focused commit.

## Target structure for this phase

```text
platform/
├── backend/
│   ├── src/
│   │   └── agentic_platform/
│   │       ├── __init__.py
│   │       ├── api/
│   │       ├── auth/
│   │       ├── domain/
│   │       ├── ports/
│   │       ├── services/
│   │       ├── storage/
│   │       ├── hermes_bridge/
│   │       └── hermes_compat/public/
│   ├── migrations/
│   └── tests/
│       ├── conftest.py
│       ├── domain/
│       ├── ports/
│       ├── services/
│       ├── api/
│       ├── storage/
│       └── hermes_bridge/
└── web/
    └── src/
        ├── app/
        ├── features/inbox/
        └── channel-renderers/
```

---

## Task 1: Canonical workspace and inbox domain contracts

**Files:**
- Create `platform/backend/src/agentic_platform/__init__.py`
- Create `platform/backend/tests/conftest.py` to expose the backend `src/` directory during repository tests
- Create `platform/backend/src/agentic_platform/domain/ids.py`
- Create `platform/backend/src/agentic_platform/domain/time.py`
- Create `platform/backend/src/agentic_platform/domain/errors.py`
- Create `platform/backend/src/agentic_platform/domain/workspaces.py`
- Create `platform/backend/src/agentic_platform/domain/channels.py`
- Create `platform/backend/src/agentic_platform/domain/inbox.py`
- Create `platform/backend/src/agentic_platform/domain/events.py`
- Create tests under `platform/backend/tests/domain/`

**Behavior:**
- Strong UUID-backed IDs for workspace, user, agent, connection, contact, conversation, message, event, attachment, and run identities.
- Immutable value objects for external identities and native platform references.
- Workspace membership roles: owner, admin, operator, developer, viewer.
- Conversation types: direct, group, channel, thread, topic, mailbox, notification.
- Conversation states: open, pending, snoozed, resolved, closed.
- Message direction and delivery/read states.
- Channel-event kinds for message, edit, delete, reaction, receipt, typing, membership and connection state.
- Validation rejects blank native IDs, naïve datetimes, cross-workspace relationships and invalid state transitions.

**Test gate:** domain tests pass with no FastAPI, database, Redis, object-storage or Hermes imports.

---

## Task 2: Repository and infrastructure ports

**Files:**
- Create `platform/backend/src/agentic_platform/ports/repositories.py`
- Create `platform/backend/src/agentic_platform/ports/event_bus.py`
- Create `platform/backend/src/agentic_platform/ports/object_storage.py`
- Create `platform/backend/src/agentic_platform/ports/secrets.py`
- Create `platform/backend/src/agentic_platform/ports/hermes.py`
- Create contract tests under `platform/backend/tests/ports/`

**Behavior:**
- Repository protocols are workspace-scoped and transaction-aware.
- Event bus supports ordered workspace streams and resumable cursors.
- Object storage returns opaque object references and validated metadata.
- Secret store accepts opaque references and never exposes values through descriptors.
- Hermes port exposes channel/provider/tool descriptors without leaking registry implementations.

---

## Task 3: In-memory adapters and deterministic transaction model

**Files:**
- Create `platform/backend/src/agentic_platform/storage/memory.py`
- Create tests under `platform/backend/tests/storage/test_memory.py`

**Behavior:**
- Test-only repositories implement every port.
- Transactions either commit all aggregate changes and outbox events or commit none.
- Workspace isolation is enforced at adapter boundaries.
- Duplicate native event keys resolve to the original canonical event.

---

## Task 4: Idempotent channel-event ingestion service

**Files:**
- Create `platform/backend/src/agentic_platform/services/ingestion.py`
- Create `platform/backend/src/agentic_platform/services/inbox.py`
- Create tests under `platform/backend/tests/services/`

**Behavior:**
- Accept normalized channel events plus raw-payload references.
- Create or resolve contact/external identity, conversation, participant and message records.
- Preserve native message/thread/reply IDs.
- Update unread count, last-message summary and delivery/read state deterministically.
- Duplicate events are no-ops returning the existing canonical result.
- Edit/delete/reaction/receipt events require a resolvable native target or return a typed deferred-resolution result.
- Successful writes append workspace realtime events to the outbox in the same transaction.

---

## Task 5: Workspace authentication and RBAC core

**Files:**
- Create `platform/backend/src/agentic_platform/auth/contracts.py`
- Create `platform/backend/src/agentic_platform/auth/policies.py`
- Create `platform/backend/src/agentic_platform/auth/service.py`
- Create `platform/backend/src/agentic_platform/services/workspaces.py`
- Create tests under `platform/backend/tests/auth/`

**Behavior:**
- Principal contains user ID, active workspace and membership role.
- Explicit permissions cover workspace administration, provider/secret configuration, channel management, inbox read/write, agent control, tool approvals and audit access.
- Deny-by-default policy with owner/admin/operator/developer/viewer matrices.
- Cross-workspace resource access always returns a not-found-safe denial.

---

## Task 6: FastAPI application shell and browser-safe API contracts

**Files:**
- Create `platform/backend/src/agentic_platform/api/app.py`
- Create `platform/backend/src/agentic_platform/api/errors.py`
- Create `platform/backend/src/agentic_platform/api/dependencies.py`
- Create `platform/backend/src/agentic_platform/api/health.py`
- Create `platform/backend/src/agentic_platform/api/workspaces.py`
- Create `platform/backend/src/agentic_platform/api/inbox.py`
- Create API tests under `platform/backend/tests/api/`

**Behavior:**
- App factory accepts service/port dependencies; no global production singletons.
- Health endpoint distinguishes process health, storage readiness and Hermes bridge readiness.
- Inbox endpoints are cursor-paginated and workspace-scoped.
- API DTOs never expose secret values or raw credentials.
- Typed domain errors map to stable HTTP error codes.

---

## Task 7: Realtime event contract and WebSocket stream

**Files:**
- Create `platform/backend/src/agentic_platform/services/realtime.py`
- Create `platform/backend/src/agentic_platform/api/realtime.py`
- Create tests under `platform/backend/tests/services/test_realtime.py` and `api/test_realtime.py`

**Behavior:**
- Workspace event envelope includes monotonically ordered cursor, event ID, aggregate reference, type, payload and timestamp.
- Clients resume from the last acknowledged cursor.
- Slow clients are disconnected with an explicit resumable error rather than unbounded buffering.
- Authorization is rechecked when workspace membership changes.

---

## Task 8: PostgreSQL schema and migrations

**Files:**
- Add Phase 1 backend dependency metadata with exact pins.
- Create `platform/backend/src/agentic_platform/storage/postgres/`
- Create `platform/backend/migrations/`
- Create integration tests under `platform/backend/tests/storage/postgres/`

**Tables:**
- workspaces, users, memberships
- agents and channel_connections
- contacts and external_identities
- conversations and participants
- messages, attachments, reactions and receipts
- channel_events and raw_event_objects
- workspace_outbox and audit_records

**Constraints:**
- Every tenant table contains `workspace_id`.
- Native uniqueness constraints include workspace and connection IDs.
- JSON payloads are versioned.
- Message/event ingestion and outbox append share one database transaction.

---

## Task 9: Redis coordination and S3-compatible object storage

**Files:**
- Create `platform/backend/src/agentic_platform/storage/redis/`
- Create `platform/backend/src/agentic_platform/storage/s3/`
- Add integration tests with isolated containers or explicit opt-in environment fixtures.

**Behavior:**
- Redis provides short-lived connector locks, presence, rate-limit counters and realtime fanout—not source-of-truth inbox storage.
- S3 adapter validates MIME, size, checksums and workspace prefixes.
- Object references are durable even when signed download URLs expire.

---

## Task 10: Hermes compatibility facade and descriptor bridge

**Files:**
- Create `platform/backend/src/agentic_platform/hermes_compat/public/`
- Create `platform/backend/src/agentic_platform/hermes_bridge/descriptors.py`
- Create `platform/backend/src/agentic_platform/hermes_bridge/channels.py`
- Create `platform/backend/src/agentic_platform/hermes_bridge/runtime.py`
- Create characterization tests under `platform/backend/tests/hermes_bridge/`

**Behavior:**
- Convert all 20 discovered channels into stable platform descriptors.
- Preserve concrete/deferred plugin loading and capability metadata.
- Provider/tool identity sets remain separate and explicitly mapped.
- Channel callbacks normalize into Task 4 ingestion contracts.
- Product code does not import plugin manager or gateway registries directly.

---

## Task 11: Browser shell and renderer SDK foundation

**Files:**
- Create `platform/web/` application package.
- Create shared inbox shell, typed API client, query keys and renderer SDK.
- Create renderer contract tests and initial generic renderer.

**Behavior:**
- Routes and membership come from backend descriptors, not static channel lists.
- Shared shell supports channel navigation, conversation list, conversation workspace and context panel.
- Renderer capabilities hide unsupported controls.
- No `window.hermesDesktop` requirement exists in the browser package.

---

## Phase 1 acceptance gate

Phase 1 is ready for review when:

1. Workspace and inbox domain tests are independent of infrastructure.
2. Duplicate native channel events are idempotent under concurrent ingestion.
3. Every durable query is workspace-scoped.
4. PostgreSQL migrations create all canonical inbox tables and constraints.
5. Redis and S3 are adapters, not hidden global dependencies.
6. WebSocket clients can resume from event cursors.
7. Hermes channel descriptors match the 20-channel Phase 0 inventory.
8. Browser APIs and renderer SDK contain no Electron-only dependency.
9. The first generic inbox flow works end-to-end through API, service, persistence and realtime events.
10. Full repository CI and focused Phase 1 tests pass.
