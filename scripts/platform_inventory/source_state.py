from __future__ import annotations

import subprocess
from pathlib import Path

from .models import InventoryError, SourceState


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise InventoryError(detail)
    return result.stdout.strip()


def read_source_state(root: Path) -> SourceState:
    root = root.resolve()
    try:
        repository_root = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
    except InventoryError as exc:
        raise InventoryError(f"{root} is not a Git repository") from exc

    branch = _git(repository_root, "branch", "--show-current") or "DETACHED"
    head_sha = _git(repository_root, "rev-parse", "HEAD")
    dirty = bool(_git(repository_root, "status", "--porcelain=v1", "--untracked-files=all"))
    remotes: dict[str, str] = {}
    for name in filter(None, _git(repository_root, "remote").splitlines()):
        remotes[name] = _git(repository_root, "remote", "get-url", name)
    return SourceState(repository_root, branch, head_sha, dirty, dict(sorted(remotes.items())))
