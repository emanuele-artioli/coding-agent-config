#!/usr/bin/python3
"""Codex PreToolUse(Bash) adapter for the shared host shell policies.

Every enforced rule lives in ../guardlib. This file only translates Codex JSON:
tool_input.command on input and hookSpecificOutput on output. Safety checks
deny; long-run and branch checks add advisory context. Per-project values come
from the nearest .agent-guards.json.
"""
from __future__ import annotations

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

DIALECT = "codex"

# Codex documents tool_input.command. Top-level aliases are cheap insurance for
# compatibility payloads; a silently inert guard is worse than a tolerant one.
_COMMAND_KEYS = ("command", "shell_command", "commandLine")

# Reserved safe live probe. The target never exists; this adapter denies it
# explicitly and records the raw payload under CODEX_HOME.
PROBE_TOKEN = "__guard_probe__"
PROBE_LOG = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "hook-probe.log"


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
    """Best-effort branch name, for the advisory branch-discipline note only.

    Must not run on every shell call. On this host a `git rev-parse` against
    a workspace with no `.git` walks up into the home directory and can sit
    in NFS D-state long enough that the synchronous hook timeout kills
    the hook, and then *every* command is blocked, not just git.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_config.payload_cwd(payload) or None,
            capture_output=True,
            text=True,
            timeout=1,
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
    detail = agent_message or user_message
    response: dict = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": permission,
        }
    }
    if detail:
        if permission == "deny":
            response["hookSpecificOutput"]["permissionDecisionReason"] = detail
        else:
            response["hookSpecificOutput"]["additionalContext"] = detail
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
        _respond("deny", agent_message="Blocked the reserved safe hook probe.")
        return 0
    if not command:
        print(
            "codex/pre-tool-use.py: no command found on payload "
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
    notes.extend(
        destructive_git.notes(command, lambda: _current_branch(payload))
    )
    _respond("allow", agent_message="\n".join(notes))
    return 0
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        # Never failClosed a Shell call because the adapter crashed.
        # The git policy is recoverability of the *command*; a sick
        # checker must not block commit/push/merge.
        print(
            f"codex/pre-tool-use.py: uncaught {exc!r} -- allowing",
            file=sys.stderr,
        )
        _respond("allow")
        sys.exit(0)
