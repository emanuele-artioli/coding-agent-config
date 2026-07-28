#!/usr/bin/env python3
"""Claude Code PreCompact adapter — strong handoff / end-of-session nudge.

Plain stdout on exit 0 is injected into context before compaction happens,
same mechanism as SessionStart. PreCompact's stdin has no fill-percentage
field (confirmed against Anthropic's hooks docs) — the message is
unconditional here, unlike Cursor where a `context_usage_percent` probe was
attempted.

Advisory only: PreCompact does not block on exit 2 (stderr is shown, then it
continues), but this stays directly executable (chmod +x, no `python3`
prefix) for the fail-open "command not found" path, matching the other
advisory Claude adapters.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from context_nudge import strong_precompact_message  # noqa: E402


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    msg = strong_precompact_message(payload)
    print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
