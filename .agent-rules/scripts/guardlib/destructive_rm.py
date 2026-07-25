"""Policy: reject `rm` against a project's protected directory trees.

A protected tree is one that is expensive or impossible to regenerate --
`outputs/` (GPU runs costing minutes to hours) and `assets/` (datasets, raw
sources, weight symlinks) in the projects on this host. Deleting one specific
`<dir>/<id>/` subdirectory stays allowed; only wiping the whole tree is denied.

The word "rm", or a protected name merely appearing inside a string literal
(`echo`, `printf`, `git commit -m`), does not trigger a denial -- only an `rm`
command whose own target is a protected tree does.
"""

from __future__ import annotations

import re
import shlex

SEGMENT_SPLIT = re.compile(r"&&|\|\||[;&|\n]")
_ENV_ASSIGNMENT = re.compile(r"^\w+=")


def reason(dirname: str, detail: str) -> str:
    return (
        f"Blocked: this rm would delete the whole '{dirname}/' tree, which is "
        f"expensive or impossible to regenerate ({detail}). If you meant to "
        f"discard one run, delete a specific {dirname}/<id>/ directory instead. "
        "See the project's AGENTS.md."
    )


def _normalize(arg: str) -> str:
    """Reduce an rm argument to the top-level dir it would wipe.

    Returns something outside `protected` for a target deeper than one level
    (a specific subdir or file), which is how those stay allowed.
    """
    a = arg.strip().lstrip("./").rstrip("/")
    return re.sub(r"/\*$", "", a)  # dir/* -> dir


def _command_words(segment: str) -> list[str]:
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()


def offending_dir(command: str, protected: set[str]) -> str | None:
    """The protected directory this command would wipe, or None."""
    if not command or not protected:
        return None

    for segment in SEGMENT_SPLIT.split(command):
        tokens = _command_words(segment)
        # Skip leading env-assignments and sudo to find the real command word.
        i = 0
        while i < len(tokens) and (
            tokens[i] == "sudo" or _ENV_ASSIGNMENT.match(tokens[i])
        ):
            i += 1
        if i >= len(tokens):
            continue
        if tokens[i].split("/")[-1] != "rm":
            continue  # this simple-command is not rm
        for arg in tokens[i + 1 :]:
            if arg.startswith("-"):
                continue
            target = _normalize(arg)
            if target in protected:
                return target
    return None


def inspect(command: str, protected: set[str], detail: str) -> str | None:
    """Return a deny reason if `command` wipes a protected tree, else None."""
    target = offending_dir(command, protected)
    return reason(target, detail) if target else None
