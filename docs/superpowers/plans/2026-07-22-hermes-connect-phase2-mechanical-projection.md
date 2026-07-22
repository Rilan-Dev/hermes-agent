# Hermes Connect Phase 2 Mechanical Projection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deterministically project the approved Hermes channel, provider, onboarding, compatibility, reference, and selected upstream-test files into `extracted/hermes-connect-kit/` with exact provenance and no behavior refactor.

**Architecture:** Strengthen the Phase 1 manifest and inventory with subsystem and Git-object provenance, then generate all synchronized files from that inventory through a staging-and-swap projection engine. Projection is committed in three reviewable slices—shared/providers, channels, onboarding/reference/host ports—while the public `hermes_connect` service facade remains out of scope until Phase 3.

**Tech Stack:** Python 3.11, dataclasses, pathlib, subprocess/Git plumbing, PyYAML, pytest, Ruff, existing Hermes plugin/registry probes, GitHub Actions and `scripts/run_tests.sh`.

## Global Constraints

- Combined source baseline: `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`.
- Upstream source baseline: `NousResearch/hermes-agent@7de554277de632364c74fcf8641daa58a9a977d9`.
- Fork `main` baseline: `Rilan-Dev/hermes-agent@d5a67ad32522273115d887560ca1c08a02bc7873`.
- Never modify, reset, prune, or merge extraction work into fork `main`.
- Create a real local worktree before executing source projection.
- Generated ownership is limited to `vendor/`, `compatibility/`, `reference/`, `tests/upstream/`, and `projection-manifest.json` under `extracted/hermes-connect-kit/`.
- Projection must not rewrite imports or change projected source bytes in Phase 2.
- Platform and model-provider membership remains registry/plugin driven; do not add duplicate membership lists.
- OpenAI API-key, OpenAI Codex OAuth, native runtime, model-catalog, and OpenAI-compatible identities remain distinct.
- Every implementation task follows RED → GREEN → focused regression → commit.
- Every slice ends with a written self-review covering unexpected files, deletions, destination changes, host-port growth, and test gaps.

---

## Required Worktree Setup

Run before Task 1 in a development checkout:

```bash
git fetch origin
git worktree add \
  .worktrees/channels-providers-phase2-2026-07-22 \
  -b worktree/channels-providers-phase2-2026-07-22 \
  origin/planning/channels-providers-phase2-2026-07-22
cd .worktrees/channels-providers-phase2-2026-07-22
git status --short
git rev-parse HEAD
```

Expected:

```text
# git status --short prints nothing
# git rev-parse HEAD includes the planning docs and descends from
# 269eb7b30e0bc3666c377e0325263e7b5bcf49b4
```

Do not continue from a dirty worktree.

## File Structure Produced by This Plan

```text
scripts/extraction/
├── schema.py                   # Manifest and projection enums/dataclasses
├── manifest.py                 # Strict manifest-v2 parser
├── git_tree.py                 # Batched Git tree/blob provenance lookup
├── filesystem_inventory.py     # Source records with Git/content provenance
├── test_inventory.py           # Deterministic selected-test expansion
├── projection.py               # Plan, stage, verify, and apply engine
└── project_sources.py          # CLI for --write and --check

tests/extraction/
├── test_manifest.py
├── test_filesystem_inventory.py
├── test_test_inventory.py
├── test_projection_plan.py
├── test_projection_apply.py
├── test_project_sources_cli.py
└── snapshots/registry-snapshot.json

extracted/hermes-connect-kit/
├── README.md                   # Hand-written package boundary documentation
├── pyproject.toml              # Hand-written Phase 2 test package metadata
├── extraction-manifest.yaml    # Manifest v2 and subsystem ownership
├── projection-manifest.json    # Generated exact provenance
├── src/hermes_connect/__init__.py
├── vendor/                     # Generated core source
├── compatibility/              # Generated host-port source
├── reference/                  # Generated optional UI/reference source
└── tests/
    ├── conftest.py             # Projected import-path harness
    └── upstream/               # Generated unchanged selected upstream tests
```

---

### Task 1: Refresh Phase 1 Evidence on the Phase 2 Baseline

**Files:**
- Modify: `extracted/hermes-connect-kit/extraction-manifest.yaml`
- Modify: `tests/extraction/test_manifest.py`
- Regenerate: `tests/extraction/snapshots/registry-snapshot.json`
- Regenerate: `docs/extraction/generated/phase-1-inventory.yaml`
- Regenerate: `docs/extraction/generated/phase-1-inventory.md`
- Regenerate: `docs/extraction/generated/phase-1-test-matrix.md`
- Create: `docs/extraction/07-phase-2-upstream-impact-review.md`

**Interfaces:**
- Consumes: existing `load_manifest()`, registry probe, and inventory builder.
- Produces: a current, deterministic evidence set whose `source_sha` is `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`.

- [ ] **Step 1: Write the failing baseline assertion**

Add to `tests/extraction/test_manifest.py`:

```python
from pathlib import Path

from scripts.extraction.manifest import load_manifest


PHASE2_SOURCE_SHA = "269eb7b30e0bc3666c377e0325263e7b5bcf49b4"


def test_manifest_uses_phase2_combined_baseline() -> None:
    manifest = load_manifest(
        Path("extracted/hermes-connect-kit/extraction-manifest.yaml")
    )
    assert manifest.source_sha == PHASE2_SOURCE_SHA
```

- [ ] **Step 2: Run the focused test and verify RED**

```bash
uv run pytest tests/extraction/test_manifest.py::test_manifest_uses_phase2_combined_baseline -v
```

Expected: FAIL showing the older `18bb6f1...` SHA.

- [ ] **Step 3: Update only the source SHA**

Change:

```yaml
source_sha: 269eb7b30e0bc3666c377e0325263e7b5bcf49b4
```

Do not change classifications in this step.

- [ ] **Step 4: Capture the isolated registry snapshot**

```bash
rm -rf .tmp/hermes-phase2-home
mkdir -p tests/extraction/snapshots
HERMES_HOME="$PWD/.tmp/hermes-phase2-home" \
HERMES_ENABLE_PROJECT_PLUGINS=0 \
HERMES_SAFE_MODE=0 \
HERMES_PLUGINS_DEBUG=0 \
PYTHONHASHSEED=0 \
OPENROUTER_API_KEY= \
OPENAI_API_KEY= \
NOUS_API_KEY= \
uv run python -m scripts.extraction.registry_probe \
  > tests/extraction/snapshots/registry-snapshot.json
uv run python -m json.tool \
  tests/extraction/snapshots/registry-snapshot.json >/dev/null
```

Expected: exit 0 with valid JSON and no network calls.

- [ ] **Step 5: Regenerate deterministic inventory outputs twice**

```bash
uv run python -m scripts.extraction.build_inventory
cp docs/extraction/generated/phase-1-inventory.yaml /tmp/phase2-inventory.yaml
cp docs/extraction/generated/phase-1-inventory.md /tmp/phase2-inventory.md
cp docs/extraction/generated/phase-1-test-matrix.md /tmp/phase2-test-matrix.md
uv run python -m scripts.extraction.build_inventory
diff -u /tmp/phase2-inventory.yaml docs/extraction/generated/phase-1-inventory.yaml
diff -u /tmp/phase2-inventory.md docs/extraction/generated/phase-1-inventory.md
diff -u /tmp/phase2-test-matrix.md docs/extraction/generated/phase-1-test-matrix.md
```

Expected: all diffs empty.

- [ ] **Step 6: Verify the refreshed evidence gate**

```bash
uv run ruff check scripts/extraction tests/extraction
uv run pytest tests/extraction -q
scripts/run_tests.sh -j 4 \
  tests/providers \
  tests/gateway \
  tests/plugins/model_providers \
  tests/agent/transports \
  tests/hermes_cli/test_provider_parity.py \
  -q
```

Expected: all commands exit 0.

- [ ] **Step 7: Write the upstream impact review**

Create `docs/extraction/07-phase-2-upstream-impact-review.md` containing exact refreshed counts and sections for:

```markdown
# Phase 2 Upstream Impact Review

- Combined baseline: `269eb7...`
- Upstream baseline: `7de554...`
- Fork main: `d5a67a...`

## Added scoped files
## Removed scoped files
## Changed classifications
## New out-of-scope dependencies
## Registry identity changes
## Test-matrix changes
## Decision

Phase 2 projection may proceed only when unresolved internal imports are zero.
```

Replace each section with actual generated evidence; do not leave headings empty.

- [ ] **Step 8: Self-review and commit**

```bash
git diff --name-status
git diff --check
git grep -nE 'TBD|TODO|PLACEHOLDER' -- \
  docs/extraction/07-phase-2-upstream-impact-review.md \
  docs/extraction/generated \
  extracted/hermes-connect-kit/extraction-manifest.yaml
```

Expected: no placeholders; no production-source paths changed.

```bash
git add \
  extracted/hermes-connect-kit/extraction-manifest.yaml \
  tests/extraction/test_manifest.py \
  tests/extraction/snapshots/registry-snapshot.json \
  docs/extraction/generated \
  docs/extraction/07-phase-2-upstream-impact-review.md
git commit -m "chore(extraction): refresh Phase 2 source evidence"
```

---

### Task 2: Upgrade the Manifest to Version 2 with Subsystem Ownership

**Files:**
- Modify: `scripts/extraction/schema.py`
- Modify: `scripts/extraction/manifest.py`
- Modify: `extracted/hermes-connect-kit/extraction-manifest.yaml`
- Modify: `tests/extraction/test_manifest.py`

**Interfaces:**
- Produces: `Subsystem`, manifest lineage fields, and `subsystem` on `RootRule`, `FileRule`, and `TestRule`.
- Later tasks consume: `manifest.upstream_sha`, `manifest.fork_main_sha`, and each rule's `subsystem`.

- [ ] **Step 1: Write failing parser tests**

Add:

```python
from scripts.extraction.schema import Subsystem


def test_manifest_v2_records_lineage_and_subsystems(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.yaml"
    manifest_path.write_text(
        """
version: 2
source_repository: Rilan-Dev/hermes-agent
source_sha: 269eb7b30e0bc3666c377e0325263e7b5bcf49b4
upstream_repository: NousResearch/hermes-agent
upstream_sha: 7de554277de632364c74fcf8641daa58a9a977d9
fork_main_sha: d5a67ad32522273115d887560ca1c08a02bc7873
dynamic_roots:
  - path: providers
    subsystem: providers
    classification: core
    destination: vendor/providers
    reason: Provider profiles.
explicit_files: []
test_rules:
  - path: tests/providers
    kind: root
    subsystem: providers
    behavior: Provider registry behavior.
internal_module_roots: [providers]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    manifest = load_manifest(manifest_path)

    assert manifest.version == 2
    assert manifest.upstream_sha.startswith("7de554")
    assert manifest.fork_main_sha.startswith("d5a67a")
    assert manifest.dynamic_roots[0].subsystem is Subsystem.PROVIDERS
    assert manifest.test_rules[0].subsystem is Subsystem.PROVIDERS


def test_manifest_v2_rejects_missing_subsystem(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text(
        """
version: 2
source_repository: Rilan-Dev/hermes-agent
source_sha: 269eb7b30e0bc3666c377e0325263e7b5bcf49b4
upstream_repository: NousResearch/hermes-agent
upstream_sha: 7de554277de632364c74fcf8641daa58a9a977d9
fork_main_sha: d5a67ad32522273115d887560ca1c08a02bc7873
dynamic_roots:
  - path: providers
    classification: core
    destination: vendor/providers
    reason: Provider profiles.
explicit_files: []
test_rules: []
internal_module_roots: [providers]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ManifestError, match="subsystem"):
        load_manifest(path)
```

- [ ] **Step 2: Run tests and verify RED**

```bash
uv run pytest tests/extraction/test_manifest.py -q
```

Expected: import/attribute failures for `Subsystem` and manifest-v2 fields.

- [ ] **Step 3: Add the schema types**

Implement in `scripts/extraction/schema.py`:

```python
class Subsystem(str, Enum):
    SHARED = "shared"
    PROVIDERS = "providers"
    CHANNELS = "channels"
    ONBOARDING = "onboarding"


@dataclass(frozen=True)
class RootRule:
    path: str
    subsystem: Subsystem
    classification: Classification
    destination: str
    reason: str


@dataclass(frozen=True)
class FileRule:
    path: str
    subsystem: Subsystem
    classification: Classification
    destination: str
    reason: str


@dataclass(frozen=True)
class TestRule:
    path: str
    kind: str
    subsystem: Subsystem
    behavior: str


@dataclass(frozen=True)
class ExtractionManifest:
    version: int
    source_repository: str
    source_sha: str
    upstream_repository: str
    upstream_sha: str
    fork_main_sha: str
    dynamic_roots: tuple[RootRule, ...]
    explicit_files: tuple[FileRule, ...]
    test_rules: tuple[TestRule, ...]
    internal_module_roots: tuple[str, ...]
```

- [ ] **Step 4: Parse version 2 strictly**

Add `_subsystem()` beside `_classification()` and require version 2:

```python
def _subsystem(value: object, field: str) -> Subsystem:
    text = _required_text(value, field)
    try:
        return Subsystem(text)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in Subsystem)
        raise ManifestError(f"{field} must be one of: {allowed}") from exc
```

Apply it to all rule constructors. Parse and SHA-validate `upstream_sha` and `fork_main_sha` exactly like `source_sha`.

- [ ] **Step 5: Migrate the real manifest**

Set:

```yaml
version: 2
source_sha: 269eb7b30e0bc3666c377e0325263e7b5bcf49b4
upstream_repository: NousResearch/hermes-agent
upstream_sha: 7de554277de632364c74fcf8641daa58a9a977d9
fork_main_sha: d5a67ad32522273115d887560ca1c08a02bc7873
```

Assign exactly one `subsystem` to every dynamic root, explicit file, and test rule. Use `shared` only for cross-cutting configuration, plugin manager, constants, logging, and common command/runtime glue.

- [ ] **Step 6: Run focused and full extraction tests**

```bash
uv run pytest tests/extraction/test_manifest.py -q
uv run pytest tests/extraction -q
uv run ruff check scripts/extraction tests/extraction
```

Expected: all pass.

- [ ] **Step 7: Self-review and commit**

```bash
python - <<'PY'
from pathlib import Path
from scripts.extraction.manifest import load_manifest
m = load_manifest(Path("extracted/hermes-connect-kit/extraction-manifest.yaml"))
assert all(rule.subsystem for rule in m.dynamic_roots)
assert all(rule.subsystem for rule in m.explicit_files)
assert all(rule.subsystem for rule in m.test_rules)
print({s.value for s in {r.subsystem for r in (*m.dynamic_roots, *m.explicit_files, *m.test_rules)}})
PY
```

Expected: all four subsystem names are present.

```bash
git add scripts/extraction/schema.py scripts/extraction/manifest.py \
  extracted/hermes-connect-kit/extraction-manifest.yaml \
  tests/extraction/test_manifest.py
git commit -m "feat(extraction): classify manifest rules by subsystem"
```

---

### Task 3: Record Git Provenance and Expand Selected Upstream Tests

**Files:**
- Create: `scripts/extraction/git_tree.py`
- Modify: `scripts/extraction/filesystem_inventory.py`
- Create: `scripts/extraction/test_inventory.py`
- Modify: `scripts/extraction/build_inventory.py`
- Modify: `tests/extraction/test_filesystem_inventory.py`
- Create: `tests/extraction/test_test_inventory.py`

**Interfaces:**
- Produces `GitTreeEntry`, enriched `FileRecord`, and `TestFileRecord`.
- `inventory_files(repo_root, manifest)` remains the public source inventory entry point.
- New: `inventory_test_files(repo_root, manifest) -> tuple[TestFileRecord, ...]`.

- [ ] **Step 1: Write RED provenance tests**

Create fixture assertions that a regular executable file and symlink retain Git identity:

```python
def test_inventory_records_git_blob_mode_and_subsystem(git_repo: Path) -> None:
    source = git_repo / "providers" / "profile.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    source.chmod(0o755)
    commit_all(git_repo)

    manifest = make_manifest(
        source_sha=git_head(git_repo),
        dynamic_roots=(root_rule("providers", "providers", "vendor/providers"),),
    )
    record = inventory_files(git_repo, manifest)[0]

    assert record.subsystem == "providers"
    assert record.git_mode == "100755"
    assert len(record.git_blob_sha) == 40
    assert record.kind == "file"
    assert record.link_target is None
```

Add a symlink test on non-Windows platforms with `pytest.mark.skipif(os.name == "nt", ...)` and assert `git_mode == "120000"`, `kind == "symlink"`, and exact `link_target`.

- [ ] **Step 2: Write RED selected-test expansion tests**

```python
def test_inventory_test_files_expands_root_file_and_glob(git_repo: Path) -> None:
    write(git_repo, "tests/providers/test_a.py", "def test_a(): pass\n")
    write(git_repo, "tests/gateway/test_b.py", "def test_b(): pass\n")
    write(git_repo, "tests/gateway/helper.txt", "ignored\n")
    commit_all(git_repo)

    manifest = make_manifest(
        source_sha=git_head(git_repo),
        test_rules=(
            test_rule("tests/providers", "root", "providers"),
            test_rule("tests/gateway/test_b.py", "file", "channels"),
            test_rule("tests/**/test_*.py", "glob", "shared"),
        ),
    )

    records = inventory_test_files(git_repo, manifest)
    assert [record.source for record in records] == [
        "tests/gateway/test_b.py",
        "tests/providers/test_a.py",
    ]
    assert all(record.destination.startswith("tests/upstream/") for record in records)
```

- [ ] **Step 3: Run tests and verify RED**

```bash
uv run pytest \
  tests/extraction/test_filesystem_inventory.py \
  tests/extraction/test_test_inventory.py -q
```

Expected: missing module/field failures.

- [ ] **Step 4: Implement batched Git tree lookup**

Create `scripts/extraction/git_tree.py` with:

```python
@dataclass(frozen=True)
class GitTreeEntry:
    path: str
    mode: str
    object_type: str
    object_sha: str


class GitTreeError(RuntimeError):
    pass


def load_tree_entries(
    repo_root: Path,
    source_sha: str,
    scoped_paths: Sequence[str],
) -> dict[str, GitTreeEntry]:
    command = ["git", "ls-tree", "-r", "-z", source_sha, "--", *scoped_paths]
    result = subprocess.run(
        command,
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    entries: dict[str, GitTreeEntry] = {}
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        metadata, path_bytes = raw.split(b"\t", 1)
        mode, object_type, object_sha = metadata.decode("ascii").split(" ")
        path = path_bytes.decode("utf-8", "surrogateescape")
        entries[path] = GitTreeEntry(path, mode, object_type, object_sha)
    return entries
```

Wrap subprocess and parse failures in `GitTreeError` with the source SHA and affected paths.

- [ ] **Step 5: Enrich `FileRecord`**

Add fields:

```python
subsystem: str
git_mode: str
git_blob_sha: str
kind: str
link_target: str | None
```

Preload Git tree entries once using all dynamic-root and explicit-file paths. For mode `120000`, hash the link target text bytes and do not follow the symlink. For regular files, retain the existing streaming SHA-256 behavior.

- [ ] **Step 6: Implement selected-test inventory**

`TestFileRecord` must include the same provenance fields plus `behavior`. Resolve rules deterministically:

- `file`: one exact file;
- `root`: recursive `test_*.py` and `*_test.py` files;
- `glob`: repository-relative `Path.glob()` matches restricted to files;
- duplicates collapse only when records are identical;
- conflicting subsystem or behavior ownership raises `InventoryError`.

- [ ] **Step 7: Add test records to generated evidence**

In `build_inventory()` add:

```python
test_files = inventory_test_files(repository, manifest)
```

Return them under `selected_test_files`, preserving `test_rules` separately.

- [ ] **Step 8: Run verification and commit**

```bash
uv run pytest \
  tests/extraction/test_filesystem_inventory.py \
  tests/extraction/test_test_inventory.py \
  tests/extraction/test_build_inventory.py -q
uv run pytest tests/extraction -q
uv run ruff check scripts/extraction tests/extraction
```

Expected: all pass.

```bash
git add scripts/extraction/git_tree.py \
  scripts/extraction/filesystem_inventory.py \
  scripts/extraction/test_inventory.py \
  scripts/extraction/build_inventory.py \
  tests/extraction/test_filesystem_inventory.py \
  tests/extraction/test_test_inventory.py
git commit -m "feat(extraction): record Git provenance and selected tests"
```

---

### Task 4: Build the Deterministic Projection Plan

**Files:**
- Create: `scripts/extraction/projection.py`
- Create: `tests/extraction/test_projection_plan.py`

**Interfaces:**
- `ProjectionRecord` is the JSON-serializable projection unit.
- `build_projection_records(inventory, subsystems) -> tuple[ProjectionRecord, ...]`.
- `merge_projection_records(existing, refreshed, selected_subsystems) -> tuple[ProjectionRecord, ...]`.
- No filesystem writes occur in this task.

- [ ] **Step 1: Write RED planning tests**

```python
def test_build_projection_records_filters_subsystems_and_sorts() -> None:
    inventory = inventory_fixture(
        files=[
            file_row("providers/a.py", "vendor/providers/a.py", "providers"),
            file_row("gateway/a.py", "vendor/gateway/a.py", "channels"),
        ],
        tests=[
            test_row("tests/providers/test_a.py", "providers"),
        ],
    )

    records = build_projection_records(inventory, {"providers"})

    assert [record.destination for record in records] == [
        "tests/upstream/tests/providers/test_a.py",
        "vendor/providers/a.py",
    ]


def test_projection_plan_rejects_destination_collision() -> None:
    inventory = inventory_fixture(
        files=[
            file_row("a.py", "vendor/shared.py", "shared"),
            file_row("b.py", "vendor/shared.py", "providers"),
        ]
    )
    with pytest.raises(ProjectionError, match="destination collision"):
        build_projection_records(inventory, {"shared", "providers"})
```

- [ ] **Step 2: Run and verify RED**

```bash
uv run pytest tests/extraction/test_projection_plan.py -q
```

Expected: module not found.

- [ ] **Step 3: Implement immutable projection records**

```python
GENERATED_ROOTS = (
    "vendor",
    "compatibility",
    "reference",
    "tests/upstream",
)


@dataclass(frozen=True)
class ProjectionRecord:
    source: str
    destination: str
    subsystem: str
    classification: str
    git_mode: str
    git_blob_sha: str
    sha256: str
    size_bytes: int
    kind: str
    link_target: str | None
    behavior: str | None = None
```

Validate every destination is repository-relative and begins with one generated root. Sort by destination, then source.

- [ ] **Step 4: Implement cumulative slice merging**

`merge_projection_records()` must remove existing records owned by selected subsystems, add refreshed selected records, reject collisions, and leave unselected records untouched. Reject an existing record whose subsystem is unknown.

- [ ] **Step 5: Serialize deterministically**

Add:

```python
def projection_manifest_data(
    *,
    source_repository: str,
    source_sha: str,
    upstream_repository: str,
    upstream_sha: str,
    fork_main_sha: str,
    records: Sequence[ProjectionRecord],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "source_repository": source_repository,
        "source_sha": source_sha,
        "upstream_repository": upstream_repository,
        "upstream_sha": upstream_sha,
        "fork_main_sha": fork_main_sha,
        "records": [asdict(record) for record in records],
    }
```

No timestamp is allowed.

- [ ] **Step 6: Verify and commit**

```bash
uv run pytest tests/extraction/test_projection_plan.py -q
uv run ruff check scripts/extraction/projection.py tests/extraction/test_projection_plan.py
```

Expected: all pass.

```bash
git add scripts/extraction/projection.py tests/extraction/test_projection_plan.py
git commit -m "feat(extraction): build deterministic projection plans"
```

---

### Task 5: Implement Staging, Atomic Apply, and Drift Checking

**Files:**
- Modify: `scripts/extraction/projection.py`
- Create: `scripts/extraction/project_sources.py`
- Create: `tests/extraction/test_projection_apply.py`
- Create: `tests/extraction/test_project_sources_cli.py`

**Interfaces:**
- `stage_projection(repo_root, kit_root, manifest_data, records) -> Path`.
- `verify_staged_projection(staging_root, records) -> None`.
- `apply_staged_projection(staging_root, kit_root) -> None`.
- `check_projection(kit_root, manifest_data) -> None`.
- CLI supports `--subsystem`, `--write`, and `--check`.

- [ ] **Step 1: Write RED no-partial-write tests**

```python
def test_failed_stage_leaves_existing_projection_unchanged(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    kit = repo / "extracted/hermes-connect-kit"
    existing = kit / "vendor/providers/existing.py"
    existing.parent.mkdir(parents=True)
    existing.write_text("old\n", encoding="utf-8")

    records = (record_for_missing_source(),)

    with pytest.raises(ProjectionError):
        stage_projection(repo, kit, lineage(), records)

    assert existing.read_text(encoding="utf-8") == "old\n"
```

Add tests for regular executable mode, symlink target, extra generated file detection, changed hash detection, and preservation of hand-written `README.md`.

- [ ] **Step 2: Run and verify RED**

```bash
uv run pytest \
  tests/extraction/test_projection_apply.py \
  tests/extraction/test_project_sources_cli.py -q
```

Expected: missing functions/CLI failures.

- [ ] **Step 3: Stage generated content**

Use `tempfile.mkdtemp(prefix="hermes-connect-projection-", dir=kit_root.parent)`. For each regular file, copy bytes from the verified repository path and apply executable bits derived from `git_mode`. For a symlink, call `os.symlink(record.link_target, destination)`.

Write `projection-manifest.json` with:

```python
json.dumps(data, indent=2, sort_keys=True) + "\n"
```

- [ ] **Step 4: Verify staged content before apply**

Walk only generated roots. Compare exact destination set, kind, link target, mode, size, and SHA-256. Report all differences in one `ProjectionError` message sorted by destination.

- [ ] **Step 5: Apply generated roots without touching hand-written paths**

For each generated root:

1. move the current root to `<name>.projection-backup`;
2. move the staged root into place;
3. after all roots succeed, delete backups;
4. on failure, restore all moved backups and raise `ProjectionError`.

Replace `projection-manifest.json` only after generated roots succeed.

- [ ] **Step 6: Implement `--check`**

`check_projection()` loads the committed projection manifest and reports:

- missing files;
- extra files;
- hash changes;
- mode changes;
- symlink changes;
- lineage mismatch with the current extraction manifest.

- [ ] **Step 7: Implement the CLI**

```text
uv run python -m scripts.extraction.project_sources \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --kit-root extracted/hermes-connect-kit \
  --subsystem shared \
  --subsystem providers \
  --write
```

Rules:

- exactly one of `--write` or `--check` is required;
- `--subsystem` may repeat;
- omitted subsystems with `--write` preserve existing projection records;
- omitted subsystems with `--check` check every committed record;
- unknown subsystem exits 2 through argparse;
- failures exit 1 with no traceback unless `--debug` is supplied.

- [ ] **Step 8: Verify and commit**

```bash
uv run pytest \
  tests/extraction/test_projection_plan.py \
  tests/extraction/test_projection_apply.py \
  tests/extraction/test_project_sources_cli.py -q
uv run ruff check scripts/extraction tests/extraction
```

Expected: all pass.

```bash
git add scripts/extraction/projection.py \
  scripts/extraction/project_sources.py \
  tests/extraction/test_projection_apply.py \
  tests/extraction/test_project_sources_cli.py
git commit -m "feat(extraction): stage and verify projected source"
```

---

### Task 6: Add the Hand-Written Package and Test Harness

**Files:**
- Create: `extracted/hermes-connect-kit/README.md`
- Create: `extracted/hermes-connect-kit/pyproject.toml`
- Create: `extracted/hermes-connect-kit/src/hermes_connect/__init__.py`
- Create: `extracted/hermes-connect-kit/tests/conftest.py`
- Create: `extracted/hermes-connect-kit/tests/test_package_boundary.py`

**Interfaces:**
- Produces an installable placeholder package and a test harness for unchanged projected tests.
- Does not expose vendor modules as stable API.

- [ ] **Step 1: Write RED package-boundary tests**

```python
def test_public_package_does_not_reexport_vendor_modules() -> None:
    import hermes_connect

    assert hermes_connect.__all__ == []
    assert not hasattr(hermes_connect, "gateway")
    assert not hasattr(hermes_connect, "providers")


def test_generated_roots_are_documented() -> None:
    readme = Path("extracted/hermes-connect-kit/README.md").read_text(
        encoding="utf-8"
    )
    for name in ("vendor/", "compatibility/", "reference/", "tests/upstream/"):
        assert name in readme
```

- [ ] **Step 2: Run and verify RED**

```bash
uv run pytest extracted/hermes-connect-kit/tests/test_package_boundary.py -q
```

Expected: package/files missing.

- [ ] **Step 3: Create minimal package metadata**

`pyproject.toml`:

```toml
[build-system]
requires = ["hatchling>=1.27,<2"]
build-backend = "hatchling.build"

[project]
name = "hermes-connect-kit"
version = "0.0.0"
requires-python = ">=3.11"
description = "Mechanically synchronized Hermes channel, provider, and onboarding source"

[tool.hatch.build.targets.wheel]
packages = ["src/hermes_connect"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

`src/hermes_connect/__init__.py`:

```python
"""Stable public facade placeholder; Phase 3 defines public services."""

__all__: list[str] = []
```

- [ ] **Step 4: Add the projected-test import harness**

`tests/conftest.py` prepends these absolute directories in order:

1. `compatibility`
2. `vendor`
3. repository root only when `HERMES_CONNECT_ALLOW_SOURCE_FALLBACK=1`

The default must not silently import unprojected source from repository root.

- [ ] **Step 5: Document the boundary**

README must state:

- generated vs hand-written paths;
- no stable vendor API;
- source/upstream/fork lineage locations;
- `project_sources --write` and `--check` commands;
- Phase 3 owns public services and dependency inversion.

- [ ] **Step 6: Verify and commit**

```bash
uv run pytest extracted/hermes-connect-kit/tests/test_package_boundary.py -q
uv run ruff check extracted/hermes-connect-kit/src extracted/hermes-connect-kit/tests
```

Expected: all pass.

```bash
git add extracted/hermes-connect-kit/README.md \
  extracted/hermes-connect-kit/pyproject.toml \
  extracted/hermes-connect-kit/src \
  extracted/hermes-connect-kit/tests/conftest.py \
  extracted/hermes-connect-kit/tests/test_package_boundary.py
git commit -m "feat(extraction): add mechanical projection package shell"
```

---

### Task 7: Project the Shared and Provider Slice

**Files:**
- Generate: `extracted/hermes-connect-kit/vendor/**`
- Generate: `extracted/hermes-connect-kit/compatibility/**` for selected shared/provider rules
- Generate: `extracted/hermes-connect-kit/reference/**` for selected shared/provider rules
- Generate: `extracted/hermes-connect-kit/tests/upstream/**` for selected shared/provider tests
- Generate: `extracted/hermes-connect-kit/projection-manifest.json`
- Create: `docs/extraction/08-phase-2-provider-slice-review.md`

**Interfaces:**
- Consumes Tasks 1–6.
- Produces the first committed projection slice.

- [ ] **Step 1: Verify the plan before writing**

```bash
uv run python -m scripts.extraction.project_sources \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --kit-root extracted/hermes-connect-kit \
  --subsystem shared \
  --subsystem providers \
  --dry-run > /tmp/provider-projection.txt
cat /tmp/provider-projection.txt
```

Expected: only `shared` and `providers` records, no destination collision, and no source outside the refreshed inventory.

- [ ] **Step 2: Write the slice**

```bash
uv run python -m scripts.extraction.project_sources \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --kit-root extracted/hermes-connect-kit \
  --subsystem shared \
  --subsystem providers \
  --write
uv run python -m scripts.extraction.project_sources \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --kit-root extracted/hermes-connect-kit \
  --check
```

Expected: both commands exit 0.

- [ ] **Step 3: Run provider characterization**

```bash
uv run pytest tests/extraction -q
scripts/run_tests.sh -j 4 \
  tests/providers \
  tests/plugins/model_providers \
  tests/agent/transports \
  tests/hermes_cli/test_provider_parity.py \
  -q
```

Expected: all pass.

Run projected tests without source fallback where they are import-complete:

```bash
cd extracted/hermes-connect-kit
uv run pytest tests/upstream/tests/providers tests/upstream/tests/plugins/model_providers -q
cd ../..
```

Document exact skipped tests and missing host imports; do not hide them with broad `--ignore` rules.

- [ ] **Step 4: Write slice self-review**

`08-phase-2-provider-slice-review.md` must include exact counts for:

- source records;
- selected upstream tests;
- `vendor`, `compatibility`, and `reference` destinations;
- provider/profile/catalog/auth identity totals;
- source-fallback-free projected tests passing;
- projected tests requiring declared host ports;
- added/removed destinations compared with the dry run.

- [ ] **Step 5: Diff guard and commit**

```bash
UNEXPECTED="$(git diff --name-only | grep -Ev '^(docs/extraction/|docs/superpowers/|scripts/extraction/|tests/extraction/|extracted/hermes-connect-kit/)' || true)"
test -z "$UNEXPECTED" || { printf '%s\n' "$UNEXPECTED"; exit 1; }
git diff --check
```

```bash
git add extracted/hermes-connect-kit docs/extraction/08-phase-2-provider-slice-review.md
git commit -m "feat(extraction): project shared and provider source"
```

---

### Task 8: Project the Channel Slice

**Files:**
- Generate/update: `extracted/hermes-connect-kit/vendor/**`
- Generate/update: `extracted/hermes-connect-kit/compatibility/**`
- Generate/update: `extracted/hermes-connect-kit/tests/upstream/**`
- Update: `extracted/hermes-connect-kit/projection-manifest.json`
- Create: `docs/extraction/09-phase-2-channel-slice-review.md`

**Interfaces:**
- Adds `channels` records while preserving existing `shared` and `providers` records byte-for-byte.

- [ ] **Step 1: Add a cumulative-preservation regression test**

```python
def test_channel_slice_preserves_existing_provider_records(tmp_path: Path) -> None:
    existing = (projection_record("providers/a.py", "providers"),)
    channels = (projection_record("gateway/a.py", "channels"),)

    combined = merge_projection_records(existing, channels, {"channels"})

    assert {record.subsystem for record in combined} == {"providers", "channels"}
    assert next(r for r in combined if r.subsystem == "providers") == existing[0]
```

Run RED by temporarily changing the implementation if necessary; the test must prove preservation, not merely pass vacuously.

- [ ] **Step 2: Write and check the channel slice**

```bash
uv run python -m scripts.extraction.project_sources \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --kit-root extracted/hermes-connect-kit \
  --subsystem channels \
  --write
uv run python -m scripts.extraction.project_sources \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --kit-root extracted/hermes-connect-kit \
  --check
```

Expected: provider/shared records remain unchanged and channel records are added.

- [ ] **Step 3: Run channel characterization**

```bash
uv run pytest tests/extraction -q
scripts/run_tests.sh -j 4 tests/gateway -q
```

Run import-complete projected gateway/platform tests without repository fallback and record exact gaps.

- [ ] **Step 4: Write channel self-review**

Include:

- platform manifest count and runtime plugin parity;
- gateway/platform/relay projected counts;
- authorization, pairing, session, delivery, streaming, and slash-command test coverage;
- host imports still required by `gateway/run.py` and status/process management;
- any new upstream channel file not yet classified.

- [ ] **Step 5: Diff guard and commit**

```bash
git diff --check
uv run ruff check scripts/extraction tests/extraction extracted/hermes-connect-kit/src
git add extracted/hermes-connect-kit \
  tests/extraction/test_projection_plan.py \
  docs/extraction/09-phase-2-channel-slice-review.md
git commit -m "feat(extraction): project channel source"
```

---

### Task 9: Project Onboarding, Host Ports, Reference Surfaces, and Finalize Phase 2

**Files:**
- Generate/update: all generated projection roots
- Update: `extracted/hermes-connect-kit/projection-manifest.json`
- Create: `docs/extraction/10-phase-2-final-review.md`
- Create: `docs/extraction/PHASE_2_REVIEW_GATE.md`

**Interfaces:**
- Completes all four manifest subsystems.
- Produces the Phase 2 review gate; does not begin Phase 3.

- [ ] **Step 1: Project onboarding records**

```bash
uv run python -m scripts.extraction.project_sources \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --kit-root extracted/hermes-connect-kit \
  --subsystem onboarding \
  --write
uv run python -m scripts.extraction.project_sources \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --kit-root extracted/hermes-connect-kit \
  --check
```

- [ ] **Step 2: Prove complete manifest coverage**

Add a test that compares all inventory source/test records with all committed projection records:

```python
def test_complete_projection_covers_every_manifest_record() -> None:
    inventory = load_yaml(INVENTORY_PATH)
    projection = load_json(PROJECTION_MANIFEST_PATH)

    expected = {
        row["destination"] for row in inventory["files"]
    } | {
        row["destination"] for row in inventory["selected_test_files"]
    }
    actual = {row["destination"] for row in projection["records"]}

    assert actual == expected
```

- [ ] **Step 3: Run the full Phase 2 verification chain**

```bash
uv run python -m scripts.extraction.project_sources \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --kit-root extracted/hermes-connect-kit \
  --check
uv run ruff check scripts/extraction tests/extraction extracted/hermes-connect-kit/src extracted/hermes-connect-kit/tests
uv run pytest tests/extraction -q
uv run pytest extracted/hermes-connect-kit/tests -q
scripts/run_tests.sh -j 4 \
  tests/providers \
  tests/gateway \
  tests/plugins/model_providers \
  tests/agent/transports \
  tests/hermes_cli/test_provider_parity.py \
  -q
```

Expected: all commands exit 0. Any projected upstream test requiring source fallback must be listed individually in the final review with its undeclared host import.

- [ ] **Step 4: Prove source and branch integrity**

```bash
git merge-base --is-ancestor \
  269eb7b30e0bc3666c377e0325263e7b5bcf49b4 HEAD
UNEXPECTED="$(git diff --name-only \
  269eb7b30e0bc3666c377e0325263e7b5bcf49b4..HEAD \
  | grep -Ev '^(docs/extraction/|docs/superpowers/|scripts/extraction/|tests/extraction/|extracted/hermes-connect-kit/)' || true)"
test -z "$UNEXPECTED" || { printf 'Unexpected changes:\n%s\n' "$UNEXPECTED"; exit 1; }
test "$(git rev-parse main)" = "d5a67ad32522273115d887560ca1c08a02bc7873"
```

Expected: no unexpected paths and local `main` remains at the fork baseline.

- [ ] **Step 5: Write the final self-review**

`10-phase-2-final-review.md` must contain:

- exact source/test/projection counts by subsystem and classification;
- proof that every record has source SHA, upstream SHA, fork-main SHA, Git blob, mode, and SHA-256;
- all host-port and optional-UI destinations;
- all source-fallback-required tests and why;
- no unresolved internal imports;
- no duplicate destinations;
- no generated cache/bytecode files;
- all corrections made during Phase 2;
- explicit risks deferred to Phase 3;
- confirmation that no public services were introduced.

- [ ] **Step 6: Create the Phase 2 review gate**

`PHASE_2_REVIEW_GATE.md` must require approval of:

1. projection completeness;
2. manifest subsystem ownership;
3. host-port classifications;
4. projected test gaps;
5. provider identity preservation;
6. channel behavior coverage;
7. onboarding/reference scope;
8. Phase 3 public-service sequence.

- [ ] **Step 7: Final commit**

```bash
git add scripts/extraction tests/extraction extracted/hermes-connect-kit docs/extraction
git commit -m "feat(extraction): complete Phase 2 mechanical projection"
git status --short
```

Expected: clean worktree.

---

## Phase 2 Execution Review Checkpoints

Stop for review after each checkpoint:

1. **Checkpoint A:** Task 1 refreshed evidence and upstream impact review.
2. **Checkpoint B:** Tasks 2–5 manifest/provenance/projection engine.
3. **Checkpoint C:** Task 7 provider/shared slice.
4. **Checkpoint D:** Task 8 channel slice.
5. **Checkpoint E:** Task 9 complete projection and final gate.

Do not combine checkpoints into one giant pull request. Each checkpoint PR targets `planning/channels-providers-phase2-2026-07-22`, never `main`.

## Plan Self-Review

- **Spec coverage:** Latest evidence refresh, deterministic projection, provenance, selected tests, three subsystem slices, compatibility shims, verification, and final review gate all have explicit tasks.
- **Placeholder scan:** No `TBD`, `TODO`, “implement later,” or unnamed error-handling steps remain.
- **Type consistency:** `Subsystem`, `GitTreeEntry`, `FileRecord`, `TestFileRecord`, and `ProjectionRecord` names and fields are consistent across tasks.
- **Scope control:** Stable services, dependency inversion refactors, UI redesign, and standalone-repository splitting are explicitly deferred to later phases.
- **Process correction:** The plan avoids temporary CI workflow mutation and requires small checkpoint PRs rather than a single large evidence PR.
- **Known environment limitation:** The ChatGPT container cannot resolve GitHub, so worktree creation and direct test execution must occur in a connected development checkout or trusted repository CI.
