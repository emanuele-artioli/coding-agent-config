"""Per-project guard values, in one file each project owns.

The *policy* is host-wide and lives in this package. The *values* it needs --
which directories are unrecoverable, which entry points are long training runs
-- are project facts, so they live in the project's own repo at
`<repo-root>/.agent-guards.json`:

    {
      "protected": ["outputs", "assets"],
      "detail": "GPU pipeline outputs / dataset and raw sources / weight symlinks",
      "entry_points": ["train_controlnet", "train_campaign"]
    }

Before this file existed, the same values were passed as CLI arguments from
each project's `.claude/settings.json`. That worked for exactly one agent:
Cursor's user-level `hooks.json` is shared by every project, so it has nowhere
to put per-project arguments. Reading them from the project instead means one
declaration serves every agent. CLI arguments still win when given, so the
existing Claude settings keep working unchanged.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_NAME = ".agent-guards.json"

DEFAULT_DETAIL = "data that is expensive or impossible to regenerate"

# Payload keys that have carried the working directory or workspace root, across
# the agents wired to these guards. Cursor's beforeShellExecution payload
# (verified 2026-07-25) sends `cwd: ""` and the real root in `workspace_roots`.
_CWD_KEYS = ("cwd", "workspace_root", "workspaceRoot", "project_root")
_CWD_LIST_KEYS = ("workspace_roots", "workspacePaths", "workspaceRoots")


@dataclass
class GuardConfig:
    protected: set[str] = field(default_factory=set)
    detail: str = DEFAULT_DETAIL
    entry_points: list[str] = field(default_factory=list)
    source: Path | None = None


def payload_cwd(payload: dict) -> Path:
    """Best guess at the directory a hook payload refers to.

    A user-level hook does not run from the project: Cursor runs user hooks
    from `~/.cursor/`, so `os.getcwd()` is the wrong answer and the payload has
    to be asked first.
    """
    for key in _CWD_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return Path(value)
    for key in _CWD_LIST_KEYS:
        value = payload.get(key)
        if isinstance(value, list) and value and isinstance(value[0], str):
            return Path(value[0])
    return Path(os.getcwd())


def find(start: Path | None = None) -> Path | None:
    """The nearest `.agent-guards.json` at or above `start`."""
    here = (start or Path(os.getcwd())).resolve()
    for directory in (here, *here.parents):
        candidate = directory / CONFIG_NAME
        if candidate.is_file():
            return candidate
    return None


def load(start: Path | None = None) -> GuardConfig:
    """Read the nearest project guard config, or return empty defaults."""
    path = find(start)
    if path is None:
        return GuardConfig()
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return GuardConfig(source=path)
    if not isinstance(data, dict):
        return GuardConfig(source=path)

    protected = data.get("protected") or []
    entry_points = data.get("entry_points") or []
    detail = data.get("detail") or DEFAULT_DETAIL
    return GuardConfig(
        protected={str(p) for p in protected if isinstance(p, (str, int))},
        detail=str(detail),
        entry_points=[str(e) for e in entry_points if isinstance(e, (str, int))],
        source=path,
    )
