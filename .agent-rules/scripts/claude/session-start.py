#!/usr/bin/env python3
"""Claude Code SessionStart adapter — candidate / pending-verification reminders.

Plain stdout on exit 0 is injected straight into Claude's context (no
hookSpecificOutput wrapper needed for this event). Also logs a side-channel
line under ~/.claude/session-start.log so live firing can be confirmed
independent of whether the injected text is visible in a given transcript.

Advisory only: SessionStart cannot block regardless of exit code, but this is
still made directly executable (chmod +x, no `python3` prefix) so a missing
file hits the real "command not found" fail-open path rather than an
interpreter error.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent.parent / "candidate-reminders.py"
_SPEC = importlib.util.spec_from_file_location("candidate_reminders", _SCRIPT)
_mod = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_mod)
messages = _mod.messages

PROBE_LOG = Path.home() / ".claude" / "session-start.log"


def _log(payload: dict, lines: list[str]) -> None:
    try:
        PROBE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with PROBE_LOG.open("a") as handle:
            handle.write(
                json.dumps(
                    {
                        "at": datetime.now().isoformat(timespec="seconds"),
                        "payload_keys": sorted(payload.keys())
                        if isinstance(payload, dict)
                        else [],
                        "session_id": payload.get("session_id"),
                        "source": payload.get("source"),
                        "lines": lines,
                    }
                )
                + "\n"
            )
    except OSError:
        pass


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    cwd = payload.get("cwd")
    cwd_path = Path(cwd) if isinstance(cwd, str) and cwd else None
    lines = messages("claude", cwd=cwd_path)
    _log(payload, lines)

    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
