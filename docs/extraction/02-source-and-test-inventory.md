# Source and Test Inventory

**Status:** Review draft  
**Source ref:** `main@18bb6f1aeaa334badee6271fc3337f39ca6bfcfb`

## 1. Inventory method

This inventory uses two complementary forms:

1. **Authoritative inclusion roots** — every current and future descendant is in scope. This is how dynamic platform/provider plugins are captured without a stale hand-written allowlist.
2. **Named load-bearing files** — shared files outside those roots that provide discovery, auth, runtime resolution, sessions, delivery, onboarding, UI contracts, and tests.

A later executable inventory must walk the filesystem at the exact source SHA, parse plugin manifests, load registries in an isolated process, inspect imports, and compare the generated result with this plan. The executable result becomes authoritative for implementation.

### Classification

- **CORE** — expected in the reusable runtime or its synchronized source layer.
- **HOST PORT** — required behavior, but should be reached through an interface rather than copied as a permanent hidden dependency.
- **OPTIONAL UI** — reference CLI/desktop/web presentation; not required by a headless consumer.
- **TEST** — characterization or contract coverage that must follow the extracted behavior.
- **EXCLUDE BY DEFAULT** — outside requested scope unless dependency analysis proves it is required.

## 2. Authoritative dynamic roots

These roots must be included recursively in the inventory. Do not replace them with static child lists.

| Root | Classification | Reason |
|---|---|---|
| `plugins/platforms/**` | CORE | Bundled messaging platform plugins, manifests, adapters, setup hooks, optional dependencies |
| `plugins/model-providers/**` | CORE | Bundled model-provider profiles and manifests |
| `providers/**` | CORE | Provider profile contract, lazy registry, compatibility discovery |
| `gateway/relay/**` | CORE | Generic connector-backed platform transport and capability contract implementation |
| `gateway/platforms/**` | CORE | Base adapter plus direct/legacy adapters and platform subpackages |
| `tests/gateway/**` | TEST | Gateway, platform, delivery, auth, session, relay, and plugin tests |
| `tests/providers/**` | TEST | Provider profile and discovery tests |
| `tests/plugins/model_providers/**` | TEST | Provider-plugin behavior tests |
| `tests/agent/transports/**` | TEST | Protocol transport tests |

The implementation manifest should support whole roots plus explicit files. A new child under a dynamic root must automatically appear in the drift report.

## 3. Messaging channels and gateway

### 3.1 Gateway core

| Path | Class | Responsibility |
|---|---|---|
| `gateway/run.py` | CORE / HOST PORT boundary | GatewayRunner, process lifecycle, adapter startup, dispatch, slash commands, AIAgent creation, running-agent state |
| `gateway/config.py` | CORE | Gateway/platform configuration, YAML/env translation, enabled platform state |
| `gateway/platform_registry.py` | CORE | Platform descriptors, factories, lazy loading, setup hooks, env/YAML bridges, cron and standalone send metadata |
| `gateway/platforms/base.py` | CORE | MessageEvent contract, adapter lifecycle, active-session guard, chunking/media helpers |
| `gateway/session.py` | CORE | SessionStore and canonical session-key construction |
| `gateway/delivery.py` | CORE | Reply, explicit-target, cross-platform, home-channel, and background delivery |
| `gateway/pairing.py` | CORE | Pairing codes and persisted authorization state |
| `gateway/authz_mixin.py` | CORE | Gateway authorization behavior and platform allowlists |
| `gateway/channel_directory.py` | CORE | Human-readable channel/target resolution and cron delivery discovery |
| `gateway/hooks.py` | CORE | Hook discovery and lifecycle dispatch |
| `gateway/mirror.py` | CORE | Cross-session/platform message mirroring |
| `gateway/status.py` | CORE | Profile/token scoped gateway locking and status |
| `gateway/dead_targets.py` | CORE | Dead/unreachable target tracking |
| `gateway/stream_events.py` | CORE | Stream event structures and normalization |
| `gateway/stream_dispatch.py` | CORE | Streaming event delivery/dispatch |
| `gateway/slash_commands.py` | CORE | Gateway command handlers and model/provider-related gateway commands |
| `gateway/builtin_hooks/**` | CORE extension point | Always-registered gateway hook namespace |
| `gateway/relay/**` | CORE | Outbound relay connector, capability descriptors, interrupt/follow-up transport |

### 3.2 Direct or legacy platform adapters

The complete recursive root `gateway/platforms/**` is authoritative. Important current paths include:

- `gateway/platforms/signal.py`
- `gateway/platforms/weixin.py`
- `gateway/platforms/bluebubbles.py`
- `gateway/platforms/qqbot/**`
- `gateway/platforms/yuanbao.py`
- `gateway/platforms/msgraph_webhook.py`
- `gateway/platforms/webhook.py`
- `gateway/platforms/api_server.py`
- `gateway/platforms/whatsapp_cloud.py`

These coexist with plugin-packaged adapters. The extraction cannot assume every platform uses the same packaging generation.

### 3.3 Plugin platform adapters

The complete recursive root `plugins/platforms/**` is authoritative. Current platform names located through manifests, registry calls, architecture docs, and tests include:

- Telegram
- Discord
- Slack
- WhatsApp
- Matrix
- Mattermost
- Email
- SMS/Twilio
- DingTalk
- Feishu/Lark
- WeCom
- LINE
- Microsoft Teams
- IRC
- Home Assistant
- Google Chat
- ntfy
- Photon
- Raft
- SimpleX

The repository also carries direct/legacy platforms listed above and may gain new plugin directories. The extraction inventory must derive the final set from manifests and registry entries at runtime.

Each plugin directory may contain more than `adapter.py` and `plugin.yaml`; setup helpers, API clients, standalone senders, tests, or package files are included recursively.

### 3.4 Gateway CLI and plugin loading

| Path | Class | Responsibility |
|---|---|---|
| `hermes_cli/gateway.py` | CORE / OPTIONAL CLI | Platform setup, status, service control, plugin-platform enablement |
| `hermes_cli/plugins.py` | CORE | Plugin sources, manifests, enable/disable policy, platform registration hooks |
| `hermes_cli/commands.py` | CORE | Shared slash-command registry consumed by CLI and gateway |
| `hermes_cli/config.py` | CORE / HOST PORT | Config schema, migration, env metadata, atomic writes |
| `hermes_cli/main.py` | OPTIONAL CLI / HOST PORT | Top-level command dispatch and provider/setup flow integration |
| `cli.py` | OPTIONAL CLI | Interactive CLI orchestration and shared command behavior |
| `hermes_constants.py` | HOST PORT | Profile-aware paths and shared endpoint constants |
| `hermes_logging.py` | HOST PORT | Profile-aware logging |
| `utils.py` | compatibility candidate | Shared URL/env/YAML helpers imported throughout the subsystem |

### 3.5 Delivery integrations outside gateway

| Path/root | Class | Responsibility |
|---|---|---|
| `tools/send_message_tool.py` | CORE / HOST PORT boundary | Agent-facing send-message integration and standalone platform sender fallback |
| `cron/jobs.py` | HOST PORT | Scheduled job delivery target model |
| `cron/scheduler.py` | HOST PORT | Scheduled delivery and home-channel resolution |
| `hermes_state.py` | HOST PORT | Session persistence substrate used by gateway/agent surfaces |
| `run_agent.py` | HOST PORT | Concrete agent execution; replace with callback/protocol in stable channel API |
| `agent/agent_init.py` | HOST PORT | Agent initialization and resolved provider consumption |
| `model_tools.py` | HOST PORT | Tool orchestration reached by concrete Hermes agent |
| `toolsets.py` | HOST PORT | Toolset definitions used by concrete Hermes runtime |

## 4. AI providers and model runtime

### 4.1 Provider definition and discovery

| Path/root | Class | Responsibility |
|---|---|---|
| `providers/base.py` | CORE | Declarative ProviderProfile fields and provider-specific hooks |
| `providers/__init__.py` | CORE | Lazy bundled/user provider discovery, aliases, override behavior, legacy module compatibility |
| `providers/README.md` | documentation evidence | Provider contract and extension instructions |
| `plugins/model-providers/**` | CORE | All bundled provider profile packages and manifests |
| `hermes_cli/plugins.py` | CORE | General plugin manifest semantics including `model-provider` kind |

### 4.2 Provider authentication and credentials

| Path | Class | Responsibility |
|---|---|---|
| `hermes_cli/auth.py` | CORE | ProviderConfig registry, auth store, OAuth/device/external/API-key/AWS behavior, token refresh, runtime credentials |
| `hermes_cli/auth_commands.py` | OPTIONAL CLI / CORE flow | Login/logout/auth command orchestration |
| `hermes_cli/credential_lifecycle.py` | CORE | Credential add/remove/update lifecycle |
| `agent/credential_pool.py` | CORE | Pooled credentials, rotation, provider matching, custom provider pool keys |
| `agent/credential_persistence.py` | CORE | Safe credential persistence/sanitization |
| `agent/secret_scope.py` | CORE / HOST PORT | Profile/workstream-scoped secret reads |
| `hermes_cli/dashboard_auth/base.py` | CORE for dashboard/remote auth | Dashboard authentication provider protocol |
| `hermes_cli/dashboard_auth/registry.py` | CORE for dashboard/remote auth | Dashboard auth provider registration and token/session subsets |
| `hermes_cli/dashboard_auth/**` | include by dependency | Provider implementations and auth-gate support discovered during executable inventory |

### 4.3 Provider catalog, model inventory, and setup

| Path | Class | Responsibility |
|---|---|---|
| `hermes_cli/provider_catalog.py` | CORE | Unified provider descriptors and CLI/GUI parity contract |
| `hermes_cli/inventory.py` | CORE | Shared provider/model inventory payload for dashboard, TUI, and pickers |
| `hermes_cli/models.py` | CORE | Canonical providers, curated/fallback/live model catalogs, pricing/capability helpers |
| `hermes_cli/providers.py` | CORE | Provider overlays, routing semantics, metadata helpers |
| `hermes_cli/model_switch.py` | CORE | Authenticated provider discovery and model switching |
| `hermes_cli/model_setup_flows.py` | CORE logic / OPTIONAL CLI presentation | Per-provider setup and selection flows |
| `hermes_cli/setup.py` | OPTIONAL CLI / HOST PORT | First-run/setup UI and persistence orchestration |
| `hermes_cli/main.py` | OPTIONAL CLI / HOST PORT | Provider picker dispatch and shared prompt helpers |
| `hermes_cli/doctor.py` | CORE optional service | Provider/config health checks |
| `hermes_cli/azure_detect.py` | provider-specific CORE | Azure endpoint/API-mode detection |
| `hermes_cli/codex_models.py` | provider-specific CORE | Codex model catalog behavior |
| `hermes_cli/portal_cli.py` | provider-specific OPTIONAL CLI | Nous Portal onboarding/control |
| `hermes_cli/nous_subscription.py` | provider-specific CORE | Nous subscription/tier behavior |
| `agent/models_dev.py` | CORE | Model metadata/capability cache used by picker/runtime |
| `agent/usage_pricing.py` | CORE optional capability | Usage/pricing metadata |
| `agent/auxiliary_client.py` | CORE integration | Auxiliary model client using provider runtime resolution |

### 4.4 Runtime provider resolution

| Path | Class | Responsibility |
|---|---|---|
| `hermes_cli/runtime_provider.py` | CORE | Shared CLI/gateway/cron/helper provider, credential, endpoint, and API-mode resolution |
| `agent/transports/__init__.py` | CORE | Transport registry and lazy transport discovery |
| `agent/transports/base.py` | CORE | Transport contract |
| `agent/transports/types.py` | CORE | Normalized response/tool/usage types |
| `agent/transports/chat_completions.py` | CORE | OpenAI-compatible Chat Completions transport |
| `agent/transports/anthropic.py` | CORE | Anthropic Messages transport |
| `agent/transports/codex.py` | CORE | Codex/Responses transport |
| `agent/transports/bedrock.py` | CORE | Bedrock transport |
| `agent/anthropic_adapter.py` | CORE compatibility | Anthropic message/tool conversion helpers |
| `agent/chat_completion_helpers.py` | CORE compatibility | Request/response helpers |
| `agent/agent_runtime_helpers.py` | HOST PORT boundary | Runtime request preparation and provider behavior consumed by AIAgent |
| `agent/turn_context.py` | HOST PORT boundary | Per-turn runtime context |
| `agent/conversation_loop.py` | HOST PORT | Concrete loop using transports and provider profiles |
| `agent/moa_loop.py` | include if MoA remains in provider universe | Virtual provider orchestration |
| `run_agent.py` | HOST PORT | AIAgent construction, clients, credential rotation, streaming, transport consumption |

### 4.5 Current provider configurations

The provider universe must be generated from `CANONICAL_PROVIDERS`, provider profiles, and auth registry at the source SHA. Located provider configurations include the following families/identifiers:

- `nous`
- `openrouter`
- `openai-api`
- `openai-codex`
- `xai` and `xai-oauth`
- `qwen-oauth`
- `copilot` and `copilot-acp`
- `gemini`
- `vertex`
- `zai`
- `kimi-coding` and `kimi-coding-cn`
- `stepfun`
- `arcee`
- `gmi`
- `minimax`, `minimax-cn`, and `minimax-oauth`
- `anthropic`
- `alibaba` and `alibaba-coding-plan`
- `deepseek`
- `deepinfra`
- `nvidia`
- `opencode-zen` and `opencode-go`
- `kilocode`
- `huggingface`
- `xiaomi`
- `tencent-tokenhub`
- `ollama-cloud`
- `bedrock`
- `azure-foundry`
- `fireworks`
- `upstage`
- `novita`
- `lmstudio`
- `custom` and named custom providers
- `moa` virtual provider

Some identifiers are auth/config entries without a dedicated profile directory; others are profile plugins auto-added to the auth registry. Therefore, neither `plugins/model-providers/` nor `PROVIDER_REGISTRY` alone is a complete source of membership. `provider_catalog()` and the canonical provider universe are the parity boundary.

## 5. Onboarding and configuration surfaces

### 5.1 Contextual onboarding

| Path | Class | Responsibility |
|---|---|---|
| `agent/onboarding.py` | CORE | One-time behavioral hints, consent-gated first-contact profile build, persisted seen flags |

### 5.2 CLI onboarding

| Path | Class | Responsibility |
|---|---|---|
| `hermes_cli/setup.py` | OPTIONAL UI / CORE workflow | Main setup wizard and reusable prompt helpers |
| `hermes_cli/main.py` | OPTIONAL UI / CORE dispatch | Provider/model selection dispatch and setup commands |
| `hermes_cli/model_setup_flows.py` | CORE workflow | Provider-specific setup branches |
| `hermes_cli/gateway.py` | CORE workflow / OPTIONAL UI | Channel setup and plugin enablement |
| `hermes_cli/auth.py` | CORE | Auth flows and persisted state |
| `hermes_cli/auth_commands.py` | OPTIONAL UI | Authentication commands |
| `hermes_cli/provider_catalog.py` | CORE | Provider membership/metadata for all surfaces |
| `hermes_cli/inventory.py` | CORE | Picker payloads |
| `hermes_cli/models.py` | CORE | Model lists and selection metadata |
| `hermes_cli/model_switch.py` | CORE | Provider/model switching |
| `hermes_cli/portal_cli.py` | provider-specific OPTIONAL UI | Nous onboarding |
| `hermes_cli/telegram_managed_bot.py` | platform-specific OPTIONAL flow | Managed Telegram setup |
| `hermes_cli/dingtalk_auth.py` | platform-specific OPTIONAL flow | DingTalk authentication/setup |
| `gateway/platforms/qqbot/onboard.py` | platform-specific OPTIONAL flow | QQ Bot onboarding |

### 5.3 Desktop onboarding and provider settings

These files are optional reference UI but important for API and parity characterization:

- `apps/desktop/src/components/onboarding/index.tsx`
- `apps/desktop/src/components/onboarding/flow.tsx`
- `apps/desktop/src/components/onboarding/providers.tsx`
- `apps/desktop/src/components/onboarding/glyph.tsx`
- `apps/desktop/src/store/onboarding.ts`
- `apps/desktop/src/lib/model-options.ts`
- `apps/desktop/src/components/model-picker.tsx`
- `apps/desktop/src/app/settings/providers-settings.tsx`
- `apps/desktop/src/app/settings/constants.ts`
- `apps/desktop/src/hermes.ts`
- `apps/desktop/src/types/hermes.ts`
- `apps/desktop/src/app/messaging/index.tsx`
- `apps/desktop/src/app/messaging/platform-icon.tsx`

The Desktop provider-row file contains presentation ordering for selected providers. This ordering may be retained as UI metadata, but provider membership must continue to come from backend catalogs.

### 5.4 Web dashboard provider configuration

Optional reference UI/API consumers:

- `web/src/components/OAuthProvidersCard.tsx`
- `web/src/components/OAuthLoginModal.tsx`
- `web/src/pages/EnvPage.tsx`
- `web/src/lib/api.ts`

The executable inventory must locate the corresponding backend API endpoint handlers, schemas, and auth middleware by searching route registrations and imports; those backend files are included if the reference UI remains in the extracted application.

## 6. Required tests

### 6.1 Whole test roots

- `tests/gateway/**`
- `tests/providers/**`
- `tests/plugins/model_providers/**`
- `tests/agent/transports/**`

### 6.2 Provider/catalog/auth tests outside those roots

Include tests matching these behavior groups:

- `tests/hermes_cli/test_provider_*.py`
- `tests/hermes_cli/test_*_provider.py`
- `tests/hermes_cli/test_api_key_providers.py`
- `tests/hermes_cli/test_provider_parity.py`
- `tests/hermes_cli/test_provider_groups.py`
- `tests/hermes_cli/test_inventory.py`
- `tests/hermes_cli/test_models*.py`
- `tests/hermes_cli/test_model_*.py`
- `tests/hermes_cli/test_auth*.py`
- `tests/hermes_cli/test_runtime_provider*.py`
- `tests/hermes_cli/test_azure_detect.py`
- `tests/agent/test_auxiliary_client.py`
- provider attribution, credential-pool, secret-scope, and transport-selection tests found through import/symbol search.

### 6.3 Desktop/reference UI tests

- `apps/desktop/e2e/onboarding.spec.ts`
- `apps/desktop/src/store/onboarding.test.ts`
- `apps/desktop/src/components/onboarding/index.test.tsx`
- `apps/desktop/src/app/settings/providers-settings.test.tsx`
- messaging settings/platform tests discovered under `apps/desktop/src/app/messaging/` and settings test paths.

### 6.4 New extraction tests

The extracted application must add:

1. **Plugin discovery parity:** generated platform/provider set equals source registry set.
2. **Provider surface parity:** CLI, API, and reference UI membership union equals canonical provider universe.
3. **Manifest completeness:** every imported source file is declared or supplied by a documented host port.
4. **No reverse imports:** stable public package cannot import the source repository outside the synchronized layer/compatibility adapters.
5. **Upstream drift:** changed/new/deleted/renamed scoped files are reported.
6. **Channel contracts:** authorization, session key, thread routing, chunking, media, pairing, home delivery, standalone delivery.
7. **Provider contracts:** auth types, endpoint/API-mode resolution, key refresh, profiles, model listing, transport selection.
8. **Clean consumer:** install and execute a minimal fake-agent/fake-config integration in a temporary project.

## 7. Excluded by default

The following areas are not part of the requested product unless a scoped file has a proven import/runtime dependency on them:

- `skills/**`
- `optional-skills/**`
- unrelated tool implementations under `tools/**`
- memory-provider plugins under `plugins/memory/**`
- context-engine plugins under `plugins/context_engine/**`
- image/video/TTS/transcription provider systems, except shared code directly required by model-provider runtime
- kanban, achievements, observability, Spotify, Google Meet, disk cleanup, and other unrelated plugins
- website translations and general documentation
- batch trajectory/research tooling
- ACP editor integration, except a narrowly required shared transport contract
- unrelated desktop pages/components

Exclusion is evidence-based. A file must not be copied merely because it resides near an in-scope module, and it must not be removed if import tracing or tests prove it is load-bearing.

## 8. Executable inventory output required before extraction

Phase 1 must generate a machine-readable report with at least:

```yaml
source_sha: 18bb6f1aeaa334badee6271fc3337f39ca6bfcfb
files:
  - source: gateway/session.py
    class: core
    destination: vendor/gateway/session.py
    sha256: ...
    reason: canonical session key and SessionStore
    imports_in_scope: []
    host_ports: []
plugins:
  platforms: []
  model_providers: []
registries:
  platform_entries: []
  provider_profiles: []
  canonical_providers: []
  auth_providers: []
tests: []
unresolved_imports: []
```

The generated report must be reviewed before any source projection or deletion begins.