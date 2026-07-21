# Verification Notes

**Status:** Final planning verification notes  
**Branch:** `planning/channels-providers-extraction-latest`

## Corrections applied

1. `03-worktree-and-upstream-sync-strategy.md` now describes the planning branch as a **review baseline**, not an approved baseline. Approval remains a user gate before any implementation worktree is created.
2. The provider inventory must account for the direct `openai` runtime/model-catalog identifier in addition to the user-facing/auth registry identifiers `openai-api` and `openai-codex`.

## OpenAI identifier classification

The inspected source has multiple OpenAI-related identities serving different layers:

- `openai-api` — API-key provider configuration and user-facing provider identity;
- `openai-codex` — OAuth/Codex provider identity;
- `openai` — native runtime/model-catalog identifier present in the model catalog;
- OpenAI-compatible providers — separate providers that may use the chat-completions or Responses transport without becoming the OpenAI provider.

Therefore, Phase 1 must generate and compare these distinct sets rather than normalize them prematurely:

```text
canonical provider descriptors
provider profile names and aliases
auth registry IDs and aliases
model-catalog provider keys
runtime-resolved provider IDs
UI account/key provider IDs
```

The generated inventory must show whether an identifier is a public provider descriptor, an alias, a runtime-only key, or a transport family. None may be silently discarded merely because another OpenAI-related identifier exists.

## Verification result

The branch comparison against `main` must remain documentation-only. No extraction, source movement, runtime change, dependency update, deletion, or pull request is part of this planning phase.