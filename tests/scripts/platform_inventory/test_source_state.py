from pathlib import Path

import pytest

from scripts.platform_inventory.source_state import InventoryError, read_source_state


def _git(repo: Path, *args: str) -> None:
    import subprocess

    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def test_read_source_state_reports_branch_head_and_clean_status(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "inventory@example.test")
    _git(repo, "config", "user.name", "Inventory Test")
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "initial")

    state = read_source_state(repo)

    assert state.branch == "main"
    assert len(state.head_sha) == 40
    assert state.dirty is False
    assert state.root == repo.resolve()


def test_read_source_state_marks_untracked_files_dirty(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "inventory@example.test")
    _git(repo, "config", "user.name", "Inventory Test")
    (repo / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "initial")
    (repo / "untracked.txt").write_text("dirty\n", encoding="utf-8")

    assert read_source_state(repo).dirty is True


def test_read_source_state_rejects_non_repository(tmp_path: Path) -> None:
    with pytest.raises(InventoryError, match="not a Git repository"):
        read_source_state(tmp_path)
