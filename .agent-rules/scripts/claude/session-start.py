#!/usr/bin/env python3
"""Claude Code SessionStart adapter — candidate / pending-verification reminders.

Plain stdout on exit 0 is injected straight into Claude's context (no
hookSpecificOutput wrapper needed for this event). Also logs a side-channel
line under ~/.claude/session-start.log so live firing can be confirmed
independent of whether the injected text is visible in a given transcript.

Advisory only: SessionStart cannot block regardless of exit code, but this is
still made directly executable (chmod +x, no `python3` prefix) so a missing
file hits the real "command not found" fail-open path rather than an
interpreter error.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS))

_SCRIPT = _SCRIPTS / "candidate-reminders.py"
_SPEC = importlib.util.spec_from_file_location("candidate_reminders", _SCRIPT)
_mod = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_mod)
messages = _mod.messages

from precompact_stub import resume_messages  # noqa: E402

PROBE_LOG = Path.home() / ".claude" / "session-start.log"


def _log(payload: dict, lines: list[str]) -> None:
    try:
        PROBE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with PROBE_LOG.open("a") as handle:
            handle.write(
                json.dumps(
                    {
                        "at": datetime.now().isoformat(timespec="seconds"),
                        "payload_keys": sorted(payload.keys())
                        if isinstance(payload, dict)
                        else [],
                        "session_id": payload.get("session_id"),
                        "source": payload.get("source"),
                        "lines": lines,
                    }
                )
                + "\n"
            )
    except OSError:
        pass


def _verify_lines() -> list[str]:
    """Report only what is actually broken, and only if checking is cheap.

    `--fast --quiet` drops the checks that spawn processes and prints nothing
    when everything passes, so a healthy session sees no noise. Failures are
    surfaced because the two kinds this catches -- a guard wired nowhere, a
    symlink pointing at a directory this host does not have -- are invisible
    until the moment they matter, and by then the session has already acted.
    """
    try:
        out = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent.parent / "verify.py"),
             "--fast", "--quiet"],
            capture_output=True, text=True, timeout=25,
        )
    except (OSError, subprocess.SubprocessError):
        return []  # never let a self-check stop a session starting
    text = (out.stdout or "").strip()
    if not text:
        return []
    return ["Config check found problems (python3 .agent-rules/scripts/verify.py):", text]


def _refresh_host_rules() -> None:
    """Regenerate Claude's split copy of AGENTS.md before the session reads it.

    `~/.claude/CLAUDE.md` imports a *generated* core, which is the one way this
    layout could bite: edit AGENTS.md, forget to sync, and every later session
    quietly reads yesterday's rules. Regenerating here bounds that to a single
    session. Failures are swallowed on purpose — a rules-formatting problem
    must never be the reason a session cannot start.
    """
    try:
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent.parent / "sync_host_rules.py")],
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    _refresh_host_rules()
    lines_from_verify = _verify_lines()

    cwd = payload.get("cwd")
    cwd_path = Path(cwd) if isinstance(cwd, str) and cwd else None
    lines = messages("claude", cwd=cwd_path)
    lines.extend(resume_messages(cwd_path))
    lines.extend(lines_from_verify)
    _log(payload, lines)

    for line in lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
