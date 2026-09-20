#!/usr/bin/env python3
"""Claude Code Stop adapter — closeout capture.

Always exits 0: on Stop, exit 2 blocks Claude from stopping (feeds stderr
back as forced continuation), which is never what an advisory hook wants.
Made directly executable (chmod +x, no `python3` prefix) so a missing file
hits the real "command not found" fail-open path instead of turning into an
interpreter error that could be mistaken for a block.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from closeout_adapter import capture_payload, emit_diagnostics  # noqa: E402


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
    # do not run again this round — avoid an advisory loop.
    if payload.get("stop_hook_active"):
        print("{}")
        return 0

    # Closeout is a conservative backstop: only an explicit boundary in the
    # payload can write operational state, and adapter failures stay advisory.
    try:
        emit_diagnostics(capture_payload(payload, "claude"), "claude")
    except Exception as exc:  # pragma: no cover - defensive hook fail-open
        print(f"claude/closeout: adapter exception ({type(exc).__name__}); skipped", file=sys.stderr)

    # Plan-wave linting is Cursor-only for now (`.cursor/plans/*.plan.md`
    # files); Claude's plan mode has no persisted-file equivalent to lint.
    # Optional later per HANDOFF-claude.md — not wired here.

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
