#!/usr/bin/python3
"""Cursor subagentStop adapter — flag a report that breaks the contract.

Same policy as the Claude adapter (guardlib/report_contract.py): a report
missing one of the five headings, carrying a Result value that is not
PASS/FAIL/STUCK, or pasting no output under Check, is a FAIL whatever it
claims. Advisory only — printed on stderr, the Hooks channel that
cursor/stop.py already uses for its nudges, with `{}` on stdout so Cursor
never reads the advisory as a control response. Always exits 0.

**Pending verification — the payload field name is unverified.** No live
`subagentStop` payload has been observed on this host, and cursor/stop.py
gives no clue: its own payload carries session-shaped keys (status,
loop_count, workspace_roots) and no final-message field at all. So this
reads `last_assistant_message` (the Claude name) and `final_message`, plus
their camelCase spellings, and stays silent when neither is present. Once
a real payload is seen, trim this list to the true field. Wiring the hook
into Cursor's settings is the senior's step.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# The interpreter reads PYTHONPYCACHEPREFIX at startup, before this script
# runs, so assign sys.pycache_prefix directly to keep .pyc files off NFS.
sys.pycache_prefix = os.environ.get("PYTHONPYCACHEPREFIX") or "/var/tmp/emanuele-pycache"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardlib import report_contract  # noqa: E402

# Unverified — see the module docstring.
MESSAGE_FIELDS = (
    "last_assistant_message",
    "final_message",
    "lastAssistantMessage",
    "finalMessage",
)


def _report(payload: dict) -> str:
    for field in MESSAGE_FIELDS:
        value = payload.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    report = _report(payload)
    if report:
        found = report_contract.problems(report)
        if found:
            print(report_contract.message(found), file=sys.stderr)

    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
