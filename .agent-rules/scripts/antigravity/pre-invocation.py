#!/usr/bin/env python3
"""Antigravity PreInvocation / SessionStart adapter — candidate / pending-verification reminders.

Plain stdout/stderr print on exit 0 is injected straight into session log / context.
Logs a side-channel line under ~/.gemini/pre-invocation.log so live firing can be confirmed.
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

PROBE_LOG = Path.home() / ".gemini" / "pre-invocation.log"


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
                        "session_id": payload.get("session_id") or payload.get("conversation_id"),
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
    lines = messages("antigravity", cwd=cwd_path)
    _log(payload, lines)

    for line in lines:
        print(line, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
