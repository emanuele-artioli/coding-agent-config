#!/usr/bin/env python3
"""Smoke tests for install.py: portable-core validation and Codex agent TOML."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INSTALL = ROOT / "install.py"


def _load_install():
    spec = importlib.util.spec_from_file_location("cac_install", INSTALL)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["cac_install"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_validate_plugin_ok() -> None:
    mod = _load_install()
    rows = mod.validate_plugin()
    problems = [f"{label}: {status}" for label, status in rows if mod._plugin_row_is_problem(status)]
    assert not problems, "portable core invalid:\n  " + "\n  ".join(problems)
    labels = {label for label, _ in rows}
    assert "plugin.json $schema" in labels
    assert "plugin.json name" in labels
    assert any(label.startswith("skills/") for label in labels)


def test_load_catalog_from_mcp_json() -> None:
    mod = _load_install()
    catalog = mod.load_catalog()
    assert catalog == {}


AGENT_FIXTURE = """---
name: tiny-probe
description: A "quoted" one-line description.
model: opus
---

Body line one, with a backslash \\ and a quote ".

- bullet
"""


class CodexAgentTomlTest(unittest.TestCase):
    """render_codex_agent() must emit the five keys Codex needs."""

    def setUp(self) -> None:
        self.mod = _load_install()

    def _render(self, stem: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            agent = Path(tmp) / f"{stem}.agent.md"
            agent.write_text(AGENT_FIXTURE, encoding="utf-8")
            return self.mod.render_codex_agent(agent, self.mod.codex_rungs())

    def test_five_keys_present(self) -> None:
        text = self._render("tiny-probe")
        keys = [
            line.split(" = ", 1)[0]
            for line in text.splitlines()
            if " = " in line and not line.startswith("#") and not line.startswith(" ")
        ]
        self.assertEqual(
            keys,
            [
                "name",
                "description",
                "developer_instructions",
                "model",
                "model_reasoning_effort",
            ],
        )
        self.assertIn('name = "tiny-probe"', text)
        self.assertIn('\\"quoted\\"', text)
        self.assertIn("developer_instructions = \"\"\"", text)
        self.assertIn("Body line one", text)
        self.assertNotIn("---", text.split("developer_instructions", 1)[1])

    def test_rung_selection(self) -> None:
        rungs = self.mod.codex_rungs()
        junior = rungs.get("junior", {})
        escalation = rungs.get("escalation", {})
        self.assertIn(f'model = "{junior.get("model", "")}"', self._render("tiny-probe"))
        stuck = self._render("stuck-escalation")
        self.assertIn(f'model = "{escalation.get("model", "")}"', stuck)
        self.assertIn(
            f'model_reasoning_effort = "{escalation.get("effort", "")}"', stuck
        )


if __name__ == "__main__":
    test_validate_plugin_ok()
    test_load_catalog_from_mcp_json()
    unittest.main(argv=[sys.argv[0]], exit=False)
    print("ok")
