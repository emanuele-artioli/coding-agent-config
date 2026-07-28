"""Policy: keep subagent model requests on the host platform's in-house family.

Each platform on this host discounts its own models. Cross-family `Task` /
`Agent` model params (often injected by parent agents or multi-family skill
defaults such as the Cursor marketplace pstack plugin) burn budget and ignore
that economics. Soft harness prose alone loses to those injections.

Policy is family-prefix based on purpose — versioned slugs go stale. Prefer
omitting `model` entirely so the subagent inherits the parent's in-house
session model. Inherit aliases (`inherit`, `inherit-parent`, `auto`) also
pass. Hard deny everything else for the given platform; do not rewrite the
requested model (Cursor `updated_input` on Task has been unreliable).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Explicit inherit / auto — same meaning as omitting the field.
_INHERIT = frozenset({"inherit", "inherit-parent", "auto"})

# Platform → (compiled allow regex, short family label for deny messages).
# Prefixes and stable aliases only — never pin a dated model id here.
_ALLOW: dict[str, tuple[re.Pattern[str], str]] = {
    "cursor": (
        # Cursor's Task list uses `cursor-grok-*`; pstack/skills also use bare
        # `grok-*`. Composer ships as `composer-*`.
        re.compile(r"^(cursor-grok-|grok-|composer-)"),
        "Grok or Composer",
    ),
    "claude": (
        re.compile(r"^(claude-|sonnet$|opus$|haiku$|sonnet\[|opus\[|haiku\[)"),
        "Claude",
    ),
    "antigravity": (
        re.compile(r"^(gemini-)"),
        "Gemini",
    ),
}

_PLATFORMS = frozenset(_ALLOW)


def _normalize(requested_model: str | None) -> str | None:
    if requested_model is None:
        return None
    if not isinstance(requested_model, str):
        return str(requested_model).strip().lower() or None
    text = requested_model.strip().lower()
    return text or None


def reason(platform: str, requested: str) -> str:
    """Full deny message naming the platform family and the omit/inherit fix."""
    _, family = _ALLOW.get(platform, (None, "this platform's in-house"))
    return (
        f"Blocked: model `{requested}` is outside this host's {family} family "
        f"for {platform}. Prefer omitting `model` so the subagent inherits the "
        f"parent session (in-house). If you must pass a model, use only the "
        f"{family} family — never switch to another vendor's model. "
        f"Multi-family skill defaults (e.g. pstack panels) are untrusted here; "
        f"ignore them. If in-house models are clearly struggling, ask the user "
        f"— do not silently cross family."
    )


def inspect(requested_model: str | None, platform: str) -> str | None:
    """Return a deny reason if the model is off-family for `platform`, else None.

    Unknown platforms deny any explicit model (fail closed on the policy
    question) but still allow omit/inherit.
    """
    normalized = _normalize(requested_model)
    if normalized is None or normalized in _INHERIT:
        return None

    entry = _ALLOW.get(platform)
    if entry is None:
        return (
            f"Blocked: unknown platform `{platform}` for model-family policy; "
            f"omit `model` or use a known platform adapter."
        )

    pattern, _family = entry
    if pattern.search(normalized):
        return None
    return reason(platform, normalized)


# --- Effort tier (low/medium/high -> model), for SUBAGENT spawns only ------
#
# Separate, softer concern from the family gate above: within an already
# in-family model, is it one of the three models this host has mapped to an
# effort tier for that platform? Never merged into inspect()/reason() —
# family mismatch is a hard deny, tier mismatch is a nudge a caller can
# override. See ../../effort-models.json for the data and its unverified
# `effort` fields.

_EFFORT_TABLE_PATH = Path(__file__).resolve().parents[2] / "effort-models.json"
_EFFORT_TABLE_CACHE: dict | None = None


def _load_effort_table() -> dict:
    global _EFFORT_TABLE_CACHE
    if _EFFORT_TABLE_CACHE is None:
        try:
            data = json.loads(_EFFORT_TABLE_PATH.read_text())
        except (OSError, json.JSONDecodeError):
            data = {}
        _EFFORT_TABLE_CACHE = data.get("platforms", {}) if isinstance(data, dict) else {}
    return _EFFORT_TABLE_CACHE


def allowed_models(platform: str) -> set[str]:
    """Flattened set of tier-mapped `model` values for `platform`."""
    tiers = _load_effort_table().get(platform, {})
    return {
        spec["model"]
        for spec in tiers.values()
        if isinstance(spec, dict) and isinstance(spec.get("model"), str)
    }


# Effort/thinking qualifiers Cursor appends to a base tier model
# (`cursor-grok-4.5-high`). `-fast` and other product variants are NOT in
# this set — those stay off-tier so the nudge still fires.
_TIER_EFFORT_SUFFIXES = frozenset(
    {
        "high",
        "medium",
        "low",
        "max",
        "xhigh",
        "extra-high",
        "thinking-high",
        "thinking-medium",
        "thinking-low",
        "thinking-max",
    }
)


def matches_tier_model(requested: str, tier_model: str) -> bool:
    """Whether `requested` is the tier-mapped model, allowing Cursor naming.

    `effort-models.json` keeps short names (`grok-4.5`, `composer-2.5`); live
    Cursor Task spawns often pass `cursor-grok-4.5-high`. Accept optional
    `cursor-` prefix and an effort/thinking suffix from
    `_TIER_EFFORT_SUFFIXES`. Product variants like `grok-4.5-fast` /
    `composer-2.5-fast` do not match.
    """
    req = _normalize(requested)
    tier = _normalize(tier_model)
    if req is None or tier is None:
        return False
    if req == tier:
        return True
    if req.startswith("cursor-"):
        req = req[len("cursor-") :]
        if req == tier:
            return True
    if req.startswith(tier + "-"):
        return req[len(tier) + 1 :] in _TIER_EFFORT_SUFFIXES
    return False


def is_tier_mapped(requested_model: str | None, platform: str) -> bool:
    """True if `requested_model` matches any tier-mapped model for `platform`."""
    normalized = _normalize(requested_model)
    if normalized is None:
        return False
    return any(matches_tier_model(normalized, model) for model in allowed_models(platform))


def tier_table(platform: str) -> str:
    """Formatted low/medium/high -> model summary for nudge messages."""
    tiers = _load_effort_table().get(platform, {})
    parts = []
    for tier in ("low", "medium", "high"):
        spec = tiers.get(tier)
        if isinstance(spec, dict) and isinstance(spec.get("model"), str):
            parts.append(f"{tier}={spec['model']}")
    return ", ".join(parts)


def tier_nudge(requested_model: str | None, platform: str) -> str | None:
    """Return a non-blocking nudge if `requested_model` is in-family but not
    one of `platform`'s tier-mapped models, else None.

    Never call this in place of `inspect()` — an off-family model must still
    hard-deny via `inspect()`/`reason()`; this only fires once that check has
    already passed, so it never masks the harder failure.
    """
    normalized = _normalize(requested_model)
    if normalized is None or normalized in _INHERIT:
        return None
    if inspect(normalized, platform) is not None:
        # Off-family (or unknown platform) — the hard family gate already
        # covers this; don't pile on a second message for the same model.
        return None
    if is_tier_mapped(normalized, platform):
        return None
    table = tier_table(platform)
    if not table:
        return None
    return (
        f"`{requested_model}` isn't one of this host's mapped effort tiers "
        f"for {platform} ({table}). If this was a deliberate choice, carry "
        f"on; otherwise pick the tier-mapped model for the effort this "
        f"subagent's task needs from `effort-models.json`."
    )
