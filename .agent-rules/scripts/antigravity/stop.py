#!/usr/bin/env python3
"""Antigravity Stop adapter — medium aging nudge + dirty-tree end-of-session hint.

Always exits 0 for advisory nudges.
Logs side-channel probe under ~/.gemini/stop-probe.log to verify payload fields.
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

    try:
        probe = Path.home() / ".gemini" / "stop-probe.log"
        probe.parent.mkdir(parents=True, exist_ok=True)
        with probe.open("a") as handle:
            handle.write(
                json.dumps(
                    {
                        "keys": sorted(payload.keys()),
                        "session_id": payload.get("session_id") or payload.get("conversation_id"),
                        "context_usage_percent": payload.get("context_usage_percent")
                        or payload.get("contextUsagePercent"),
                    }
                )
                + "\n"
            )
    except OSError:
        pass

    msg = medium_aging_message(payload)
    if msg:
        print(f"context-nudge medium: {msg}", file=sys.stderr)

    if _git_dirty():
        print(
            "Knowledge loop — dirty tree; consider end-of-session "
            "(commit on invoke, ask before push).",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
