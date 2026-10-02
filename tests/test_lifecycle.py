import json
import os
from pathlib import Path
import subprocess
import sys
import time
import threading
from unittest.mock import patch

from agentctl import compute, runner, sandbox, worker_profile
from agentctl.common import Refused, execute, home, write_json
from test_runner import GitFixture, protocol


class LifecycleTests(GitFixture):
    def test_pilot_excludes_bad_target_then_selects_eligible(self):
        p = protocol()
        p["candidates"].append({"name": "too-cheap", "parameters": {"quality": 0.1, "cost": 0.01}})
        p["preflight_seconds"] = 30
        result = runner.launch(runner.prepare(self.spec(kind="compute", seconds=45, compute=p)), attended=True)
        self.assertEqual(result["status"], "succeeded", result.get("reason"))
        self.assertEqual(result["compute_evidence"]["selected_candidate"], "fast")

    def test_failed_confirmation_never_promotes(self):
        p = protocol()
        stage = self.repository / "stage.py"
        stage.write_text(stage.read_text().replace("float(sys.argv[2])", "(0.2 if p.name.startswith('confirmation') else float(sys.argv[2]))"))
        result = runner.launch(runner.prepare(self.spec(kind="compute", seconds=40, compute=p, changes=["stage.py"])), attended=True)
        self.assertEqual(result["status"], "needs_attention")
        self.assertFalse(any(Path(result["output"]).glob("full-*")))

    def test_reuse_valid_evidence_and_invalidate_selected_code(self):
        first = runner.launch(runner.prepare(self.spec(kind="compute", seconds=40, compute=protocol())), attended=True)
        second = runner.launch(runner.prepare(self.spec(kind="compute", seconds=40, compute=protocol(), reuse_evidence=first["id"])), attended=True)
        self.assertEqual(second["status"], "succeeded", second.get("reason"))
        self.assertEqual(second["compute_evidence"]["reused_from"], first["id"])
        self.assertFalse(any(Path(second["output"]).glob("smoke-*")))
        (self.repository / "source.txt").write_text("relevant change\n")
        third = runner.launch(runner.prepare(self.spec(kind="compute", seconds=40, compute=protocol(), changes=["source.txt"], reuse_evidence=first["id"])), attended=True)
        self.assertEqual(third["status"], "needs_attention")
        self.assertIn("stale", third["reason"])
        self.assertFalse(any(Path(third["output"]).glob("full-*")))

    def test_input_manifest_changes_invalidate_reuse(self):
        manifest = self.root / "manifest.json"
        manifest.write_text('{"input":"first"}')
        p = protocol()
        p["fingerprint_files"] = [str(manifest)]
        first = runner.launch(runner.prepare(self.spec(kind="compute", seconds=40, compute=p, changes=["stage.py"])), attended=True)
        manifest.write_text('{"input":"changed"}')
        second = runner.launch(runner.prepare(self.spec(kind="compute", seconds=40, compute=p, reuse_evidence=first["id"])), attended=True)
        self.assertEqual(second["status"], "needs_attention")
        self.assertIn("stale", second["reason"])

    def test_live_cancel_preserves_checkpoint(self):
        record = runner.prepare(self.spec(seconds=20, argv=[sys.executable, "-c", "import pathlib,time; pathlib.Path('checkpoint').write_text('saved'); time.sleep(15)"]))
        supervisor = threading.Thread(target=runner.supervise, args=(record["id"],), kwargs={"attended": True})
        supervisor.start()
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and not Path(record["workspace"], "checkpoint").exists():
            time.sleep(0.1)
        self.assertTrue(Path(record["workspace"], "checkpoint").exists(), runner.status(record["id"]))
        runner.cancel(record["id"])
        while time.monotonic() < deadline and runner.status(record["id"])["status"] == "running":
            time.sleep(0.1)
        supervisor.join(timeout=5)
        self.assertFalse(supervisor.is_alive())
        self.assertEqual(runner.status(record["id"])["status"], "cancelled")
        self.assertEqual(Path(record["workspace"], "checkpoint").read_text(), "saved")

    def test_saved_oauth_profile_excludes_external_tools_and_api_keys(self):
        source = self.root / "codex"
        source.mkdir()
        write_json(source / "auth.json", {"auth_mode": "chatgpt", "OPENAI_API_KEY": "must-not-copy", "tokens": {"access_token": "fixture-token"}})
        (source / "config.toml").write_text('model = "chosen-native-model"\n[mcp_servers.external]\ncommand = "unsafe"\n')
        record = runner.prepare(self.spec(kind="agent", harness="codex", prompt="fixture", checks=[[sys.executable, "-c", "pass"]]))
        with patch.dict(os.environ, {"CODEX_HOME": str(source)}):
            environment, target = worker_profile.codex(record)
        profile = Path(environment["CODEX_HOME"])
        self.assertNotIn("OPENAI_API_KEY", json.loads((profile / "auth.json").read_text()))
        text = (profile / "config.toml").read_text()
        self.assertIn('model = "chosen-native-model"', text)
        self.assertNotIn("mcp_servers", text)
        self.assertIn("apps = false", text)
        self.assertIn(str(profile / "hooks.json"), record["protected"])

    def test_api_key_only_profile_refused(self):
        source = self.root / "codex"
        source.mkdir()
        write_json(source / "auth.json", {"auth_mode": "apikey", "OPENAI_API_KEY": "fixture"})
        record = runner.prepare(self.spec(kind="agent", harness="codex", prompt="fixture", checks=[[sys.executable, "-c", "pass"]]))
        with patch.dict(os.environ, {"CODEX_HOME": str(source)}), self.assertRaises(Refused):
            worker_profile.codex(record)

    def test_pointstream_case_insensitive_restriction(self):
        project = self.root / "PointStream"
        self.repository.rename(project)
        self.repository = project
        with self.assertRaises(Refused):
            runner.prepare(self.spec(kind="agent", harness="codex", prompt="do work", checks=[[sys.executable, "-c", "pass"]]))

    def test_native_session_recovered_on_failure_no_fallback(self):
        record = runner.prepare(self.spec(kind="agent", harness="codex", prompt="fixture", checks=[[sys.executable, "-c", "pass"]]))
        def fail(record, *args, **kwargs):
            Path(record["log"]).write_text('{"type":"thread.started","thread_id":"native-fixture-id"}\n')
            raise Refused("quota exhausted")
        with patch("agentctl.harnesses.command", return_value=[sys.executable, "-c", "pass"]), patch("agentctl.runner.run_process", side_effect=fail):
            runner.supervise(record["id"], attended=True)
        result = runner.load(record["id"])
        self.assertEqual(result["status"], "needs_attention")
        self.assertEqual(result["native_session"], "native-fixture-id")
        self.assertEqual(result["spec"]["harness"], "codex")

    def test_publication_is_idempotent_and_no_merge(self):
        record = runner.prepare(self.spec())
        calls = []
        def command(argv, **kwargs):
            calls.append(argv)
            if argv[:3] == ["gh", "pr", "list"]:
                return b'[{"url":"https://github.com/example/repo/pull/1"}]'
            if "rev-parse" in argv:
                return b"revision\n"
            return b""
        record["origin"] = "https://github.com/example/repo.git"
        with patch("agentctl.runner.execute", side_effect=command):
            runner.publish(record)
            runner.publish(record)
        self.assertFalse(any("create" in argv or "merge" in argv for argv in calls))
        self.assertEqual(record["pull_request"], "https://github.com/example/repo/pull/1")

    def test_memory_counts_descendants_across_sessions(self):
        rows = ["100 1 12", "101 100 20", "102 101 30", "200 1 900"]
        self.assertEqual(runner.descendant_rss(100, rows), 62)

    def test_git_metadata_symlink_refuses_parent_execution(self):
        record = runner.prepare(self.spec())
        index = Path(record["workspace"]) / ".git" / "index"
        index.unlink()
        victim = self.root / "user-owned-index"
        victim.write_text("preserve")
        index.symlink_to(victim)
        with self.assertRaisesRegex(Refused, "symlink"):
            runner.trusted_git(record)
        self.assertEqual(victim.read_text(), "preserve")

    def test_pointstream_alias_cannot_bypass_project_restriction(self):
        execute(["git", "remote", "add", "origin", "https://example.invalid/owner/PointStream.git"], cwd=self.repository)
        with self.assertRaisesRegex(Refused, "prohibits"):
            runner.prepare(self.spec(kind="agent", harness="codex", prompt="do work", checks=[[sys.executable, "-c", "pass"]]))

    def test_outputs_and_recovery_are_outside_ephemeral_runtime(self):
        result = runner.launch(runner.prepare(self.spec()), attended=True)
        self.assertEqual(result["status"], "succeeded", result.get("recovery_error"))
        self.assertFalse(Path(result["output"]).is_relative_to(self.root / "runtime"))
        self.assertTrue((Path(result["recovery"]) / "snapshot.bundle").is_file())
        self.assertTrue((Path(result["recovery"]) / "task.json").is_file())

    def test_unverified_mac_process_lifetime_blocks_unattended_workers(self):
        if sys.platform != "darwin":
            self.skipTest("Darwin lifetime admission")
        record = runner.prepare(self.spec())
        runner.supervise(record["id"])
        result = runner.load(record["id"])
        self.assertEqual(result["status"], "needs_attention")
        self.assertIn("lifetime", result["reason"])

    def test_project_features_cannot_reenable_external_tools(self):
        source = self.root / "codex"
        source.mkdir()
        write_json(source / "auth.json", {"auth_mode":"chatgpt", "tokens":{"access_token":"fixture"}})
        record = runner.prepare(self.spec(kind="agent", harness="codex", prompt="fixture", checks=[[sys.executable,"-c","pass"]]))
        configuration = Path(record["workspace"]) / ".codex/config.toml"
        configuration.parent.mkdir()
        configuration.write_text('[features]\napps = true\n')
        with patch.dict(os.environ, {"CODEX_HOME":str(source)}), self.assertRaisesRegex(Refused,"external"):
            worker_profile.codex(record)
