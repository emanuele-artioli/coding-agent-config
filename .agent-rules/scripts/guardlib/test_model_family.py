"""Policy claim tests for model_family — omit/inherit/family allowlists."""

from __future__ import annotations

import unittest

from guardlib import model_family


class ModelFamilyInspect(unittest.TestCase):
    def test_omit_and_inherit_allow_on_every_platform(self) -> None:
        for platform in ("cursor", "claude", "antigravity"):
            for value in (None, "", "  ", "inherit", "inherit-parent", "auto", "AUTO"):
                with self.subTest(platform=platform, value=value):
                    self.assertIsNone(model_family.inspect(value, platform))

    def test_cursor_allows_grok_and_composer(self) -> None:
        for slug in (
            "grok-4.5",
            "grok-4.5-fast-xhigh",
            "cursor-grok-4.5-high",
            "composer-2.5",
            "composer-2.5-fast",
        ):
            with self.subTest(slug=slug):
                self.assertIsNone(model_family.inspect(slug, "cursor"))

    def test_cursor_denies_claude_and_gpt(self) -> None:
        for slug in (
            "claude-sonnet-4.6",
            "claude-fable-5-thinking-max",
            "sonnet",
            "gpt-5.6-sol-max",
            "gemini-2.5-pro",
        ):
            with self.subTest(slug=slug):
                reason = model_family.inspect(slug, "cursor")
                self.assertIsNotNone(reason)
                assert reason is not None
                self.assertIn("Grok or Composer", reason)
                self.assertIn("omitting", reason.lower())
                self.assertNotIn("use sonnet", reason.lower())
                self.assertNotIn("use claude", reason.lower())

    def test_claude_allows_family_and_aliases(self) -> None:
        for slug in ("claude-opus-4", "sonnet", "opus", "haiku", "opus[1m]"):
            with self.subTest(slug=slug):
                self.assertIsNone(model_family.inspect(slug, "claude"))

    def test_claude_denies_grok(self) -> None:
        reason = model_family.inspect("grok-4.5", "claude")
        self.assertIsNotNone(reason)
        assert reason is not None
        self.assertIn("Claude", reason)

    def test_antigravity_allows_gemini(self) -> None:
        self.assertIsNone(model_family.inspect("gemini-2.5-pro", "antigravity"))

    def test_antigravity_denies_claude(self) -> None:
        reason = model_family.inspect("sonnet", "antigravity")
        self.assertIsNotNone(reason)


class ModelFamilyTierNudge(unittest.TestCase):
    def test_tier_mapped_models_never_nudge(self) -> None:
        for platform in ("claude", "antigravity", "cursor"):
            for model in model_family.allowed_models(platform):
                with self.subTest(platform=platform, model=model):
                    self.assertIsNone(model_family.tier_nudge(model, platform))

    def test_omit_and_inherit_never_nudge(self) -> None:
        for platform in ("claude", "antigravity", "cursor"):
            for value in (None, "", "  ", "inherit", "inherit-parent", "auto"):
                with self.subTest(platform=platform, value=value):
                    self.assertIsNone(model_family.tier_nudge(value, platform))

    def test_off_family_model_does_not_double_up_with_nudge(self) -> None:
        # The hard family deny already covers this; tier_nudge must stay
        # quiet so callers don't emit two messages for one bad model.
        self.assertIsNone(model_family.tier_nudge("grok-4.5", "claude"))
        self.assertIsNone(model_family.tier_nudge("sonnet", "cursor"))

    def test_in_family_off_tier_model_nudges(self) -> None:
        nudge = model_family.tier_nudge("haiku", "claude")
        self.assertIsNotNone(nudge)
        assert nudge is not None
        self.assertIn("haiku", nudge)
        self.assertIn("low=sonnet", nudge)
        self.assertIn("high=opus", nudge)

    def test_cursor_live_slug_matches_tier_table(self) -> None:
        # Live Task/subagentStart passes cursor-grok-4.5-high; JSON keeps grok-4.5.
        self.assertIsNone(model_family.tier_nudge("cursor-grok-4.5-high", "cursor"))
        self.assertIsNone(model_family.tier_nudge("grok-4.5", "cursor"))
        self.assertIsNone(model_family.tier_nudge("composer-2.5", "cursor"))

    def test_cursor_fast_variants_still_nudge(self) -> None:
        for slug in ("grok-4.5-fast", "composer-2.5-fast", "cursor-grok-4.5-fast"):
            with self.subTest(slug=slug):
                nudge = model_family.tier_nudge(slug, "cursor")
                self.assertIsNotNone(nudge)
                assert nudge is not None
                self.assertIn(slug, nudge)

    def test_allowed_models_reflects_effort_models_json(self) -> None:
        self.assertEqual(model_family.allowed_models("claude"), {"sonnet", "opus"})
        self.assertEqual(model_family.allowed_models("antigravity"), {"gemini-flash-3.6"})
        self.assertEqual(model_family.allowed_models("cursor"), {"composer-2.5", "grok-4.5"})


if __name__ == "__main__":
    unittest.main()
