"""Unit tests for SessionStart repo-status lines.

Behaviour
1. Dirty primary on the default branch advises `git worktree add` from origin/default
2. That call does not create a worktree and does not change HEAD
3. Clean primary on the default branch lists state and does not advise a worktree
4. Clean primary off the default branch still advises a worktree
5. Dirty linked worktree is not treated as the primary
6. Other worktrees are listed

Plausible misuse
7. cwd None / not a git directory → no lines (fail-open)

Deliberately not testing
- Adapter JSON dialects (thin wrappers; Cursor additional_context is covered
  in harness/cursor/test_session_start.py)
- Missing git binary / git timeouts
- origin/HEAD unset beyond master/main fallback
"""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent / "session-status.py"
_SPEC = importlib.util.spec_from_file_location("session_status", _SCRIPT)
_mod = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_mod)
status_lines = _mod.status_lines
inspect_repo = _mod.inspect_repo


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True
    )


def _make_primary(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    _git(["init", "-b", "master"], cwd=repo)
    _git(["config", "user.name", "Test User"], cwd=repo)
    _git(["config", "user.email", "test@example.com"], cwd=repo)
    (repo / "file.txt").write_text("initial")
    _git(["add", "file.txt"], cwd=repo)
    _git(["commit", "-m", "initial"], cwd=repo)
    _git(["remote", "add", "origin", str(repo)], cwd=repo)
    sha = _git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()
    _git(["update-ref", "refs/remotes/origin/master", sha], cwd=repo)
    _git(
        ["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/master"],
        cwd=repo,
    )
    return repo


class TestSessionStatus(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.primary = _make_primary(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _blob(self, cwd: Path) -> str:
        return "\n".join(status_lines(cwd))

    def test_dirty_primary_advises_worktree_add(self) -> None:
        (self.primary / "dirty.txt").write_text("uncommitted")
        text = self._blob(self.primary)
        self.assertIn("branch: master", text)
        self.assertIn("dirty: yes", text)
        self.assertIn("cwd: primary checkout", text)
        self.assertIn("git worktree add", text)
        self.assertIn("origin/master", text)
        self.assertIn("leave the primary alone", text)
        self.assertIn("Do not checkout another branch on this primary", text)

    def test_dirty_primary_does_not_create_or_checkout(self) -> None:
        (self.primary / "dirty.txt").write_text("uncommitted")
        before = _git(["worktree", "list", "--porcelain"], cwd=self.primary).stdout
        head = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=self.primary).stdout.strip()
        status_lines(self.primary)
        after = _git(["worktree", "list", "--porcelain"], cwd=self.primary).stdout
        self.assertEqual(after, before)
        self.assertEqual(
            _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=self.primary).stdout.strip(),
            head,
        )
        self.assertEqual(head, "master")
        state = inspect_repo(self.primary)
        self.assertIsNotNone(state)
        self.assertTrue(state.advise_worktree)

    def test_clean_primary_on_default_does_not_advise(self) -> None:
        text = self._blob(self.primary)
        self.assertIn("branch: master", text)
        self.assertIn("dirty: no", text)
        self.assertIn("cwd: primary checkout", text)
        self.assertIn("other worktrees: none", text)
        self.assertNotIn("git worktree add", text)
        self.assertNotIn("leave the primary alone", text)

    def test_clean_primary_off_default_advises(self) -> None:
        _git(["checkout", "-b", "task-branch"], cwd=self.primary)
        text = self._blob(self.primary)
        self.assertIn("branch: task-branch", text)
        self.assertIn("dirty: no", text)
        self.assertIn("not on origin/master", text)
        self.assertIn("git worktree add", text)
        self.assertIn("leave the primary alone", text)

    def test_dirty_linked_worktree_is_not_primary(self) -> None:
        _git(["branch", "feat", "master"], cwd=self.primary)
        linked = self.root / "linked"
        _git(["worktree", "add", str(linked), "feat"], cwd=self.primary)
        (linked / "extra.txt").write_text("dirty in the linked tree")
        text = self._blob(linked)
        self.assertIn("cwd: linked worktree", text)
        self.assertIn("dirty: yes", text)
        self.assertNotIn("git worktree add", text)
        self.assertNotIn("leave the primary alone", text)
        self.assertIn(str(self.primary.resolve()), text)

    def test_other_worktrees_listed_from_primary(self) -> None:
        _git(["branch", "feat", "master"], cwd=self.primary)
        linked = self.root / "linked"
        _git(["worktree", "add", str(linked), "feat"], cwd=self.primary)
        text = self._blob(self.primary)
        listed = text.split("other worktrees:", 1)[1].splitlines()[0]
        self.assertIn(str(linked.resolve()), listed)
        self.assertNotIn("none", listed)

    def test_missing_cwd_is_silent(self) -> None:
        self.assertEqual(status_lines(None), [])

    def test_non_git_directory_is_silent(self) -> None:
        empty = self.root / "not-a-repo"
        empty.mkdir()
        self.assertEqual(status_lines(empty), [])


if __name__ == "__main__":
    unittest.main()
