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

import re

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
