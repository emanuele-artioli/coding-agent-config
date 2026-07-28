#!/usr/bin/env python3
"""Claude Code Stop adapter — medium aging nudge + dirty-tree end-of-session hint.

Always exits 0: on Stop, exit 2 blocks Claude from stopping (feeds stderr
back as forced continuation), which is never what an advisory nudge wants.
Made directly executable (chmod +x, no `python3` prefix) so a missing file
hits the real "command not found" fail-open path instead of turning into an
interpreter error that could be mistaken for a block.
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
        probe = Path.home() / ".claude" / "stop-probe.log"
        probe.parent.mkdir(parents=True, exist_ok=True)
        with probe.open("a") as handle:
            handle.write(
                json.dumps(
                    {
                        "keys": sorted(payload.keys()),
                        "session_id": payload.get("session_id"),
                        "stop_hook_active": payload.get("stop_hook_active"),
                    }
                )
                + "\n"
            )
    except OSError:
        pass

    # Recursion guard: if a previous Stop hook already forced continuation,
    # do not nudge again this round — avoid an advisory loop.
    if payload.get("stop_hook_active"):
        print("{}")
        return 0

    msg = medium_aging_message(payload)
    if msg:
        print(f"context-nudge medium: {msg}", file=sys.stderr)

    if _git_dirty():
        print(
            "Knowledge loop — dirty tree; consider end-of-session "
            "(commit on invoke, ask before push).",
            file=sys.stderr,
        )

    # Plan-wave linting is Cursor-only for now (`.cursor/plans/*.plan.md`
    # files); Claude's plan mode has no persisted-file equivalent to lint.
    # Optional later per HANDOFF-claude.md — not wired here.

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
