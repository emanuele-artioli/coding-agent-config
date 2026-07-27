#!/usr/bin/env python3
"""Cursor beforeSubmitPrompt — task-change detection (soft tier).

Documented outputs: continue + user_message when blocked. Soft allow-and-whisper
is not documented, so v1 always continues and logs to stderr; set
CONTEXT_NUDGE_BLOCK_SOFT=1 to block with user_message instead.
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
        print(json.dumps({"continue": True}))
        return 0
    if not isinstance(payload, dict):
        print(json.dumps({"continue": True}))
        return 0

    # Probe for undocumented fill %.
    for key in ("context_usage_percent", "contextUsagePercent"):
        if key in payload:
            print(
                f"cursor/before-submit-prompt: saw {key}={payload[key]!r}",
                file=sys.stderr,
            )

    prompt = payload.get("prompt") if isinstance(payload.get("prompt"), str) else ""
    attachments = payload.get("attachments")
    if not isinstance(attachments, list):
        attachments = []

    msg = soft_task_change_message(payload, prompt, attachments)
    if not msg:
        print(json.dumps({"continue": True}))
        return 0

    print(f"context-nudge soft: {msg}", file=sys.stderr)
    if os.environ.get("CONTEXT_NUDGE_BLOCK_SOFT") == "1":
        print(json.dumps({"continue": False, "user_message": msg}))
    else:
        print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
