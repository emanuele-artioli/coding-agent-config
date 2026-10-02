#!/usr/bin/env python3
"""Claude Code SubagentStop adapter — flag a report that breaks the contract.

The report contract (skills/session/SKILL.md) says a report missing a
heading, or with no pasted output, is a FAIL whatever its Result line
says. A parent reading a confident `## Result: PASS` will not notice the
missing evidence on its own, so this hook names the defect for it.

Advisory only, and always exits 0: the child has already finished, there
is nothing to block, and a non-zero exit on a stop-shaped event turns an
advisory into a forced continuation. Bad JSON, a missing field, or a
non-string message all fail open — the report is simply not checked.

Wiring this into ~/.claude/settings.json (PreToolUse-style `SubagentStop`
entry) is the senior's step; nothing here touches any settings file.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# PYTHONPYCACHEPREFIX is read by the interpreter at startup, before this
# line runs, so setting it in os.environ here would be a no-op — assign
# sys.pycache_prefix directly, which does apply to imports below.
sys.pycache_prefix = os.environ.get("PYTHONPYCACHEPREFIX") or "/var/tmp/emanuele-pycache"

_HOST = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_HOST / "hooks"))

from guardlib import report_contract  # noqa: E402


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0

    report = payload.get("last_assistant_message")
    if not isinstance(report, str) or not report.strip():
        return 0

    found = report_contract.problems(report)
    if found:
        print(json.dumps({"systemMessage": report_contract.message(found)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
