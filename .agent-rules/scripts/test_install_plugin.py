#!/usr/bin/env python3
"""Smoke tests for install.py: portable-core validation and Codex agent TOML."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 is unsupported here.
    tomllib = None  # type: ignore[assignment]

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
rung: junior
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
            rung = "escalation" if stem == "stuck-escalation" else "junior"
            agent.write_text(
                AGENT_FIXTURE.replace("rung: junior", f"rung: {rung}"),
                encoding="utf-8",
            )
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

    def test_luna_max_metadata_is_current_and_validated(self) -> None:
        rungs = self.mod.codex_rungs()
        self.assertEqual(
            (rungs["junior"]["model"], rungs["junior"]["effort"]),
            ("gpt-5.6-luna", "max"),
        )
        self.assertEqual(
            (rungs["escalation"]["model"], rungs["escalation"]["effort"]),
            ("gpt-5.6-astra", "low"),
        )
        self.assertEqual(self.mod.validate_codex_rungs(rungs), [])

    def test_stale_model_metadata_is_rejected(self) -> None:
        rungs = self.mod.codex_rungs()
        stale = {
            key: value.copy() if isinstance(value, dict) else value
            for key, value in rungs.items()
        }
        stale["junior"]["effort"] = "xhigh"
        issues = self.mod.validate_codex_rungs(stale)
        self.assertTrue(any("junior.effort" in issue for issue in issues))
        with tempfile.TemporaryDirectory() as tmp:
            agent = Path(tmp) / "tiny-probe.agent.md"
            agent.write_text(AGENT_FIXTURE, encoding="utf-8")
            with self.assertRaises(ValueError):
                self.mod.render_codex_agent(agent, stale)

    def test_claude_only_controls_are_omitted_with_diagnostics(self) -> None:
        text = self._render("tiny-probe")
        parsed = tomllib.loads(text) if tomllib is not None else {}
        for field in ("tools", "omitClaudeMd", "maxTurns"):
            self.assertNotIn(field, parsed)
            self.assertIn(field, text)
        self.assertIn("source model/effort are overridden", text)

    def test_invalid_source_rung_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agent = Path(tmp) / "tiny-probe.agent.md"
            agent.write_text(
                AGENT_FIXTURE.replace("rung: junior", "rung: unknown"),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                self.mod.render_codex_agent(agent, self.mod.codex_rungs())

    def test_all_shared_roles_render_as_owned_native_toml(self) -> None:
        if tomllib is None:
            self.skipTest("tomllib is unavailable")
        rendered = self.mod.codex_agent_files()
        self.assertEqual(len(rendered), 7)
        rungs = self.mod.codex_rungs()
        for destination, text in rendered:
            parsed = tomllib.loads(text)
            stem = destination.stem
            rung = "escalation" if stem == "stuck-escalation" else "junior"
            self.assertEqual(parsed["model"], rungs[rung]["model"])
            self.assertEqual(
                parsed["model_reasoning_effort"], rungs[rung]["effort"]
            )
            self.assertEqual(self.mod._codex_ownership(text), "managed")
            self.assertNotIn("tools =", text)
            self.assertNotIn("omitClaudeMd =", text)
            self.assertNotIn("maxTurns =", text)

    def test_quotes_backslashes_parse_as_toml(self) -> None:
        if tomllib is None:
            self.skipTest("tomllib is unavailable")
        text = self._render("tiny-probe")
        parsed = tomllib.loads(text)
        self.assertEqual(parsed["name"], "tiny-probe")
        self.assertIn('backslash \\ and a quote "', parsed["developer_instructions"])


class CodexInstallerSafetyTest(unittest.TestCase):
    """Ownership and filesystem behavior for generated Codex artifacts."""

    def setUp(self) -> None:
        self.mod = _load_install()
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.host = root / "host"
        self.host.mkdir()
        self.agents = self.host / "agents"
        self.agents.mkdir()
        self.codex_home = root / "codex"
        self.codex_home.mkdir()
        self.mod.HOST = self.host
        self.mod.HOME = root / "home"
        self.mod.CODEX_HOME = self.codex_home
        self.mod.CODEX_HOME_SET = True
        self.mod.AGENTS = self.agents
        self.mod.HOST_RULES = self.host / "AGENTS.md"
        self.mod.HOST_RULES.write_text("portable host rules\n", encoding="utf-8")
        self.mod.CODEX_HOST_RULES = self.host / "generated" / "codex-AGENTS.md"
        self.mod.CODEX_HOST_RULES.parent.mkdir()
        self.mod.CODEX_HOST_RULES.write_text("rules with `../relative`\n", encoding="utf-8")
        self.agent = self.agents / "tiny-probe.agent.md"
        self.agent.write_text(AGENT_FIXTURE, encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _destinations(self) -> list[tuple[Path, str]]:
        return self.mod.codex_host_rules_file() + self.mod.codex_agent_files()

    def test_unowned_files_are_conflicts_and_unchanged(self) -> None:
        for dest, _ in self._destinations():
            dest.parent.mkdir(parents=True, exist_ok=True)
            original = "user-owned content\n"
            dest.write_text(original, encoding="utf-8")
        result = self.mod.apply_codex_agents(check=False)
        self.assertTrue(result)
        self.assertTrue(all(status == "conflict" for _, status in result))
        for dest, _ in self._destinations():
            self.assertEqual(dest.read_text(encoding="utf-8"), "user-owned content\n")

    def test_created_noop_and_modified_managed_file(self) -> None:
        first = self.mod.apply_codex_agents(check=False)
        self.assertTrue(all(status == "created" for _, status in first))
        desired = {dest: content for dest, content in self._destinations()}
        second = self.mod.apply_codex_agents(check=False)
        self.assertTrue(all(status == "ok" for _, status in second))
        for dest, content in desired.items():
            self.assertEqual(dest.read_text(encoding="utf-8"), content)
            dest.write_text(content + "user edit\n", encoding="utf-8")
        result = self.mod.apply_codex_agents(check=False)
        self.assertTrue(all(status == "conflict" for _, status in result))
        for dest, content in desired.items():
            self.assertEqual(dest.read_text(encoding="utf-8"), content + "user edit\n")

    def test_stale_managed_artifact_updates(self) -> None:
        self.mod.apply_codex_agents(check=False)
        self.agent.write_text(AGENT_FIXTURE.replace("Body line one", "Body line two"), encoding="utf-8")
        result = self.mod.apply_codex_agents(check=False)
        statuses = dict(result)
        self.assertEqual(statuses["Codex agent tiny-probe.toml"], "updated")
        expected = dict(self._destinations())[self.codex_home / "agents" / "tiny-probe.toml"]
        self.assertEqual(
            (self.codex_home / "agents" / "tiny-probe.toml").read_text(encoding="utf-8"),
            expected,
        )

    def test_legacy_file_is_preserved_unless_identical(self) -> None:
        for dest, content in self._destinations():
            dest.parent.mkdir(parents=True, exist_ok=True)
            legacy = content.replace(
                self.mod.CODEX_OWNER_MARKER + "\n", "", 1
            ).replace(
                next(line for line in content.splitlines() if line.startswith(self.mod.CODEX_DIGEST_PREFIX)) + "\n",
                "",
                1,
            )
            dest.write_text(legacy + "legacy change\n", encoding="utf-8")
        result = self.mod.apply_codex_agents(check=False)
        self.assertTrue(all(status == "conflict" for _, status in result))

    def test_known_symlink_is_retired_but_unknown_is_preserved(self) -> None:
        role_dest = self.codex_home / "agents" / "tiny-probe.toml"
        role_dest.parent.mkdir(parents=True, exist_ok=True)
        role_dest.symlink_to(self.agent)
        unknown_target = self.host / "unrelated.md"
        unknown_target.write_text("unrelated\n", encoding="utf-8")
        rules_dest = self.codex_home / "AGENTS.md"
        rules_dest.symlink_to(unknown_target)
        result = dict(self.mod.apply_codex_agents(check=False))
        self.assertEqual(result["Codex agent tiny-probe.toml"], "updated")
        self.assertTrue(role_dest.is_file())
        self.assertFalse(role_dest.is_symlink())
        self.assertEqual(result["Codex host rules AGENTS.md"], "conflict")
        self.assertTrue(rules_dest.is_symlink())
        self.assertEqual(rules_dest.resolve(), unknown_target.resolve())

    def test_check_does_not_create_parents_or_change_symlinks(self) -> None:
        self.codex_home = self.mod.CODEX_HOME
        self.mod.CODEX_HOME = Path(self.tmp.name) / "check-codex"
        self.mod.CODEX_HOME.mkdir()
        self.mod.CODEX_HOST_RULES = self.host / "missing-generated-rules"
        role_dest = self.mod.CODEX_HOME / "agents" / "tiny-probe.toml"
        result = dict(self.mod.apply_codex_agents(check=True))
        self.assertEqual(result["Codex agent tiny-probe.toml"], "missing")
        self.assertFalse(role_dest.parent.exists())

    def test_host_overlay_absent_keeps_portable_link_plan(self) -> None:
        self.mod.CODEX_HOST_RULES = self.host / "does-not-exist"
        entries = self.mod.codex_host_rules_file()
        self.assertEqual(entries, [])
        rules = [item for item in self.mod.plan() if item.link == self.mod.CODEX_HOME / "AGENTS.md"]
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].target, self.mod.HOST_RULES)



if __name__ == "__main__":
    test_validate_plugin_ok()
    test_load_catalog_from_mcp_json()
    unittest.main(argv=[sys.argv[0]], exit=False)
    print("ok")
