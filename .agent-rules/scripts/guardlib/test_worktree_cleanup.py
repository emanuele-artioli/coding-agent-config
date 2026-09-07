"""Unit tests for worktree_cleanup policy."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from .worktree_cleanup import execute_cleanup, get_repo_root, scan_worktrees


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True)


@pytest.fixture
def test_repo(tmp_path: Path) -> Path:
    """Create a temporary git repo with initial commit on main."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "-b", "main"], cwd=repo)
    _git(["config", "user.name", "Test User"], cwd=repo)
    _git(["config", "user.email", "test@example.com"], cwd=repo)

    file_a = repo / "file_a.txt"
    file_a.write_text("initial")
    _git(["add", "file_a.txt"], cwd=repo)
    _git(["commit", "-m", "initial commit"], cwd=repo)
    return repo


def test_get_repo_root(test_repo: Path) -> None:
    assert get_repo_root(test_repo) == test_repo.resolve()
    assert get_repo_root(test_repo / "nonexistent") is None


def test_root_worktree_never_removed(test_repo: Path) -> None:
    report = scan_worktrees(test_repo, target_ref="main")
    assert len(report.worktrees) == 1
    root = report.worktrees[0]
    assert root.is_root
    assert root.action == "root"


def test_clean_merged_worktree_removed(test_repo: Path, tmp_path: Path) -> None:
    wt_path = tmp_path / "wt_merged"
    _git(["branch", "merged-feat", "main"], cwd=test_repo)
    _git(["worktree", "add", str(wt_path), "merged-feat"], cwd=test_repo)

    report = scan_worktrees(test_repo, target_ref="main")
    assert len(report.worktrees) == 2
    merged_wt = [w for w in report.worktrees if not w.is_root][0]
    assert merged_wt.action == "remove"
    assert merged_wt.is_merged
    assert not merged_wt.is_dirty

    execute_cleanup(report, dry_run=False)
    assert not wt_path.exists()

    # Verify branch was deleted
    code = subprocess.run(["git", "rev-parse", "--verify", "merged-feat"], cwd=test_repo).returncode
    assert code != 0


def test_dirty_worktree_skipped(test_repo: Path, tmp_path: Path) -> None:
    wt_path = tmp_path / "wt_dirty"
    _git(["branch", "dirty-feat", "main"], cwd=test_repo)
    _git(["worktree", "add", str(wt_path), "dirty-feat"], cwd=test_repo)

    # Make it dirty with an untracked file
    (wt_path / "untracked.txt").write_text("dirty content")

    report = scan_worktrees(test_repo, target_ref="main")
    dirty_wt = [w for w in report.worktrees if not w.is_root][0]
    assert dirty_wt.is_dirty
    assert dirty_wt.action == "skip_dirty"

    execute_cleanup(report, dry_run=False)
    assert wt_path.exists()


def test_unmerged_worktree_skipped(test_repo: Path, tmp_path: Path) -> None:
    wt_path = tmp_path / "wt_unmerged"
    _git(["checkout", "-b", "unmerged-feat"], cwd=test_repo)
    (test_repo / "new_file.txt").write_text("unmerged")
    _git(["add", "new_file.txt"], cwd=test_repo)
    _git(["commit", "-m", "unmerged commit"], cwd=test_repo)
    _git(["checkout", "main"], cwd=test_repo)

    _git(["worktree", "add", str(wt_path), "unmerged-feat"], cwd=test_repo)

    report = scan_worktrees(test_repo, target_ref="main")
    unmerged_wt = [w for w in report.worktrees if not w.is_root][0]
    assert not unmerged_wt.is_merged
    assert unmerged_wt.action == "skip_unmerged"
    assert len(unmerged_wt.unmerged_commits) == 1

    execute_cleanup(report, dry_run=False)
    assert wt_path.exists()


def test_detached_merged_worktree_removed(test_repo: Path, tmp_path: Path) -> None:
    wt_path = tmp_path / "wt_detached"
    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=test_repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    _git(["worktree", "add", "--detach", str(wt_path), head_sha], cwd=test_repo)

    report = scan_worktrees(test_repo, target_ref="main")
    detached_wt = [w for w in report.worktrees if not w.is_root][0]
    assert detached_wt.is_detached
    assert detached_wt.is_merged
    assert detached_wt.action == "remove"

    execute_cleanup(report, dry_run=False)
    assert not wt_path.exists()

