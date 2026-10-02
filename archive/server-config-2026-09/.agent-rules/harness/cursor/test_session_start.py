"""Cursor sessionStart includes the dirty-primary worktree advisory."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "session-start.py"


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True
    )


def _dirty_primary(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    _git(["init", "-b", "master"], repo)
    _git(["config", "user.name", "Test User"], repo)
    _git(["config", "user.email", "test@example.com"], repo)
    (repo / "file.txt").write_text("initial")
    _git(["add", "file.txt"], repo)
    _git(["commit", "-m", "initial"], repo)
    _git(["remote", "add", "origin", str(repo)], repo)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True, check=True
    ).stdout.strip()
    _git(["update-ref", "refs/remotes/origin/master", sha], repo)
    _git(
        ["symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/master"],
        repo,
    )
    (repo / "dirty.txt").write_text("uncommitted")
    return repo


class TestSessionStartDirtyPrimary(unittest.TestCase):
    def test_additional_context_advises_worktree_and_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            home.mkdir()
            repo = _dirty_primary(Path(tmp))
            env = os.environ.copy()
            env["HOME"] = str(home)
            proc = subprocess.run(
                [sys.executable, str(SCRIPT)],
                input=json.dumps({"cwd": str(repo), "session_id": "test-session"}),
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(proc.returncode, 0)
            payload = json.loads(proc.stdout)
            context = payload.get("additional_context", "")
            self.assertIn("dirty: yes", context)
            self.assertIn("cwd: primary checkout", context)
            self.assertIn("git worktree add", context)
            self.assertIn("origin/master", context)
            self.assertIn("leave the primary alone", context)
            log = (home / ".cursor" / "session-start.log").read_text(encoding="utf-8")
            self.assertIn("test-session", log)
            self.assertIn("git worktree add", log)


if __name__ == "__main__":
    unittest.main()
