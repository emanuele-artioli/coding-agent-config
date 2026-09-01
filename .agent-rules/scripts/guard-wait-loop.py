#!/usr/bin/env python3
"""PreToolUse guard (Claude Code / Copilot CLI dialect): block wait loops.

Thin adapter. The policy -- what counts as a hand-rolled process-wait loop and
why it can never work here -- lives in `guardlib/wait_loop.py`, shared with
every other agent on this host. This file only knows how Claude Code phrases a
hook: tool-call JSON on stdin with `tool_name` / `tool_input.command`, and a
`hookSpecificOutput` block on stdout to deny.

Invoked via `python3 <path>` (not direct-exec) deliberately, matching
guard-rm.py: if this script's path ever goes missing, the resulting exit 2
blocks the whole Bash call rather than silently letting a hand-rolled wait
loop through unchecked.
"""

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONPYCACHEPREFIX", "/var/tmp/emanuele-pycache")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from guardlib import wait_loop  # noqa: E402


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # Malformed input: stay out of the way.

    if payload.get("tool_name") != "Bash":
        sys.exit(0)

    command = payload.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command:
        sys.exit(0)

    reason = wait_loop.inspect(command, dialect="claude")
    if reason:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason,
                    }
                }
            )
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
