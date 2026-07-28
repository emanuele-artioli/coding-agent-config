#!/usr/bin/env python3
"""preToolUse (Task) / subagentStart hook (Cursor dialect): model-family gate.

Thin adapter over `guardlib/model_family.py`. Keeps Task / subagent spawns on
Cursor's in-house families (Grok / Composer) or inherit/omit. Denies
cross-family injections (parent-passed Claude/GPT, pstack multi-family
defaults) with a clear agent_message — never rewrites `updated_input`. Also
logs (never blocks) an effort-tier nudge from `../../effort-models.json` when
an allowed model is in-family but off this host's mapped low/medium/high
tiers for Cursor — no confirmed "ask" equivalent has been exercised for this
hook yet (see `candidates/pending-verification/cursor.md`), so this stays
advisory-only in the log until that's checked.

Wired from `~/.cursor/hooks.json` on both `preToolUse` (matcher Task) and
`subagentStart`, with `failClosed: true`.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardlib import model_family  # noqa: E402

PLATFORM = "cursor"
PROBE_LOG = Path.home() / ".cursor" / "model-family-hook.log"

# Prefer spawn-specific fields over a top-level `model` that may be the
# parent session model on some Cursor events.
def _model(payload: dict) -> str | None:
    nested = payload.get("tool_input")
    if isinstance(nested, dict):
        for key in ("model", "subagent_model"):
            value = nested.get(key)
            if isinstance(value, str) and value.strip():
                return value
    for key in ("subagent_model", "model"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _log(
    payload: dict,
    requested: str | None,
    decision: str,
    tier_nudge: str | None = None,
) -> None:
    try:
        PROBE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with PROBE_LOG.open("a") as handle:
            entry = {
                "at": datetime.now().isoformat(timespec="seconds"),
                "decision": decision,
                "requested_model": requested,
                "payload_keys": sorted(payload.keys()),
                "hook_event_name": payload.get("hook_event_name")
                or payload.get("hookEventName"),
            }
            if tier_nudge:
                entry["tier_nudge_non_blocking"] = tier_nudge
            handle.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def _respond(permission: str, user_message: str = "", agent_message: str = "") -> None:
    response: dict[str, str] = {"permission": permission}
    if user_message:
        response["user_message"] = user_message
    if agent_message:
        response["agent_message"] = agent_message
    print(json.dumps(response))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        _respond("allow")
        return 0
    if not isinstance(payload, dict):
        _respond("allow")
        return 0

    requested = _model(payload)
    deny = model_family.inspect(requested, PLATFORM)
    if deny:
        _log(payload, requested, "deny")
        _respond(
            "deny",
            user_message="Blocked an off-family subagent model on Cursor.",
            agent_message=deny,
        )
        return 0

    nudge = model_family.tier_nudge(requested, PLATFORM)
    _log(payload, requested, "allow", tier_nudge=nudge)
    _respond("allow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
