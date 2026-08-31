"""Claim tests for pre-compact resume stubs.

Proposed list (plan-approved scope for agent-loop efficiency work):

Behaviour
1. safe_conversation_id sanitizes path-hostile ids and collapses empty → unknown
2. write_stub creates a template file at stub_path_for(id) with required sections
3. most_recent_stub returns the newest in-age .md and ignores stale / non-md
4. resume_messages points at a fresh stub and at a fresh cwd/HANDOFF.md
5. strong_precompact_message names the stub path (and fill % when present)

Plausible misuse
6. write_stub returns None on OSError (fail-open; message still usable)
7. resume_messages ignores HANDOFF.md / stubs older than max_age_sec
8. safe_conversation_id on '' / '///' / only-punctuation → 'unknown'

Deliberately not testing
- SessionStart adapter JSON dialects (thin wrappers; covered by live probes)
- Concurrent stub writers / filesystem races
- Exact MSG_STRONG wording beyond stub-path inclusion
"""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import context_nudge
import precompact_stub as stub


class SafeId(unittest.TestCase):
    def test_path_hostile_chars_are_replaced(self) -> None:
        self.assertEqual(stub.safe_conversation_id("a/b\\c:d"), "a_b_c_d")

    def test_empty_and_junk_become_unknown(self) -> None:
        for raw in ("", "   ", "///", "...", "___"):
            with self.subTest(raw=raw):
                self.assertEqual(stub.safe_conversation_id(raw), "unknown")


class WriteStub(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self._patch = mock.patch.object(stub, "PRECOMPACT_DIR", self.dir)
        self._patch.start()

    def tearDown(self) -> None:
        self._patch.stop()
        self._tmp.cleanup()

    def test_writes_template_with_required_sections(self) -> None:
        path = stub.write_stub("sess-1")
        self.assertIsNotNone(path)
        assert path is not None
        self.assertEqual(path, self.dir / "sess-1.md")
        text = path.read_text()
        for needle in (
            "# Pre-compact resume stub",
            "## Task (one paragraph)",
            "## Done and verified",
            "## In progress",
            "## Running or queued jobs",
            "## Next three steps",
            "## Landmarks",
            "HANDOFF.md",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_fail_open_on_oserror(self) -> None:
        with mock.patch.object(Path, "write_text", side_effect=OSError("denied")):
            self.assertIsNone(stub.write_stub("sess-2"))


class AgeGate(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self._patch = mock.patch.object(stub, "PRECOMPACT_DIR", self.dir)
        self._patch.start()

    def tearDown(self) -> None:
        self._patch.stop()
        self._tmp.cleanup()

    def test_most_recent_prefers_newest_in_age(self) -> None:
        older = self.dir / "old.md"
        newer = self.dir / "new.md"
        older.write_text("old")
        newer.write_text("new")
        now = time.time()
        os.utime(older, (now - 3600, now - 3600))
        os.utime(newer, (now - 10, now - 10))
        self.assertEqual(
            stub.most_recent_stub(max_age_sec=7200, now=now), newer
        )

    def test_stale_stub_ignored(self) -> None:
        path = self.dir / "stale.md"
        path.write_text("stale")
        now = time.time()
        # Older than the 48h default gate (48 * 3600 = 172800).
        os.utime(path, (now - 200_000, now - 200_000))
        self.assertIsNone(stub.most_recent_stub(max_age_sec=48 * 3600, now=now))

    def test_non_md_ignored(self) -> None:
        (self.dir / "note.txt").write_text("nope")
        self.assertIsNone(stub.most_recent_stub())


class ResumeMessages(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.pre = self.root / "precompact"
        self.pre.mkdir()
        self.project = self.root / "project"
        self.project.mkdir()
        self._patch = mock.patch.object(stub, "PRECOMPACT_DIR", self.pre)
        self._patch.start()

    def tearDown(self) -> None:
        self._patch.stop()
        self._tmp.cleanup()

    def test_points_at_stub_and_fresh_handoff(self) -> None:
        stub_path = stub.write_stub("cid")
        handoff = self.project / "HANDOFF.md"
        handoff.write_text("# handoff\n")
        now = time.time()
        lines = stub.resume_messages(self.project, max_age_sec=3600, now=now)
        self.assertEqual(len(lines), 2)
        self.assertIn(str(stub_path), lines[0])
        self.assertIn(str(handoff), lines[1])

    def test_ignores_stale_handoff(self) -> None:
        handoff = self.project / "HANDOFF.md"
        handoff.write_text("# handoff\n")
        now = time.time()
        os.utime(handoff, (now - 10_000, now - 10_000))
        self.assertEqual(
            stub.resume_messages(self.project, max_age_sec=3600, now=now), []
        )


class StrongMessage(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self._patch = mock.patch.object(stub, "PRECOMPACT_DIR", self.dir)
        self._patch.start()
        # Avoid writing real nudge state during tests.
        self._state = mock.patch.object(
            context_nudge, "STATE_PATH", self.dir / "nudge-state.json"
        )
        self._state.start()
        context_nudge.STATE_DIR = self.dir

    def tearDown(self) -> None:
        self._state.stop()
        self._patch.stop()
        self._tmp.cleanup()

    def test_message_includes_stub_path_and_fill(self) -> None:
        msg = context_nudge.strong_precompact_message(
            {"session_id": "abc-123", "context_usage_percent": 87}
        )
        self.assertIn("87", msg)
        self.assertIn(str(self.dir / "abc-123.md"), msg)
        self.assertTrue((self.dir / "abc-123.md").is_file())

    def test_message_survives_write_failure(self) -> None:
        with mock.patch.object(stub, "write_stub", return_value=None):
            msg = context_nudge.strong_precompact_message({"session_id": "x"})
        self.assertIn("HANDOFF.md", msg)
        self.assertIn("Compaction imminent", msg)


if __name__ == "__main__":
    unittest.main()
