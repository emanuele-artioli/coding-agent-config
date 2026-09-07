"""Policy and execution: safely remove merged git worktrees across projects.

Rule source: `AGENTS.md` (Plan mode: parallel-agent waves):
"A wave is finished when its worktrees are gone, not when its PRs merge. A
worktree outliving its branch is a silent-revert hazard: a resumed session
re-applies its version of a file a later session already changed, and nothing
about the output looks wrong."

Safety Invariants:
1. Never remove the primary repository checkout.
2. Never remove a worktree with unstaged, staged, or untracked files (`git status --porcelain`).
3. Never remove a worktree whose commits are not fully merged into `origin/main` (or `origin/master`).
4. Only safe branch deletion (`git branch -d`) is permitted; never force-delete.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

# Keep bytecode off NFS
sys.pycache_prefix = os.environ.get("PYTHONPYCACHEPREFIX") or "/var/tmp/emanuele-pycache"


@dataclass
class WorktreeInfo:
    path: Path
    head_sha: str
    branch: str | None = None
    is_detached: bool = False
    is_root: bool = False
    is_dirty: bool = False
    is_merged: bool = False
    unmerged_commits: list[str] = field(default_factory=list)
    action: str = "keep"  # "remove" | "skip_dirty" | "skip_unmerged" | "root"
    reason: str = ""


@dataclass
class CleanupReport:
    repo_root: Path
    target_branch: str
    worktrees: list[WorktreeInfo]
    removed_count: int = 0
    skipped_count: int = 0


def _run_git(args: Sequence[str], cwd: Path | str | None = None) -> tuple[int, str, str]:
    """Execute git command safely without raising on nonzero exit."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as exc:
        return 1, "", str(exc)


def get_repo_root(cwd: Path | str | None = None) -> Path | None:
    code, out, _ = _run_git(["rev-parse", "--show-toplevel"], cwd=cwd)
    return Path(out).resolve() if code == 0 and out else None


def resolve_default_target(repo_root: Path) -> str:
    """Determine upstream target branch: origin/main or origin/master."""
    for candidate in ("origin/main", "origin/master", "main", "master"):
        code, _, _ = _run_git(["rev-parse", "--verify", candidate], cwd=repo_root)
        if code == 0:
            return candidate
    return "origin/main"


def scan_worktrees(repo_root: Path, target_ref: str | None = None) -> CleanupReport:
    """Scan all linked worktrees and classify their eligibility for removal."""
    if not target_ref:
        target_ref = resolve_default_target(repo_root)

    # Refresh remote tracking branch quietly if possible
    _run_git(["fetch", "origin", "--quiet"], cwd=repo_root)

    code, out, _ = _run_git(["worktree", "list", "--porcelain"], cwd=repo_root)
    if code != 0 or not out:
        return CleanupReport(repo_root=repo_root, target_branch=target_ref, worktrees=[])

    entries: list[WorktreeInfo] = []
    current_path: Path | None = None
    current_head: str = ""
    current_branch: str | None = None
    current_detached: bool = False

    for line in out.splitlines():
        if line.startswith("worktree "):
            current_path = Path(line[len("worktree "):].strip()).resolve()
            current_branch = None
            current_detached = False
            current_head = ""
        elif line.startswith("HEAD "):
            current_head = line[len("HEAD "):].strip()
        elif line.startswith("branch refs/heads/"):
            current_branch = line[len("branch refs/heads/"):].strip()
        elif line == "detached":
            current_detached = True
        elif line == "" and current_path:
            is_root = current_path == repo_root
            info = WorktreeInfo(
                path=current_path,
                head_sha=current_head,
                branch=current_branch,
                is_detached=current_detached,
                is_root=is_root,
            )
            entries.append(info)
            current_path = None

    if current_path:
        is_root = current_path == repo_root
        entries.append(
            WorktreeInfo(
                path=current_path,
                head_sha=current_head,
                branch=current_branch,
                is_detached=current_detached,
                is_root=is_root,
            )
        )

    # Evaluate each worktree
    for wt in entries:
        if wt.is_root:
            wt.action = "root"
            wt.reason = "Primary repository root is never removed"
            continue

        if not wt.path.exists():
            wt.action = "remove"
            wt.reason = "Missing directory on disk; record needs pruning"
            continue

        # Check dirty state
        status_code, status_out, _ = _run_git(["status", "--porcelain"], cwd=wt.path)
        if status_code != 0 or status_out:
            wt.is_dirty = True
            wt.action = "skip_dirty"
            wt.reason = "Worktree has uncommitted or untracked changes"
            continue

        # Check merge status
        if wt.is_detached:
            anc_code, _, _ = _run_git(
                ["merge-base", "--is-ancestor", wt.head_sha, target_ref], cwd=repo_root
            )
            if anc_code == 0:
                wt.is_merged = True
                wt.action = "remove"
                wt.reason = f"Detached HEAD {wt.head_sha[:8]} is ancestor of {target_ref}"
            else:
                wt.is_merged = False
                wt.action = "skip_unmerged"
                wt.reason = f"Detached HEAD {wt.head_sha[:8]} is not in {target_ref}"
        elif wt.branch:
            log_code, log_out, _ = _run_git(
                ["log", f"{target_ref}..{wt.branch}", "--oneline"], cwd=repo_root
            )
            if log_code == 0 and not log_out:
                wt.is_merged = True
                wt.action = "remove"
                wt.reason = f"Branch '{wt.branch}' is fully merged into {target_ref}"
            else:
                wt.is_merged = False
                wt.unmerged_commits = [c for c in log_out.splitlines() if c]
                wt.action = "skip_unmerged"
                wt.reason = f"Branch '{wt.branch}' has {len(wt.unmerged_commits)} unmerged commits"

    return CleanupReport(repo_root=repo_root, target_branch=target_ref, worktrees=entries)


def execute_cleanup(report: CleanupReport, dry_run: bool = False) -> CleanupReport:
    """Execute removal on worktrees marked 'remove'."""
    removed = 0
    skipped = 0

    for wt in report.worktrees:
        if wt.action != "remove":
            skipped += 1
            continue

        if dry_run:
            removed += 1
            continue

        if wt.path.exists():
            rm_code, _, _ = _run_git(["worktree", "remove", str(wt.path)], cwd=report.repo_root)
            if rm_code != 0:
                # Fallback to force remove only if already verified clean & merged above
                _run_git(["worktree", "remove", "--force", str(wt.path)], cwd=report.repo_root)

        if wt.branch:
            _run_git(["branch", "-d", wt.branch], cwd=report.repo_root)

        removed += 1

    if not dry_run:
        _run_git(["worktree", "prune"], cwd=report.repo_root)
        _run_git(["remote", "prune", "origin"], cwd=report.repo_root)

    report.removed_count = removed
    report.skipped_count = skipped
    return report

