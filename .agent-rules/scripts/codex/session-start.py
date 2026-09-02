#!/usr/bin/python3
"""Codex SessionStart adapter for candidates and resume reminders.

Returns documented additionalContext and logs a side-channel probe under the
active CODEX_HOME so fresh-session firing can be verified independently.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS))

_SCRIPT = _SCRIPTS / "candidate-reminders.py"
_SPEC = importlib.util.spec_from_file_location("candidate_reminders", _SCRIPT)
_mod = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_mod)
messages = _mod.messages

from precompact_stub import resume_messages  # noqa: E402

PROBE_LOG = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "session-start.log"


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


def _cwd(payload: dict) -> Path | None:
    for key in ("cwd", "workspace_root", "workspaceRoot"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return Path(value)
    roots = payload.get("workspace_roots")
    if isinstance(roots, list) and roots and isinstance(roots[0], str):
        return Path(roots[0])
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    cwd = _cwd(payload)
    lines = messages("codex", cwd=cwd)
    lines.extend(resume_messages(cwd))
    for line in lines:
        print(line, file=sys.stderr)
    _log(payload, lines)

    if lines:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(lines),
        }}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
