# Hermes Connect Phase 2 Mechanical Projection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reproduce the reviewed Hermes channel, provider, onboarding, host-boundary, optional-reference, and selected-test source as one byte-identical source-relative tree under `extracted/hermes-connect-kit/upstream/`, with deterministic provenance and no behavior refactor.

**Architecture:** Refresh Phase 1 evidence at the approved combined baseline, upgrade the manifest to version 2, enrich inventory with Git-object provenance, then stage and verify one complete projection tree before a rollback-safe directory swap. Classification, subsystem ownership, and planned Phase 3 layers remain metadata; they never create separate Python import roots.

**Tech Stack:** Python 3.11, dataclasses, pathlib, subprocess/Git plumbing, PyYAML, pytest, Ruff, existing Hermes registry probes, and the repository’s canonical isolated test runner. No new or expanded GitHub Actions workflow is part of this plan.

## Global Constraints

- Combined source baseline: `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`.
- Upstream source baseline: `NousResearch/hermes-agent@7de554277de632364c74fcf8641daa58a9a977d9`.
- Fork `main`: `Rilan-Dev/hermes-agent@d5a67ad32522273115d887560ca1c08a02bc7873` and must remain unchanged.
- Canonical design: `docs/superpowers/specs/2026-07-22-hermes-connect-phase2-projection-design.md`.
- Detailed companion design: `docs/extraction/07-phase-2-mechanical-projection-design.md`.
- Generated ownership is limited to `extracted/hermes-connect-kit/upstream/` and `extracted/hermes-connect-kit/projection-lock.json`.
- Every projected path is `upstream/<original repository-relative path>`.
- Classification and subsystem values are metadata only.
- Phase 2 performs no import rewriting, package renaming, compatibility wrapping, provider-ID normalization, or public-service implementation.
- Platform and model-provider membership remains registry/plugin driven.
- OpenAI API-key, OpenAI Codex OAuth/runtime, native model identifiers, and OpenAI-compatible endpoints remain distinct.
- Every implementation task follows RED → GREEN → focused regression → commit.
- Every gate ends with a written self-review.
- Stop rather than claim success when a required local command cannot be executed.

---

## Required Local Worktree Setup

The remote work branch already exists. In a connected development checkout, run:

```bash
git fetch origin
git show-ref --verify --quiet \
  refs/heads/worktree/channels-providers-phase2-2026-07-22 \
  || git branch --track \
    worktree/channels-providers-phase2-2026-07-22 \
    origin/worktree/channels-providers-phase2-2026-07-22

git worktree add \
  .worktrees/channels-providers-phase2-2026-07-22 \
  worktree/channels-providers-phase2-2026-07-22

cd .worktrees/channels-providers-phase2-2026-07-22
git status --short
git merge-base --is-ancestor \
  269eb7b30e0bc3666c377e0325263e7b5bcf49b4 HEAD
```

Expected:

- `git status --short` prints nothing.
- `git merge-base --is-ancestor` exits 0.

Do not execute projection from a dirty checkout.

## Files Created or Modified

```text
scripts/extraction/
├── schema.py
├── manifest.py
├── git_tree.py
├── filesystem_inventory.py
├── test_inventory.py
├── build_inventory.py
├── projection.py
├── project_sources.py
├── verify_projection.py
├── report_upstream_drift.py
└── run_projected_tests.py

tests/extraction/
├── test_manifest.py
├── test_filesystem_inventory.py
├── test_test_inventory.py
├── test_projection_plan.py
├── test_projection_apply.py
├── test_project_sources_cli.py
├── test_verify_projection.py
├── test_upstream_drift.py
└── snapshots/registry-snapshot.json

extracted/hermes-connect-kit/
├── README.md                         # Hand-written
├── extraction-manifest.yaml          # Hand-written manifest v2
├── projection-lock.json              # Generated
└── upstream/                          # Generated exact source tree

docs/extraction/
├── generated/phase-1-inventory.yaml
├── generated/phase-1-inventory.md
├── generated/phase-1-test-matrix.md
├── 08-phase-2-upstream-impact-review.md
├── 09-phase-2-projection-review.md
├── 10-phase-2-test-evidence.md
└── PHASE_2_REVIEW_GATE.md
```

---

### Task 1: Refresh Evidence at the Approved Phase 2 Baseline

**Files:**
- Modify: `extracted/hermes-connect-kit/extraction-manifest.yaml`
- Modify: `tests/extraction/test_manifest.py`
- Regenerate: `tests/extraction/snapshots/registry-snapshot.json`
- Regenerate: `docs/extraction/generated/phase-1-inventory.yaml`
- Regenerate: `docs/extraction/generated/phase-1-inventory.md`
- Regenerate: `docs/extraction/generated/phase-1-test-matrix.md`
- Create: `docs/extraction/08-phase-2-upstream-impact-review.md`

**Interfaces:**
- Consumes: current manifest v1, `registry_probe`, and `build_inventory`.
- Produces: refreshed evidence whose `source_sha` is `269eb7b30e0bc3666c377e0325263e7b5bcf49b4`.

- [ ] **Step 1: Write the failing source-baseline test**

Add to `tests/extraction/test_manifest.py`:

```python
from pathlib import Path

from scripts.extraction.manifest import load_manifest


PHASE2_SOURCE_SHA = "269eb7b30e0bc3666c377e0325263e7b5bcf49b4"


def test_manifest_uses_phase2_source_baseline() -> None:
    manifest = load_manifest(
        Path("extracted/hermes-connect-kit/extraction-manifest.yaml")
    )
    assert manifest.source_sha == PHASE2_SOURCE_SHA
```

- [ ] **Step 2: Run the focused test and verify RED**

```bash
uv run pytest \
  tests/extraction/test_manifest.py::test_manifest_uses_phase2_source_baseline \
  -v
```

Expected: FAIL showing the older `18bb6f1...` value.

- [ ] **Step 3: Update only the v1 source SHA**

Set:

```yaml
source_sha: 269eb7b30e0bc3666c377e0325263e7b5bcf49b4
```

Do not change classifications or projection fields yet.

- [ ] **Step 4: Capture the registry snapshot in an isolated home**

```bash
rm -rf .tmp/hermes-phase2-home
mkdir -p .tmp/hermes-phase2-home tests/extraction/snapshots
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

Expected: both commands exit 0.

- [ ] **Step 5: Regenerate evidence twice and prove determinism**

```bash
uv run python -m scripts.extraction.build_inventory
cp docs/extraction/generated/phase-1-inventory.yaml /tmp/phase2-inventory.yaml
cp docs/extraction/generated/phase-1-inventory.md /tmp/phase2-inventory.md
cp docs/extraction/generated/phase-1-test-matrix.md /tmp/phase2-test-matrix.md
cp tests/extraction/snapshots/registry-snapshot.json /tmp/phase2-registry.json

uv run python -m scripts.extraction.build_inventory

diff -u /tmp/phase2-inventory.yaml \
  docs/extraction/generated/phase-1-inventory.yaml
diff -u /tmp/phase2-inventory.md \
  docs/extraction/generated/phase-1-inventory.md
diff -u /tmp/phase2-test-matrix.md \
  docs/extraction/generated/phase-1-test-matrix.md
diff -u /tmp/phase2-registry.json \
  tests/extraction/snapshots/registry-snapshot.json
```

Expected: all diffs are empty.

- [ ] **Step 6: Verify refreshed characterization**

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

- [ ] **Step 7: Write the exact upstream-impact review**

`docs/extraction/08-phase-2-upstream-impact-review.md` must contain actual generated values for:

- source, upstream, and fork-main SHAs;
- added/removed/changed scoped paths since `18bb6f1...`;
- changed dynamic roots;
- new out-of-scope internal dependencies;
- `windows_ssh_runtime.py`, `_subprocess_compat.py`, route identity, bootstrap, service/process, and hard-exit classifications;
- registry membership/identity changes;
- selected-test changes;
- unresolved internal import count.

The final decision line is exactly:

```markdown
Projection is permitted only when unresolved in-scope internal imports equal zero.
```

- [ ] **Step 8: Self-review and commit**

```bash
git diff --check
UNEXPECTED="$(git diff --name-only | grep -Ev \
  '^(docs/extraction/|tests/extraction/|extracted/hermes-connect-kit/extraction-manifest.yaml$)' \
  || true)"
test -z "$UNEXPECTED" || {
  printf 'Unexpected Gate A paths:\n%s\n' "$UNEXPECTED"
  exit 1
}

git add \
  extracted/hermes-connect-kit/extraction-manifest.yaml \
  tests/extraction/test_manifest.py \
  tests/extraction/snapshots/registry-snapshot.json \
  docs/extraction/generated \
  docs/extraction/08-phase-2-upstream-impact-review.md
git commit -m "chore(extraction): refresh Phase 2 evidence"
```

**Checkpoint A:** Stop for evidence review before schema or projector work.

---

### Task 2: Introduce Manifest Version 2 Without Import-Root Destinations

**Files:**
- Modify: `scripts/extraction/schema.py`
- Modify: `scripts/extraction/manifest.py`
- Modify: `extracted/hermes-connect-kit/extraction-manifest.yaml`
- Modify: `tests/extraction/test_manifest.py`

**Interfaces:**
- Produces: `Subsystem`, `PlannedLayer`, manifest lineage, and `projection_root`.
- Projected path is derived; rules no longer carry runtime destination paths.

- [ ] **Step 1: Write failing v2 tests**

Add:

```python
from scripts.extraction.schema import PlannedLayer, Subsystem


def test_manifest_v2_derives_projection_paths(tmp_path: Path) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text(
        """
version: 2
source_repository: Rilan-Dev/hermes-agent
source_sha: 269eb7b30e0bc3666c377e0325263e7b5bcf49b4
upstream_repository: NousResearch/hermes-agent
upstream_sha: 7de554277de632364c74fcf8641daa58a9a977d9
fork_main_sha: d5a67ad32522273115d887560ca1c08a02bc7873
projection_root: upstream
dynamic_roots:
  - path: providers
    subsystem: providers
    classification: core
    planned_layer: vendor
    reason: Provider profiles.
explicit_files: []
test_rules:
  - path: tests/providers
    kind: root
    subsystem: providers
    behavior: Provider behavior.
internal_module_roots: [providers]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    manifest = load_manifest(path)

    assert manifest.version == 2
    assert manifest.projection_root == "upstream"
    assert manifest.dynamic_roots[0].subsystem is Subsystem.PROVIDERS
    assert manifest.dynamic_roots[0].planned_layer is PlannedLayer.VENDOR
    assert manifest.projected_path("providers/base.py") == (
        "upstream/providers/base.py"
    )


def test_manifest_v2_rejects_runtime_destination(tmp_path: Path) -> None:
    path = write_manifest_v2(
        tmp_path,
        dynamic_rule={
            "path": "providers",
            "subsystem": "providers",
            "classification": "core",
            "planned_layer": "vendor",
            "destination": "vendor/providers",
            "reason": "Provider profiles.",
        },
    )

    with pytest.raises(ManifestError, match="destination"):
        load_manifest(path)
```

- [ ] **Step 2: Run and verify RED**

```bash
uv run pytest tests/extraction/test_manifest.py -q
```

Expected: missing enums/fields and unsupported version 2.

- [ ] **Step 3: Implement schema types**

In `scripts/extraction/schema.py` add:

```python
class Subsystem(str, Enum):
    SHARED = "shared"
    PROVIDERS = "providers"
    CHANNELS = "channels"
    ONBOARDING = "onboarding"


class PlannedLayer(str, Enum):
    VENDOR = "vendor"
    COMPATIBILITY = "compatibility"
    REFERENCE = "reference"


@dataclass(frozen=True)
class RootRule:
    path: str
    subsystem: Subsystem
    classification: Classification
    planned_layer: PlannedLayer | None
    reason: str


@dataclass(frozen=True)
class FileRule:
    path: str
    subsystem: Subsystem
    classification: Classification
    planned_layer: PlannedLayer | None
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
    projection_root: str
    dynamic_roots: tuple[RootRule, ...]
    explicit_files: tuple[FileRule, ...]
    test_rules: tuple[TestRule, ...]
    internal_module_roots: tuple[str, ...]

    def projected_path(self, source_path: str) -> str:
        return PurePosixPath(self.projection_root, source_path).as_posix()
```

Import `PurePosixPath` in `schema.py`.

- [ ] **Step 4: Parse v2 strictly**

`manifest.py` must:

- require `version == 2`;
- SHA-validate `source_sha`, `upstream_sha`, and `fork_main_sha`;
- require `projection_root == "upstream"`;
- require one subsystem on every source/test rule;
- accept optional planned layer only on source rules;
- reject the legacy `destination` key with `ManifestError`;
- reject unknown keys rather than silently ignoring them.

- [ ] **Step 5: Migrate the real manifest**

Set top-level lineage fields and remove every `destination`. Convert each old destination class to `planned_layer` metadata:

```yaml
version: 2
source_repository: Rilan-Dev/hermes-agent
source_sha: 269eb7b30e0bc3666c377e0325263e7b5bcf49b4
upstream_repository: NousResearch/hermes-agent
upstream_sha: 7de554277de632364c74fcf8641daa58a9a977d9
fork_main_sha: d5a67ad32522273115d887560ca1c08a02bc7873
projection_root: upstream
```

Assign exactly one subsystem to each source/test rule.

- [ ] **Step 6: Verify and commit**

```bash
uv run pytest tests/extraction/test_manifest.py -q
uv run pytest tests/extraction -q
uv run ruff check scripts/extraction tests/extraction

git add scripts/extraction/schema.py scripts/extraction/manifest.py \
  extracted/hermes-connect-kit/extraction-manifest.yaml \
  tests/extraction/test_manifest.py
git commit -m "feat(extraction): define source-relative manifest v2"
```

---

### Task 3: Add Git-Object Provenance and Selected-Test Inventory

**Files:**
- Create: `scripts/extraction/git_tree.py`
- Modify: `scripts/extraction/filesystem_inventory.py`
- Create: `scripts/extraction/test_inventory.py`
- Modify: `scripts/extraction/build_inventory.py`
- Modify: `tests/extraction/test_filesystem_inventory.py`
- Create: `tests/extraction/test_test_inventory.py`

**Interfaces:**
- Produces `GitTreeEntry`, enriched `FileRecord`, and `TestFileRecord`.
- Every record carries a mechanically derived projected path.

- [ ] **Step 1: Write failing regular-file and symlink tests**

```python
def test_inventory_records_git_provenance(git_repo: Path) -> None:
    source = git_repo / "providers" / "profile.py"
    source.parent.mkdir(parents=True)
    source.write_text("VALUE = 1\n", encoding="utf-8")
    source.chmod(0o755)
    commit_all(git_repo)

    manifest = make_manifest_v2(
        source_sha=git_head(git_repo),
        roots=(root_rule("providers", "providers", "vendor"),),
    )
    record = inventory_files(git_repo, manifest)[0]

    assert record.projected_path == "upstream/providers/profile.py"
    assert record.subsystem == "providers"
    assert record.planned_layer == "vendor"
    assert record.git_mode == "100755"
    assert record.git_object_type == "blob"
    assert len(record.git_blob_sha) == 40
    assert record.kind == "file"
    assert record.link_target is None
```

Add a non-Windows symlink test asserting `git_mode == "120000"`, exact relative link target, and rejection of absolute or escaping targets.

- [ ] **Step 2: Write failing selected-test expansion tests**

```python
def test_selected_tests_keep_original_projected_paths(git_repo: Path) -> None:
    write(git_repo, "tests/providers/test_a.py", "def test_a(): pass\n")
    write(git_repo, "tests/gateway/test_b.py", "def test_b(): pass\n")
    commit_all(git_repo)

    manifest = make_manifest_v2(
        source_sha=git_head(git_repo),
        test_rules=(
            test_rule("tests/providers", "root", "providers"),
            test_rule("tests/gateway/test_b.py", "file", "channels"),
        ),
    )

    records = inventory_test_files(git_repo, manifest)

    assert [record.projected_path for record in records] == [
        "upstream/tests/gateway/test_b.py",
        "upstream/tests/providers/test_a.py",
    ]
```

- [ ] **Step 3: Verify RED**

```bash
uv run pytest \
  tests/extraction/test_filesystem_inventory.py \
  tests/extraction/test_test_inventory.py -q
```

- [ ] **Step 4: Implement batched Git tree lookup**

Create:

```python
@dataclass(frozen=True)
class GitTreeEntry:
    path: str
    mode: str
    object_type: str
    object_sha: str


def load_tree_entries(
    repo_root: Path,
    source_sha: str,
    scoped_paths: Sequence[str],
) -> dict[str, GitTreeEntry]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "-z", source_sha, "--", *scoped_paths],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    entries: dict[str, GitTreeEntry] = {}
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        metadata, encoded_path = raw.split(b"\t", 1)
        mode, object_type, object_sha = metadata.decode("ascii").split(" ")
        path = encoded_path.decode("utf-8", "surrogateescape")
        entries[path] = GitTreeEntry(path, mode, object_type, object_sha)
    return entries
```

Wrap subprocess/parse errors in a `GitTreeError` that includes the source SHA.

- [ ] **Step 5: Enrich source and test records**

Required fields:

```python
source: str
projected_path: str
subsystem: str
classification: str
planned_layer: str | None
reason: str
sha256: str
size_bytes: int
git_mode: str
git_object_type: str
git_blob_sha: str
kind: str
link_target: str | None
```

`TestFileRecord` additionally carries `behavior` and uses classification `test`.

- [ ] **Step 6: Verify source SHA against HEAD without requiring equality**

Add a source-guard test proving:

- `source_sha` may be an ancestor of `HEAD`;
- extraction-only commits after `source_sha` are allowed;
- changing one scoped source after `source_sha` fails;
- a Git mode or symlink-target change fails.

- [ ] **Step 7: Add selected tests to generated evidence**

`build_inventory()` returns:

```python
"files": [...],
"selected_test_files": [...],
```

Sort records by source path and reject projected-path collisions across source and selected-test records.

- [ ] **Step 8: Verify and commit**

```bash
uv run pytest \
  tests/extraction/test_filesystem_inventory.py \
  tests/extraction/test_test_inventory.py \
  tests/extraction/test_build_inventory.py -q
uv run pytest tests/extraction -q
uv run ruff check scripts/extraction tests/extraction

git add scripts/extraction/git_tree.py \
  scripts/extraction/filesystem_inventory.py \
  scripts/extraction/test_inventory.py \
  scripts/extraction/build_inventory.py \
  tests/extraction/test_filesystem_inventory.py \
  tests/extraction/test_test_inventory.py
git commit -m "feat(extraction): record projection provenance"
```

**Checkpoint B:** Review manifest-v2 and provenance before projector implementation.

---

### Task 4: Build the Complete Projection Plan and Deterministic Lock

**Files:**
- Create: `scripts/extraction/projection.py`
- Create: `tests/extraction/test_projection_plan.py`

**Interfaces:**
- `build_projection_plan(inventory: Mapping[str, object]) -> ProjectionPlan`.
- `projection_lock_data(plan: ProjectionPlan, manifest_sha256: str) -> dict[str, object]`.
- No filesystem writes occur in this task.

- [ ] **Step 1: Write failing plan tests**

```python
def test_projection_plan_uses_one_source_relative_tree() -> None:
    inventory = inventory_fixture(
        files=[file_row("gateway/session.py", "channels", "core")],
        tests=[test_row("tests/gateway/test_session.py", "channels")],
    )

    plan = build_projection_plan(inventory)

    assert [record.projected_path for record in plan.records] == [
        "upstream/gateway/session.py",
        "upstream/tests/gateway/test_session.py",
    ]


def test_projection_plan_rejects_projected_path_collision() -> None:
    inventory = inventory_fixture(
        files=[file_row("a.py", "shared", "core")],
        tests=[test_row("a.py", "shared")],
    )

    with pytest.raises(ProjectionError, match="collision"):
        build_projection_plan(inventory)
```

- [ ] **Step 2: Verify RED**

```bash
uv run pytest tests/extraction/test_projection_plan.py -q
```

- [ ] **Step 3: Implement immutable records and plan**

```python
@dataclass(frozen=True)
class ProjectionRecord:
    source: str
    projected_path: str
    subsystem: str
    classification: str
    planned_layer: str | None
    reason: str
    sha256: str
    size_bytes: int
    git_mode: str
    git_object_type: str
    git_blob_sha: str
    kind: str
    link_target: str | None
    behavior: str | None = None


@dataclass(frozen=True)
class ProjectionPlan:
    source_repository: str
    source_sha: str
    upstream_repository: str
    upstream_sha: str
    fork_main_sha: str
    projection_root: str
    records: tuple[ProjectionRecord, ...]
```

Require every projected path to start with `upstream/` and to equal `PurePosixPath("upstream", source)`.

- [ ] **Step 4: Serialize the deterministic lock**

The lock contains:

```python
{
    "schema_version": 1,
    "generator_version": 1,
    "source_repository": plan.source_repository,
    "source_sha": plan.source_sha,
    "upstream_repository": plan.upstream_repository,
    "upstream_sha": plan.upstream_sha,
    "fork_main_sha": plan.fork_main_sha,
    "projection_root": plan.projection_root,
    "manifest_sha256": manifest_sha256,
    "records": [asdict(record) for record in plan.records],
}
```

Sort records by `(projected_path, source)`. Do not add timestamps.

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest tests/extraction/test_projection_plan.py -q
uv run ruff check scripts/extraction/projection.py \
  tests/extraction/test_projection_plan.py

git add scripts/extraction/projection.py \
  tests/extraction/test_projection_plan.py
git commit -m "feat(extraction): build deterministic projection plan"
```

---

### Task 5: Implement Staging, Verification, and Rollback-Safe Swap

**Files:**
- Modify: `scripts/extraction/projection.py`
- Create: `scripts/extraction/project_sources.py`
- Create: `scripts/extraction/verify_projection.py`
- Create: `tests/extraction/test_projection_apply.py`
- Create: `tests/extraction/test_project_sources_cli.py`
- Create: `tests/extraction/test_verify_projection.py`

**Interfaces:**
- `stage_projection(repo_root, kit_root, plan, lock_data) -> Path`.
- `verify_tree(tree_root, plan) -> None`.
- `apply_projection(staging_root, kit_root) -> None`.
- CLI: `--write`, `--check`, `--dry-run`, and `--debug`.

- [ ] **Step 1: Write failing safety tests**

Cover:

```python
def test_failed_stage_preserves_existing_upstream_tree(tmp_path: Path) -> None:
    kit = tmp_path / "extracted/hermes-connect-kit"
    existing = kit / "upstream/gateway/existing.py"
    existing.parent.mkdir(parents=True)
    existing.write_text("old\n", encoding="utf-8")

    with pytest.raises(ProjectionError):
        stage_projection(tmp_path, kit, plan_with_missing_source(), lock_data())

    assert existing.read_text(encoding="utf-8") == "old\n"


def test_projector_preserves_handwritten_files(tmp_path: Path) -> None:
    kit = tmp_path / "extracted/hermes-connect-kit"
    readme = kit / "README.md"
    readme.parent.mkdir(parents=True)
    readme.write_text("hand written\n", encoding="utf-8")

    apply_valid_projection(tmp_path, kit)

    assert readme.read_text(encoding="utf-8") == "hand written\n"
```

Also test exact bytes, executable mode, safe symlink recreation, escaping-symlink rejection, extra-file detection, changed-hash detection, and rollback when the second rename fails.

- [ ] **Step 2: Verify RED**

```bash
uv run pytest \
  tests/extraction/test_projection_apply.py \
  tests/extraction/test_project_sources_cli.py \
  tests/extraction/test_verify_projection.py -q
```

- [ ] **Step 3: Stage the complete tree**

Use a sibling temporary directory:

```python
staging = Path(
    tempfile.mkdtemp(
        prefix="hermes-connect-upstream-",
        dir=kit_root.parent,
    )
)
```

Create `staging/upstream/<source>` for every record. Copy regular-file bytes without text decoding. Derive executable permission from Git mode. Recreate only safe relative symlinks.

- [ ] **Step 4: Verify staged content before swap**

`verify_tree()` reports all sorted differences in one error:

- missing paths;
- extra paths;
- byte/hash changes;
- mode changes;
- object-kind changes;
- symlink-target changes.

- [ ] **Step 5: Implement rollback-safe replacement**

Use these sibling paths:

```text
upstream/
upstream.projection-backup/
upstream.projection-staging/
```

Algorithm:

1. verify staging;
2. remove a stale backup only when it is recorded as a prior interrupted backup;
3. rename current `upstream/` to backup;
4. rename staged `upstream/` into place;
5. write `projection-lock.json.tmp`, fsync it, then `os.replace()` it;
6. verify the installed tree;
7. remove backup;
8. on failure, restore backup and report retained staging path.

Describe this as rollback-safe, not universally atomic.

- [ ] **Step 6: Implement CLI behavior**

Commands:

```bash
uv run python -m scripts.extraction.project_sources --dry-run
uv run python -m scripts.extraction.project_sources --write
uv run python -m scripts.extraction.project_sources --check
```

Exactly one mode is required. `--check` performs no writes. Normal failures print one concise error and exit 1; `--debug` re-raises.

- [ ] **Step 7: Verify and commit**

```bash
uv run pytest \
  tests/extraction/test_projection_plan.py \
  tests/extraction/test_projection_apply.py \
  tests/extraction/test_project_sources_cli.py \
  tests/extraction/test_verify_projection.py -q
uv run pytest tests/extraction -q
uv run ruff check scripts/extraction tests/extraction

git add scripts/extraction/projection.py \
  scripts/extraction/project_sources.py \
  scripts/extraction/verify_projection.py \
  tests/extraction/test_projection_apply.py \
  tests/extraction/test_project_sources_cli.py \
  tests/extraction/test_verify_projection.py
git commit -m "feat(extraction): stage and verify exact source projection"
```

---

### Task 6: Add Deterministic Upstream Drift Reporting

**Files:**
- Create: `scripts/extraction/report_upstream_drift.py`
- Create: `tests/extraction/test_upstream_drift.py`

**Interfaces:**
- `build_drift_report(old_lock, new_plan, new_inventory) -> DriftReport`.
- CLI compares the committed lock with the refreshed plan.

- [ ] **Step 1: Write failing drift tests**

```python
def test_drift_report_classifies_source_and_metadata_changes() -> None:
    old = lock_fixture(
        record("gateway/a.py", sha="a" * 64, subsystem="channels")
    )
    new = plan_fixture(
        record("gateway/a.py", sha="b" * 64, subsystem="shared"),
        record("gateway/b.py", sha="c" * 64, subsystem="channels"),
    )

    report = build_drift_report(old, new, inventory_fixture())

    assert report.added == ("gateway/b.py",)
    assert report.changed_hashes == ("gateway/a.py",)
    assert report.changed_subsystems == ("gateway/a.py",)
```

Also cover removed paths, mode/target/classification/planned-layer changes, registry changes, unresolved imports, and selected-test changes.

- [ ] **Step 2: Verify RED**

```bash
uv run pytest tests/extraction/test_upstream_drift.py -q
```

- [ ] **Step 3: Implement deterministic report models and Markdown**

Use frozen dataclasses with sorted tuples. Markdown contains sections for every change category and prints `None` for an empty category; it never omits a category.

- [ ] **Step 4: Add CLI**

```bash
uv run python -m scripts.extraction.report_upstream_drift \
  --lock extracted/hermes-connect-kit/projection-lock.json \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --markdown docs/extraction/generated/phase-2-upstream-drift.md
```

When no prior lock exists, report every planned path as added and label the run `initial_projection: true`.

- [ ] **Step 5: Verify and commit**

```bash
uv run pytest tests/extraction/test_upstream_drift.py -q
uv run ruff check scripts/extraction/report_upstream_drift.py \
  tests/extraction/test_upstream_drift.py

git add scripts/extraction/report_upstream_drift.py \
  tests/extraction/test_upstream_drift.py
git commit -m "feat(extraction): report deterministic upstream drift"
```

**Checkpoint C:** Review projector safety and drift behavior before generating source.

---

### Task 7: Generate the Complete Exact Projection

**Files:**
- Create/update: `extracted/hermes-connect-kit/upstream/**`
- Create: `extracted/hermes-connect-kit/projection-lock.json`
- Create: `extracted/hermes-connect-kit/README.md`
- Create: `docs/extraction/generated/phase-2-upstream-drift.md`
- Create: `docs/extraction/09-phase-2-projection-review.md`

**Interfaces:**
- Consumes Tasks 1–6.
- Produces one complete projected tree, not partial subsystem runtime trees.

- [ ] **Step 1: Preview the exact plan**

```bash
uv run python -m scripts.extraction.project_sources --dry-run \
  > /tmp/hermes-connect-projection-plan.txt
cat /tmp/hermes-connect-projection-plan.txt
```

Expected: one source-relative `upstream/` destination per refreshed source/test record and zero collisions.

- [ ] **Step 2: Write and immediately verify**

```bash
uv run python -m scripts.extraction.project_sources --write
uv run python -m scripts.extraction.project_sources --check
```

Expected: both commands exit 0.

- [ ] **Step 3: Generate initial drift report**

```bash
uv run python -m scripts.extraction.report_upstream_drift \
  --lock extracted/hermes-connect-kit/projection-lock.json \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --markdown docs/extraction/generated/phase-2-upstream-drift.md
```

Expected: initial projection lists every path as added and no removed paths.

- [ ] **Step 4: Verify no generated caches or undeclared files**

```bash
find extracted/hermes-connect-kit/upstream \
  \( -name __pycache__ -o -name '*.pyc' -o -name '*.pyo' \) -print
uv run python -m scripts.extraction.verify_projection
```

Expected: `find` prints nothing and verifier exits 0.

- [ ] **Step 5: Document the generated boundary**

README must state:

- `upstream/` is generated and must not be edited;
- classification/planned layer are lock metadata;
- projected imports are not stable consumer API;
- exact write/check/drift commands;
- Phase 3 owns `hermes_connect.*` and adaptations.

- [ ] **Step 6: Write projection self-review**

`09-phase-2-projection-review.md` records exact counts by subsystem, classification, planned layer, file kind, and test/source status. It lists all removed/renamed paths, host boundaries, optional UI paths, and unexpected growth.

- [ ] **Step 7: Diff guard and commit**

```bash
UNEXPECTED="$(git diff --name-only | grep -Ev \
  '^(docs/extraction/|docs/superpowers/|scripts/extraction/|tests/extraction/|extracted/hermes-connect-kit/)' \
  || true)"
test -z "$UNEXPECTED" || {
  printf 'Unexpected projection paths:\n%s\n' "$UNEXPECTED"
  exit 1
}
git diff --check

git add extracted/hermes-connect-kit \
  docs/extraction/generated/phase-2-upstream-drift.md \
  docs/extraction/09-phase-2-projection-review.md
git commit -m "feat(extraction): project exact Hermes source tree"
```

---

### Task 8: Run Projected Tests from the Projected Root

**Files:**
- Create: `scripts/extraction/run_projected_tests.py`
- Create: `tests/extraction/test_run_projected_tests.py`
- Create: `docs/extraction/10-phase-2-test-evidence.md`

**Interfaces:**
- `run_projected_tests(projected_root, test_files, jobs) -> TestRunSummary`.
- Each test file runs in a fresh subprocess with cwd and `PYTHONPATH` set to the projected root.

- [ ] **Step 1: Write failing runner tests**

```python
def test_runner_executes_each_file_in_isolated_projected_process(
    tmp_path: Path,
) -> None:
    root = make_projected_fixture(tmp_path)
    summary = run_projected_tests(
        root,
        ("tests/providers/test_a.py", "tests/gateway/test_b.py"),
        jobs=2,
    )

    assert summary.failed == ()
    assert summary.passed == (
        "tests/gateway/test_b.py",
        "tests/providers/test_a.py",
    )
```

Add a test proving repository-root shadow modules are not importable unless they also exist under projected root.

- [ ] **Step 2: Verify RED**

```bash
uv run pytest tests/extraction/test_run_projected_tests.py -q
```

- [ ] **Step 3: Implement isolated subprocess execution**

Each child command is:

```python
[
    sys.executable,
    "-m",
    "pytest",
    test_file,
    "-q",
]
```

Environment:

```python
env["PYTHONPATH"] = str(projected_root)
env["OPENROUTER_API_KEY"] = ""
env["OPENAI_API_KEY"] = ""
env["NOUS_API_KEY"] = ""
```

Use bounded `ThreadPoolExecutor` only to manage subprocesses. Sort summaries by test path.

- [ ] **Step 4: Run source characterization and projected regressions**

```bash
uv run pytest tests/extraction -q
scripts/run_tests.sh -j 4 \
  tests/providers \
  tests/gateway \
  tests/plugins/model_providers \
  tests/agent/transports \
  tests/hermes_cli/test_provider_parity.py \
  -q
uv run python -m scripts.extraction.run_projected_tests \
  --root extracted/hermes-connect-kit/upstream \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --jobs 4
```

Expected: all selected projected tests pass. Any failure must be fixed by correcting manifest completeness or projected test selection, not by editing files inside `upstream/`.

- [ ] **Step 5: Write exact test evidence**

`10-phase-2-test-evidence.md` contains:

- exact commands;
- commit SHA;
- pass/fail counts;
- failed test names and root cause if any;
- proof of projected-root `PYTHONPATH`;
- registry and unresolved-import results;
- confirmation that no source fallback was enabled.

Do not write “all passed” unless the commands above exited 0 in this checkout.

- [ ] **Step 6: Verify and commit**

```bash
uv run pytest tests/extraction/test_run_projected_tests.py -q
uv run ruff check scripts/extraction tests/extraction

git add scripts/extraction/run_projected_tests.py \
  tests/extraction/test_run_projected_tests.py \
  docs/extraction/10-phase-2-test-evidence.md
git commit -m "test(extraction): verify projected Hermes behavior"
```

**Checkpoint D:** Stop for generated-tree and test-evidence review.

---

### Task 9: Final Phase 2 Integrity Review and Gate

**Files:**
- Create: `docs/extraction/11-phase-2-final-self-review.md`
- Create: `docs/extraction/PHASE_2_REVIEW_GATE.md`
- Modify: `docs/extraction/README.md`

- [ ] **Step 1: Run the fresh completion verification**

```bash
uv run python -m scripts.extraction.project_sources --check
uv run python -m scripts.extraction.verify_projection
uv run ruff check scripts/extraction tests/extraction
uv run pytest tests/extraction -q
uv run python -m scripts.extraction.run_projected_tests \
  --root extracted/hermes-connect-kit/upstream \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --jobs 4
```

Expected: every command exits 0.

- [ ] **Step 2: Prove branch and source integrity**

```bash
git merge-base --is-ancestor \
  269eb7b30e0bc3666c377e0325263e7b5bcf49b4 HEAD

test "$(git rev-parse main)" = \
  "d5a67ad32522273115d887560ca1c08a02bc7873"

UNEXPECTED="$(git diff --name-only \
  269eb7b30e0bc3666c377e0325263e7b5bcf49b4..HEAD \
  | grep -Ev \
  '^(docs/extraction/|docs/superpowers/|scripts/extraction/|tests/extraction/|extracted/hermes-connect-kit/)' \
  || true)"
test -z "$UNEXPECTED" || {
  printf 'Unexpected Phase 2 paths:\n%s\n' "$UNEXPECTED"
  exit 1
}
```

- [ ] **Step 3: Write final self-review**

`11-phase-2-final-self-review.md` must record:

- exact source/test/projection counts;
- exact source/upstream/fork-main SHAs;
- deterministic lock proof;
- all corrections made during Phase 2;
- every host-port and optional-UI classification;
- provider/platform identity verification;
- no unresolved internal imports;
- no cache/bytecode files;
- no source fallback;
- no production-source or workflow changes;
- risks deferred to Phase 3;
- confirmation that no public API was introduced.

- [ ] **Step 4: Create the human review gate**

`PHASE_2_REVIEW_GATE.md` requires explicit approval of:

1. source-tree completeness;
2. manifest-v2 metadata;
3. lock provenance;
4. drift/deletion policy;
5. host-boundary classifications;
6. provider/platform identities;
7. onboarding/reference scope;
8. projected regression evidence;
9. Phase 3 service sequence.

- [ ] **Step 5: Final commit and clean status**

```bash
git add docs/extraction
git commit -m "docs(extraction): add Phase 2 review gate"
git status --short
```

Expected: clean worktree.

**Checkpoint E:** Open a draft PR targeting `planning/channels-providers-phase2-2026-07-22`. Do not merge it and do not begin Phase 3 without explicit human approval.

---

## Plan Self-Review

- **Spec coverage:** Evidence refresh, manifest v2, source guard, Git provenance, selected tests, exact projection, rollback, drift, projected-root tests, and final review gate each have explicit tasks.
- **Placeholder scan:** No `TBD`, `TODO`, “implement later,” or unnamed error-handling step remains.
- **Type consistency:** `Subsystem`, `PlannedLayer`, `GitTreeEntry`, `FileRecord`, `TestFileRecord`, `ProjectionRecord`, and `ProjectionPlan` are defined once and used consistently.
- **Architecture correction:** No generated `vendor/`, `compatibility/`, `reference/`, or separate test import root remains. All synchronized files use one `upstream/` tree.
- **Source-guard correction:** The plan requires `source_sha` to be an ancestor and scoped Git objects to match; it does not incorrectly require `HEAD == source_sha`.
- **Transaction wording:** The plan promises a rollback-safe staged swap, not universal cross-platform atomicity.
- **CI policy:** No workflow file is added or modified. Execution depends on a connected local worktree.
- **Scope control:** Stable services, dependency inversion, import adapters, and consumer APIs remain Phase 3 work.
