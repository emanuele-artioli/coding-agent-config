#!/usr/bin/env python3
"""Unit tests for scripts/lessons.py — temp queues only, never the real one."""

from __future__ import annotations

import importlib.util
import io
import contextlib
import concurrent.futures
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

_SPEC = importlib.util.spec_from_file_location(
    "lessons", Path(__file__).resolve().parent / "lessons.py"
)
lessons = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(lessons)


FULL = """---
id: 2026-08-03-process-count-checks-match-their-own-command
created: 2026-08-03
axis: platform
status: applied
summary: A pgrep/ps/pkill from a harness Bash call matches the call's own command line - a count reads wrong, and a pkill -f kills its own shell
occurrences: 2
keywords: [pgrep, pkill, self-match, process, harness]
---

Body text.
"""

# No occurrences:, no keywords: — the shape of all 18 files already in done/.
LEGACY = """---
id: 2026-07-31-torch-sqlite3-cxxabi-import-order
created: 2026-07-31
axis: project
status: applied
summary: On this host import torch before import sqlite3 breaks sqlite3 (CXXABI_1.3.15)
---

Body text.
"""

OPEN_ONE = """---
id: 2026-09-10-open-example
created: 2026-09-10
axis: project
status: open
summary: An unrelated open candidate about paper markers and figures
---

Body.
"""


class QueueCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "candidates"
        (self.root / "open" / "project").mkdir(parents=True)
        (self.root / "open" / "platform").mkdir(parents=True)
        (self.root / "done").mkdir(parents=True)
        (self.root / "done" / "2026-08-03-process-count-checks-match-their-own-command.md").write_text(FULL)
        (self.root / "done" / "2026-07-31-torch-sqlite3-cxxabi-import-order.md").write_text(LEGACY)
        (self.root / "open" / "project" / "2026-09-10-open-example.md").write_text(OPEN_ONE)
        self.addCleanup(self.tmp.cleanup)

    def run_cli(self, *argv: str) -> str:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = lessons.main(["--root", str(self.root), *argv])
        self.assertEqual(code, 0, buf.getvalue())
        return buf.getvalue()

    def add_candidate(
        self,
        ident: str,
        *,
        axis: str = "project",
        status: str = "open",
        occurrences: int | None = 1,
        summary: str = "A repeated test symptom",
        directory: str = "done",
        filename: str | None = None,
    ) -> Path:
        path = self.root / directory
        if directory == "open":
            path /= axis
        path.mkdir(parents=True, exist_ok=True)
        destination = path / (filename or f"{ident}.md")
        count = "" if occurrences is None else f"occurrences: {occurrences}\n"
        destination.write_text(
            "---\n"
            f"id: {ident}\n"
            "created: 2026-09-19\n"
            f"axis: {axis}\n"
            f"status: {status}\n"
            f"summary: {summary}\n"
            f"{count}"
            "---\n\nBody.\n"
        )
        return destination

    def record(self, ident: str, event: str, **extra: str) -> tuple[int, str]:
        args = ["--root", str(self.root), "record", ident, "--event-id", event]
        for key, value in extra.items():
            args.extend([f"--{key.replace('_', '-')}", value])
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = lessons.main(args)
        return code, out.getvalue() + err.getvalue()


class TestList(QueueCase):
    def test_lists_open_and_done(self) -> None:
        out = self.run_cli("list")
        self.assertIn("2026-09-10-open-example", out)
        self.assertIn("2026-07-31-torch-sqlite3-cxxabi-import-order", out)
        self.assertEqual(len(out.strip().splitlines()), 3)

    def test_missing_fields_tolerated(self) -> None:
        entries = {e.id: e for e in lessons.load(self.root)}
        legacy = entries["2026-07-31-torch-sqlite3-cxxabi-import-order"]
        self.assertEqual(legacy.occurrences, 1)  # absent occurrences: -> 1
        self.assertIn("sqlite3", legacy.keywords)  # keywords derived from slug
        self.assertEqual(legacy.where, "done")


class TestMatch(QueueCase):
    def test_restated_summary_ranks_the_right_file_first(self) -> None:
        out = self.run_cli(
            "match", "pgrep count check matched its own command line"
        )
        first = [ln for ln in out.splitlines() if ln.startswith("  [")][0]
        self.assertIn("process-count-checks-match-their-own-command", first)

    def test_full_list_appended_while_corpus_is_small(self) -> None:
        out = self.run_cli("match", "pgrep self match")
        self.assertIn("All 3 candidates:", out)

    def test_no_overlap_says_so(self) -> None:
        out = self.run_cli("match", "zzz qqq wwww")
        self.assertIn("No keyword overlap", out)


class TestRecord(QueueCase):
    def test_moves_done_file_back_to_open_and_bumps(self) -> None:
        self.run_cli(
            "record",
            "2026-08-03-process-count-checks-match-their-own-command",
            "--project", "/home/itec/emanuele/presley",
            "--platform", "claude",
            "--date", "2026-09-19",
        )
        old = self.root / "done" / "2026-08-03-process-count-checks-match-their-own-command.md"
        new = (
            self.root / "open" / "platform"
            / "promote-2026-08-03-process-count-checks-match-their-own-command.md"
        )
        self.assertFalse(old.exists())
        self.assertTrue(new.exists())
        text = new.read_text()
        self.assertIn("status: recurring", text)
        self.assertIn("occurrences: 3", text)
        self.assertIn("## Occurrence 3, 2026-09-19, /home/itec/emanuele/presley (claude)", text)
        self.assertNotIn("status: applied", text)

    def test_legacy_file_gains_occurrences_field(self) -> None:
        self.run_cli(
            "record", "2026-07-31-torch-sqlite3-cxxabi-import-order",
            "--date", "2026-09-19",
        )
        new = (
            self.root / "open" / "project"
            / "promote-2026-07-31-torch-sqlite3-cxxabi-import-order.md"
        )
        text = new.read_text()
        self.assertIn("occurrences: 2", text)
        self.assertIn("## Occurrence 2, 2026-09-19", text)
        self.assertTrue(text.startswith("---\n"))

    def test_unknown_id_fails(self) -> None:
        code = lessons.main(["--root", str(self.root), "record", "nope"])
        self.assertEqual(code, 1)

    def test_first_observation_starts_at_one(self) -> None:
        ident = "2026-09-19-first-observation"
        self.add_candidate(ident, occurrences=0)
        code, output = self.record(ident, "capture-1")
        self.assertEqual(code, 0, output)
        destination = self.root / "open" / "project" / f"promote-{ident}.md"
        text = destination.read_text()
        self.assertIn("occurrences: 1", text)
        self.assertIn('recorded_events: ["capture-1"]', text)

    def test_same_event_is_a_true_noop_and_independent_event_survives(self) -> None:
        ident = "2026-09-19-idempotent-event"
        self.add_candidate(ident)
        code, first = self.record(ident, "capture-1")
        self.assertEqual(code, 0, first)
        destination = self.root / "open" / "project" / f"promote-{ident}.md"
        before = destination.read_text()
        code, replay = self.record(ident, "capture-1")
        self.assertEqual(code, 0, replay)
        self.assertIn("already recorded", replay)
        self.assertEqual(before, destination.read_text())
        code, independent = self.record(ident, "capture-2")
        self.assertEqual(code, 0, independent)
        text = destination.read_text()
        self.assertIn("occurrences: 3", text)
        self.assertEqual(text.count("lessons-event:"), 2)
        self.assertIn('"capture-1"', text)
        self.assertIn('"capture-2"', text)

    def test_prior_status_is_retained_for_reopened_entries(self) -> None:
        for status in ("applied", "discarded", "pending"):
            ident = f"2026-09-19-prior-{status}"
            self.add_candidate(ident, status=status)
            code, output = self.record(ident, f"capture-{status}")
            self.assertEqual(code, 0, output)
            destination = self.root / "open" / "project" / f"promote-{ident}.md"
            text = destination.read_text()
            self.assertIn(f'previous_status: "{status}"', text)
            self.assertIn(f'"{status}"', text.split("status_history:", 1)[1].split("\n", 1)[0])
            self.assertIn("status: recurring", text)

    def test_same_symptom_in_different_scopes_is_kept(self) -> None:
        project_id = "2026-09-19-scope-project"
        platform_id = "2026-09-19-scope-platform"
        self.add_candidate(project_id, axis="project", summary="same symptom")
        self.add_candidate(platform_id, axis="platform", summary="same symptom")
        self.assertEqual(self.record(project_id, "project-event")[0], 0)
        self.assertEqual(self.record(platform_id, "platform-event")[0], 0)
        self.assertTrue((self.root / "open" / "project" / f"promote-{project_id}.md").exists())
        self.assertTrue((self.root / "open" / "platform" / f"promote-{platform_id}.md").exists())

    def test_duplicate_ids_are_rejected(self) -> None:
        ident = "2026-09-19-duplicate-id"
        self.add_candidate(ident, filename=f"{ident}-one.md")
        self.add_candidate(ident, filename=f"{ident}-two.md")
        code, output = self.record(ident, "capture-duplicate")
        self.assertEqual(code, 1)
        self.assertIn("duplicate candidate id", output)
        self.assertFalse((self.root / "open" / "project" / f"promote-{ident}.md").exists())

    def test_invalid_axis_and_malformed_metadata_are_preserved(self) -> None:
        invalid = self.add_candidate("2026-09-19-invalid-axis")
        invalid.write_text(invalid.read_text().replace("axis: project", "axis: everywhere"))
        before_invalid = invalid.read_text()
        code, output = self.record("2026-09-19-invalid-axis", "capture-axis")
        self.assertEqual(code, 1)
        self.assertIn("invalid axis", output)
        self.assertEqual(before_invalid, invalid.read_text())

        malformed = self.root / "done" / "2026-09-19-malformed.md"
        malformed.write_text(
            "---\n"
            "id: 2026-09-19-malformed\n"
            "axis: project\n"
            "status: open\n"
            "occurrences: many\n"
            "summary: malformed count\n"
            "---\n\nBody.\n"
        )
        before_malformed = malformed.read_text()
        code, output = self.record("2026-09-19-malformed", "capture-malformed")
        self.assertEqual(code, 1)
        self.assertIn("not an integer", output)
        self.assertEqual(before_malformed, malformed.read_text())

    def test_concurrent_distinct_events_do_not_lose_an_update(self) -> None:
        ident = "2026-09-19-concurrent-events"
        self.add_candidate(ident)
        barrier = threading.Barrier(2)

        def run(event: str) -> tuple[int, str]:
            barrier.wait()
            return self.record(ident, event)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(run, ("concurrent-1", "concurrent-2")))
        self.assertEqual([code for code, _output in results], [0, 0])
        destination = self.root / "open" / "project" / f"promote-{ident}.md"
        text = destination.read_text()
        self.assertIn("occurrences: 3", text)
        self.assertIn('"concurrent-1"', text)
        self.assertIn('"concurrent-2"', text)

    def test_interrupted_replace_is_reconciled_on_retry(self) -> None:
        ident = "2026-09-19-interrupted-move"
        source = self.add_candidate(ident)
        destination = self.root / "open" / "project" / f"promote-{ident}.md"
        real_replace = lessons.os.replace
        failed = False

        def replace_then_fail(src: str, dst: Path) -> None:
            nonlocal failed
            real_replace(src, dst)
            if not failed:
                failed = True
                raise OSError("simulated interruption after rename")

        with mock.patch.object(lessons.os, "replace", replace_then_fail):
            code, output = self.record(ident, "interrupted-1")
        self.assertEqual(code, 1)
        self.assertTrue(source.exists())
        self.assertTrue(destination.exists())
        code, output = self.record(ident, "interrupted-1")
        self.assertEqual(code, 0, output)
        self.assertFalse(source.exists())
        self.assertEqual(destination.read_text().count("lessons-event:"), 1)
        self.assertIn("occurrences: 2", destination.read_text())

    def test_destination_collision_is_not_overwritten(self) -> None:
        ident = "2026-09-19-collision"
        source = self.add_candidate(ident)
        destination = self.root / "open" / "project" / f"promote-{ident}.md"
        destination.write_text(
            "---\n"
            "id: unrelated-candidate\n"
            "axis: project\n"
            "status: open\n"
            "summary: unrelated destination\n"
            "---\n\nDo not overwrite.\n"
        )
        before = destination.read_text()
        code, output = self.record(ident, "collision-event")
        self.assertEqual(code, 1)
        self.assertIn("destination collision", output)
        self.assertEqual(before, destination.read_text())
        self.assertTrue(source.exists())


if __name__ == "__main__":
    unittest.main()
