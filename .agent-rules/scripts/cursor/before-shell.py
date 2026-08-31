#!/usr/bin/env python3
"""beforeShellExecution hook (Cursor dialect): the host's shell guards.

Thin adapter. Every rule it enforces lives in `../guardlib/`, shared with the
Claude Code entry points in the parent directory. This file only knows Cursor's
hook contract, which differs from Claude's in both directions:

  in   JSON on stdin with a top-level `command` (not `tool_input.command`)
  out  {"permission": "allow" | "ask" | "deny", "user_message": …,
        "agent_message": …} on stdout -- not a `hookSpecificOutput` block

One script covers all three shell policies because Cursor fires a single
`beforeShellExecution` event rather than Claude's per-tool `PreToolUse`
matchers. Denials come from the two safety guards; the long-run check is
advisory, so it writes to stderr (visible in Cursor's Hooks output channel) and
still allows the command.

Wired from `~/.cursor/hooks.json`, which is shared by every project on this
host -- so per-project values (protected dirs, training entry points) are read
from the nearest `.agent-guards.json`, never passed as arguments.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guardlib import (  # noqa: E402
    destructive_git,
    destructive_rm,
    long_run,
    project_config,
    wait_loop,
)

DIALECT = "cursor"

# Keys that have carried the command string on a beforeShellExecution payload.
# `command` is what Cursor's own documented example reads; the rest are cheap
# insurance against a schema change, since a guard that silently stops matching
# is worse than one that never worked.
_COMMAND_KEYS = ("command", "shell_command", "commandLine")

# Running `rm -rf __guard_probe__` from any shell is the safe way to check that
# this hook is wired: the directory never exists, so the command is a no-op
# whether or not the guard fires, `__guard_probe__` is listed as protected in
# ~/.agent-guards.json so a working guard denies it, and the raw payload is
# recorded here either way. An empty log after a probe means Cursor never
# invoked the hook (most likely it has not reloaded hooks.json yet); a log entry
# with no `cwd` means the payload does not carry one and project config
# discovery is falling back to the process working directory.
PROBE_TOKEN = "__guard_probe__"
PROBE_LOG = Path.home() / ".cursor" / "hook-probe.log"


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
    """Best-effort branch name, for the advisory branch-discipline note only."""
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


def _log_probe(payload: dict) -> None:
    try:
        PROBE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with PROBE_LOG.open("a") as handle:
            handle.write(
                json.dumps(
                    {
                        "at": datetime.now().isoformat(timespec="seconds"),
                        "process_cwd": os.getcwd(),
                        "payload": payload,
                    }
                )
                + "\n"
            )
    except OSError:
        pass  # A diagnostic must never be the reason a shell call fails.


def _respond(permission: str, user_message: str = "", agent_message: str = "") -> None:
    response: dict[str, str] = {"permission": permission}
    if user_message:
        response["user_message"] = user_message
    if agent_message:
        response["agent_message"] = agent_message
    print(json.dumps(response))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        _respond("allow")  # Malformed input: stay out of the way.
        return 0
    if not isinstance(payload, dict):
        _respond("allow")
        return 0

    command = _command(payload)
    if PROBE_TOKEN in json.dumps(payload):
        _log_probe(payload)
    if not command:
        print(
            "cursor/before-shell.py: no command found on payload "
            f"(keys: {sorted(payload)}) -- allowing",
            file=sys.stderr,
        )
        _respond("allow")
        return 0

    reason = wait_loop.inspect(command, dialect=DIALECT)
    if reason:
        _respond(
            "deny",
            user_message="Blocked a hand-rolled wait-for-process loop.",
            agent_message=reason,
        )
        return 0

    reason = destructive_git.inspect(command)
    if reason:
        _respond(
            "deny",
            user_message="Blocked a git operation that cannot be undone.",
            agent_message=reason,
        )
        return 0

    config = project_config.load(project_config.payload_cwd(payload))

    if config.protected:
        reason = destructive_rm.inspect(command, config.protected, config.detail)
        if reason:
            _respond(
                "deny",
                user_message="Blocked an rm against a protected directory tree.",
                agent_message=reason,
            )
            return 0

    notes = long_run.notes(command, config.entry_points, dialect=DIALECT)
    if notes:
        print("Long-run check: " + "; ".join(notes), file=sys.stderr)

    for note in destructive_git.notes(command, _current_branch(payload)):
        print("git branch check: " + note, file=sys.stderr)

    _respond("allow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
