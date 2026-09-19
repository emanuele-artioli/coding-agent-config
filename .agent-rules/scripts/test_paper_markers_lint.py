"""Claim tests for the paper marker lint.

Proposed list (the four rules the script states, plus the CLI surface):

Behaviour
1. a clean file passes, with the right per-kind counts
2. a CLAIM whose src= resolves against the paper directory's parent passes
3. a marker inside archive/ is ignored
4. --json prints an object with files / failures / markers / urls
5. a CLAIM whose src= ends in trailing punctuation passes
6. a CLAIM with an https:// source passes and is counted as a url

Plausible misuse
5. a CLAIM with no src= fails, naming the missing src=
6. a CLAIM whose src= path exists nowhere fails, naming the path
7. a marker with an empty id fails
8. two HOLEs on one id fail
9. a HOLE and a CLAIM on one id fail

Deliberately not testing
- LaTeX parsing beyond the single marker line (continuations are out of scope)
- unreadable files / permission errors (the caller cannot produce them here)
- exact column widths of the counts table
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "paper-markers-lint.py"


class LintCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.paper = self.root / "paper"
        self.paper.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, relative: str, text: str) -> Path:
        path = self.paper / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def run_lint(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.paper), *extra],
            capture_output=True,
            text=True,
        )


class CleanPaper(LintCase):
    def test_clean_file_passes_with_counts(self) -> None:
        (self.paper / "outputs").mkdir()
        (self.paper / "outputs" / "report.json").write_text("{}")
        self.write(
            "main.tex",
            "% STATUS(main.tex) 2026-09-01: fine.\n"
            "% GOAL(sec:intro): say the thing.\n"
            "% NOTE(sec:intro): a caveat.\n"
            "% NEXT(sec:intro): tidy later.\n"
            "% CLAIM(sec:intro): src=outputs/report.json date=2026-09-01\n"
            "\\section{Intro}\n",
        )
        result = self.run_lint()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("5 markers, 0 failure(s)", result.stdout)
        self.assertIn("main.tex", result.stdout)
        self.assertNotIn("FAIL", result.stdout)

    def test_src_resolves_against_parent_directory(self) -> None:
        (self.root / "outputs").mkdir()
        (self.root / "outputs" / "run.json").write_text("{}")
        self.write("main.tex", "% CLAIM(sec:eval): src=outputs/run.json date=2026-09-01\n")
        result = self.run_lint()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 markers, 0 failure(s)", result.stdout)

    def test_trailing_punctuation_is_stripped_from_src(self) -> None:
        (self.paper / "outputs").mkdir()
        (self.paper / "outputs" / "x.json").write_text("{}")
        self.write("main.tex", "% CLAIM(sec:eval): src=outputs/x.json;\n")
        result = self.run_lint()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 markers, 0 failure(s)", result.stdout)

    def test_url_source_passes_and_is_counted(self) -> None:
        self.write("main.tex", "% CLAIM(sec:eval): src=https://example.com/run.json\n")
        result = self.run_lint()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 markers, 1 url source(s), 0 failure(s)", result.stdout)
        payload = json.loads(self.run_lint("--json").stdout)
        self.assertEqual(payload["urls"], 1)

    def test_archive_directory_is_ignored(self) -> None:
        self.write("archive/old.tex", "% HOLE(sec:dead): stale marker.\n")
        self.write("main.tex", "% GOAL(sec:intro): live marker.\n")
        result = self.run_lint()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 markers, 0 failure(s)", result.stdout)
        self.assertNotIn("archive/old.tex", result.stdout)


class Failures(LintCase):
    def test_claim_without_src_fails(self) -> None:
        self.write("main.tex", "% CLAIM(sec:eval): the number came from somewhere.\n")
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn("main.tex:1: CLAIM(sec:eval) has no src=", result.stdout)
        self.assertIn("1 markers, 1 failure(s)", result.stdout)

    def test_claim_with_missing_path_fails(self) -> None:
        self.write("main.tex", "% CLAIM(sec:eval): src=outputs/nowhere-at-all.json\n")
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "main.tex:1: CLAIM(sec:eval) src=outputs/nowhere-at-all.json does not exist",
            result.stdout,
        )

    def test_empty_id_fails(self) -> None:
        self.write("main.tex", "% GOAL(): nameless.\n")
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn("main.tex:1: GOAL() has an empty id", result.stdout)

    def test_two_holes_on_one_id_fail(self) -> None:
        self.write("main.tex", "% HOLE(sec:eval): first gap.\n")
        self.write("sections/eval.tex", "% HOLE(sec:eval): second gap.\n")
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "sections/eval.tex:1: HOLE(sec:eval) duplicates the open HOLE at main.tex:1",
            result.stdout,
        )

    def test_hole_and_claim_on_one_id_fail(self) -> None:
        (self.paper / "outputs").mkdir()
        (self.paper / "outputs" / "report.json").write_text("{}")
        self.write(
            "main.tex",
            "% HOLE(sec:eval): missing curves.\n"
            "% CLAIM(sec:eval): src=outputs/report.json date=2026-09-01\n",
        )
        result = self.run_lint()
        self.assertEqual(result.returncode, 1)
        self.assertIn("main.tex:1: HOLE(sec:eval) has a CLAIM at main.tex:2", result.stdout)


class JsonOutput(LintCase):
    def test_json_has_the_three_keys(self) -> None:
        self.write(
            "main.tex",
            "% GOAL(sec:intro): say the thing.\n% CLAIM(sec:intro): no source here.\n",
        )
        result = self.run_lint("--json")
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(set(payload), {"files", "failures", "markers", "urls"})
        self.assertEqual(payload["markers"], 2)
        self.assertEqual(payload["files"]["main.tex"]["GOAL"], 1)
        self.assertEqual(len(payload["failures"]), 1)


if __name__ == "__main__":
    unittest.main()
