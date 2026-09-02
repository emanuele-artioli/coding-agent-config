#!/usr/bin/python3
"""Codex UserPromptSubmit adapter for the soft task-change nudge."""

from __future__ import annotations

import json
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
    if msg:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": msg,
        }}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
