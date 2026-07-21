# Phase 1 Approval Checklist

Approve Phase 2 only after confirming:

- [ ] The generated inventory includes every intended channel, onboarding, provider, transport, auth, and host-integration path.
- [ ] Every entry is classified correctly as core, host port, optional UI, test, or excluded.
- [ ] Generated `__pycache__`, `.pyc`, and `.pyo` artifacts are absent from the inventory.
- [ ] Platform manifest identities match runtime plugin identities.
- [ ] Provider plugin identities and intentional multi-profile aliases are understood.
- [ ] OpenAI API, OpenAI Codex OAuth, native runtime, and OpenAI-compatible identities remain distinct.
- [ ] Host dependencies that need ports or adapters are identified.
- [ ] The new `hermes_cli/windows_ssh_runtime.py` dependency is classified before CLI integration code is copied.
- [ ] Desktop and web onboarding surfaces remain consumers of backend provider truth.
- [ ] The selected regression test matrix is sufficient for the first extraction slice.
- [ ] A local isolated worktree will be created before production source movement begins.

Approval of this checklist authorizes planning for Phase 2, not an automatic merge into `main`.
