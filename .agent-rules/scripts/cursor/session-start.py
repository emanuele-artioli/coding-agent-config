#!/usr/bin/env python3
"""Cursor sessionStart adapter — candidate / pending-verification reminders.

Returns `additional_context` per Cursor's sessionStart contract. Also logs a
side-channel line under ~/.cursor/session-start.log so live firing can be
confirmed even when Cursor drops additional_context (known IDE race).
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

PROBE_LOG = Path.home() / ".cursor" / "session-start.log"


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
                        "session_id": payload.get("session_id")
                        or payload.get("conversation_id"),
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

    lines = messages("cursor")
    for line in lines:
        print(line, file=sys.stderr)
    _log(payload, lines)

    if lines:
        print(json.dumps({"additional_context": "\n".join(lines)}))
    else:
        print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
