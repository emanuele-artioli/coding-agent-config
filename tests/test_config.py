import base64
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agentctl.common import Refused
from agentctl import install, policy, transport


class Isolated(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.environment = patch.dict(os.environ, {"AGENTCTL_HOME": str(self.root / "control"), "AGENTCTL_RUNTIME": str(self.root / "runtime")})
        self.environment.start()
        # Native discovery overrides belong to the test, never the host profile.
        for name in ("CODEX_HOME", "CLAUDE_CONFIG_DIR", "CURSOR_CONFIG_DIR"):
            os.environ.pop(name, None)

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()


class InstallerTests(Isolated):
    def test_effective_codex_configuration_directory(self):
        custom = self.root / "custom-codex"
        with patch.dict(os.environ, {"CODEX_HOME": str(custom)}):
            changes = install.plan_install(base=self.root / "user", harnesses=["codex"])
        self.assertIn(str(custom / "config.toml"), changes)
        self.assertIn(str(custom / "AGENTS.md"), changes)
        self.assertFalse(any("/user/.codex/" in path for path in changes))

    def test_effective_claude_configuration_directory(self):
        custom = self.root / "custom-claude"
        with patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(custom)}):
            changes = install.plan_install(base=self.root / "user", harnesses=["claude"])
        self.assertIn(str(custom / "CLAUDE.md"), changes)
        self.assertIn(str(custom / "settings.json"), changes)
        self.assertFalse(any("/user/.claude/" in path for path in changes))

    def test_preserves_native_config_and_rolls_back_exactly(self):
        base = self.root / "user"
        config = base / ".codex/config.toml"
        config.parent.mkdir(parents=True)
        original = '# custom\nmodel = "native-choice"\napproval_policy = "never"\nsandbox_mode = "danger-full-access"\n[plugins.custom]\nenabled = true\n'
        config.write_text(original)
        changes = install.plan_install(base=base, harnesses=["codex"])
        preview = install.install(changes, dry_run=True)
        self.assertTrue(preview["changes"])
        self.assertEqual(config.read_text(), original)
        applied = install.install(changes)
        self.assertIn('model = "native-choice"', config.read_text())
        self.assertIn('sandbox_mode = "workspace-write"', config.read_text())
        self.assertIn('[plugins.custom]', config.read_text())
        self.assertEqual(install.install(install.plan_install(base=base, harnesses=["codex"]))["changes"], [])
        install.rollback(applied["transaction"])
        self.assertEqual(config.read_text(), original)
        self.assertFalse((base / ".codex/AGENTS.md").exists())

    def test_conflict_never_overwrites_user_edits(self):
        base = self.root / "user"
        applied = install.install(install.plan_install(base=base, harnesses=["claude"]))
        instructions = base / ".claude/CLAUDE.md"
        instructions.write_text(instructions.read_text() + "human edit\n")
        with self.assertRaises(Refused):
            install.install(install.plan_install(base=base, harnesses=["claude"]))
        with self.assertRaises(Refused):
            install.rollback(applied["transaction"])
        self.assertTrue(instructions.read_text().endswith("human edit\n"))

    def test_project_shim_and_cursor_rule_preserve_existing_guidance(self):
        base, project = self.root / "user", self.root / "project"
        project.mkdir()
        (project / "AGENTS.md").write_text("project scientific protocol\n")
        (project / "CLAUDE.md").write_text("existing special constraint\n")
        install.install(install.plan_install(base, project, harnesses=["claude", "cursor", "antigravity"]))
        self.assertIn("@AGENTS.md", (project / "CLAUDE.md").read_text())
        self.assertIn("existing special constraint", (project / "CLAUDE.md").read_text())
        self.assertTrue((project / ".cursor/rules/agentctl.mdc").read_text().startswith("---\nalwaysApply: true"))
        hooks = json.loads((base / ".gemini/config/hooks.json").read_text())
        self.assertIn("PreToolUse", hooks["agentctl"])

    def test_existing_hooks_preserved_legacy_retired_only_on_request(self):
        data = {"hooks": {"PreToolUse": [{"hooks": [{"command": "user-check"}, {"command": "python /home/user/.agent-rules/guard.py"}]}]}, "model": "custom"}
        entry = {"hooks": [{"command": "python -m agentctl hook codex"}]}
        result = install.merge_hooks(data, "PreToolUse", entry, True)
        self.assertEqual(result["hooks"]["PreToolUse"][0]["hooks"], [{"command": "user-check"}])
        self.assertEqual(result["model"], "custom")

    def test_unmanaged_skill_and_symlink_conflicts(self):
        base = self.root / "user"
        target = base / ".agents/skills/remote-work/SKILL.md"
        target.parent.mkdir(parents=True)
        target.write_text("---\nname: remote-work\n---\nMy different workflow")
        with self.assertRaises(Refused):
            install.install(install.plan_install(base, harnesses=["codex"]))
        target.unlink()
        (base / ".codex").mkdir()
        (base / ".codex/AGENTS.md").symlink_to(self.root / "elsewhere")
        with self.assertRaises(Refused):
            install.plan_install(base, harnesses=["codex"])


class ProtectionTests(Isolated):
    def test_recursive_symlink_targets_and_discovery_bound(self):
        root = self.root / "raw"
        root.mkdir()
        external = self.root / "external"
        external.mkdir()
        evidence = self.root / "evidence.txt"
        evidence.write_text("preserve")
        (root / "external").symlink_to(external, target_is_directory=True)
        (external / "evidence").symlink_to(evidence)
        roots = policy.expand_protected([root])
        self.assertIn(str(external), roots)
        self.assertIn(str(evidence), roots)
        with self.assertRaises(Refused):
            policy.inspect("Edit", {"file_path":str(evidence)}, str(self.root), roots)
        with self.assertRaisesRegex(Refused,"bound"):
            policy.expand_protected([root], max_entries=0)

    def setUp(self):
        super().setUp()
        self.work = self.root / "project"
        self.saved = self.work / "outputs/run-1"
        self.saved.mkdir(parents=True)
        (self.work / "alias").symlink_to(self.saved)

    def test_descendant_absolute_ancestor_and_symlink_deletions(self):
        for path in ("outputs/run-1/data", str(self.saved / "data"), "outputs", "alias/data"):
            with self.subTest(path=path), self.assertRaises(Refused):
                policy.inspect("Bash", {"command": "rm -rf " + path}, str(self.work), [str(self.saved)])
        policy.inspect("Bash", {"command": "cat outputs/run-1/result.json"}, str(self.work), [str(self.saved)])

    def test_dirty_git_destruction_and_integration(self):
        for command in ("git reset --hard", "git -C repo reset --hard HEAD", "git clean -fd", "git push --force-with-lease", "git push origin :main", "gh pr merge 12"):
            with self.subTest(command=command), self.assertRaises(Refused):
                policy.inspect("exec_command", {"cmd": command}, str(self.work))
        policy.inspect("exec_command", {"cmd": "git diff"}, str(self.work))

    def test_native_edits_and_opaque_mcp_fail_closed(self):
        for name, args in (("Write", {"file_path": str(self.saved / "result")}), ("write_to_file", {"TargetFile": str(self.saved / "result")}), ("apply_patch", {"patch": "*** Delete File: outputs/run-1/result"})):
            with self.subTest(tool=name), self.assertRaises(Refused):
                policy.inspect(name, args, str(self.work), [str(self.saved)])
        with self.assertRaises(Refused):
            policy.inspect("mcp__external__delete", {}, str(self.work))

    def test_malformed_hook_denied_in_all_dialects(self):
        policy_file = self.root / "policy.json"
        policy_file.write_text('{"protected_paths": []}')
        for harness in ("codex", "claude", "cursor", "antigravity"):
            with patch("sys.stdin", io.StringIO("{invalid")), patch("sys.stdout", new_callable=io.StringIO) as output:
                self.assertEqual(policy.hook(harness, policy_file), 2)
                result = json.loads(output.getvalue())
                self.assertIn("deny", json.dumps(result))

    def test_antigravity_real_payload(self):
        policy_file = self.root / "policy.json"
        policy_file.write_text(json.dumps({"protected_paths": [str(self.saved)]}))
        payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": "rm -rf outputs", "Cwd": str(self.work)}}, "workspacePaths": [str(self.work)]}
        with patch("sys.stdin", io.StringIO(json.dumps(payload))), patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(policy.hook("antigravity", policy_file), 2)
            self.assertEqual(json.loads(output.getvalue())["decision"], "deny")

    def test_archive_rejects_path_escape(self):
        import tarfile
        archive_data = io.BytesIO()
        with tarfile.open(fileobj=archive_data, mode="w:gz") as archive:
            info = tarfile.TarInfo("../escape")
            info.size = 3
            archive.addfile(info, io.BytesIO(b"bad"))
        with self.assertRaises(Refused):
            transport.extract(archive_data.getvalue(), self.root / "received")
        self.assertFalse((self.root / "escape").exists())
