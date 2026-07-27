#!/usr/bin/env python3
"""SessionStart advisory: pending-verification + open candidates.

Fail-open. Pass --platform when the adapter knows which agent is running.
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", default="cursor")
    args = parser.parse_args()
    platform = args.platform

    pending = _pending_open(platform)
    if pending:
        print(
            f"Knowledge loop — {pending} open pending-verification item(s) "
            f"for {platform}: {PENDING / (platform + '.md')}. "
            "Verify or check off what you can this session.",
            file=sys.stderr,
        )

    opened = _open_count()
    cwd = Path.cwd().resolve()
    # coding-agent-config on this host is $HOME (contains .agent-rules/).
    in_config = cwd == HOME or cwd == HOST or HOST in cwd.parents
    if opened and in_config:
        print(
            f"Knowledge loop — {opened} open candidate(s) under "
            f"{CANDIDATES / 'open'}. Consider the evaluate-candidates skill.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
