#!/usr/bin/env python3
"""PreToolUse guard (Antigravity dialect): model-family gate.

Thin adapter over `guardlib/model_family.py`. Antigravity denies by non-zero
exit status (not Cursor/Claude JSON). Message goes to stderr. Also logs (never
blocks) an effort-tier nudge from `../../effort-models.json` when a spawned
subagent's model is in-family but off this host's mapped low/medium/high
tiers for Antigravity — no confirmed "ask" equivalent exists on this
platform yet (see `candidates/pending-verification/antigravity.md`), so this
stays advisory-only until that's checked.

Wire from an Antigravity session only — see
`candidates/pending-verification/antigravity.md`. Use an absolute path in
`~/.gemini/config/hooks.json` (relative paths exit 127 and silently bypass).
Invoked via `python3 <absolute-path>` so a missing file fails closed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardlib import model_family  # noqa: E402

# Tools that may carry a model when spawning work. Expand when verifying live.
_SPAWN_HINTS = frozenset({"run_command", "invoke_subagent", "Agent", "Task", "task", "agent"})


def _requested_model(payload: dict) -> str | None:
    tool_call = payload.get("toolCall") or payload.get("tool_call")
    if isinstance(tool_call, dict):
        args = tool_call.get("args")
        if isinstance(args, dict):
            subagents = args.get("Subagents") or args.get("subagents")
            if isinstance(subagents, list) and subagents:
                for s in subagents:
                    if isinstance(s, dict) and s.get("Model"):
                        return s.get("Model")
            for key in ("model", "Model", "subagent_model"):
                val = args.get(key)
                if isinstance(val, str) and val.strip():
                    return val

    for key in ("model", "Model", "subagent_model"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    nested = payload.get("tool_input") or payload.get("args")
    if isinstance(nested, dict):
        for key in ("model", "Model", "subagent_model"):
            value = nested.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    # If the matcher already narrowed to the spawn tool, still inspect.
    # Unknown tool names with an explicit model are also checked.
    requested = _requested_model(payload)
    if requested is None and tool and tool not in _SPAWN_HINTS:
        return 0

    reason = model_family.inspect(requested, "antigravity")
    if reason:
        print(reason, file=sys.stderr)
        return 2

    nudge = model_family.tier_nudge(requested, "antigravity")
    if nudge:
        print(f"[effort-tier nudge, non-blocking] {nudge}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
