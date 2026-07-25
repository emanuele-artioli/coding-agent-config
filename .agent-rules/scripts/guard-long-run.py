#!/usr/bin/env python3
"""PreToolUse hook (Claude Code dialect): nudge when a long job looks unsafe.

Thin adapter over `guardlib/long_run.py`. Advisory: it prints to stderr and
always exits 0, because checkpoint cadence usually lives in a config file the
command line never names.

Entry-point names come from repeated `--entry-point` args or, when none are
given, the nearest `.agent-guards.json` at or above the working directory.

Because it's advisory, it's meant to be made executable (`chmod +x`) and
invoked directly (no `python3` prefix) -- see .agent-rules/README.md's note on
why advisory and safety-guard scripts are invoked differently.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from guardlib import long_run, project_config  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entry-point", action="append", default=[])
    args, _unknown = parser.parse_known_args()
    return args


def main() -> None:
    args = parse_args()

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    command = (payload.get("tool_input") or {}).get("command", "")
    if not command:
        return

    entry_points = list(args.entry_point)
    if not entry_points:
        entry_points = project_config.load(
            project_config.payload_cwd(payload)
        ).entry_points

    if not entry_points:
        # Misconfigured hook config -- say so loudly rather than silently
        # checking nothing.
        print(
            "guard-long-run.py: no entry points configured (no --entry-point "
            "args and no .agent-guards.json found), nothing to check",
            file=sys.stderr,
        )
        return

    notes = long_run.notes(command, entry_points, dialect="claude")
    if notes:
        print("Long-run check: " + "; ".join(notes), file=sys.stderr)


if __name__ == "__main__":
    main()
