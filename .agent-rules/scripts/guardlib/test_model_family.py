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


if __name__ == "__main__":
    unittest.main()
