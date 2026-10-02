import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

from agentctl import compute, runner, sandbox, transport
from agentctl.cli import collect
from agentctl.common import Refused, execute, home, write_json
from test_config import Isolated


def protocol():
    stages = {}
    for name in ("smoke", "pilot", "confirmation", "full"):
        stages[name] = {"argv": [sys.executable, "stage.py", "{output}", "{quality}", "{cost}"],
                        "seconds": 5, "entrypoint": "stage.py", "production_path": True, "metrics_file": "metrics.json"}
    return {"targets": {"quality": {"min": 0.8}}, "representative_input": "real-fixture-v1", "runtime_environment": "python-fixture-v1",
            "hardware": "CPU", "preflight_seconds": 25, "confirmation_required": True,
            "candidates": [{"name": "slow", "parameters": {"quality": 0.9, "cost": 4}},
                           {"name": "fast", "parameters": {"quality": 0.85, "cost": 1}}], "stages": stages}


class ComputeTests(Isolated):
    def test_budget_target_entrypoint_and_confirmation_validation(self):
        self.assertEqual(compute.validate(protocol(), 40), ["smoke", "pilot", "confirmation", "full"])
        for edit in (lambda p: p.update(preflight_seconds=1), lambda p: p["stages"]["pilot"].update(entrypoint="mock.py"),
                     lambda p: p["stages"]["smoke"].update(mock=True), lambda p: p.update(confirmation_required=False),
                     lambda p: p["targets"]["quality"].update(min=float("nan"))):
            p = protocol()
            edit(p)
            with self.assertRaises(Refused):
                compute.validate(p, 40)

    def test_reduced_quality_pilot_cannot_promote_different_full_configuration(self):
        p = protocol()
        p["stages"]["pilot"]["argv"][3] = "0.1"
        with self.assertRaisesRegex(Refused, "production arguments"):
            compute.validate(p, 40)

    def test_missing_nonfinite_out_of_bounds_metrics(self):
        path = self.root / "metrics.json"
        for observed in ({"valid": True, "metrics": {}, "cost": 1}, {"valid": True, "metrics": {"quality": float("nan")}, "cost": 1},
                         {"valid": True, "metrics": {"quality": 0.3}, "cost": 1}, {"valid": False, "metrics": {"quality": 0.9}, "cost": 1}):
            path.write_text(json.dumps(observed))
            with self.assertRaises(Refused):
                compute.metrics(path, protocol()["targets"])

    def test_stale_or_failed_evidence_cannot_promote(self):
        evidence = {"fingerprint": "a", "selected_candidate": "fast", "stages": {"smoke": {"passed": True}, "pilot": {"passed": True}, "confirmation": {"passed": True}}}
        compute.admissible(evidence, "a", ["smoke", "pilot", "confirmation", "full"])
        with self.assertRaises(Refused):
            compute.admissible(evidence, "changed", ["smoke", "pilot", "full"])
        evidence["stages"]["confirmation"]["passed"] = False
        with self.assertRaises(Refused):
            compute.admissible(evidence, "a", ["smoke", "pilot", "confirmation", "full"])


class GitFixture(Isolated):
    def setUp(self):
        super().setUp()
        self.repository = self.root / "repo"
        self.repository.mkdir()
        execute(["git", "init", "-b", "main"], cwd=self.repository)
        execute(["git", "config", "user.name", "Fixture"], cwd=self.repository)
        execute(["git", "config", "user.email", "fixture@example.invalid"], cwd=self.repository)
        (self.repository / "source.txt").write_text("initial\n")
        (self.repository / "stage.py").write_text('import json,pathlib,sys\np=pathlib.Path(sys.argv[1]); p.mkdir(exist_ok=True)\n(p/"metrics.json").write_text(json.dumps({"valid":True,"metrics":{"quality":float(sys.argv[2])},"cost":float(sys.argv[3])}))\n')
        execute(["git", "add", "source.txt", "stage.py"], cwd=self.repository)
        execute(["git", "commit", "-m", "fixture"], cwd=self.repository)

    def spec(self, **extra):
        return {"kind": "command", "repo": str(self.repository), "seconds": 15,
                "resources": {"cpu_threads": 1, "memory_mb": 2048}, "argv": [sys.executable, "-c", "print('done')"], **extra}


class RunnerTests(GitFixture):
    def test_snapshot_only_selected_changes_and_original_untouched(self):
        (self.repository / "source.txt").write_text("unfinished edit\n")
        (self.repository / "private.txt").write_text("excluded\n")
        (self.repository / "selected.txt").write_text("included\n")
        record = runner.prepare(self.spec(changes=["source.txt", "selected.txt"]))
        workspace = Path(record["workspace"])
        self.assertEqual((workspace / "source.txt").read_text(), "unfinished edit\n")
        self.assertEqual((workspace / "selected.txt").read_text(), "included\n")
        self.assertFalse((workspace / "private.txt").exists())
        self.assertEqual((self.repository / "source.txt").read_text(), "unfinished edit\n")
        record["status"] = "needs_attention"
        runner.save(record)
        collected = collect(record["id"], self.root / "collected")
        self.assertTrue(Path(collected["collected"]).joinpath("untracked/selected.txt").exists())

    def test_attended_command_checks_and_collection(self):
        record = runner.prepare(self.spec(checks=[[sys.executable, "-c", "assert 2+2==4"]]))
        result = runner.launch(record, attended=True)
        self.assertEqual(result["status"], "succeeded", result)
        self.assertTrue(result["checks"][0]["passed"])
        self.assertIn("done", Path(result["log"]).read_text())
        with self.assertRaises(Refused):
            runner.prepare(self.spec(), task=record["id"])

    def test_missing_sandbox_blocks_unattended(self):
        record = runner.prepare(self.spec())
        with patch("agentctl.sandbox.probe", return_value={"verified": False, "detail": "unavailable"}):
            runner.supervise(record["id"])
        result = runner.load(record["id"])
        self.assertEqual(result["status"], "needs_attention")
        self.assertFalse(Path(result["log"]).exists())

    def test_compute_selects_cheapest_eligible_and_records_evidence(self):
        record = runner.prepare(self.spec(kind="compute", seconds=40, compute=protocol()))
        result = runner.launch(record, attended=True)
        self.assertEqual(result["status"], "succeeded", result.get("reason"))
        self.assertEqual(result["compute_evidence"]["selected_candidate"], "fast")
        self.assertTrue(Path(result["output"], "full-fast", "metrics.json").exists())

    def test_failed_smoke_never_starts_full(self):
        p = protocol()
        stage = self.repository / "stage.py"
        stage.write_text(stage.read_text() + "\nif p.name.startswith('smoke'): raise SystemExit(1)\n")
        record = runner.prepare(self.spec(kind="compute", seconds=40, compute=p, changes=["stage.py"]))
        result = runner.launch(record, attended=True)
        self.assertEqual(result["status"], "needs_attention")
        self.assertFalse(any(Path(result["output"]).glob("full-*")))

    def test_command_budget_exhaustion_preserves_files(self):
        record = runner.prepare(self.spec(seconds=0.2, argv=[sys.executable, "-c", "import pathlib,time; pathlib.Path('checkpoint').write_text('saved'); time.sleep(20)"]))
        result = runner.launch(record, attended=True)
        self.assertEqual(result["status"], "needs_attention")
        self.assertIn("budget exhausted", result["reason"])
        self.assertEqual(Path(result["workspace"], "checkpoint").read_text(), "saved")

    def test_gpu_paid_and_long_job_bypass_denied(self):
        for spec in (self.spec(seconds=8000), self.spec(paid_compute=True), self.spec(resources={"cpu_threads": 1, "memory_mb": 2048, "gpu_uuid": "GPU-test", "gpu_memory_mb": 100})):
            with self.assertRaises(Refused):
                runner.validate_spec(spec)

    def test_python_write_to_protected_path_denied_by_real_sandbox(self):
        verification = sandbox.probe()
        if not verification.get("filesystem_verified", verification["verified"]):
            self.skipTest("OS sandbox unavailable in this test environment: " + verification.get("detail", ""))
        outside = self.root / "evidence"
        outside.write_text("keep")
        record = runner.prepare(self.spec(read_only=[str(outside)], argv=[sys.executable, "-c", f"from pathlib import Path; Path({str(outside)!r}).write_text('lost')"]))
        command = sandbox.wrap(record["spec"]["argv"], [record["workspace"]], [outside], readable=[sys.prefix, record["workspace"], outside])
        result = subprocess.run(command, capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        runner.supervise(record["id"])
        self.assertEqual(outside.read_text(), "keep")
        self.assertEqual(runner.load(record["id"])["status"], "needs_attention")

    def test_lost_supervisor_unknown_and_no_stale_pid_cancel(self):
        record = runner.prepare(self.spec())
        record["status"] = "running"
        record["supervisor_pid"] = os.getpid()
        runner.save(record)
        self.assertEqual(runner.status(record["id"])["status"], "unknown")
        with self.assertRaises(Refused):
            runner.cancel(record["id"])

    def test_transport_disconnect_keeps_inspectable_task_id(self):
        with patch("agentctl.transport.remote", side_effect=Refused("disconnected")):
            result = transport.dispatch("gpu1", self.spec())
        self.assertEqual(result["status"], "unknown")
        self.assertEqual(transport.routed_host(result["id"]), "gpu1")
