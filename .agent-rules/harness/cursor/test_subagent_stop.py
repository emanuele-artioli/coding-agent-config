"""Unit tests for cursor subagent-stop.py."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "subagent-stop.py"

LONG_PROMPT = (
    "1. Goal. Stop claiming a live Cursor report-contract. "
    "subagentStop fires but the native payload has no child-final-text "
    "field, so the adapter must stay silent unless a real final-text "
    "field appears. Check the pending-verification item with the "
    "2026-09-20 / wave 0.1 evidence. Add a test that a payload with "
    "only task produces no advisory. Read first. Only these files. "
    "Allowed paths. Write only the adapter, its test, the contract "
    "docstring, and the pending-verification item. Do not invent a "
    "workaround that treats task as the child's last message."
)

BROKEN_REPORT = "\n".join([
    "## Result: PASS",
    "I finished the work and the check passed.",
])


def _run_adapter(payload: dict, home: Path) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


class TestSubagentStop(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.home = Path(self._tmpdir.name)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_task_only_payload_produces_no_advisory(self):
        code, stdout, stderr = _run_adapter({"task": LONG_PROMPT}, self.home)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout), {})
        self.assertNotIn("Report contract", stderr)

    def test_broken_last_assistant_message_prints_advisory(self):
        code, stdout, stderr = _run_adapter(
            {"last_assistant_message": BROKEN_REPORT},
            self.home,
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout), {})
        self.assertIn("Report contract", stderr)


if __name__ == "__main__":
    unittest.main()
