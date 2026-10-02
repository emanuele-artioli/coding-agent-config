"""Claim tests for the tiered split in sync_agent_rules.

The claim worth testing is not "the script runs" but "no rule silently
disappears": every byte of a project's hand-written AGENTS.md has to end up in
either the always-on core or exactly one scoped rule file. An earlier version
of `split_scoped` failed precisely that -- two adjacent scoped sections
produced overlapping cut ranges and ate an unrelated heading out of the core,
which no smoke test would have noticed.
"""

from __future__ import annotations

import unittest

import sync_agent_rules as sync

ADJACENT = """# DEMO

Intro.

## Entry point

How to run it.

<!-- scope: src/** -->
## Architecture

Source rules.

<!-- scope: tests/** -->
## Testing

Test rules.

## Where to look for more

Tail.
"""


class SplitScoped(unittest.TestCase):
    def test_unmarked_text_stays_whole(self) -> None:
        core, scoped = sync.split_scoped("# A\n\n## One\n\nbody\n")
        self.assertEqual(scoped, [])
        self.assertIn("## One", core)
        self.assertIn("body", core)

    def test_adjacent_sections_do_not_eat_the_next_heading(self) -> None:
        core, scoped = sync.split_scoped(ADJACENT)
        self.assertEqual([item.title for item in scoped], ["Architecture", "Testing"])
        # The heading after the last scoped section is the one that went missing.
        self.assertIn("## Where to look for more", core)
        self.assertIn("Tail.", core)
        self.assertIn("## Entry point", core)

    def test_a_scoped_body_never_carries_the_next_marker(self) -> None:
        _, scoped = sync.split_scoped(ADJACENT)
        for item in scoped:
            with self.subTest(section=item.title):
                self.assertNotIn("<!-- scope:", item.body)

    def test_every_section_lands_somewhere_exactly_once(self) -> None:
        core, scoped = sync.split_scoped(ADJACENT)
        for marker, home in (
            ("How to run it.", core),
            ("Source rules.", scoped[0].body),
            ("Test rules.", scoped[1].body),
            ("Tail.", core),
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, home)
        # ...and nowhere else: a scoped body must be gone from the core.
        self.assertNotIn("Source rules.", core)
        self.assertNotIn("Test rules.", core)
        self.assertNotIn("## Architecture", core)

    def test_globs_are_split_and_stripped(self) -> None:
        _, scoped = sync.split_scoped(
            "# A\n\n<!-- scope: src/** ,  tests/**  -->\n## One\n\nbody\n"
        )
        self.assertEqual(scoped[0].globs, ("src/**", "tests/**"))

    def test_scoped_section_at_end_of_file(self) -> None:
        _, scoped = sync.split_scoped("# A\n\n<!-- scope: src/** -->\n## Last\n\nbody\n")
        self.assertEqual(len(scoped), 1)
        self.assertIn("body", scoped[0].body)

    def test_marker_not_above_a_heading_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            sync.split_scoped("# A\n\n<!-- scope: src/** -->\n\nloose prose\n")

    def test_marker_with_no_globs_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            sync.split_scoped("# A\n\n<!-- scope:  -->\n## One\n\nbody\n")


class Slugify(unittest.TestCase):
    def test_headings_become_filenames(self) -> None:
        for title, slug in (
            ("Architecture rules", "architecture-rules"),
            ("`outputs/` and `assets/` — deletion is unrecoverable",
             "outputs-and-assets-deletion-is-unrecoverable"),
            ("Testing — the suite is a failsafe", "testing-the-suite-is-a-failsafe"),
        ):
            with self.subTest(title=title):
                self.assertEqual(sync.slugify(title), slug)

    def test_slugs_are_unique_across_a_real_section_set(self) -> None:
        _, scoped = sync.split_scoped(ADJACENT)
        slugs = [item.slug for item in scoped]
        self.assertEqual(len(slugs), len(set(slugs)))


class GeneratedFrontmatter(unittest.TestCase):
    def test_claude_rule_defers_with_paths(self) -> None:
        _, scoped = sync.split_scoped(ADJACENT)
        rule = sync.claude_rule(scoped[0])
        self.assertTrue(rule.startswith("---\npaths:\n"))
        self.assertIn('  - "src/**"', rule)
        self.assertIn(sync.BANNER, rule)

    def test_copilot_rule_defers_with_applyto(self) -> None:
        _, scoped = sync.split_scoped(ADJACENT)
        rule = sync.copilot_rule(scoped[0])
        self.assertTrue(rule.startswith('---\napplyTo: "src/**"\n---'))

    def test_core_points_at_what_it_dropped(self) -> None:
        core, scoped = sync.split_scoped(ADJACENT)
        rendered = sync.claude_core(core, scoped)
        for item in scoped:
            with self.subTest(section=item.title):
                self.assertIn(item.title, rendered)
                self.assertIn(item.globs[0], rendered)


if __name__ == "__main__":
    unittest.main()
