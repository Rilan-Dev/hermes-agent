# Agentic AI Platform Delivery Roadmap

**Status:** Active execution control document  
**Planning branch:** `planning/agentic-platform-phases-1-6`  
**Implementation rule:** A later phase cannot begin until the preceding phase acceptance gate is verified on the current `main` merge candidate.

## 1. Mandatory task format

Every implementation task in every phase must contain all of the following before code is written:

1. Exact files to create, modify, and test.
2. Explicit consumed and produced interfaces, including type signatures.
3. One focused failing test that demonstrates the missing behavior.
4. A recorded red-test result.
5. The smallest implementation that satisfies the test.
6. Focused test verification.
7. Full phase regression verification.
8. Repository lint, type, compile, dependency-lock, and diff checks.
9. Security review for workspace isolation, secrets, external input, and unsafe tools.
10. A focused commit and a documented rollback boundary.

A task is not complete because code exists. It is complete only when its acceptance checks pass on GitHub CI for the exact commit.

## 2. Branch and pull-request policy

- One implementation branch per phase.
- One focused commit per independently reviewable task.
- Draft PR while tasks are incomplete.
- Do not merge a dependent PR into a temporary base branch and assume it reached `main`.
- Before merge, compare the phase branch directly with current `main`.
- Keep production runtime edits separate from documentation-only planning commits.
- Never force-push reviewed history unless recovery is explicitly approved.
- Preserve upstream Hermes paths; locally owned product code imports stable `agentic_platform.*` or `hermes_compat.public.*` contracts only.

## 3. Current reconciliation gate

Phase 0 is on `main`. Phase 1 is being reconciled through PR #3 from `worktree/agentic-platform-phase-1` into `main`.

Phase 1 is **not complete** until Tasks 7–11 below are implemented and all Phase 1 acceptance checks pass.

---

# Phase 1 — Platform Foundation and Omnichannel Core

## Completed task groups

1. Canonical workspace and inbox domain.
2. Workspace-scoped repository and infrastructure ports.
3. Deterministic transactional in-memory adapters.
4. Concurrent idempotent channel-event ingestion.
5. Deny-by-default workspace RBAC.
6. Browser-safe FastAPI API shell.

## Remaining Task 7 — Realtime and resumable WebSocket stream

**Deliverables**

- Ordered workspace event batches based on `EventCursor`.
- WebSocket route scoped to one workspace.
- Resume from the last acknowledged cursor.
- Bounded server-side buffering.
- Explicit slow-client close code and resumable cursor.
- Authorization recheck before each delivered batch.
- Focused service and API tests.

**Gate**

A disconnected client reconnects with its last cursor and receives each later event exactly once and in order. A slow client cannot create unbounded memory growth.

## Remaining Task 8 — PostgreSQL persistence and migrations

**Deliverables**

- Exact-pinned backend dependency metadata.
- Versioned SQL migrations.
- PostgreSQL implementations of all repository and unit-of-work ports.
- Canonical tables for workspaces, users, memberships, agents, channel connections, contacts, identities, conversations, participants, messages, attachments, reactions, receipts, channel events, raw event objects, outbox events, and audit records.
- Workspace-scoped primary/foreign/unique indexes.
- Atomic ingestion plus outbox transaction.
- Migration upgrade/downgrade tests and repository contract tests.

**Gate**

The same repository contract suite passes against memory and PostgreSQL adapters. Concurrent duplicate ingestion produces one canonical message and one outbox event.

## Remaining Task 9 — Redis coordination and S3-compatible object storage

**Deliverables**

- Redis adapter for connector locks, presence, rate-limit counters, and realtime fanout only.
- S3-compatible adapter for durable attachments and raw payloads.
- Workspace-prefixed object keys.
- MIME, size, checksum, and metadata validation.
- Expiring download URLs that do not replace durable object references.
- Failure and retry tests.

**Gate**

Redis loss does not lose inbox truth. Expired signed URLs can be regenerated from durable references. Cross-workspace object access is rejected.

## Remaining Task 10 — Hermes compatibility facade and descriptor bridge

**Deliverables**

- Stable public Hermes facade.
- Channel descriptor bridge covering all 20 Phase 0 runtime channels.
- Separate provider profile/auth/canonical/catalog/transport/service identities.
- Tool and toolset descriptor bridge.
- Concrete and deferred plugin loading preserved.
- Hermes channel callbacks normalized into the canonical ingestion service.
- Characterization tests proving no arbitrary product import of gateway or plugin internals.

**Gate**

The generated bridge channel set exactly matches the Phase 0 inventory, and adding or removing a manifest produces a deterministic contract-test change.

## Remaining Task 11 — Browser application shell and renderer SDK

**Deliverables**

- `platform/web` React application.
- Typed browser API client.
- Workspace and RBAC-aware routing.
- Shared four-column inbox shell: channel navigation, conversation list, conversation workspace, context panel.
- Backend-driven channel navigation.
- Renderer SDK and generic renderer.
- Capability-gated controls.
- WebSocket cursor resume support.
- No Electron bridge dependency.

**Gate**

A browser-only end-to-end test ingests a normalized event, persists it, receives the realtime update, displays it in the generic inbox, reloads, resumes from the cursor, and displays no duplicate.

## Phase 1 acceptance gate

Phase 1 can be marked complete only when all conditions are verified:

1. Domain tests remain infrastructure-independent.
2. Concurrent duplicate channel events are idempotent.
3. Every durable query is workspace-scoped.
4. PostgreSQL migrations create all canonical tables and constraints.
5. Redis and S3 remain replaceable adapters.
6. WebSocket clients resume from event cursors.
7. Hermes descriptors match the 20-channel inventory.
8. Browser APIs and renderer SDK contain no Electron-only dependency.
9. The generic inbox flow works end to end.
10. Current-main merge CI is fully green.

---

# Phase 2 — First Native Channel Interfaces

## Task 2.1 — Channel capability schema expansion

- Formalize message, thread, reaction, receipt, typing, media, card, poll, template, mention, moderation, history-sync, and connection capabilities.
- Add backend descriptor versioning and renderer compatibility validation.
- Add generic fallback behavior for unknown capabilities.

## Task 2.2 — Channel connection and onboarding workspace

- Connection catalog and multiple accounts per platform.
- Opaque secret-reference forms.
- OAuth/device/API-key/QR/callback setup flows as reported by descriptors.
- Test, connect, disconnect, restart, health, and rate-limit status.
- Connection-level agent and provider policy binding.

## Task 2.3 — WhatsApp native-inspired workspace

- Conversation and contact layout.
- Incoming/outgoing bubble rendering.
- Reply preview, media, documents, voice notes, delivery/read ticks, templates, and business identity.
- WhatsApp-specific composer capability restrictions.
- Inbound, outbound, retry, receipt, and reconnect tests.

## Task 2.4 — Telegram native-inspired workspace

- Direct chats, groups, channels, topics, replies, reactions, stickers, voice, files, and media albums.
- Bot command and inline-button rendering where supported.
- Topic/thread routing tests.

## Task 2.5 — Slack native-inspired workspace

- Workspace/channel navigation.
- Author-row messages, threads, mentions, reactions, files, code blocks, and edits.
- Thread composer and reply synchronization tests.

## Task 2.6 — Discord native-inspired workspace

- Server/channel navigation.
- Roles, author rows, embeds, threads, reactions, attachments, and moderation controls gated by capability and permission.
- Guild/channel/thread isolation tests.

## Task 2.7 — Cross-channel operator regression suite

- One canonical conversation model across all four renderers.
- Channel-specific rendering snapshot and interaction tests.
- Switching channels preserves workspace, assignment, unread, and cursor state.
- Generic renderer remains functional for every other discovered channel.

## Phase 2 acceptance gate

- WhatsApp, Telegram, Slack, and Discord have working dedicated inbox routes.
- Unsupported controls never appear.
- Native IDs, thread/topic IDs, receipts, reactions, edits, deletes, and attachments round-trip correctly.
- Connection onboarding and health checks work from browser UI.
- Full backend, web, connector, and end-to-end CI is green.

---

# Phase 3 — Agents, AI Providers, Tools, and MCP

## Task 3.1 — Versioned agent registry

- Agent identity, instructions, status, revisions, publish, pause, rollback, budgets, timeouts, languages, business hours, handoff policy, channel bindings, and test cases.

## Task 3.2 — Provider account and model catalog control plane

- OAuth, API key, cloud credential, CLI-managed, local, and OpenAI-compatible accounts.
- Provider health, capability, price, context, latency, region, and availability metadata.
- Secret-safe account APIs and browser forms.

## Task 3.3 — Provider routing and failover engine

- Workspace, agent, channel-binding, workflow, and conversation override hierarchy.
- Fixed, ordered fallback, cheapest-compatible, fastest-healthy, quality, capability-required, region-restricted, budget-limited, weighted, and A/B strategies.
- Circuit breaking, rate-limit-aware retry, route reason, cost, and fallback audit records.

## Task 3.4 — Tool and toolset registry

- Dynamic built-in, plugin, MCP, and platform tool discovery.
- Input/output schemas, readiness, credentials, installation, risk class, metrics, and compatibility.
- No static duplicate membership list.

## Task 3.5 — Permission and approval engine

- Workspace, agent, channel, workflow, and conversation tool policies.
- Denials override enablement.
- Human approval queue for external write, local write, command execution, sensitive-data, and administrative tools.
- Public-channel safe defaults.

## Task 3.6 — MCP management

- Add, edit, enable, disable, authenticate, test, and remove MCP servers.
- Dynamic toolset refresh and schema-change audit.
- Process/network isolation policy.

## Task 3.7 — Agent Builder and test laboratory

- Browser UI for instructions, provider policy, tools, skills, memory, knowledge, channel bindings, approval policy, limits, and test conversations.
- Trace viewer showing model routes, tools, approvals, tokens, cost, latency, and errors.

## Phase 3 acceptance gate

- A browser-created agent can be published, bound to a channel, route across providers with audited fallback, call an allowed tool, request approval for a dangerous tool, and be rolled back to an earlier revision.

---

# Phase 4 — Remaining Channel Families

## Task 4.1 — Renderer-family contracts

- Mobile messaging, team collaboration, community/server, mailbox, notification, and generic families.

## Task 4.2 — Email mailbox renderer

- Folders, participants, subject/threading, HTML/plain text, attachments, reply/forward, delivery failure, and mailbox sync.

## Task 4.3 — SMS and notification renderers

- SMS segmentation/status and minimal notification channels such as webhook and ntfy.

## Task 4.4 — Remaining mobile messaging adapters

- Signal, LINE, WeChat/Weixin, SimpleX, BlueBubbles, and other discovered mobile adapters.

## Task 4.5 — Remaining collaboration adapters

- Mattermost, Teams, Google Chat, Feishu, WeCom, DingTalk, and other discovered collaboration adapters.

## Task 4.6 — Remaining community adapters

- Matrix, IRC, QQ, and other discovered community/server adapters.

## Task 4.7 — Capability matrix and fallback regression

- Every discovered runtime channel resolves to a connection descriptor, a renderer family, and a tested generic fallback.

## Phase 4 acceptance gate

- Every runtime channel from the current inventory is configurable and usable from Web UI.
- Dedicated renderers exist where platform concepts require them; generic fallback covers the rest without data loss.

---

# Phase 5 — Workflows and Human Inbox Operations

## Task 5.1 — Versioned workflow domain

- Message, schedule, webhook, and manual triggers.
- Conditions, branches, delays, retries, failure routes, and versioning.

## Task 5.2 — Workflow action runtime

- Agent calls, tool calls, messages, assignment, tags, CRM actions, subagents, and human approvals.
- Idempotent execution and durable checkpoints.

## Task 5.3 — Workflow builder UI

- Validated node graph, configuration panels, test run, publish, pause, clone, and rollback.

## Task 5.4 — Assignment and handoff

- Teams, queues, ownership, agent pause/resume, human takeover, collision detection, and release back to agent.

## Task 5.5 — Internal collaboration

- Internal notes, mentions, tags, priority, saved replies, and complete audit history.

## Task 5.6 — Business hours, SLA, and lifecycle states

- Open, pending, snoozed, resolved, closed, due times, escalations, and breach events.

## Phase 5 acceptance gate

- An inbound channel event can trigger a versioned workflow, call an agent, request tool approval, route to a human queue, satisfy or breach an SLA, and preserve a complete auditable timeline.

---

# Phase 6 — Production Hardening, Operations, and Upstream Sync

## Task 6.1 — Security review and hardening

- Threat model, workspace isolation, secret encryption/rotation, OAuth state/PKCE, webhook signatures, SSRF, MIME/size validation, malware-scan integration, prompt-injection boundaries, tool sandboxing, PII retention/export/delete/redaction, and penetration tests.

## Task 6.2 — Observability and audit

- Structured logs, traces, metrics, request IDs, connector health, provider routes, model/tool usage, approvals, queue depth, failures, dashboards, and alerts.

## Task 6.3 — Usage, cost, and analytics

- Per workspace/agent/channel/provider/model/tool usage, cost allocation, latency, quality, fallback, resolution, SLA, and export APIs.

## Task 6.4 — Reliability and performance

- Load, soak, reconnect, backpressure, retry-storm, duplicate-event, large-attachment, and multi-workspace tests.
- Recovery objectives and capacity limits.

## Task 6.5 — Backup, restore, and disaster recovery

- PostgreSQL backups/PITR, object-storage versioning, secret-store recovery, restore drills, and documented RPO/RTO evidence.

## Task 6.6 — Deployment and release

- Docker Compose reference deployment, production configuration validation, migrations, health/readiness, zero-downtime upgrade strategy, and Kubernetes-compatible manifests.

## Task 6.7 — Upstream Hermes synchronization

- Source-SHA pinning, deterministic drift reports, added/removed/renamed file detection, compatibility patch tracking, inventory regeneration, and blocking characterization tests.

## Phase 6 acceptance gate

- Security, restore, load, upgrade, rollback, observability, and upstream-sync drills pass using production-like infrastructure.
- The platform has a versioned release, reproducible deployment, support runbook, and no unresolved critical findings.

---

## 4. Completion rule

The project is not declared complete based on a percentage, a branch name, or a merged PR. Completion requires fresh evidence for every phase acceptance gate on the exact release commit.