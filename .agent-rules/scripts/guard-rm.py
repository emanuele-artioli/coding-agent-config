#!/usr/bin/env python3
"""PreToolUse guard: block destructive rm against a project's protected dirs.

Shared across projects. Each project's own .claude/settings.json supplies
the protected directory names and a human-readable detail for the deny
message via CLI args, e.g.:

    guard-rm.py --protected outputs --protected assets \\
        --detail "GPU pipeline outputs / dataset and raw sources / weight symlinks"

Reads the Claude Code hook JSON on stdin. If a Bash command actually runs
`rm` against the whole tree of one of the protected directories, it denies
the call and points at removing a specific <dir>/<id>/ subdirectory instead.
Everything else is allowed through.

Deleting a single <dir>/<id>/ subdirectory stays allowed. The word "rm" or a
protected name merely appearing inside a string literal (echo/printf/git
commit -m) does NOT trigger a block -- only an rm command whose target is a
protected tree does.

Invoked via `python3 <path>` (not direct-exec) deliberately: if this script's
path ever goes missing, the resulting exit 2 blocks the whole Bash call
rather than silently letting a destructive rm through. Fail-closed is the
right default for an actual safety guard.
"""
import argparse
import json
import re
import shlex
import sys

SEGMENT_SPLIT = re.compile(r"&&|\|\||[;&|\n]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protected", action="append", default=[])
    parser.add_argument(
        "--detail",
        default="data that is expensive or impossible to regenerate",
    )
    args, _unknown = parser.parse_known_args()
    return args


def _deny(dirname: str, detail: str) -> None:
    reason = (
        f"Blocked: this rm would delete the whole '{dirname}/' tree, which is "
        f"expensive or impossible to regenerate ({detail}). If you meant to "
        f"discard one run, delete a specific {dirname}/<id>/ directory instead. "
        "See CLAUDE.md."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def _normalize(arg: str) -> str:
    """Reduce an rm argument to the top-level dir it would wipe, or '' if it
    targets something deeper (a specific subdir/file, which is allowed)."""
    a = arg.strip().lstrip("./").rstrip("/")
    a = re.sub(r"/\*$", "", a)  # dir/* -> dir
    return a


def main() -> int:
    args = parse_args()
    protected = set(args.protected)
    if not protected:
        # Misconfigured settings.json (missing --protected args) -- say so
        # loudly rather than silently behaving as if nothing were protected.
        print(
            "guard-rm.py: no --protected dirs configured, nothing to check",
            file=sys.stderr,
        )
        return 0

    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # never block on unparseable input
    if data.get("tool_name") != "Bash":
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not cmd:
        return 0

    for segment in SEGMENT_SPLIT.split(cmd):
        try:
            tokens = shlex.split(segment)
        except ValueError:
            tokens = segment.split()
        # Strip leading env-assignments and sudo so we find the real command.
        i = 0
        while i < len(tokens) and (tokens[i] == "sudo" or "=" in tokens[i]
                                   and re.match(r"^\w+=", tokens[i])):
            i += 1
        if i >= len(tokens):
            continue
        if tokens[i].split("/")[-1] != "rm":
            continue  # this simple-command is not rm
        # Inspect rm's non-flag arguments.
        for arg in tokens[i + 1:]:
            if arg.startswith("-"):
                continue
            if _normalize(arg) in protected:
                _deny(_normalize(arg), args.detail)
                return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
