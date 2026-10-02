"""The report contract is only worth having if a silent miss is caught.

Two failure directions matter. A missed heading means the parent reads a
confident `## Result: PASS` with no pasted output and believes it — the
exact failure the contract exists to stop. A false alarm on a good report
teaches the parent to ignore the hook, which costs the same thing more
slowly. So the cases below pin both: complete reports pass untouched, and
each single defect is named on its own.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardlib import report_contract as rc  # noqa: E402

FENCE = "`" * 3

COMPLETE = "\n".join([
    "## Result: PASS",
    "## Changed",
    "- scripts/guardlib/report_contract.py",
    "## Check",
    FENCE,
    "python3 -m unittest guardlib.test_report_contract",
    "OK",
    FENCE,
    "## Not verified",
    "nothing",
    "## Assumptions",
    "ran as opus, medium effort",
])

STUCK = "\n".join([
    "## Result: STUCK",
    "STUCK: out of ideas.",
    "## Changed",
    "nothing",
    "## Check",
    "command: pytest -q",
    "output: 3 failed, unable to diagnose",
    "## Not verified",
    "everything",
    "## Assumptions",
    "none",
])


def without(heading: str) -> str:
    """COMPLETE with the one line that carries `heading` removed."""
    kept = [
        line for line in COMPLETE.splitlines()
        if not line.strip().startswith(heading)
    ]
    return "\n".join(kept)


class TestGoodReports(unittest.TestCase):
    def test_complete_pass_report_has_no_problems(self):
        self.assertEqual(rc.problems(COMPLETE), [])

    def test_stuck_report_with_all_headings_passes(self):
        self.assertEqual(rc.problems(STUCK), [])

    def test_check_section_with_a_fenced_block_passes(self):
        text = COMPLETE.replace("OK\n", "")
        self.assertNotIn(rc.NO_OUTPUT, rc.problems(text))


class TestMissingHeadings(unittest.TestCase):
    def test_each_missing_heading_is_named(self):
        for heading in rc.REQUIRED_HEADINGS[1:]:
            with self.subTest(heading=heading):
                found = rc.problems(without(heading))
                self.assertIn(rc.MISSING.format(heading), found)

    def test_missing_result_heading_is_named(self):
        found = rc.problems(without("## Result"))
        self.assertIn(rc.MISSING.format(rc.RESULT_HEADING), found)

    def test_empty_text_lists_five_missing_headings(self):
        found = rc.problems("")
        self.assertEqual(len(found), 5)
        for heading in rc.REQUIRED_HEADINGS:
            self.assertIn(rc.MISSING.format(heading), found)


class TestCheckSection(unittest.TestCase):
    def test_prose_with_no_output_is_flagged(self):
        text = "\n".join([
            "## Result: PASS",
            "## Changed",
            "- a file",
            "## Check",
            "I ran the tests and they passed.",
            "## Not verified",
            "nothing",
            "## Assumptions",
            "none",
        ])
        self.assertEqual(rc.problems(text), [rc.NO_OUTPUT])

    def test_empty_check_section_is_flagged(self):
        text = COMPLETE.replace(
            "\n".join([
                FENCE,
                "python3 -m unittest guardlib.test_report_contract",
                "OK",
                FENCE,
            ]),
            "",
        )
        self.assertIn(rc.NO_OUTPUT, rc.problems(text))


class TestResultValue(unittest.TestCase):
    def test_wrong_result_value_is_flagged(self):
        text = COMPLETE.replace("## Result: PASS", "## Result: DONE")
        found = rc.problems(text)
        self.assertIn(rc.BAD_RESULT, found)

    def test_template_line_left_unedited_is_flagged(self):
        text = COMPLETE.replace("## Result: PASS", rc.RESULT_HEADING)
        self.assertIn(rc.BAD_RESULT, rc.problems(text))

    def test_fail_is_a_legal_value(self):
        text = COMPLETE.replace("## Result: PASS", "## Result: FAIL")
        self.assertEqual(rc.problems(text), [])


class TestMessage(unittest.TestCase):
    def test_no_problems_means_no_message(self):
        self.assertEqual(rc.message([]), "")

    def test_message_carries_every_problem_and_the_verdict(self):
        found = rc.problems("")
        text = rc.message(found)
        for problem in found:
            self.assertIn(problem, text)
        self.assertIn("FAIL", text)
        self.assertIn("re-run the check", text)


if __name__ == "__main__":
    unittest.main()
