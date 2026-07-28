#!/usr/bin/env python3
"""Claude Code UserPromptSubmit adapter — task-change detection (soft tier).

Locked decision (HANDOFF-claude.md): soft task-change stays log-only. Always
exits 0 and never sets `hookSpecificOutput` to block — set
CONTEXT_NUDGE_BLOCK_SOFT=1 to actually block with a message instead (not the
default; mirrors the Cursor adapter's opt-in).

Made directly executable (chmod +x, no `python3` prefix) for the fail-open
"command not found" path, matching the other advisory Claude adapters.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from context_nudge import soft_task_change_message  # noqa: E402


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0

    prompt = payload.get("prompt") if isinstance(payload.get("prompt"), str) else ""

    msg = soft_task_change_message(payload, prompt, [])
    if not msg:
        return 0

    print(f"context-nudge soft: {msg}", file=sys.stderr)
    if os.environ.get("CONTEXT_NUDGE_BLOCK_SOFT") == "1":
        print(msg, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
