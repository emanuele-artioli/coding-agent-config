#!/usr/bin/env python3
"""Claude model-family adapter must no-op on Cursor-shaped payloads."""

from __future__ import annotations

import importlib.util
import io
import json
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "guard_model_family", ROOT / "guard-model-family.py"
)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def _run(payload: dict) -> str:
    stdin = io.StringIO(json.dumps(payload))
    stdout = io.StringIO()
    with mock.patch.object(mod.sys, "stdin", stdin), mock.patch.object(
        mod.sys, "stdout", stdout
    ), mock.patch.object(mod.sys, "exit", side_effect=SystemExit):
        try:
            mod.main()
        except SystemExit:
            pass
    return stdout.getvalue()


class GuardModelFamilyCursorImport(unittest.TestCase):
    def test_cursor_payload_does_not_deny_grok(self) -> None:
        payload = {
            "hook_event_name": "preToolUse",
            "cursor_version": "1.0.0",
            "tool_name": "Task",
            "tool_input": {"model": "cursor-grok-4.6-high"},
        }
        self.assertEqual(_run(payload).strip(), "")

    def test_claude_payload_still_denies_grok(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Task",
            "tool_input": {"model": "cursor-grok-4.6-high"},
        }
        out = json.loads(_run(payload))
        self.assertEqual(
            out["hookSpecificOutput"]["permissionDecision"],
            "deny",
        )

    def test_is_cursor_payload_helpers(self) -> None:
        self.assertTrue(mod._is_cursor_payload({"cursor_version": "1.0.0"}))
        self.assertTrue(mod._is_cursor_payload({"hook_event_name": "subagentStart"}))
        self.assertFalse(mod._is_cursor_payload({"hook_event_name": "PreToolUse"}))


if __name__ == "__main__":
    unittest.main()
