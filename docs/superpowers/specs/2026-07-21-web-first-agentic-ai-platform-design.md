# Web-First Agentic AI Platform Design

**Status:** Approved for Phase 0 implementation  
**Source project:** `Rilan-Dev/hermes-agent`  
**Implementation branch:** `worktree/agentic-platform-phase-0`

## 1. Product goal

Build a production-capable, browser-first Agentic AI Platform on top of the Hermes runtime. The platform must let workspace users configure agents, connect AI providers, assign tools, connect messaging channels, operate channel-specific inboxes, run workflows, supervise agent activity, and receive upstream Hermes improvements without repeatedly rebuilding the product.

The Web UI is the primary product surface. Desktop and CLI remain useful reference clients and compatibility surfaces, but they do not define the final application boundary.

## 2. Corrected scope

The earlier extraction plan was too narrow because it treated web and Desktop code as optional consumers around a reusable channels/providers package. The approved scope is larger:

1. Preserve Hermes as the upstream-compatible agent runtime.
2. Extract and formalize channels, providers, tools, onboarding, sessions, delivery, credentials, and runtime APIs.
3. Add a durable omnichannel inbox domain.
4. Add browser-safe APIs and real-time events.
5. Add dedicated channel workspaces that reflect each platform's concepts.
6. Add agent, provider-routing, tool-permission, workflow, analytics, audit, and team-management control planes.
7. Keep upstream-synchronized code separate from locally owned application contracts.

## 3. Architectural approach

Use a modular monolith first, with explicit internal boundaries and background workers. Avoid premature microservices.

```text
Browser Web UI
        |
        v
Web API + Authentication + WebSocket Gateway
        |
        +-- Workspace and RBAC
        +-- Agent Registry
        +-- Provider Router
        +-- Tool Registry and Runtime
        +-- Omnichannel Inbox
        +-- Channel Connector Runtime
        +-- Workflow Engine
        +-- Knowledge and Memory
        +-- Audit, Usage and Observability
              |
              +-- PostgreSQL
              +-- Redis
              +-- S3-compatible object storage
              +-- Background workers
```

Hermes compatibility is maintained through a synchronized source/adapter layer. New web-product code imports stable local contracts and does not depend directly on arbitrary upstream internals.

## 4. Repository structure target

```text
platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── workspaces/
│   │   ├── agents/
│   │   ├── providers/
│   │   ├── tools/
│   │   ├── channels/
│   │   ├── inbox/
│   │   ├── workflows/
│   │   ├── knowledge/
│   │   ├── analytics/
│   │   ├── audit/
│   │   ├── realtime/
│   │   └── storage/
│   ├── migrations/
│   └── tests/
├── web/
│   ├── src/app/
│   ├── src/features/
│   │   ├── inbox/
│   │   ├── agents/
│   │   ├── providers/
│   │   ├── tools/
│   │   ├── channels/
│   │   ├── workflows/
│   │   ├── knowledge/
│   │   ├── analytics/
│   │   └── settings/
│   ├── src/channel-renderers/
│   └── tests/
├── hermes_compat/
│   ├── public/
│   ├── adapters/
│   ├── vendor/
│   └── manifests/
├── scripts/platform_inventory/
├── generated/platform_inventory/
└── docs/platform/
```

This is a target structure, not a Phase 0 scaffolding requirement. Phase 0 creates only the inventory and planning foundations needed to confirm exact paths and boundaries.

## 5. Omnichannel inbox domain

### 5.1 Workspace

Owns users, agents, provider accounts, tools, channel connections, conversations, workflows, secrets, usage, and audit records.

### 5.2 Channel connection

Represents one configured external account or endpoint, such as a WhatsApp Business number, Telegram bot, Slack workspace, Discord bot, email mailbox, or webhook endpoint. A workspace may have multiple connections for the same platform.

### 5.3 Contact and external identity

A contact represents a real person or organization. External identities link that contact to platform-specific identities such as phone numbers, Telegram IDs, Slack member IDs, Discord users, or email addresses.

### 5.4 Conversation

A canonical inbox conversation stores channel connection, external chat/thread identity, type, participants, status, priority, tags, unread count, assignment, SLA timestamps, bound agent, handoff state, and last-message summary.

### 5.5 Message

A durable message stores native platform ID, direction, sender identity, text, structured content, attachments, replies, thread information, reactions, delivery/read status, edit/delete state, raw event reference, agent run reference, provider/model attribution, usage, and timestamps.

### 5.6 Channel event

Stores the original normalized event and raw platform payload for messages, edits, deletes, reactions, receipts, typing, member changes, and connection state. Event ingestion must be idempotent.

## 6. Channel connector contract

Every channel plugin must expose a backend descriptor and may expose a frontend renderer descriptor.

Required backend metadata:

- platform ID and display name;
- connection and authentication schema;
- supported conversation types;
- message types and attachment limits;
- threads/topics;
- reactions;
- edit/delete support;
- delivery/read receipts;
- typing/presence;
- mentions;
- buttons/cards/polls/templates;
- contact/history synchronization;
- transport mode and callback requirements;
- security and rate-limit constraints.

Required runtime operations:

- connect, disconnect, test, and report health;
- normalize inbound events;
- send, edit, delete, and react where supported;
- fetch history/contact metadata where supported;
- preserve external IDs and idempotency keys;
- expose deterministic error categories.

## 7. Channel-specific Web UI

The application uses a shared inbox shell with plugin renderers. Each channel receives a dedicated route and recognizable, native-inspired interaction model without impersonating the official application.

Shared shell:

```text
Channel navigation | Conversation list | Conversation workspace | Context panel
```

Renderer families:

- Mobile messaging: WhatsApp, Telegram, Signal, LINE, WeChat, SimpleX.
- Team collaboration: Slack, Mattermost, Teams, Google Chat, Feishu, WeCom, DingTalk.
- Community/server: Discord, Matrix, IRC, QQ.
- Mailbox: Email.
- Notification: SMS, ntfy, webhook.

Initial reference renderers:

1. WhatsApp — bubble layout, delivery/read ticks, reply previews, voice notes, media and business identity.
2. Telegram — chats/groups/channels/topics, replies, stickers, voice, media albums and reactions.
3. Slack — workspaces/channels, author rows, threads, mentions, reactions, files and code blocks.
4. Discord — servers/channels, roles, author rows, embeds, threads, reactions and moderation capabilities.

The UI must render only capabilities reported by the backend descriptor.

## 8. Agent control plane

Each agent includes:

- identity, avatar and description;
- versioned system instructions;
- provider-routing policy;
- default and fallback models;
- allowed toolsets and tools;
- approval policy;
- skills;
- memory provider;
- knowledge sources;
- channel bindings and routing rules;
- automatic response and human handoff rules;
- business hours;
- language and response style;
- safety policy;
- iteration, timeout and budget limits;
- test conversations;
- publish, pause and rollback state.

One agent may serve multiple channels, and a channel connection may route different conversations to different agents.

## 9. Provider control plane

Provider accounts support OAuth, API keys, cloud credentials, custom OpenAI-compatible endpoints, and local model endpoints.

Model metadata includes:

- text, vision, audio and reasoning capabilities;
- tool calling and structured output;
- context/output limits;
- cost;
- latency class;
- region/data residency;
- health and availability.

Policy resolution order:

```text
Workspace policy
  -> Agent policy
  -> Channel binding policy
  -> Workflow policy
  -> Temporary conversation override
```

Routing strategies include fixed, ordered fallback, cheapest compatible, fastest healthy, highest quality, capability-required, data-region-restricted, budget-limited, weighted distribution and A/B testing.

Every routing decision and fallback must be auditable.

## 10. Tool control plane

The platform must inventory all built-in, plugin and MCP tools dynamically.

Each tool descriptor includes:

- name, source, description and schema;
- toolset membership;
- required credentials/installations;
- readiness and health;
- risk class;
- approval policy;
- agent/channel compatibility;
- usage/error metrics.

Configuration levels are workspace, agent, channel binding, workflow and conversation override. Denials and safety restrictions take precedence over lower-level enablement.

Risk classes:

- read-only;
- external write;
- local write;
- command execution;
- sensitive data;
- administrative.

Dangerous actions may require Web UI approval. Public messaging agents must not inherit terminal, filesystem or administrative tools by default.

## 11. Workflow engine

Workflows support message, schedule and webhook triggers; conditions; agent calls; human approvals; tool calls; branching; delays; messages; assignment; tags; CRM integration; subagents; retries and failure routes.

Workflows are versioned, testable and auditable.

## 12. Human inbox operations

Required operations include assignment, pause/resume agent, internal notes, team mentions, tags, priority, open/pending/snoozed/resolved states, saved replies, business hours, SLA timers, collision detection, human handoff and complete audit history.

## 13. Security requirements

Mandatory requirements:

- workspace isolation and role-based access;
- encrypted secret storage;
- secrets never returned to normal clients;
- OAuth state/PKCE validation;
- webhook signature verification;
- idempotent channel ingestion;
- connector rate limiting;
- SSRF protection;
- attachment size/MIME validation and malware scanning integration;
- tool sandboxing and approval policy;
- public-channel safe defaults;
- prompt-injection boundaries;
- audit logging;
- PII retention, export, deletion and redaction;
- backups and disaster recovery.

Existing Hermes profile isolation, credential scoping, pairing, authorization, media safety and multiplexing guards are compatibility requirements, not optional legacy behavior.

## 14. Technology direction

- Frontend: React 19, TypeScript, Vite, React Router, TanStack Query.
- Backend: Python with FastAPI-compatible APIs.
- Database: PostgreSQL.
- Cache/locks/queues: Redis.
- Attachments: S3-compatible object storage.
- Realtime: WebSockets with resumable event cursors.
- Initial search: PostgreSQL full-text search.
- Deployment: Docker Compose first; Kubernetes-compatible later.

SQLite remains supported for current Hermes local-session compatibility and import, not as the primary multi-user inbox database.

## 15. Upstream compatibility

Maintain two layers:

1. Mechanically synchronized upstream source and manifests.
2. Locally owned public contracts, adapters and product code.

Source synchronization records origin paths, source SHA, hashes, additions, removals, renames, plugin membership and compatibility patches. Locally owned public APIs are never overwritten by synchronization.

## 16. Delivery phases

### Phase 0 — Refresh and machine inventory

- Pin source refs and compare fork/upstream/planning branches.
- Generate channel, provider, tool, frontend, API, dependency and test inventories.
- Generate capability matrices and coupling reports.
- Identify Electron-only code and browser-safe APIs.
- Define extraction manifest schema.
- Produce a reviewable Phase 0 report.

### Phase 1 — Platform foundation and omnichannel core

- Browser application shell.
- Authentication, workspaces and RBAC.
- PostgreSQL, Redis and object storage.
- Canonical inbox schema.
- Event ingestion and WebSocket updates.
- Unified inbox and renderer SDK.
- Hermes adapter bridge.

### Phase 2 — First native channel interfaces

WhatsApp, Telegram, Slack and Discord.

### Phase 3 — Agents, providers and tools

Agent builder, provider routing/failover, tool registry, MCP management, permissions and approvals.

### Phase 4 — Remaining channel renderers

Email, SMS and all discovered bundled/direct channel adapters.

### Phase 5 — Workflows and human operations

Workflow builder, assignments, handoffs, internal notes, SLA and saved replies.

### Phase 6 — Production hardening

Security review, observability, analytics, backup/recovery, load tests, upstream-sync automation and deployment.

## 17. Phase 0 success criteria

Phase 0 is complete only when:

1. The inspected source commit is explicit and reproducible.
2. Every bundled/direct channel is discovered from code/manifests, not a static guess.
3. Every canonical/auth/runtime/model provider identifier is classified.
4. Every built-in/plugin/MCP tool registration path is mapped.
5. Existing Web/Desktop/API surfaces are mapped to backend endpoints and Electron dependencies.
6. Scoped tests and optional dependency requirements are generated.
7. Unresolved imports and dynamic-loading risks are reported.
8. A machine-readable extraction manifest draft and human-readable capability report are committed.
9. No production source has been deleted or moved.
10. The report is sufficient to write the Phase 1 implementation plan without guessing.