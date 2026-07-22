# Phase 2 Mechanical Projection Execution Corrections

> **Normative status:** This document is part of the Phase 2 implementation plan. It overrides the conflicting steps in `2026-07-22-hermes-connect-phase2-mechanical-projection.md`. An executor must apply these corrections before beginning Task 5 or later.

**Goal:** Close three execution gaps found during the final self-review: initial drift must be captured before the new lock replaces the old state, interrupted swaps must require deterministic recovery rather than automatic deletion, and projected tests must run in a dependency-only environment that cannot import the source checkout through an editable installation.

**Affected tasks:** Task 5, Task 6, Task 7, Task 8, and Task 9 of the main implementation plan.

---

## Correction 1: Capture the Previous Lock Before Projection

### Defect

The original Task 7 sequence wrote the new projection and lock before generating the “initial drift” report. A drift command comparing the newly committed lock with the newly generated plan would report no changes and hide the initial added set.

### Required interface changes

Modify `scripts/extraction/report_upstream_drift.py` so its CLI has explicit old-state and new-state inputs:

```python
from argparse import ArgumentParser
from pathlib import Path


def build_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "--previous-lock",
        type=Path,
        help="Previous projection lock. Omit only for the first projection.",
    )
    parser.add_argument(
        "--proposed-lock",
        type=Path,
        required=True,
        help="Lock generated from the proposed projection plan.",
    )
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    return parser
```

The CLI must never infer the previous lock from the same path as the proposed lock.

Add a plan-only lock command to `scripts/extraction/project_sources.py`:

```bash
uv run python -m scripts.extraction.project_sources \
  --proposed-lock /tmp/hermes-proposed-projection-lock.json
```

This command:

1. loads and validates the manifest;
2. runs the scoped source guard;
3. builds the complete plan;
4. writes only the deterministic proposed lock to the requested path;
5. does not create, modify, rename, or delete `upstream/` or the committed lock.

### Required failing tests

Add to `tests/extraction/test_upstream_drift.py` and `tests/extraction/test_project_sources_cli.py`:

```python
def test_initial_drift_uses_no_previous_lock() -> None:
    report = build_drift_report(
        previous_lock=None,
        proposed_lock=lock_fixture("gateway/a.py", "providers/base.py"),
        inventory=inventory_fixture(),
    )
    assert report.initial_projection is True
    assert report.added == ("gateway/a.py", "providers/base.py")
    assert report.removed == ()


def test_same_previous_and_proposed_lock_path_is_rejected(tmp_path: Path) -> None:
    lock = tmp_path / "projection-lock.json"
    lock.write_text("{}\n", encoding="utf-8")

    with pytest.raises(DriftError, match="different paths"):
        load_drift_inputs(lock, lock)


def test_proposed_lock_mode_does_not_write_projection_tree(
    repo_fixture: Path,
) -> None:
    output = repo_fixture / "proposed-lock.json"
    result = run_project_sources(repo_fixture, "--proposed-lock", str(output))

    assert result.returncode == 0
    assert output.is_file()
    assert not (repo_fixture / "extracted/hermes-connect-kit/upstream").exists()
    assert not (
        repo_fixture / "extracted/hermes-connect-kit/projection-lock.json"
    ).exists()
```

### Corrected Task 7 sequence

Run this sequence **before** `--write`:

```bash
rm -f /tmp/hermes-previous-projection-lock.json \
  /tmp/hermes-proposed-projection-lock.json

if test -f extracted/hermes-connect-kit/projection-lock.json; then
  cp extracted/hermes-connect-kit/projection-lock.json \
    /tmp/hermes-previous-projection-lock.json
fi

uv run python -m scripts.extraction.project_sources \
  --proposed-lock /tmp/hermes-proposed-projection-lock.json

if test -f /tmp/hermes-previous-projection-lock.json; then
  uv run python -m scripts.extraction.report_upstream_drift \
    --previous-lock /tmp/hermes-previous-projection-lock.json \
    --proposed-lock /tmp/hermes-proposed-projection-lock.json \
    --inventory docs/extraction/generated/phase-1-inventory.yaml \
    --markdown docs/extraction/generated/phase-2-upstream-drift.md
else
  uv run python -m scripts.extraction.report_upstream_drift \
    --proposed-lock /tmp/hermes-proposed-projection-lock.json \
    --inventory docs/extraction/generated/phase-1-inventory.yaml \
    --markdown docs/extraction/generated/phase-2-upstream-drift.md
fi
```

Review the drift report before writing generated source.

Then run:

```bash
uv run python -m scripts.extraction.project_sources --write
uv run python -m scripts.extraction.project_sources --check
cmp /tmp/hermes-proposed-projection-lock.json \
  extracted/hermes-connect-kit/projection-lock.json
```

Expected: `cmp` exits 0. The reviewed proposed lock must be exactly the installed lock.

---

## Correction 2: Never Automatically Delete Interrupted Swap State

### Defect

The original Task 5 said a stale backup may be removed when it is “recorded as a prior interrupted backup” but did not define the record or deterministic recovery behavior. Automatic cleanup could destroy the only known-good generated tree.

### Generated transaction paths

Use only:

```text
extracted/hermes-connect-kit/upstream/
extracted/hermes-connect-kit/.upstream.projection-staging/
extracted/hermes-connect-kit/.upstream.projection-backup/
extracted/hermes-connect-kit/projection-lock.json
extracted/hermes-connect-kit/.projection-lock.staging.json
extracted/hermes-connect-kit/.projection-lock.backup.json
extracted/hermes-connect-kit/.projection-transaction.json
```

`.projection-transaction.json` is temporary transaction state and contains deterministic fields only:

```json
{
  "schema_version": 1,
  "phase": "staged|backed_up|installed|verified",
  "source_sha": "<40-hex SHA>",
  "proposed_lock_sha256": "<64-hex SHA>"
}
```

It contains no timestamp, hostname, username, PID, or absolute path.

### Normal write behavior

`--write` must fail without deleting anything when any staging, backup, or transaction path already exists:

```python
def assert_no_interrupted_transaction(paths: TransactionPaths) -> None:
    existing = tuple(
        path
        for path in (
            paths.staging_tree,
            paths.backup_tree,
            paths.staging_lock,
            paths.backup_lock,
            paths.transaction,
        )
        if path.exists() or path.is_symlink()
    )
    if existing:
        rendered = ", ".join(path.name for path in existing)
        raise ProjectionError(
            f"interrupted projection state exists: {rendered}; run --recover"
        )
```

Normal `--write` must never guess which stale path is safe to remove.

### Recovery command

Add:

```bash
uv run python -m scripts.extraction.project_sources --recover
```

`--recover` follows this exact state table:

| Final tree | Backup tree | Transaction phase | Action |
|---|---|---|---|
| missing | present | `backed_up` or `installed` | Restore backup tree and backup lock; retain staging for inspection; remove transaction only after verification. |
| present | present | `installed` | Verify final against staged/proposed lock. If valid, keep final and delete backup. If invalid, move invalid final to `.upstream.failed-install`, restore backup, and fail. |
| present | present | `verified` | Re-verify final, then delete backup and transaction. |
| present | missing | `installed` or `verified` | Verify final. If valid, remove transaction. If invalid, fail without deleting final. |
| missing | missing | any transaction phase | Fail and retain transaction file for manual investigation. |
| any | any | missing or unreadable transaction | Fail without mutation. |

The recovery command must never remove staging automatically. Add an explicit command after successful recovery:

```bash
uv run python -m scripts.extraction.project_sources --discard-staging
```

`--discard-staging` is allowed only when:

- no transaction file exists;
- no backup tree/lock exists;
- the final projection passes `--check`;
- the path to remove is exactly `.upstream.projection-staging`.

### Required failing tests

Add to `tests/extraction/test_projection_apply.py` and `tests/extraction/test_project_sources_cli.py`:

```python
def test_write_refuses_interrupted_state_without_deleting_it(
    kit_root: Path,
) -> None:
    staging = kit_root / ".upstream.projection-staging"
    staging.mkdir(parents=True)
    marker = staging / "keep.txt"
    marker.write_text("inspect me\n", encoding="utf-8")

    with pytest.raises(ProjectionError, match="--recover"):
        write_projection(kit_root, valid_plan())

    assert marker.read_text(encoding="utf-8") == "inspect me\n"


def test_recover_restores_backup_when_final_is_missing(kit_root: Path) -> None:
    create_verified_backup(kit_root)
    write_transaction(kit_root, phase="backed_up")

    recover_projection(kit_root)

    assert (kit_root / "upstream/gateway/old.py").is_file()
    assert not (kit_root / ".upstream.projection-backup").exists()
    assert not (kit_root / ".projection-transaction.json").exists()


def test_recover_never_mutates_without_valid_transaction(kit_root: Path) -> None:
    backup = create_verified_backup(kit_root)

    with pytest.raises(ProjectionError, match="transaction"):
        recover_projection(kit_root)

    assert backup.exists()
```

Update the main plan’s Task 5 wording: the transaction is **rollback-safe and explicitly recoverable**, not universally atomic.

---

## Correction 3: Projected Tests Must Use a Dependency-Only Virtual Environment

### Defect

Running projected tests with the current repository interpreter plus `PYTHONPATH=<projected-root>` is insufficient. An editable Hermes installation can register `.pth` files or import finders in site-packages, allowing missing projected modules to fall back to the source checkout.

### Manifest field

Add a reviewed top-level manifest-v2 field:

```yaml
projected_test_extras:
  - dev
  - messaging
  - matrix
  - slack
  - cli
```

This is a test-dependency list, not a provider/platform membership list. The evidence refresh may add or remove an extra only when selected tests prove it necessary.

Update `ExtractionManifest`:

```python
@dataclass(frozen=True)
class ExtractionManifest:
    version: int
    source_repository: str
    source_sha: str
    upstream_repository: str
    upstream_sha: str
    fork_main_sha: str
    projection_root: str
    projected_test_extras: tuple[str, ...]
    dynamic_roots: tuple[RootRule, ...]
    explicit_files: tuple[FileRule, ...]
    test_rules: tuple[TestRule, ...]
    internal_module_roots: tuple[str, ...]
```

The parser must reject an extra absent from `[project.optional-dependencies]`.

### Dependency requirements generator

Create `scripts/extraction/build_projected_test_requirements.py`:

```python
from __future__ import annotations

from pathlib import Path
import tomllib

from scripts.extraction.manifest import load_manifest


def build_requirements(
    pyproject_path: Path,
    manifest_path: Path,
) -> tuple[str, ...]:
    project_data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))[
        "project"
    ]
    manifest = load_manifest(manifest_path)
    optional = project_data.get("optional-dependencies", {})

    requirements = list(project_data.get("dependencies", ()))
    for extra in manifest.projected_test_extras:
        if extra not in optional:
            raise ValueError(f"unknown projected-test extra: {extra}")
        requirements.extend(optional[extra])

    return tuple(sorted(dict.fromkeys(requirements)))


def write_requirements(requirements: tuple[str, ...], output: Path) -> None:
    output.write_text("\n".join(requirements) + "\n", encoding="utf-8")
```

Add tests proving:

- core requirements are included;
- reviewed extras are included;
- duplicates are removed deterministically;
- unknown extras fail;
- `hermes-agent`, `-e`, local paths, Git URLs, and direct file URLs are rejected.

### Clean environment command

Create the environment outside the worktree:

```bash
rm -rf /tmp/hermes-projection-test-venv \
  /tmp/hermes-projection-test-requirements.txt

uv run python -m scripts.extraction.build_projected_test_requirements \
  --pyproject pyproject.toml \
  --manifest extracted/hermes-connect-kit/extraction-manifest.yaml \
  --output /tmp/hermes-projection-test-requirements.txt

uv venv --python 3.11 /tmp/hermes-projection-test-venv
uv pip install \
  --python /tmp/hermes-projection-test-venv/bin/python \
  -r /tmp/hermes-projection-test-requirements.txt
```

On Windows, use:

```powershell
uv venv --python 3.11 $env:TEMP\hermes-projection-test-venv
uv pip install `
  --python $env:TEMP\hermes-projection-test-venv\Scripts\python.exe `
  -r $env:TEMP\hermes-projection-test-requirements.txt
```

Do not install `hermes-agent`, the current repository, or the projected tree into this environment.

### Corrected runner interface

`run_projected_tests.py` must require an explicit clean interpreter:

```bash
uv run python -m scripts.extraction.run_projected_tests \
  --python /tmp/hermes-projection-test-venv/bin/python \
  --root extracted/hermes-connect-kit/upstream \
  --inventory docs/extraction/generated/phase-1-inventory.yaml \
  --source-root "$PWD" \
  --jobs 4
```

Before running tests, the runner executes this probe with the supplied interpreter:

```python
PROBE = r"""
import importlib.metadata
import json
import pathlib
import site
import sys

source_root = pathlib.Path(sys.argv[1]).resolve()
projected_root = pathlib.Path(sys.argv[2]).resolve()

paths = [pathlib.Path(p).resolve() for p in sys.path if p]
source_leaks = [str(p) for p in paths if p == source_root or source_root in p.parents]

try:
    distribution = importlib.metadata.distribution("hermes-agent")
except importlib.metadata.PackageNotFoundError:
    distribution = None

print(json.dumps({
    "source_leaks": source_leaks,
    "hermes_distribution_installed": distribution is not None,
    "projected_root": str(projected_root),
    "user_site_enabled": site.ENABLE_USER_SITE,
}))
"""
```

The runner must fail unless:

- `source_leaks == []`;
- `hermes_distribution_installed is False`;
- the interpreter is inside a virtual environment (`sys.prefix != sys.base_prefix`);
- user-site loading is disabled by `PYTHONNOUSERSITE=1`;
- the projected root is the first import path for each child.

Each test child uses:

```python
env = os.environ.copy()
env["PYTHONNOUSERSITE"] = "1"
env["PYTHONPATH"] = str(projected_root)
env["OPENROUTER_API_KEY"] = ""
env["OPENAI_API_KEY"] = ""
env["NOUS_API_KEY"] = ""

command = (
    str(clean_python),
    "-m",
    "pytest",
    test_file,
    "-q",
)
```

The child `cwd` is the projected root.

### Required fallback-detection test

Add to `tests/extraction/test_run_projected_tests.py`:

```python
def test_runner_rejects_interpreter_with_source_checkout_on_sys_path(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    projected_root = tmp_path / "projected"
    source_root.mkdir()
    projected_root.mkdir()

    result = validate_test_interpreter(
        python=Path(sys.executable),
        source_root=source_root,
        projected_root=projected_root,
        probe_result={
            "source_leaks": [str(source_root)],
            "hermes_distribution_installed": False,
            "user_site_enabled": False,
        },
    )

    assert result.ok is False
    assert "source checkout" in result.reason
```

### Corrected Task 8 and Task 9 commands

Replace every projected-test command in the main plan with the clean-interpreter command above. Test evidence must include the interpreter probe JSON and confirm:

```text
source_leaks: []
hermes_distribution_installed: false
user_site_enabled: false
```

Do not report projected parity when the clean environment cannot install the reviewed dependencies. Record the dependency failure and keep Checkpoint D blocked.

---

## Corrected Execution Order

The mandatory order is:

1. Complete Checkpoint A evidence refresh.
2. Complete manifest-v2 and provenance work.
3. Implement projection planning and deterministic proposed-lock output.
4. Implement explicit transaction recovery.
5. Generate and review drift from the previous lock to the proposed lock.
6. Write the projection and prove the installed lock equals the reviewed proposed lock.
7. Build the dependency-only virtual environment.
8. Run projected tests with no source or editable-install fallback.
9. Complete the final review gate.

## Correction Self-Review

- The initial added/removed set can no longer be erased by writing the new lock before drift generation.
- Interrupted backup/staging state is never guessed away or automatically deleted.
- Recovery behavior is deterministic and testable for every supported state.
- Projected tests cannot silently import the source checkout through an editable installation or user site.
- The dependency list is explicit review metadata and does not duplicate provider/platform membership.
- No GitHub Actions workflow or paid execution path is introduced.
- No change is made to fork `main`.
