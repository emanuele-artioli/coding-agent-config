"""Policy: reject hand-rolled process-wait loops.

The harness of every agent on this host runs a shell command via
`bash -c "<the whole command string>"`, and that string *contains* the pattern
the loop greps for — so `pgrep -f` matches the watcher's own process and the
condition can never become true. The watched job finishes, the watcher spins
until timeout, and the completion goes unnoticed. This has burned >1h of wall
clock at least twice, under more than one agent.

There is also nothing to poll for: every agent here already reports a
background job's completion (Claude Code re-invokes on exit, Cursor notifies
at end of turn).

Narrow by construction — a denial needs all three of a loop keyword, a
process-liveness check, and a sleep in the body. A bare `pgrep`, a bare
`sleep`, or a polling loop over something other than process liveness (a file,
an HTTP endpoint, a CI run) passes.

Heredoc bodies are stripped first, as in `destructive_git` and
`destructive_rm`: a loop written *about* rather than run — in a PR body, a
rule file, this docstring — is prose, not a command. Missing that call is
what blocked a `gh pr create` whose `--body` text quoted the pattern
(2026-09-01). The accepted cost is the one the other two policies already
take: a real waiter piped into `bash <<EOF` is not caught. Deliberate —
see `shell.strip_heredocs`.
"""

from __future__ import annotations

import re

from . import shell

LOOP = re.compile(r"\b(until|while)\b")
SLEEP = re.compile(r"\bsleep\s+[\d.]+")
# Process-liveness probes -- the class of condition that can self-match.
PROBE = re.compile(
    r"\bpgrep\b|\bpidof\b|\bkill\s+-0\b|\bps\s+(-p|-e|aux|ax)\b|\bpkill\s+-0\b"
)

_PREAMBLE = (
    "Blocked: this looks like a hand-rolled wait-for-process loop. It cannot "
    'work here -- the harness runs your command as `bash -c "<whole command '
    'string>"`, so the loop\'s own process matches its own pgrep/ps pattern '
    "and the condition never becomes true. The job finishes and the watcher "
    "spins until timeout.\n\n"
)

# Each agent's replacement for the loop, named in that agent's own vocabulary.
# Keeping these here rather than in the adapters means the *policy* and the
# advice stay in one file; only the output format is per-platform.
ALTERNATIVES = {
    "claude": (
        "Use instead:\n"
        "  - Bash with run_in_background: true -- detaches, survives across "
        "turns, and re-invokes you on exit with the output-file path. No "
        "polling.\n"
        "  - Monitor -- if you want progress events during the run. Filter for "
        "failure signatures (Traceback|Error|Killed|OOM) too, not just "
        "success.\n"
        "  - Foreground Bash with an explicit timeout (max 600000 ms) if the "
        "job genuinely finishes in under 10 minutes.\n\n"
        "See the waiting rule in the global CLAUDE.md."
    ),
    "cursor": (
        "Use instead:\n"
        "  - Shell with block_until_ms: 0 -- detaches, streams to a terminal "
        "file, and notifies you on completion at the end of the turn.\n"
        "  - AwaitShell with that shell_id, if the next step genuinely cannot "
        "proceed without the result. Add `pattern` to return early on a known "
        "success or failure line.\n"
        "  - notify_on_output, if you want progress while it runs. Match "
        "failure signatures (Traceback|Error|Killed|OOM) too, not just "
        "success.\n\n"
        "See the waiting rule in .agent-rules/harness/cursor.md."
    ),
}


def reason(dialect: str = "claude") -> str:
    """The full deny message, with alternatives named for the given agent."""
    return _PREAMBLE + ALTERNATIVES.get(dialect, ALTERNATIVES["claude"])


def inspect(command: str, dialect: str = "claude") -> str | None:
    """Return a deny reason if `command` is a hand-rolled waiter, else None."""
    if not command:
        return None
    code = shell.strip_heredocs(command)
    if LOOP.search(code) and PROBE.search(code) and SLEEP.search(code):
        return reason(dialect)
    return None
