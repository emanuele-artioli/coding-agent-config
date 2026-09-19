#!/usr/bin/env python3
"""Unit tests for scripts/lessons.py — temp queues only, never the real one."""

from __future__ import annotations

import importlib.util
import io
import contextlib
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
