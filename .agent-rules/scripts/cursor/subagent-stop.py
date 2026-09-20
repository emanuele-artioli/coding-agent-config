#!/usr/bin/python3
"""Cursor subagentStop adapter — flag a report that breaks the contract.

Same policy as the Claude adapter (guardlib/report_contract.py): a report
missing one of the five headings, carrying a Result value that is not
PASS/FAIL/STUCK, or pasting no output under Check, is a FAIL whatever it
claims. Advisory only — printed on stderr, the Hooks channel that
cursor/stop.py already uses for its nudges, with `{}` on stdout so Cursor
never reads the advisory as a control response. Always exits 0.

The payload field that carries the child's final message is still
taken from the first live `subagentStop` log line. This adapter reads
Claude's `last_assistant_message`, `final_message`, camelCase spellings,
and a few other string fields, then stays silent when none are present.
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardlib import report_contract  # noqa: E402

PROBE_LOG = Path.home() / ".cursor" / "subagent-stop.log"

# Live 2026-09-20: subagentStop wiring is committed; the field that carries
# the child's final message is still confirmed from the first real payload.
MESSAGE_FIELDS = (
    "last_assistant_message",
    "final_message",
    "lastAssistantMessage",
    "finalMessage",
    "message",
    "text",
    "output",
    "result",
    "content",
    "response",
    "summary",
    "task",
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
