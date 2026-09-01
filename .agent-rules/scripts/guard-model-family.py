#!/usr/bin/env python3
"""PreToolUse guard (Claude Code dialect): model-family gate for Agent / Task.

Thin adapter over `guardlib/model_family.py`. Allows omit/inherit and Claude
family models; denies cross-family spawns (hard). Also asks for confirmation
(soft — never blocks) when a subagent's requested model is in-family but not
one of this host's low/medium/high effort tiers for Claude, per
`../effort-models.json`. This only ever applies to a spawned `Agent`/`Task`
subagent — never to the user's own top-level session model.

Wire from a Claude Code session only (platform write-ownership) — see
`candidates/pending-verification/claude.md`. Invoked via `python3 <path>` so a
missing file fails closed.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Keep bytecode off NFS. Setting the env var here would be a no-op -- the
# interpreter reads PYTHONPYCACHEPREFIX at startup, before this line runs --
# so assign sys.pycache_prefix directly, which does apply to imports below.
sys.pycache_prefix = os.environ.get("PYTHONPYCACHEPREFIX") or "/var/tmp/emanuele-pycache"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from guardlib import model_family  # noqa: E402

_SPAWN_TOOLS = frozenset({"Agent", "Task"})


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool = payload.get("tool_name")
    if tool not in _SPAWN_TOOLS:
        sys.exit(0)

    tool_input = payload.get("tool_input")
    requested = None
    if isinstance(tool_input, dict):
        value = tool_input.get("model")
        if isinstance(value, str):
            requested = value

    reason = model_family.inspect(requested, "claude")
    if reason:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                }
            )
        )
        sys.exit(0)

    nudge = model_family.tier_nudge(requested, "claude")
    if nudge:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "ask",
                        "permissionDecisionReason": nudge,
                    }
                }
            )
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
