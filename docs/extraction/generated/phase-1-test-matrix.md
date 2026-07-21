# Phase 1 Test Matrix

| Kind | Path or pattern | Protected behavior |
|---|---|---|
| root | tests/gateway | Gateway, channel adapter, delivery, authorization, session, relay, and plugin behavior. |
| root | tests/providers | Provider profile registration, aliases, and lazy discovery. |
| root | tests/plugins/model_providers | Bundled model-provider plugin profile behavior. |
| root | tests/agent/transports | Provider protocol transport requests, responses, tools, and usage normalization. |
| glob | tests/hermes_cli/test_provider_*.py | Provider catalog, setup, metadata, grouping, and parity contracts. |
| glob | tests/hermes_cli/test_*_provider.py | Provider runtime and integration behavior using provider-suffixed test modules. |
| file | tests/hermes_cli/test_api_key_providers.py | API-key provider setup and credential behavior. |
| file | tests/hermes_cli/test_provider_parity.py | Canonical provider parity across CLI and desktop provider surfaces. |
| file | tests/hermes_cli/test_provider_groups.py | Provider presentation group behavior without redefining membership. |
| file | tests/hermes_cli/test_inventory.py | Shared provider and model inventory payload. |
| glob | tests/hermes_cli/test_models*.py | Canonical and discovered model catalog behavior. |
| glob | tests/hermes_cli/test_model_*.py | Model selection and provider setup workflows. |
| glob | tests/hermes_cli/test_auth*.py | Provider authentication stores, flows, refresh, and logout behavior. |
| glob | tests/hermes_cli/test_runtime_provider*.py | Runtime provider endpoint, API mode, credential, and pool resolution. |
| file | tests/hermes_cli/test_azure_detect.py | Azure endpoint and API-mode detection. |
| file | tests/agent/test_auxiliary_client.py | Auxiliary client provider runtime integration. |
| glob | tests/agent/test_*credential*.py | Credential pooling, rotation, attribution, and persistence behavior. |
| glob | tests/agent/test_secret_scope*.py | Profile and workstream secret scoping. |
| glob | tests/agent/test_*transport*.py | Runtime transport selection outside the transport test root. |
| file | apps/desktop/e2e/onboarding.spec.ts | Desktop first-run onboarding workflow. |
| file | apps/desktop/src/store/onboarding.test.ts | Desktop onboarding state transitions and persistence. |
| file | apps/desktop/src/components/onboarding/index.test.tsx | Desktop onboarding component behavior. |
| file | apps/desktop/src/app/settings/providers-settings.test.tsx | Desktop provider settings membership and interaction behavior. |
| glob | apps/desktop/src/app/messaging/*.test.tsx | Desktop messaging platform configuration and presentation behavior. |
