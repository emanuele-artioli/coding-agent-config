#!/usr/bin/env python3
"""Cursor sessionStart adapter — candidate / pending-verification reminders."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "candidate-reminders.py"


def main() -> int:
    try:
        json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        pass
    # Fire-and-forget advisory; sessionStart does not require a JSON body.
    subprocess.run(
        [sys.executable, str(SCRIPT), "--platform", "cursor"],
        check=False,
    )
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
