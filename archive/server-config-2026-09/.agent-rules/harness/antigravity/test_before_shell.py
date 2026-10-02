"""Unit tests for antigravity before-shell.py."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "before-shell.py"

DENIED_COMMANDS = [
    "git push --force",
    "git push --force-with-lease",
    "git push --delete origin old-branch",
    "git clean -fd",
]

ALLOWED_COMMANDS = [
    'git commit -m "a test commit"',
    "git push -u origin feature/x",
    "git merge --ff-only feature/x",
    "git reset --hard HEAD~1",
    "git branch -D local-branch",
    'git commit -m "do not run git push --force on main"',
]

HEREDOC_ALLOWED = """cat > doc.md <<'EOF'
git push --force origin main
git clean -fd
EOF
"""

HEREDOC_DENIED = HEREDOC_ALLOWED + "\ngit push --force origin main"



def _run_guard(payload: dict) -> tuple[int, dict, str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    stdout_json = {}
    if proc.stdout.strip():
        try:
            stdout_json = json.loads(proc.stdout)
        except json.JSONDecodeError:
            pass
    return proc.returncode, stdout_json, proc.stderr


class TestBeforeShell(unittest.TestCase):
    def test_denied_commands_protojson(self):
        for command in DENIED_COMMANDS:
            with self.subTest(command=command):
                payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": command}}}
                code, out, stderr = _run_guard(payload)
                self.assertNotEqual(code, 0, f"Expected non-zero exit for {command}")
                self.assertEqual(out.get("decision"), "deny", f"Expected decision=deny for {command}, got {out}")
                self.assertTrue(out.get("reason"), "Expected reason in output JSON")
                self.assertTrue(stderr, "Expected stderr explanation")

    def test_allowed_commands_protojson(self):
        for command in ALLOWED_COMMANDS:
            with self.subTest(command=command):
                payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": command}}}
                code, out, stderr = _run_guard(payload)
                self.assertEqual(code, 0, f"Expected zero exit for {command}, stderr: {stderr}")
                self.assertEqual(out.get("decision"), "allow", f"Expected decision=allow for {command}, got {out}")

    def test_heredoc_body_is_allowed(self):
        payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": HEREDOC_ALLOWED}}}
        code, out, stderr = _run_guard(payload)
        self.assertEqual(code, 0, f"Expected heredoc to be allowed, stderr: {stderr}")
        self.assertEqual(out.get("decision"), "allow")

    def test_real_command_after_heredoc_is_denied(self):
        payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": HEREDOC_DENIED}}}
        code, out, stderr = _run_guard(payload)
        self.assertNotEqual(code, 0)
        self.assertEqual(out.get("decision"), "deny")

    def test_commit_message_mentioning_denied_command(self):
        payload = {
            "toolCall": {
                "name": "run_command",
                "args": {"CommandLine": 'git commit -m "avoid git push --force and git clean -fd"'},
            }
        }
        code, out, stderr = _run_guard(payload)
        self.assertEqual(code, 0, f"Commit message false positive: {stderr}")
        self.assertEqual(out.get("decision"), "allow")

    def test_legacy_flat_payload(self):
        payload = {"CommandLine": "git push --force"}
        code, out, stderr = _run_guard(payload)
        self.assertNotEqual(code, 0)
        self.assertEqual(out.get("decision"), "deny")


if __name__ == "__main__":
    unittest.main()
