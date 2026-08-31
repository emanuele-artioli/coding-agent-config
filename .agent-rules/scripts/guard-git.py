#!/usr/bin/env python3
"""PreToolUse guard (Claude Code dialect): block irreversible git operations.

Thin adapter. The policy lives in `guardlib/destructive_git.py`, shared with
every other agent on this host; this file only knows Claude Code's hook
dialect (tool-call JSON on stdin, `hookSpecificOutput` on stdout).

The bargain this guard exists to make explicit: an agent should not need
permission for anything it can undo — commit, push a branch, merge, rebase,
`reset --hard` — and should be stopped from the short list it cannot. Denying
the second is what makes allowing the first reasonable.

Committing straight to `main`/`master` is *not* denied; it is reversible. It
does produce an advisory line on stderr, because the host rules ask for a
branch so intermediate work can be dropped and parallel sessions do not
collide.

Invoked via `python3 <path>` (not direct-exec) deliberately: if this script's
path ever goes missing, the resulting exit 2 blocks the Bash call rather than
silently letting a force push through. Fail-closed is the right default for a
safety guard.
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from guardlib import destructive_git  # noqa: E402


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


def _current_branch(cwd: str | None) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=1,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # never block on unparseable input
    if data.get("tool_name") != "Bash":
        return 0
    command = (data.get("tool_input") or {}).get("command", "")
    if not command:
        return 0

    reason = destructive_git.inspect(command)
    if reason:
        _deny(reason)
        return 0

    # Advisory only. Branch discipline is a preference, not a safety boundary,
    # and a guard that blocks reversible things trains people to route around it.
    # The resolver is passed *uncalled*: `notes` runs it only for a commit or a
    # push, so an ordinary shell call never spawns git. See the note in
    # `guardlib/destructive_git.notes`.
    for note in destructive_git.notes(command, lambda: _current_branch(data.get("cwd"))):
        print("git branch check: " + note, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
