# Source-Derived Agentic Web Platform Design

**Date:** 2026-07-22  
**Status:** Design approved in conversation; written specification awaiting review  
**Planning branch:** `planning/agentic-platform-web-foundation-2026-07-22`  
**Preserved fork main:** `d5a67ad32522273115d887560ca1c08a02bc7873`  
**Extraction source baseline awaiting Checkpoint A refresh:** `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`  
**Included upstream baseline:** `NousResearch/hermes-agent@7de554277de632364c74fcf8641daa58a9a977d9`

## 1. Purpose

Build a browser-first agentic and conversational AI platform by extracting, cataloguing, projecting, and presenting capabilities already implemented in Hermes Agent.

The platform must not invent provider identities, models, authentication methods, channel fields, tool definitions, workflow actions, onboarding steps, command parameters, agent behavior, or chat capability rules. Those facts remain owned by reviewed Hermes source, manifests, registries, schemas, plugins, commands, and existing UI components.

New platform code is permitted only for generic integration concerns that cannot exist as byte-identical Hermes source:

- deterministic source inspection and catalogue generation;
- provenance and drift verification;
- stable API/domain adapters around extracted runtime capabilities;
- generic browser rendering of source-derived descriptors;
- workspace authorization, persistence, realtime delivery, and audit boundaries already established in the platform foundation;
- browser-safe replacement of terminal-only presentation without changing the underlying command or runtime behavior.

No provider-specific, channel-specific, tool-specific, workflow-specific, or model-specific business logic may be manually recreated in the platform layer.

## 2. Existing foundations

### 2.1 Agentic platform backend already merged

The existing platform foundation provides:

- canonical workspace and omnichannel inbox domain objects;
- deny-by-default workspace RBAC;
- idempotent external channel-event ingestion;
- transaction-aware repository ports and deterministic in-memory adapters;
- a browser-safe FastAPI application shell;
- health and cursor-paginated inbox endpoints;
- Hermes descriptor ports that do not leak arbitrary registry internals.

Product code continues to import only stable `agentic_platform.*` contracts. It must not import arbitrary `agent.*`, `gateway.*`, `hermes_cli.*`, `tools.*`, provider, or plugin-manager internals.

### 2.2 Extraction work already designed

Phase 2 extraction uses one byte-identical, source-relative generated tree:

```text
extracted/hermes-connect-kit/upstream/<original-repository-relative-path>
```

Classification and subsystem ownership remain metadata. The projection must not rewrite imports, rename packages, normalize provider identifiers, introduce compatibility wrappers, or refactor runtime behavior.

### 2.3 Current source characterization

The last completed extraction evidence recorded:

- 285 scoped source files;
- 20 channel/platform manifests;
- 32 model-provider manifests;
- 53 runtime plugins;
- 36 provider profiles;
- 41 canonical providers;
- 44 authentication-provider entries;
- zero unresolved in-scope internal imports.

These are characterization values, not permanent product constants. The platform must consume refreshed generated catalogues instead of embedding these numbers or identities.

## 3. Scope decomposition

The full request contains several independent but connected products. They must be implemented as separate reviewed cycles sharing one source-derived contract.

1. **Capability catalogue and provenance**
2. **Provider, authentication, and model management**
3. **Channel catalogue, configuration, and onboarding**
4. **Agentic runtime, tools, approvals, and execution logs**
5. **Conversational inbox and chat surfaces**
6. **Workflow discovery, execution, and run history**
7. **CLI/TUI capability projection into browser surfaces**
8. **Existing web, shared, and desktop component reuse**
9. **Operations, diagnostics, audit, and runtime observability**

The first implementation cycle is limited to item 1 plus the generic renderer foundation required by later items. It must not claim full provider, channel, workflow, or agent operation until their source-backed adapters are implemented and verified.

## 4. Core architectural rule

The platform has four layers with explicit ownership.

```text
Reviewed Hermes source
        │
        ▼
Exact mechanical projection
        │
        ▼
Generated capability catalogue + provenance lock
        │
        ▼
Stable platform adapters and APIs
        │
        ▼
Generic browser renderer and reused source UI
```

### 4.1 Reviewed Hermes source

This remains the authority for:

- provider identities and profiles;
- authentication methods;
- model identifiers and provider relationships;
- channel/plugin identities and capabilities;
- configuration fields and setup behavior;
- agent runtime behavior;
- tools, toolsets, parameters, and approvals;
- workflow or command behavior;
- CLI commands and arguments;
- TUI states and actions;
- chat event and rendering semantics;
- runtime logging and error identities.

### 4.2 Exact projection

The generated projection preserves repository-relative paths and Git object identity. It is not a forked implementation layer.

Every projected path must be traceable to:

- source repository;
- source commit;
- original source path;
- Git object mode;
- Git blob SHA or symlink target;
- projection lock entry.

### 4.3 Generated capability catalogue

The catalogue mechanically derives browser-consumable descriptors from source-owned data. It may normalize representation shape but must not normalize semantic identity.

For example, OpenAI API-key authentication, OpenAI Codex OAuth/runtime, native model identifiers, and OpenAI-compatible endpoints remain separate identities even when they share visible branding.

### 4.4 Stable platform adapters

Adapters expose source capabilities through stable workspace-safe contracts. They translate between platform domain DTOs and extracted Hermes runtime interfaces without duplicating Hermes behavior.

### 4.5 Browser renderer

The browser is descriptor-driven. It renders generic lists, forms, wizards, tables, timelines, logs, and execution states. It must not contain hard-coded provider/channel/tool registries.

## 5. Source-derived capability catalogue

The catalogue is a generated, deterministic, versioned artifact. It is produced only from reviewed source and runtime registry probes executed in an isolated Hermes home.

### 5.1 Catalogue domains

The catalogue must contain separate namespaces for:

- `providers`
- `provider_profiles`
- `authentication_providers`
- `model_providers`
- `models`
- `platforms`
- `channels`
- `channel_connections`
- `onboarding_flows`
- `agents`
- `tools`
- `toolsets`
- `commands`
- `workflows`
- `chat_capabilities`
- `runtime_events`
- `runtime_logs`
- `existing_ui_surfaces`

Absence from the catalogue means the browser does not present the capability as available.

### 5.2 Required descriptor provenance

Every generated descriptor includes:

```text
catalogue schema version
source repository
source commit
source path
source blob SHA
source object mode
runtime registry identity, when applicable
manifest identity, when applicable
classification
subsystem
host-boundary classification
browser projection classification
generation tool version
generation content digest
```

### 5.3 Identity preservation

The catalogue must retain both native and canonical relationships instead of flattening them.

Required relationship kinds include:

- canonical provider to provider profiles;
- provider profile to authentication provider;
- provider profile to runtime implementation;
- provider profile to model picker grouping;
- provider to native models;
- provider to compatible transport, if declared;
- platform manifest to runtime plugin identity;
- channel to onboarding flow;
- tool to toolset;
- command to handler;
- UI surface to source capability;
- CLI/TUI action to browser projection class.

Aliases remain explicit relationship records. They must not be silently merged.

### 5.4 Determinism

Given the same source tree, source commit, isolated registry environment, and generator version, two runs must produce byte-identical catalogue artifacts.

Catalogue generation fails on:

- unresolved in-scope internal imports;
- duplicate identities without an explicit alias relationship;
- source paths outside the reviewed projection;
- missing provenance fields;
- schema-invalid descriptors;
- secret values in generated output;
- unstable ordering;
- references to unreviewed project plugins;
- unknown browser projection classifications.

## 6. Provider, authentication, and model management

### 6.1 Source authority

Provider UI is generated from provider manifests, provider-profile registries, authentication registries, model-provider plugins, model metadata, setup commands, and existing source UI.

### 6.2 Provider browser surfaces

The platform may present:

- provider catalogue;
- provider/profile distinctions;
- authentication method;
- connection/setup state;
- API-key secret-reference form;
- OAuth initiation and callback status;
- Codex login/runtime status;
- OpenAI-compatible endpoint configuration;
- model catalogue and selection;
- capability metadata such as tools, vision, context, or streaming only when source declares it;
- provider runtime health;
- source-derived errors and diagnostic logs.

### 6.3 Secret boundary

Source schemas may describe credential fields, but catalogue artifacts and browser responses never include credential values.

The platform stores opaque secret references. Secret resolution occurs only inside authorized runtime adapters.

### 6.4 No static model lists

The browser must not commit manually maintained model arrays. Native and dynamically discovered models are returned by source-backed adapters and cached with provenance and refresh metadata.

## 7. Channels, configuration, and onboarding

### 7.1 Channel authority

Channel identity and capability come from platform manifests, runtime plugins, gateway transports, setup commands, configuration schemas, onboarding text, and existing UI components.

### 7.2 Source-derived channel surfaces

The browser may render:

- channel catalogue;
- manifest/runtime identity;
- channel capabilities;
- connection status;
- required configuration fields;
- secret-reference fields;
- webhook, callback, polling, or local-session requirements as source declares;
- onboarding steps and validation;
- conversation and message capability flags;
- attachments, reactions, threads, receipts, edits, deletes, typing, and membership controls only when supported;
- channel-specific diagnostic logs.

### 7.3 Generic forms

Channel setup forms are rendered from source-derived field descriptors. A manually coded provider/channel form is prohibited unless it is a direct browser-compatible reuse of an existing source component and retains provenance.

### 7.4 Host-boundary operations

Some onboarding or runtime behavior requires filesystem, subprocess, SSH, browser callback, daemon, port binding, or native application access.

Each capability is classified as one of:

- browser-direct;
- server-mediated;
- local-agent-mediated;
- embedded-terminal-only;
- host-administration-only;
- unsupported-in-browser.

The browser must not pretend that a host-bound operation is browser-native.

## 8. Agentic AI, tools, and execution

### 8.1 Agent runtime ownership

Hermes remains the agent runtime. The platform does not create a competing planner, tool loop, memory engine, or prompt execution engine.

### 8.2 Agent surfaces

The browser may expose source-backed controls for:

- agent selection and descriptors;
- provider/model assignment;
- system and session configuration already supported by source;
- toolset selection;
- tool approval policy;
- memory/context configuration;
- run creation, cancellation, retry, and history;
- streaming output;
- tool-call progress;
- runtime events, errors, and logs;
- channel bindings and conversational assignments.

### 8.3 Tool catalogue

Tool identity, description, schema, toolset membership, availability, runtime requirements, and approval requirements are extracted from the source tool registry and tool definitions.

Generic forms may render source tool parameters. They must not redefine validation or execution semantics.

### 8.4 Tool safety

Workspace and channel policies remain deny-by-default. Public-channel agents do not receive terminal, filesystem, administrative, secret-management, or external-write tools unless an explicit authorized policy permits them.

## 9. Workflows

### 9.1 Source-backed meaning

The platform must distinguish between source-defined workflows and ordinary agent/tool execution sequences.

A workflow browser surface is enabled only where reviewed source provides a workflow, task, command-sequence, or equivalent executable definition that can be represented without inventing semantics.

### 9.2 Workflow surfaces

Source-backed workflow UI may render:

- identity and description;
- input schema;
- step structure;
- agent and tool references;
- dependencies and conditions;
- run state;
- step logs;
- outputs;
- retries and failures;
- execution history;
- provenance.

A visual workflow editor is out of scope until source supports round-trippable workflow definitions and validation.

## 10. Conversational inbox and chat

### 10.1 Existing platform domain

The canonical workspace, connection, contact, conversation, message, event, and attachment domain remains the durable browser-facing model.

Native platform IDs are preserved alongside canonical IDs.

### 10.2 Chat source reuse

Chat behavior and visual components are collected from:

- existing Hermes web source;
- shared application packages;
- desktop source where browser-safe;
- gateway message transports;
- TUI chat behavior;
- agent event streams;
- tool-call and command output renderers.

### 10.3 Chat surfaces

The browser may render:

- omnichannel conversation list;
- conversation timeline;
- streamed assistant output;
- markdown and code;
- tool-call and command-output cards;
- attachments;
- agent/provider/model indicators;
- stop, retry, and reconnect states;
- channel-specific message metadata;
- delivery/read/edit/delete/reaction/thread controls only when supported;
- human handoff and authorization states;
- runtime errors and recovery guidance.

### 10.4 Renderer capability contract

Channel renderers receive capability descriptors. Unsupported controls are absent rather than disabled by guessed rules.

A generic renderer is always available for valid source-derived events that have no specialized browser-compatible source renderer.

## 11. CLI and TUI browser projection

### 11.1 Constraint

Python CLI/TUI presentation cannot be copied unchanged into a React browser and remain executable. The underlying commands, handlers, schemas, and runtime behavior remain source-owned, while the browser presentation is generated.

### 11.2 Projection classifications

Every discovered CLI command, subcommand, TUI screen, and actionable state is classified as exactly one of:

- `existing_web_ui`
- `reused_browser_component`
- `generated_form`
- `generated_wizard`
- `generated_table`
- `generated_log_view`
- `generated_chat_view`
- `server_command_action`
- `local_agent_action`
- `embedded_terminal_only`
- `host_administration_only`
- `unsupported_in_browser`

No command or TUI action is silently omitted. Unsupported entries remain visible in review reports even when hidden from end users.

### 11.3 Command execution

Generated command forms submit typed source-derived arguments to an authorized server-side command adapter. The browser never constructs arbitrary shell strings.

The adapter invokes the original source handler or a reviewed public facade. It captures structured stdout/stderr/events, exit status, cancellation, and provenance.

### 11.4 Terminal fallback

Commands whose semantics are inherently interactive, host-bound, or unsuitable for safe structured invocation remain embedded-terminal or local-agent operations. The platform labels those boundaries explicitly.

## 12. Existing UI reuse

### 12.1 Source locations

Reusable components are discovered from:

```text
web/
apps/shared/
apps/desktop/
ui-tui/
```

### 12.2 Reuse rules

A component may be reused when:

- its license and repository ownership permit reuse;
- it is browser-compatible or can be isolated from native bindings;
- its source path and blob SHA are recorded;
- it does not require `window.hermesDesktop` or an Electron bridge in browser execution;
- it consumes source-derived descriptors or stable platform APIs;
- it does not embed static provider/channel/tool identity lists that conflict with the catalogue.

### 12.3 Adaptation rule

When a source component requires adaptation, the original component remains unmodified in the projection. A small platform wrapper may translate stable API descriptors into its props. Business rules remain in source-backed adapters.

## 13. Web application boundary

The independent product application will live under:

```text
apps/platform-web/
```

This path already fits the repository `apps/*` workspace pattern and remains separate from the upstream Hermes `web/` application.

The application may use the existing React, TypeScript, Vite, Tailwind, React Router, Vitest, Motion, GSAP, `@nous-research/ui`, and shared Hermes packages already present in the repository.

The platform web application must not require Electron or desktop globals.

## 14. Stable API boundary

The browser talks only to stable `agentic_platform` APIs. It does not import Python source or registries directly.

Required API groups are introduced incrementally:

- health and runtime readiness;
- capability catalogue and provenance;
- provider/authentication/model descriptors and actions;
- channel descriptors, connections, and onboarding actions;
- agent descriptors and runs;
- tools, toolsets, approvals, and execution events;
- workflows and run history;
- conversations, messages, attachments, and realtime events;
- command/TUI projection descriptors and actions;
- logs, diagnostics, and audit records.

Every API is workspace-scoped where applicable and checks explicit permissions.

## 15. Logging, observability, and audit

### 15.1 Source-derived runtime events

The platform captures provider, channel, agent, tool, workflow, gateway, and command events without changing their source identity.

### 15.2 Stable envelope

Events are wrapped in a platform envelope containing:

- workspace ID;
- event ID;
- source capability identity;
- run/connection/conversation reference;
- source timestamp and received timestamp;
- severity and event type;
- structured payload reference;
- provenance reference;
- resumable realtime cursor.

### 15.3 Secret redaction

Raw logs are filtered by reviewed redaction rules before durable storage or browser delivery. Provider keys, tokens, OAuth credentials, authorization headers, and secret field values must never appear in catalogue artifacts, API responses, or audit payloads.

### 15.4 Audit requirements

Administrative configuration, provider login, channel connection, tool approval, workflow execution, command execution, and secret-reference changes create workspace audit records.

## 16. Error handling

Errors are separated into:

- catalogue generation errors;
- source drift/provenance errors;
- unsupported browser-boundary errors;
- authentication and authorization errors;
- provider/model errors;
- channel connection/onboarding errors;
- agent/tool/workflow runtime errors;
- host/local-agent errors;
- transport/realtime errors.

The browser shows the source capability identity, stable platform error code, safe message, retryability, correlation ID, and relevant provenance. It never exposes secret values or arbitrary tracebacks to ordinary users.

## 17. Security model

- Workspace ID is mandatory on durable product records and queries.
- RBAC is deny-by-default.
- Secrets are opaque references.
- Browser forms cannot submit unknown fields outside source-derived schemas.
- Command execution uses typed allowlisted actions, never arbitrary shell text.
- Host-bound operations require explicit local-agent or administrator authorization.
- Tool approvals are enforced server-side.
- Public channel agents receive restricted tool policies by default.
- Source catalogue generation runs with project plugins disabled and in an isolated Hermes home.
- Catalogue and projection artifacts are content-addressed and drift-checked.

## 18. Testing strategy

### 18.1 Extraction and projection gates

Before capability integration:

- Checkpoint A evidence is refreshed;
- manifest and Git provenance are verified;
- projection lock matches the reviewed proposed lock;
- every projected source object matches the approved source baseline;
- projected tests run in a dependency-only environment without fallback to the source checkout.

### 18.2 Catalogue tests

Tests must prove:

- deterministic generation;
- complete required provenance;
- identity relationship preservation;
- no secrets;
- no duplicate unclassified identities;
- zero unresolved internal imports;
- every reviewed CLI/TUI item has a projection classification;
- every browser descriptor references a reviewed source object.

### 18.3 Adapter contract tests

Each source-backed adapter has characterization tests against the projected source and contract tests against stable platform ports.

### 18.4 Browser tests

Browser tests verify:

- no hard-coded provider/channel/tool lists;
- descriptor-driven routes and forms;
- unsupported capabilities are not displayed;
- loading, empty, offline, permission, source-drift, and runtime-error states;
- no Electron dependency;
- provenance is available for administrative review;
- keyboard and screen-reader accessibility;
- responsive desktop and mobile layouts.

### 18.5 End-to-end gates

Each product slice must prove one real source-backed flow end to end before expanding breadth. Examples:

- provider authentication and model selection;
- channel onboarding and first incoming conversation;
- agent run with a source tool and streamed logs;
- workflow execution and step history;
- CLI command represented as a generated safe form.

## 19. Development and review gates

### Gate 0 — Checkpoint A extraction evidence

Refresh and review the approved Phase 2 source characterization. No schema-v2 or projection work precedes this gate.

### Gate 1 — Exact projection

Complete manifest v2, provenance, projector safety, source-object parity, clean projected tests, and human review.

### Gate 2 — Capability catalogue

Generate the complete deterministic catalogue, identity graph, CLI/TUI classification report, and source UI reuse report.

### Gate 3 — Stable descriptor APIs

Expose read-only catalogue APIs and provenance through the platform backend. No mutation actions yet.

### Gate 4 — Generic platform web foundation

Create the independent browser shell, descriptor renderer SDK, health screen, catalogue explorer, and existing inbox list integration.

### Gate 5 — Vertical source-backed slices

Implement and review one slice at a time in this order:

1. providers/authentication/models;
2. channels/onboarding;
3. agent runs/tools/logs;
4. conversational chat;
5. workflows;
6. CLI/TUI projected actions;
7. operations and diagnostics.

Each gate uses an isolated planning branch, implementation branch, draft PR, focused verification, self-review, and human approval before merge.

## 20. First implementation cycle

The first cycle after this design is approved in written form is:

**Source-Derived Capability Catalogue and Generic Renderer Foundation**

It will design and plan:

- catalogue schema;
- source scanners and registry probes;
- provenance records and content digests;
- identity graph;
- CLI/TUI projection classification;
- existing UI reuse inventory;
- read-only platform catalogue API;
- independent `apps/platform-web` shell;
- generic descriptor list/detail/form/table/log renderer contracts;
- health and provenance screens;
- tests and review evidence.

It will not implement provider login, channel connection, arbitrary command execution, agent mutation, tool execution, workflow editing, or full chat sending.

## 21. Explicit non-goals

The following are not authorized by this design:

- manually recreating Hermes business behavior;
- rewriting all Hermes source into a new framework;
- static provider/model/channel/tool registries in the browser;
- provider or channel identity normalization that loses source distinctions;
- modifying the exact projection to make imports easier;
- a competing agent runtime;
- arbitrary browser shell access;
- automatic enabling or expansion of GitHub Actions;
- changing fork `main` before reviewed PR gates;
- claiming a feature exists when its source-backed adapter is absent;
- claiming tests passed when the required local commands could not run.

## 22. Acceptance criteria

This design is successfully implemented when:

1. All exposed capabilities originate from reviewed source, runtime registries, or existing source UI.
2. Every capability shown in the platform has complete provenance.
3. Provider, authentication, model, channel, tool, command, workflow, and UI identities remain distinct and traceable.
4. The browser contains no manually maintained source capability registry.
5. CLI and TUI coverage is complete through explicit projection classification.
6. Browser-safe source components are reused where appropriate.
7. Terminal-only and host-bound behavior is labelled and mediated rather than falsely converted.
8. The platform backend remains workspace-safe, permission-controlled, and secret-safe.
9. Each vertical slice proves a real end-to-end source-backed flow.
10. Fork `main` changes only through reviewed, verified pull requests.

## 23. Final design decision

Use **source-derived generation**.

Hermes source remains authoritative for capabilities and behavior. The project adds only deterministic extraction, provenance, stable adapters, generic browser rendering, workspace controls, and necessary browser-safe wrappers. It does not invent domain-specific provider, channel, agent, tool, workflow, onboarding, command, or chat behavior.
