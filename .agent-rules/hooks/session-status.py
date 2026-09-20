#!/usr/bin/env python3
"""SessionStart advisory: where this session is, and whether to add a worktree.

Several agents work these repos at once. The states that cause trouble are
invisible unless you look: a dirty primary checkout, or a session sitting on
the default branch that everyone else also uses.

Advisory only — never blocks, never creates a worktree, never checks out a
branch. SessionStart hooks cannot refuse to start.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def git(*args: str, cwd: Path | None = None) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


class SessionRepoState:
    """Git location of a SessionStart cwd.

    `advise_worktree` is true only for the primary checkout when it is dirty
    or not on the origin default branch. Callers must not treat that as a
    reason to exit non-zero or to run `git worktree add` themselves.
    """

    def __init__(
        self,
        branch: str,
        dirty: bool,
        is_primary: bool,
        default_branch: str,
        other_worktrees: tuple[str, ...],
    ) -> None:
        self.branch = branch
        self.dirty = dirty
        self.is_primary = is_primary
        self.default_branch = default_branch
        self.other_worktrees = other_worktrees

    @property
    def advise_worktree(self) -> bool:
        return self.is_primary and (
            self.dirty or self.branch != self.default_branch
        )


def _default_branch(cwd: Path) -> str:
    ref = git("symbolic-ref", "--short", "refs/remotes/origin/HEAD", cwd=cwd)
    if ref:
        return ref.rsplit("/", 1)[-1]
    for name in ("master", "main"):
        if git("rev-parse", "--verify", f"refs/remotes/origin/{name}", cwd=cwd):
            return name
        if git("rev-parse", "--verify", f"refs/heads/{name}", cwd=cwd):
            return name
    return "master"


def _worktree_paths(cwd: Path) -> list[Path]:
    paths: list[Path] = []
    for line in git("worktree", "list", "--porcelain", cwd=cwd).splitlines():
        if line.startswith("worktree "):
            paths.append(Path(line[len("worktree "):]).resolve())
    return paths


def inspect_repo(cwd: Path | None) -> SessionRepoState | None:
    """Return git state at `cwd`, or None when it is not a work tree.

    Never creates a worktree and never checks out a branch. Raises nothing:
    a broken git invocation is treated as "not a repo".
    """
    if cwd is None:
        return None
    try:
        cwd = cwd.resolve()
    except OSError:
        return None
    if not cwd.is_dir():
        return None
    if git("rev-parse", "--is-inside-work-tree", cwd=cwd) != "true":
        return None
    toplevel = git("rev-parse", "--show-toplevel", cwd=cwd)
    if not toplevel:
        return None
    toplevel_path = Path(toplevel).resolve()
    branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=cwd) or "(detached)"
    if branch == "HEAD":
        branch = "(detached)"
    dirty = bool(git("status", "--porcelain", cwd=cwd))
    listed = _worktree_paths(cwd)
    is_primary = bool(listed) and listed[0] == toplevel_path
    if not listed:
        git_dir = git("rev-parse", "--absolute-git-dir", cwd=cwd)
        common = git("rev-parse", "--git-common-dir", cwd=cwd)
        if git_dir and common:
            is_primary = Path(git_dir).resolve() == (cwd / common).resolve() if not Path(common).is_absolute() else Path(git_dir).resolve() == Path(common).resolve()
        else:
            is_primary = True
    other = tuple(str(p) for p in listed if p != toplevel_path)
    return SessionRepoState(
        branch=branch,
        dirty=dirty,
        is_primary=is_primary,
        default_branch=_default_branch(cwd),
        other_worktrees=other,
    )


def status_lines(cwd: Path | None) -> list[str]:
    """SessionStart lines: branch, dirty, primary or linked, other worktrees.

    If `cwd` is the primary checkout and it is dirty or not on the origin
    default branch, append an instruction to `git worktree add` from
    `origin/<default>` and leave the primary alone. Do not refuse to start.
    Do not create a worktree.
    """
    try:
        state = inspect_repo(cwd)
    except Exception:
        return []
    if state is None:
        return []
    lines = [
        f"branch: {state.branch}",
        f"dirty: {'yes' if state.dirty else 'no'}",
        f"cwd: {'primary checkout' if state.is_primary else 'linked worktree'}",
    ]
    if state.other_worktrees:
        lines.append("other worktrees: " + ", ".join(state.other_worktrees))
    else:
        lines.append("other worktrees: none")
    if state.advise_worktree:
        reasons: list[str] = []
        if state.dirty:
            reasons.append("dirty")
        if state.branch != state.default_branch:
            reasons.append(f"not on origin/{state.default_branch}")
        lines.append(
            f"Primary checkout is {' and '.join(reasons)}. "
            "Do not checkout another branch on this primary. "
            f"`git worktree add` from origin/{state.default_branch} "
            "for this task and leave the primary alone."
        )
    return lines


def main() -> None:
    for line in status_lines(Path.cwd()):
        print(line, file=sys.stderr)


if __name__ == "__main__":
    main()
