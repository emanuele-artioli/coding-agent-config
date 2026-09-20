#!/usr/bin/env python3
"""Tests for the deterministic close-out core; every queue is temporary."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


_SPEC = importlib.util.spec_from_file_location(
    "closeout", Path(__file__).resolve().parent / "closeout.py"
)
closeout = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(closeout)


class CloseoutCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "state"
        self.addCleanup(self.tmp.cleanup)

    def capture(self, *args: object, **kwargs: object) -> closeout.CloseoutResult:
        return closeout.closeout(self.root, *args, **kwargs)

    def receipt(self, result: closeout.CloseoutResult) -> dict[str, object]:
        return json.loads(result.receipt_path.read_text())

    def candidate(self, candidate_id: str) -> Path:
        return self.root / "candidates" / "open" / "project" / f"promote-{candidate_id}.md"


class TestBoundaries(CloseoutCase):
    def test_explicit_session_handoff_and_completed_report_record_lessons(self) -> None:
        first = self.capture(
            "session-1", "session", "completed",
            [{"candidate_id": "same-lesson", "summary": "A repeat"}],
            event_id="event-1", when="2026-09-20",
        )
        self.assertEqual(first.status, "completed")
        self.assertEqual(first.observations[0].status, "recorded")
        self.assertEqual(self.receipt(first)["kind"], "session")

        handoff = self.capture(
            "handoff-1", "handoff", "pending",
            [{"candidate_id": "same-lesson"}],
            event_id="event-2", when="2026-09-20",
        )
        report = self.capture(
            "report-1", "report", "completed",
            [{"candidate_id": "same-lesson"}],
            event_id="event-3", when="2026-09-20",
        )
        self.assertEqual(handoff.status, "completed")
        self.assertEqual(report.status, "completed")
        text = self.candidate("same-lesson").read_text()
        self.assertIn("occurrences: 3", text)
        self.assertEqual(text.count("lessons-event:"), 3)

    def test_progress_and_question_are_explicit_ignored_boundaries(self) -> None:
        for kind in ("progress", "question"):
            result = self.capture(
                f"{kind}-1", kind, "in_progress",
                [{"candidate_id": f"must-not-record-{kind}", "summary": "Ignored"}],
                when="2026-09-20",
            )
            self.assertEqual(result.status, "ignored")
            self.assertFalse(result.captured)
            self.assertTrue(result.no_lessons)
            self.assertFalse((self.root / "candidates").exists())
            self.assertEqual(self.receipt(result)["reason"],
                             "explicit progress/question or incomplete report boundary")

    def test_completed_boundary_with_no_lessons_has_an_explicit_receipt(self) -> None:
        result = self.capture("empty-1", "session", "completed", when="2026-09-20")
        self.assertEqual(result.status, "completed")
        self.assertTrue(result.no_lessons)
        receipt = self.receipt(result)
        self.assertTrue(receipt["no_lessons"])
        self.assertEqual(receipt["observations"], [])
        self.assertTrue(result.receipt_path.parent.name == "receipts")
        self.assertFalse(result.receipt_path.is_relative_to(self.root / "candidates"))


class TestReplayAndRecovery(CloseoutCase):
    def test_same_event_replays_without_mutation_and_independent_event_is_preserved(self) -> None:
        first = self.capture(
            "boundary", "session", "completed",
            [{"candidate_id": "lesson", "summary": "Repeat"}],
            event_id="event-1", when="2026-09-20",
        )
        before = first.receipt_path.read_text()
        replay = self.capture(
            "boundary", "session", "completed",
            [{"candidate_id": "lesson", "summary": "Repeat"}],
            event_id="event-1", when="2026-09-20",
        )
        self.assertTrue(replay.replay)
        self.assertEqual(before, replay.receipt_path.read_text())
        independent = self.capture(
            "boundary", "session", "completed",
            [{"candidate_id": "lesson", "summary": "Repeat"}],
            event_id="event-2", when="2026-09-20",
        )
        self.assertFalse(independent.replay)
        text = self.candidate("lesson").read_text()
        self.assertIn("occurrences: 2", text)
        self.assertEqual(text.count("lessons-event:"), 2)

    def test_candidate_mutation_failure_is_pending_and_retry_is_idempotent(self) -> None:
        real = closeout._record_observation
        calls = 0

        def record_then_fail(root: Path, item: object) -> object:
            nonlocal calls
            calls += 1
            result = real(root, item)
            if calls == 1:
                raise OSError("interrupted after ledger write")
            return result

        with mock.patch.object(closeout, "_record_observation", side_effect=record_then_fail):
            failed = self.capture(
                "retry", "session", "completed",
                [{"candidate_id": "ledger-once", "summary": "Retry me"}],
                event_id="event-retry", when="2026-09-20",
            )
        self.assertEqual(failed.status, "pending")
        self.assertEqual(self.receipt(failed)["status"], "pending")
        retried = self.capture(
            "retry", "session", "completed",
            [{"candidate_id": "ledger-once", "summary": "Retry me"}],
            event_id="event-retry", when="2026-09-20",
        )
        self.assertEqual(retried.status, "completed")
        self.assertEqual(retried.observations[0].status, "already_recorded")
        text = self.candidate("ledger-once").read_text()
        self.assertIn("occurrences: 1", text)
        self.assertEqual(text.count("lessons-event:"), 1)

    def test_receipt_checkpoint_failure_is_reconciled_without_double_counting(self) -> None:
        real_write = closeout._write_json
        writes = 0

        def write_then_fail(path: Path, document: object) -> None:
            nonlocal writes
            writes += 1
            real_write(path, document)
            if writes == 2:  # after the first ledger observation checkpoint
                raise OSError("interrupted receipt checkpoint")

        with mock.patch.object(closeout, "_write_json", side_effect=write_then_fail):
            failed = self.capture(
                "receipt-retry", "session", "completed",
                [{"candidate_id": "receipt-once", "summary": "Retry receipt"}],
                event_id="event-receipt", when="2026-09-20",
            )
        self.assertEqual(failed.status, "pending")
        retried = self.capture(
            "receipt-retry", "session", "completed",
            [{"candidate_id": "receipt-once", "summary": "Retry receipt"}],
            event_id="event-receipt", when="2026-09-20",
        )
        self.assertEqual(retried.status, "completed")
        self.assertIn("occurrences: 1", self.candidate("receipt-once").read_text())


class TestCLI(CloseoutCase):
    def test_cli_accepts_json_observation_and_documents_exit_status(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = closeout.main([
                "--root", str(self.root), "--boundary-id", "cli-boundary",
                "--event-id", "cli-event", "--kind", "session", "--state", "completed",
                "--date", "2026-09-20", "--observation",
                json.dumps({"candidate_id": "cli-lesson", "summary": "CLI lesson"}),
            ])
        self.assertEqual(code, 0, output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["status"], "completed")


if __name__ == "__main__":
    unittest.main()
