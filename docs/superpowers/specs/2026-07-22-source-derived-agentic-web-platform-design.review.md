# Source-Derived Agentic Web Platform Design Self-Review

**Reviewed specification:** `docs/superpowers/specs/2026-07-22-source-derived-agentic-web-platform-design.md`  
**Review date:** 2026-07-22  
**Result:** Ready for human review

## Placeholder scan

- No `TBD`, `TODO`, placeholder, or incomplete design section remains.
- Baseline values are explicitly marked as awaiting Checkpoint A refresh rather than treated as permanent product constants.

## Internal consistency

- Hermes remains the owner of provider, channel, model, agent, tool, workflow, onboarding, command, chat, and runtime behavior.
- Exact projected source remains unmodified.
- Generated descriptors may normalize representation shape but may not normalize semantic identities.
- Browser code is limited to generic rendering, stable adapters, workspace controls, and browser-safe wrappers.
- CLI/TUI behavior is not falsely described as byte-identical browser code; underlying handlers remain source-owned while presentation is mechanically generated.
- Existing platform backend contracts remain the only product-facing Python boundary.

## Scope review

The complete platform is too large for one implementation cycle and is explicitly decomposed into reviewed vertical slices.

The first cycle is limited to:

- deterministic capability catalogue;
- provenance and identity graph;
- CLI/TUI projection classification;
- existing UI reuse inventory;
- read-only descriptor APIs;
- independent browser shell and generic renderer foundation.

It excludes provider login, channel connection, arbitrary command execution, agent mutation, tool execution, workflow editing, and full chat sending.

## Ambiguity review

The phrase “do not generate your own code” is resolved as follows:

- no manually recreated domain-specific Hermes behavior;
- no manually maintained provider, channel, model, tool, workflow, command, or capability lists;
- generic extraction, provenance, stable adapters, and browser rendering code is allowed only where required to expose source-owned behavior safely;
- every exposed capability must retain source provenance;
- unsupported or host-bound capabilities are explicitly classified rather than silently omitted or falsely converted.

## Branch integrity

Compared with preserved fork `main` commit `d5a67ad32522273115d887560ca1c08a02bc7873`, the planning branch initially added only the design specification. This review document is documentation-only and does not authorize implementation.

No production source, dependency metadata, test source, extraction evidence, generated projection, or GitHub Actions workflow is changed by the design review.

## Gate

Human review of the written specification is required before invoking `superpowers:writing-plans` and creating the first implementation plan.
