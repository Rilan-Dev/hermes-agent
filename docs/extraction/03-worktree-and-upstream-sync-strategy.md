# Isolated Worktree and Upstream Sync Strategy

**Status:** Review draft  
**Planning branch:** `planning/channels-providers-extraction-latest`

## 1. Branch roles

| Branch | Purpose | Allowed changes |
|---|---|---|
| `main` | Fork mirror/integration branch | Upstream changes and separately reviewed fork changes only |
| `planning/channels-providers-extraction-latest` | Review baseline for design and inventory | Documents and review corrections only |
| `worktree/channels-providers-extraction-latest` | Later implementation branch | Manifest, characterization tests, projected package, compatibility adapters |
| optional phase branches | Narrow implementation increments | One reviewed phase at a time |

The implementation worktree must be created from the planning branch after document approval, not directly from an unreviewed or dirty local `main` checkout.

## 2. Worktree creation after document approval

Suggested commands from a clean primary clone:

```bash
git fetch origin
git worktree add \
  .worktrees/channels-providers-extraction \
  -b worktree/channels-providers-extraction-latest \
  origin/planning/channels-providers-extraction-latest
```

Verification before editing:

```bash
cd .worktrees/channels-providers-extraction
git branch --show-current
git status --short
git rev-parse HEAD
```

Expected branch:

```text
worktree/channels-providers-extraction-latest
```

The worktree must be clean before every phase begins. Unrelated local files or modifications must not be included in extraction commits.

## 3. Upstream/fork synchronization model

Use two remotes where possible:

```text
origin    -> Rilan-Dev/hermes-agent
upstream  -> NousResearch/hermes-agent
```

Refresh fork `main` independently of extraction work:

```bash
git fetch upstream main
git switch main
git merge --ff-only upstream/main
git push origin main
```

If fork `main` intentionally contains commits not present upstream, replace `--ff-only` with the repository's reviewed merge/rebase policy. Do not force-push shared branches.

After `origin/main` is refreshed, update the implementation branch inside its worktree:

```bash
git fetch origin
git switch worktree/channels-providers-extraction-latest
git merge origin/main
```

A merge is preferred during active extraction because it records the exact integration point and avoids rewriting review history. A rebase may be used only before a branch is shared and only when no review references depend on its commit IDs.

## 4. Two-layer synchronization model

The extracted package should separate upstream-synchronized code from locally designed public APIs.

```text
extracted/hermes-connect-kit/
├── src/hermes_connect/              # Locally owned public contracts/facades
│   ├── channels/
│   ├── providers/
│   ├── onboarding/
│   └── compatibility/
└── src/hermes_connect/vendor/       # Mechanically synchronized source layer
```

Rules:

1. `vendor/` files carry origin path, source SHA, and content hash in the generated manifest.
2. A sync may replace an unmodified vendor file automatically.
3. A vendor file with local modifications is not overwritten automatically; the sync produces a conflict report.
4. Public facade files are never generated from upstream and are never overwritten by the sync.
5. Consumer projects import only public facade modules.
6. Compatibility patches are recorded separately from the copied upstream snapshot.

## 5. Extraction manifest

The manifest should be committed and deterministic. It needs:

- source repository and source SHA;
- recursive inclusion roots;
- explicit source files outside those roots;
- destination mapping;
- classification (`core`, `host-port`, `optional-ui`, `test`);
- expected hashes;
- known compatibility patches;
- allowed host-provided modules;
- excluded roots;
- test selection rules.

Illustrative shape:

```yaml
version: 1
source:
  repository: Rilan-Dev/hermes-agent
  ref: main
  sha: 18bb6f1aeaa334badee6271fc3337f39ca6bfcfb
include_roots:
  - source: plugins/platforms
    destination: plugins/platforms
    class: core
  - source: plugins/model-providers
    destination: plugins/model-providers
    class: core
  - source: providers
    destination: src/hermes_connect/vendor/providers
    class: core
files:
  - source: gateway/platform_registry.py
    destination: src/hermes_connect/vendor/gateway/platform_registry.py
    class: core
host_ports:
  - run_agent.AIAgent
  - hermes_state.SessionDB
exclude_roots:
  - skills
  - optional-skills
```

The actual manifest is created only after the generated inventory is reviewed.

## 6. Sync algorithm

For a requested update from old source SHA `A` to new source SHA `B`:

1. Verify the implementation worktree is clean.
2. Resolve every manifest root and explicit file at `B`.
3. Discover platform manifests, provider manifests, registry entries, and canonical provider membership at `B`.
4. Compare discovered membership with `A`.
5. Detect path additions, deletions, renames, and modifications.
6. Compare current vendor-file hashes with the hashes recorded for `A`.
7. Automatically update only vendor files that still match their recorded `A` hash.
8. Emit conflicts for locally changed vendor files.
9. Emit unresolved imports and newly required dependencies.
10. Update provenance only after tests pass.
11. Run characterization, parity, contract, and clean-consumer tests.
12. Commit the source refresh separately from any compatibility/refactor changes.

Recommended commit separation:

```text
chore(sync): refresh scoped Hermes sources from <A> to <B>
fix(compat): adapt channel/provider package to upstream <B>
test(sync): cover new platform/provider behavior from <B>
```

## 7. Drift report

Every sync must report:

- previous and new source SHAs;
- included file counts by classification;
- new/removed/renamed platform and provider plugins;
- canonical provider membership changes;
- auth-type and required-env changes;
- API-mode/transport changes;
- channel setup/config-schema changes;
- locally patched vendor files;
- unresolved imports;
- test additions/removals/failures.

No automatic sync commit should be created when unresolved imports or modified-vendor conflicts remain.

## 8. Non-scoped file removal policy

Removal applies only to the extracted application, never to fork `main`.

A projected file may be removed only when all are true:

1. no in-scope file imports it;
2. no plugin manifest or runtime discovery path loads it;
3. no selected test requires it;
4. no public contract exposes its behavior;
5. clean-consumer tests pass without it;
6. the removal is recorded in the manifest/review report.

Directory proximity is not sufficient evidence for inclusion, and apparent lack of a direct import is not sufficient evidence for exclusion because registries load modules dynamically.

## 9. Handling dynamic plugins

Platform and provider plugin roots are directory-driven. The sync must not use a fixed list such as `telegram`, `discord`, or `openrouter` as the inclusion mechanism.

Instead:

- enumerate child directories containing valid manifests;
- validate manifest kind;
- inspect/register each plugin in an isolated process;
- compare the result with the corresponding runtime registry;
- include all files below every accepted plugin directory;
- report a plugin that fails to import rather than silently dropping it.

User-installed plugins under `HERMES_HOME` are runtime extensions, not copied source. The extracted application must retain compatible external plugin search paths through configuration.

## 10. Conflict policy

When upstream changes touch a locally patched synchronized file:

- do not overwrite it;
- show upstream base, local version, and new upstream version;
- first decide whether the local patch belongs in the public facade/compatibility layer;
- move reusable local behavior out of vendor code whenever possible;
- keep the smallest unavoidable vendor patch as a named patch with a test;
- record whether the patch was reapplied, changed, or removed.

The long-term target is zero direct modifications in synchronized vendor files.

## 11. CI gates for the implementation branch

The implementation branch should eventually require:

1. manifest validation;
2. generated inventory matches committed inventory;
3. no undeclared imports outside package/host-port allowlist;
4. provider catalog parity;
5. platform/provider plugin discovery parity;
6. selected upstream tests;
7. extracted contract tests;
8. clean package build/install;
9. clean temporary consumer integration;
10. no modifications to files outside the approved extraction paths.

## 12. Optional standalone repository

After the extracted directory is stable:

```bash
git subtree split \
  --prefix=extracted/hermes-connect-kit \
  -b release/hermes-connect-kit
```

That branch can seed a standalone repository without making the standalone repository the primary upstream-sync mechanism. The fork remains the place where source refreshes are generated and verified.

## 13. Rollback

Every implementation phase must be independently revertible. Do not combine source projection, facade refactoring, dependency removal, and upstream refresh in the same commit.

If a phase fails, remove its worktree branch or revert its phase commits; `main` and the planning branch remain unchanged.