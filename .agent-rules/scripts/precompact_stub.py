"""Pre-compact resume stub — bridge to handoff, not a second state machine.

PreCompact payloads do not carry the conversation transcript, so this module
cannot invent "what was done." It writes a fixed empty template the agent can
fill (or replace with a full HANDOFF.md) and lets SessionStart re-point at a
recent stub / HANDOFF after compaction.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

HOST = Path(__file__).resolve().parent.parent
PRECOMPACT_DIR = HOST / "var" / "precompact"
STUB_MAX_AGE_SEC = 48 * 60 * 60

_SAFE_ID = re.compile(r"[^a-zA-Z0-9._-]+")

STUB_TEMPLATE = """# Pre-compact resume stub

Written automatically when compaction was imminent. The hook has **no**
transcript — fill the sections below (or write a full `HANDOFF.md` and point
at it) before relying on auto-summary. After compact / on a fresh session,
read this file first.

- **Prefer** a full `handoff` → `HANDOFF.md` at the project root if you still
  have turns left; this stub is a bridge, not a replacement.

## Task (one paragraph)



## Done and verified



## In progress



## Running or queued jobs (and how to check them)



## Next three steps



## Landmarks (files / commands)



"""


def safe_conversation_id(raw: str) -> str:
    """Filesystem-safe id; empty / junk collapses to 'unknown'."""
    cleaned = _SAFE_ID.sub("_", (raw or "").strip()).strip("._-")
    return (cleaned[:200] if cleaned else "unknown")


def stub_path_for(conversation_id: str) -> Path:
    return PRECOMPACT_DIR / f"{safe_conversation_id(conversation_id)}.md"


def write_stub(conversation_id: str) -> Path | None:
    """Create or refresh the stub template. Fail-open: return None on I/O error."""
    path = stub_path_for(conversation_id)
    try:
        PRECOMPACT_DIR.mkdir(parents=True, exist_ok=True)
        # Refresh mtime even if content already matches, so SessionStart age gate works.
        path.write_text(STUB_TEMPLATE)
        return path
    except OSError:
        return None


def _age_ok(path: Path, *, max_age_sec: float, now: float | None = None) -> bool:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return False
    clock = time.time() if now is None else now
    return (clock - mtime) <= max_age_sec


def most_recent_stub(
    *, max_age_sec: float = STUB_MAX_AGE_SEC, now: float | None = None
) -> Path | None:
    """Newest stub under PRECOMPACT_DIR within max_age_sec, or None."""
    if not PRECOMPACT_DIR.is_dir():
        return None
    newest: Path | None = None
    newest_mtime = -1.0
    try:
        entries = list(PRECOMPACT_DIR.iterdir())
    except OSError:
        return None
    for path in entries:
        if not path.is_file() or path.suffix != ".md":
            continue
        if not _age_ok(path, max_age_sec=max_age_sec, now=now):
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime > newest_mtime:
            newest = path
            newest_mtime = mtime
    return newest


def handoff_path(cwd: Path | None) -> Path | None:
    if cwd is None:
        return None
    try:
        candidate = cwd.resolve() / "HANDOFF.md"
    except OSError:
        return None
    return candidate if candidate.is_file() else None


def resume_messages(
    cwd: Path | None = None,
    *,
    max_age_sec: float = STUB_MAX_AGE_SEC,
    now: float | None = None,
) -> list[str]:
    """One-line SessionStart pointers at a recent stub and/or project HANDOFF."""
    out: list[str] = []
    stub = most_recent_stub(max_age_sec=max_age_sec, now=now)
    if stub is not None:
        out.append(
            f"Pre-compact resume stub (fill or replace with HANDOFF.md): {stub}"
        )
    handoff = handoff_path(cwd)
    if handoff is not None and _age_ok(handoff, max_age_sec=max_age_sec, now=now):
        out.append(f"Recent project HANDOFF.md — resume from: {handoff}")
    return out
