#!/usr/bin/env python3
"""PreToolUse guard (Claude Code dialect): block rm against protected dirs.

Thin adapter. The policy lives in `guardlib/destructive_rm.py`, shared with
every other agent on this host; this file only knows Claude Code's hook
dialect (tool-call JSON on stdin, `hookSpecificOutput` on stdout).

The protected directory names come from either source:

    guard-rm.py --protected outputs --protected assets \\
        --detail "GPU pipeline outputs / dataset and raw sources"

or, when no `--protected` is given, the nearest `.agent-guards.json` at or
above the session's working directory. The file is preferred for new wiring --
it is the only form Cursor can use, since its user-level hooks.json is shared
by every project and has nowhere to put per-project arguments.

Invoked via `python3 <path>` (not direct-exec) deliberately: if this script's
path ever goes missing, the resulting exit 2 blocks the whole Bash call rather
than silently letting a destructive rm through. Fail-closed is the right
default for an actual safety guard.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from guardlib import destructive_rm, project_config  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protected", action="append", default=[])
    parser.add_argument("--detail", default=None)
    args, _unknown = parser.parse_known_args()
    return args


def _deny(reason: str) -> None:
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


def main() -> int:
    args = parse_args()

    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # never block on unparseable input
    if data.get("tool_name") != "Bash":
        return 0
    command = (data.get("tool_input") or {}).get("command", "")
    if not command:
        return 0

    protected = set(args.protected)
    detail = args.detail or project_config.DEFAULT_DETAIL
    if not protected:
        config = project_config.load(project_config.payload_cwd(data))
        protected = config.protected
        detail = args.detail or config.detail

    if not protected:
        # Neither CLI args nor a project .agent-guards.json -- say so loudly
        # rather than silently behaving as if nothing were protected.
        print(
            "guard-rm.py: no protected dirs configured (no --protected args and "
            "no .agent-guards.json found), nothing to check",
            file=sys.stderr,
        )
        return 0

    reason = destructive_rm.inspect(command, protected, detail)
    if reason:
        _deny(reason)
    return 0


if __name__ == "__main__":
    sys.exit(main())
