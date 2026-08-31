#!/usr/bin/env python3
"""PreToolUse shell guard (Antigravity dialect): the host's shell policies.

Thin adapter over `guardlib/`. Antigravity denies by **non-zero exit status**
rather than the JSON verdict Claude Code and Cursor return, and its message
goes to stderr — so one script covers every shell policy the way Cursor's
`before-shell.py` does, but answers in this platform's dialect.

Policies applied, all shared verbatim with the other harnesses:

  deny     `destructive_git`  — git operations that cannot be undone
  deny     `destructive_rm`   — rm against a project's protected trees
  deny     `wait_loop`        — hand-rolled wait-for-process loops
  advise   `long_run`         — checkpointing reminders, stderr only
  advise   `destructive_git.notes` — committing straight to main/master

**Not verified live.** This was written from a Claude Code session, so the
payload keys it reads and the exit-status contract are inferred from
`antigravity/guard-model-family.py` rather than observed. Wire and check it
from an Antigravity session; there is a row for it in
`candidates/pending-verification/antigravity.md`. Until then it is dormant —
an unwired hook denies nothing.

Wire with an **absolute** path in `~/.gemini/config/hooks.json` (relative
paths exit 127 and silently bypass), invoked as `python3 <absolute-path>` so a
missing file fails closed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardlib import (  # noqa: E402
    destructive_git,
    destructive_rm,
    long_run,
    project_config,
    wait_loop,
)

DIALECT = "antigravity"
DENY = 2  # non-zero blocks; 2 matches the model-family guard on this platform

_COMMAND_KEYS = ("command", "shell_command", "commandLine")


def _command(payload: dict) -> str:
    for key in _COMMAND_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    nested = payload.get("tool_input")
    if isinstance(nested, dict):
        value = nested.get("command")
        if isinstance(value, str):
            return value
    return ""


def _current_branch(payload: dict) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_config.payload_cwd(payload) or None,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # malformed input: stay out of the way
    if not isinstance(payload, dict):
        return 0

    command = _command(payload)
    if not command:
        print(
            "antigravity/before-shell.py: no command on payload "
            f"(keys: {sorted(payload)}) -- allowing",
            file=sys.stderr,
        )
        return 0

    for reason in (
        destructive_git.inspect(command),
        wait_loop.inspect(command, dialect=DIALECT),
    ):
        if reason:
            print(reason, file=sys.stderr)
            return DENY

    config = project_config.load(project_config.payload_cwd(payload))
    if config.protected:
        reason = destructive_rm.inspect(command, config.protected, config.detail)
        if reason:
            print(reason, file=sys.stderr)
            return DENY

    notes = long_run.notes(command, config.entry_points, dialect=DIALECT)
    if notes:
        print("Long-run check: " + "; ".join(notes), file=sys.stderr)
    for note in destructive_git.notes(command, _current_branch(payload)):
        print("git branch check: " + note, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
