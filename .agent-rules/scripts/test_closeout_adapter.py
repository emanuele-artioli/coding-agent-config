"""Fixture tests for the four fail-open lifecycle adapters.

These tests exercise only explicit JSON boundary fields.  A normal Stop is
intentionally indistinguishable from an ordinary turn to the closeout layer.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import closeout_adapter as adapter


HARNESS_FIXTURES = ("claude", "cursor", "antigravity", "codex")


class CloseoutAdapterCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "operational-state"
        self.addCleanup(self.tmp.cleanup)

    def tearDown(self) -> None:
        # The adapter must never use a tracked project rules directory as its
        # default destination in these tests.
        self.assertFalse((self.root / ".agent-rules").exists())

    def capture(self, payload: object, harness: str) -> adapter.CaptureResult:
        return adapter.capture_payload(payload, harness, state_root=self.root)

    def boundary(
        self,
        harness: str,
        kind: str,
        suffix: str,
        *,
        observations: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        return {
            "session_id": f"{harness}-session-{suffix}",
            "closeout": {
                "boundary_kind": kind,
                "boundary_id": f"{harness}-boundary-{suffix}",
                "event_id": f"{harness}-event-{suffix}",
                "observations": observations or [],
            },
        }


class ExplicitBoundaryFixtures(CloseoutAdapterCase):
    def test_each_harness_accepts_explicit_end_handoff_report_blocked_and_no_lessons(self) -> None:
        for harness in HARNESS_FIXTURES:
            with self.subTest(harness=harness):
                end = self.capture(
                    {
                        "end_of_session": True,
                        "session_id": f"{harness}-end-session",
                        "observations": [
                            {
                                "candidate_id": f"{harness}-end-lesson",
                                "summary": "An explicit closeout observation",
                            }
                        ],
                    },
                    harness,
                )
                self.assertIsNotNone(end.event)
                assert end.event is not None
                self.assertEqual(end.event.boundary_kind, "completed_session")
                self.assertTrue(end.captured)

                handoff = self.capture(self.boundary(harness, "handoff", "handoff"), harness)
                report = self.capture(self.boundary(harness, "completed_report", "report"), harness)
                blocked = self.capture(self.boundary(harness, "blocked_transfer", "blocked"), harness)
                no_lessons = self.capture(self.boundary(harness, "no_lessons", "empty"), harness)
                self.assertEqual(handoff.event.boundary_kind, "handoff")  # type: ignore[union-attr]
                self.assertEqual(report.event.boundary_kind, "completed_report")  # type: ignore[union-attr]
                self.assertEqual(blocked.event.boundary_kind, "blocked_transfer")  # type: ignore[union-attr]
                self.assertEqual(no_lessons.event.boundary_kind, "no_lessons")  # type: ignore[union-attr]
                self.assertTrue(no_lessons.result.no_lessons)  # type: ignore[union-attr]

        receipts = list((self.root / ".closeout" / "receipts").glob("*.json"))
        # Five explicit boundaries per harness, with no ignored/no-op receipt.
        self.assertEqual(len(receipts), 5 * len(HARNESS_FIXTURES))

    def test_cursor_observation_inherits_harness_platform(self) -> None:
        result = self.capture(
            {
                "end_of_session": True,
                "session_id": "cursor-platform-session",
                "observations": [
                    {
                        "candidate_id": "cursor-platform-lesson",
                        "axis": "platform",
                        "summary": "Cursor closeout must not default to Codex",
                    }
                ],
            },
            "cursor",
        )
        self.assertTrue(result.captured)
        assert result.event is not None
        self.assertEqual(result.event.platform, "cursor")
        receipt = json.loads(result.result.receipt_path.read_text())  # type: ignore[union-attr]
        self.assertEqual(receipt["observations"][0]["platform"], "cursor")
        candidate = self.root / "candidates" / "open" / "platform" / "promote-cursor-platform-lesson.md"
        self.assertIn('source_platform: "cursor"', candidate.read_text())

    def test_explicit_end_flag_needs_stable_identity(self) -> None:
        result = self.capture({"end_of_session": True}, "codex")
        self.assertTrue(result.skipped)
        self.assertIn("missing stable boundary/event identity", result.diagnostics[0])
        self.assertFalse(self.root.exists())


class NoOpFixtures(CloseoutAdapterCase):
    def test_ordinary_child_progress_question_reentry_and_malformed_payloads_do_nothing(self) -> None:
        payloads: tuple[object, ...] = (
            {},
            {"session_id": "ordinary-stop"},
            {"session_id": "child", "report_type": "child", "state": "completed"},
            {"session_id": "progress", "boundary_kind": "progress", "boundary_id": "p"},
            {"session_id": "question", "boundary_kind": "question", "boundary_id": "q"},
            {"session_id": "approval", "awaiting_approval": True},
            {"session_id": "reentry", "stop_hook_active": True, "end_of_session": True},
            "{ malformed json",
            None,
        )
        for harness in HARNESS_FIXTURES:
            for payload in payloads:
                with self.subTest(harness=harness, payload=payload):
                    result = self.capture(payload, harness)
                    self.assertTrue(result.skipped)
                    self.assertFalse(result.captured)
                    self.assertIsNone(result.event)
        self.assertFalse(self.root.exists())

    def test_unsupported_kind_and_malformed_observations_are_diagnostic_no_ops(self) -> None:
        unsupported = self.capture(
            {"boundary_kind": "harness_claimed_event", "boundary_id": "bad"}, "cursor"
        )
        malformed = self.capture(
            {
                "boundary_kind": "completed_session",
                "boundary_id": "bad-observations",
                "observations": {"candidate_id": "not-a-list"},
            },
            "cursor",
        )
        self.assertIn("unsupported boundary kind", unsupported.diagnostics[0])
        self.assertIn("observations must be a JSON list", malformed.diagnostics[0])
        self.assertFalse(self.root.exists())


class ReplayAndConcurrency(CloseoutAdapterCase):
    def test_replay_uses_core_identity_without_a_second_occurrence(self) -> None:
        payload = self.boundary(
            "codex",
            "completed_session",
            "replay",
            observations=[{"candidate_id": "same-lesson", "summary": "Repeat once"}],
        )
        first = self.capture(payload, "codex")
        replay = self.capture(payload, "codex")
        self.assertTrue(first.captured)
        self.assertTrue(replay.replay)
        candidate = self.root / "candidates" / "open" / "project" / "promote-same-lesson.md"
        self.assertIn("occurrences: 1", candidate.read_text())
        self.assertEqual(candidate.read_text().count("lessons-event:"), 1)

    def test_concurrent_same_hook_event_is_harmless(self) -> None:
        payload = self.boundary(
            "cursor",
            "completed_session",
            "concurrent",
            observations=[{"candidate_id": "concurrent-lesson", "summary": "One event"}],
        )
        with ThreadPoolExecutor(max_workers=6) as pool:
            results = list(pool.map(lambda _: self.capture(payload, "cursor"), range(6)))
        self.assertEqual(sum(result.captured for result in results), 6)
        self.assertEqual(sum(result.replay for result in results), 5)
        candidate = self.root / "candidates" / "open" / "project" / "promote-concurrent-lesson.md"
        self.assertIn("occurrences: 1", candidate.read_text())


class FailOpenAndConfiguration(CloseoutAdapterCase):
    def test_core_exception_is_reported_and_never_raised(self) -> None:
        payload = self.boundary("claude", "completed_session", "exception")
        with mock.patch.object(adapter._core, "closeout", side_effect=RuntimeError("storage offline")):
            result = self.capture(payload, "claude")
        self.assertTrue(result.skipped)
        self.assertIn("adapter exception (RuntimeError)", result.diagnostics[0])
        self.assertFalse(self.root.exists())

    def test_explicit_environment_root_is_operational_and_separate_from_project_rules(self) -> None:
        payload = self.boundary("antigravity", "no_lessons", "configured")
        with mock.patch.dict("os.environ", {"CLOSEOUT_STATE_ROOT": str(self.root)}, clear=False):
            result = adapter.capture_payload(payload, "antigravity")
        self.assertTrue(result.captured)
        self.assertTrue((self.root / ".closeout" / "receipts").is_dir())
        self.assertFalse((self.root / ".agent-rules").exists())


if __name__ == "__main__":
    unittest.main()
