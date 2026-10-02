#!/usr/bin/python3
"""Cursor subagentStop adapter — flag a report that breaks the contract.

Wave 0.1 (2026-09-20): subagentStop fires. The native payload does not
contain the child's final text. `task` is the prompt, not the child's last
message. A broken report contract cannot reach the parent.

Stay silent unless a real final-text field appears
(`last_assistant_message`, `final_message`, and their camelCase
spellings). Do not treat `task` or other prompt/status keys as the
child's last message.

Same policy as the Claude adapter (guardlib/report_contract.py): a report
missing one of the five headings, carrying a Result value that is not
PASS/FAIL/STUCK, or pasting no output under Check, is a FAIL whatever it
claims. Advisory only — printed on stderr, the Hooks channel that
cursor/stop.py already uses for its nudges, with `{}` on stdout so Cursor
never reads the advisory as a control response. Always exits 0.

It always writes payload keys to `~/.cursor/subagent-stop.log`.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# The interpreter reads PYTHONPYCACHEPREFIX at startup, before this script
# runs, so assign sys.pycache_prefix directly to keep .pyc files off NFS.
sys.pycache_prefix = os.environ.get("PYTHONPYCACHEPREFIX") or "/var/tmp/emanuele-pycache"

_HOST = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_HOST / "hooks"))

from guardlib import report_contract  # noqa: E402

PROBE_LOG = Path.home() / ".cursor" / "subagent-stop.log"

# Wave 0.1 (2026-09-20): native payload has no child-final-text field.
# Stay silent unless one of these real final-text names appears.
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

    try:
        PROBE_LOG.parent.mkdir(parents=True, exist_ok=True)
        strings = {
            key: len(value)
            for key, value in payload.items()
            if isinstance(value, str)
        }
        with PROBE_LOG.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "keys": sorted(payload.keys()),
                        "string_lengths": strings,
                        "matched_message_field": next(
                            (
                                field
                                for field in MESSAGE_FIELDS
                                if isinstance(payload.get(field), str)
                                and str(payload.get(field)).strip()
                            ),
                            None,
                        ),
                        "subagent_type": payload.get("subagent_type"),
                        "subagent_model": payload.get("subagent_model")
                        or payload.get("model"),
                        "status": payload.get("status"),
                    }
                )
                + "\n"
            )
    except OSError:
        pass

    report = _report(payload)
    if report:
        found = report_contract.problems(report)
        if found:
            print(report_contract.message(found), file=sys.stderr)

    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
