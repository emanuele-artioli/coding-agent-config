#!/usr/bin/env python3
"""Cursor stop adapter — medium aging nudge + dirty-tree end-of-session hint.

Medium tier prints to stderr (Hooks channel). Does not set followup_message
(reserved for rare strong loops). Never auto-runs handoff.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from context_nudge import medium_aging_message  # noqa: E402


def _git_dirty() -> bool:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return bool(out.stdout.strip()) if out.returncode == 0 else False
    except (OSError, subprocess.SubprocessError):
        return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    for key in ("context_usage_percent", "contextUsagePercent"):
        if key in payload:
            print(
                f"cursor/stop: saw {key}={payload[key]!r}",
                file=sys.stderr,
            )

    msg = medium_aging_message(payload)
    if msg:
        print(f"context-nudge medium: {msg}", file=sys.stderr)

    if _git_dirty():
        print(
            "Knowledge loop — dirty tree; consider end-of-session "
            "(commit on invoke, ask before push).",
            file=sys.stderr,
        )

    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
