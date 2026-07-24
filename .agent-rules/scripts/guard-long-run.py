#!/usr/bin/env python3
"""PreToolUse/Bash hook: nudge when a long job may not be checkpointing.

SSH to this host drops a couple of times a day. A training/experiment run
that only saves at the end of an epoch can lose hours to a dropped
connection, and the loss is silent — the job is simply gone. This looks at
commands that launch a known long-running entry point and warns if nothing
on the command line suggests checkpointing is configured, or if the command
looks attached to the shell rather than detached.

Shared across projects. Each project's own hook config supplies its own
entry-point names via repeated --entry-point args, e.g.:

    guard-long-run.py --entry-point train_controlnet --entry-point train_pix2pix

Advisory: it prints to stderr and always exits 0. Checkpoint cadence usually
lives in a config file the command line does not name, so blocking here
would be wrong far more often than it would be right. The real enforcement
belongs in the training/experiment scripts themselves, which should refuse
to start without a writable checkpoint dir. Because it's advisory, it's
meant to be made executable (`chmod +x`) and invoked directly (no `python3`
prefix) — see .agent-rules/README.md's note on why advisory vs. safety-guard
scripts are invoked differently.
"""

import argparse
import json
import re
import sys

# Anything that plausibly names a checkpoint setting, in a flag or a config path.
CHECKPOINT_HINTS = re.compile(
    r"checkpoint|ckpt|save[-_]?(every|steps|interval|freq)|resume|--out[-_]weights",
    re.IGNORECASE,
)

DETACHED = re.compile(r"\bnohup\b|\bsetsid\b|&\s*$|\bdisown\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entry-point", action="append", default=[])
    args, _unknown = parser.parse_known_args()
    return args


def main():
    args = parse_args()
    if not args.entry_point:
        # Misconfigured hook config (missing --entry-point args) — say so
        # loudly rather than silently checking nothing.
        print(
            "guard-long-run.py: no --entry-point values configured, nothing to check",
            file=sys.stderr,
        )
        return

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    command = (payload.get("tool_input") or {}).get("command", "")
    if not command:
        return
    if not any(entry in command for entry in args.entry_point):
        return

    notes = []
    if not CHECKPOINT_HINTS.search(command):
        notes.append(
            "nothing on this command line names a checkpoint setting — confirm the "
            "config checkpoints at least hourly, and that resume has been tested"
        )
    if not DETACHED.search(command):
        notes.append(
            "this looks attached to the shell; an SSH drop would take the run with it "
            "(use run_in_background, or `setsid nohup ... < /dev/null &`)"
        )

    if notes:
        print("Long-run check: " + "; ".join(notes), file=sys.stderr)


if __name__ == "__main__":
    main()
