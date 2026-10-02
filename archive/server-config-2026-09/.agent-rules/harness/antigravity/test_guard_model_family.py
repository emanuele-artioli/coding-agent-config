"""Unit tests for antigravity guard-model-family.py."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "guard-model-family.py"


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


class TestGuardModelFamily(unittest.TestCase):
    def test_default_omit_model_allowed(self):
        # Subagent spawn without explicit model should allow (inherits parent Gemini session)
        payload = {
            "toolCall": {
                "name": "invoke_subagent",
                "args": {
                    "Subagents": [
                        {"TypeName": "budget-default", "Role": "Worker"}
                    ]
                },
            }
        }
        code, out, stderr = _run_guard(payload)
        self.assertEqual(code, 0, f"Expected code 0 for omitted model, got {code} (stderr: {stderr})")
        self.assertEqual(out.get("decision"), "allow")

    def test_in_family_model_allowed(self):
        in_family_models = ["flash", "flash_lite", "pro", "gemini-2.5-flash", "gemini-3.8-flash"]
        for model in in_family_models:
            with self.subTest(model=model):
                payload = {
                    "toolCall": {
                        "name": "invoke_subagent",
                        "args": {
                            "Subagents": [
                                {"TypeName": "worker", "Model": model}
                            ]
                        },
                    }
                }
                code, out, stderr = _run_guard(payload)
                self.assertEqual(code, 0, f"Expected code 0 for in-family {model}, got {code} (stderr: {stderr})")
                self.assertEqual(out.get("decision"), "allow")

    def test_off_family_model_denied(self):
        off_family_models = ["claude-sonnet-5", "gpt-4o", "opus", "cursor-grok-4.5"]
        for model in off_family_models:
            with self.subTest(model=model):
                payload = {
                    "toolCall": {
                        "name": "invoke_subagent",
                        "args": {
                            "Subagents": [
                                {"TypeName": "worker", "Model": model}
                            ]
                        },
                    }
                }
                code, out, stderr = _run_guard(payload)
                self.assertEqual(code, 2, f"Expected code 2 for off-family {model}, got {code}")
                self.assertEqual(out.get("decision"), "deny")
                self.assertTrue(out.get("reason"))
                self.assertTrue(stderr)

    def test_non_spawn_tool_allowed(self):
        payload = {
            "toolCall": {
                "name": "view_file",
                "args": {"AbsolutePath": "/tmp/test.txt"},
            }
        }
        code, out, stderr = _run_guard(payload)
        self.assertEqual(code, 0)
        self.assertEqual(out.get("decision"), "allow")


if __name__ == "__main__":
    unittest.main()
