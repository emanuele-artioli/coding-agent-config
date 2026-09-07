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


def test_branch_deleted_when_head_not_target(test_repo: Path, tmp_path: Path) -> None:
    """Verify branch is deleted even if repo HEAD is on another branch lacking the commit."""
    # Commit c1 already on main
    # Create diverged branch 'temp' at c1
    _git(["checkout", "-b", "temp"], cwd=test_repo)

    # Create 'feat' from main, add commit c2, merge to main
    _git(["checkout", "main"], cwd=test_repo)
    _git(["checkout", "-b", "feat"], cwd=test_repo)
    (test_repo / "f2.txt").write_text("c2")
    _git(["add", "f2.txt"], cwd=test_repo)
    _git(["commit", "-m", "commit c2"], cwd=test_repo)
    _git(["checkout", "main"], cwd=test_repo)
    _git(["merge", "feat"], cwd=test_repo)

    # Add worktree for feat
    wt_path = tmp_path / "wt_feat"
    _git(["worktree", "add", str(wt_path), "feat"], cwd=test_repo)

    # Switch repo HEAD to 'temp' which does not have c2
    _git(["checkout", "temp"], cwd=test_repo)

    report = scan_worktrees(test_repo, target_ref="main")
    feat_wt = [w for w in report.worktrees if not w.is_root][0]
    assert feat_wt.action == "remove"
    assert feat_wt.is_merged

    execute_cleanup(report, dry_run=False)
    assert not wt_path.exists()

    # Verify branch 'feat' was deleted
    code = subprocess.run(["git", "rev-parse", "--verify", "feat"], cwd=test_repo).returncode
    assert code != 0


def test_post_merge_hook_end_to_end_and_chaining(tmp_path: Path) -> None:
    """Verify git-hooks/post-merge cleans up merged worktrees and chains to repo-local hook."""
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(["init", "--bare", "-b", "main"], cwd=origin)

    clone = tmp_path / "clone"
    _git(["clone", str(origin), str(clone)], cwd=tmp_path)
    _git(["config", "user.name", "Test"], cwd=clone)
    _git(["config", "user.email", "test@example.com"], cwd=clone)

    (clone / "readme.txt").write_text("init")
    _git(["add", "readme.txt"], cwd=clone)
    _git(["commit", "-m", "init commit"], cwd=clone)
    _git(["push", "origin", "main"], cwd=clone)

    # Create merged worktree
    wt_path = tmp_path / "wt_merged_hook"
    _git(["checkout", "-b", "feat-hook"], cwd=clone)
    (clone / "feat.txt").write_text("feature")
    _git(["add", "feat.txt"], cwd=clone)
    _git(["commit", "-m", "feat commit"], cwd=clone)
    _git(["push", "origin", "feat-hook:main"], cwd=clone)  # simulate PR merge to main

    _git(["checkout", "main"], cwd=clone)
    _git(["worktree", "add", str(wt_path), "feat-hook"], cwd=clone)
    assert wt_path.exists()

    # Set up local hook in clone/.git/hooks/post-merge
    local_hook_marker = tmp_path / "local_hook_called.txt"
    local_hook = clone / ".git" / "hooks" / "post-merge"
    local_hook.parent.mkdir(parents=True, exist_ok=True)
    local_hook.write_text(f"#!/bin/sh\necho CALLED \"$@\" > {local_hook_marker}\n")
    local_hook.chmod(0o755)

    # Execute host-wide post-merge hook directly
    hook_script = Path(__file__).resolve().parent.parent.parent / "git-hooks" / "post-merge"
    res = subprocess.run([str(hook_script), "0"], cwd=str(clone), capture_output=True, text=True)
    assert res.returncode == 0, f"Hook failed: {res.stderr}"

    # Worktree should have been removed
    assert not wt_path.exists()

    # Branch feat-hook should have been deleted
    code = subprocess.run(["git", "rev-parse", "--verify", "feat-hook"], cwd=clone).returncode
    assert code != 0

    # Local hook must have been chained and called
    assert local_hook_marker.is_file()
    assert "CALLED 0" in local_hook_marker.read_text()


def test_post_merge_hook_preserves_dirty_worktree(tmp_path: Path) -> None:
    """Verify git-hooks/post-merge preserves dirty worktrees."""
    origin = tmp_path / "origin"
    origin.mkdir()
    _git(["init", "--bare", "-b", "main"], cwd=origin)

    clone = tmp_path / "clone"
    _git(["clone", str(origin), str(clone)], cwd=tmp_path)
    _git(["config", "user.name", "Test"], cwd=clone)
    _git(["config", "user.email", "test@example.com"], cwd=clone)

    (clone / "readme.txt").write_text("init")
    _git(["add", "readme.txt"], cwd=clone)
    _git(["commit", "-m", "init commit"], cwd=clone)
    _git(["push", "origin", "main"], cwd=clone)

    wt_path = tmp_path / "wt_dirty_hook"
    _git(["branch", "dirty-branch", "main"], cwd=clone)
    _git(["worktree", "add", str(wt_path), "dirty-branch"], cwd=clone)
    (wt_path / "untracked.txt").write_text("dirty")

    hook_script = Path(__file__).resolve().parent.parent.parent / "git-hooks" / "post-merge"
    res = subprocess.run([str(hook_script)], cwd=str(clone), capture_output=True, text=True)
    assert res.returncode == 0

    # Worktree must still exist
    assert wt_path.exists()
    assert (wt_path / "untracked.txt").exists()


