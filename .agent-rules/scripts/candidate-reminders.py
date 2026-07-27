#!/usr/bin/env python3
"""SessionStart advisory: pending-verification + open candidates.

Fail-open. Pass --platform when the adapter knows which agent is running.
Adapters may call `messages(platform)` and inject into platform-specific
context channels (Cursor: additional_context); CLI still prints stderr.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HOST = Path(__file__).resolve().parent.parent
CANDIDATES = HOST / "candidates"
OPEN_DIRS = (CANDIDATES / "open" / "project", CANDIDATES / "open" / "platform")
PENDING = CANDIDATES / "pending-verification"
HOME = Path.home().resolve()


def _open_count() -> int:
    n = 0
    for directory in OPEN_DIRS:
        if not directory.is_dir():
            continue
        n += sum(
            1
            for p in directory.iterdir()
            if p.is_file() and p.suffix == ".md" and p.name != ".gitkeep"
        )
    return n


def _pending_open(platform: str) -> int:
    path = PENDING / f"{platform}.md"
    if not path.is_file():
        return 0
    try:
        text = path.read_text()
    except OSError:
        return 0
    return sum(1 for line in text.splitlines() if line.strip().startswith("- [ ]"))


def messages(platform: str = "cursor", *, cwd: Path | None = None) -> list[str]:
    """Return advisory lines for SessionStart (may be empty)."""
    out: list[str] = []
    pending = _pending_open(platform)
    if pending:
        out.append(
            f"Knowledge loop — {pending} open pending-verification item(s) "
            f"for {platform}: {PENDING / (platform + '.md')}. "
            "Verify or check off what you can this session."
        )

    opened = _open_count()
    here = (cwd or Path.cwd()).resolve()
    # coding-agent-config on this host is $HOME (contains .agent-rules/).
    in_config = here == HOME or here == HOST or HOST in here.parents
    if opened and in_config:
        out.append(
            f"Knowledge loop — {opened} open candidate(s) under "
            f"{CANDIDATES / 'open'}. Consider the evaluate-candidates skill."
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", default="cursor")
    args = parser.parse_args()
    for line in messages(args.platform):
        print(line, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
