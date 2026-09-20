#!/usr/bin/env python3
"""Claude Code UserPromptSubmit adapter — pass-through.

Always exits 0 and never sets `hookSpecificOutput` to block.

Made directly executable (chmod +x, no `python3` prefix) for the fail-open
"command not found" path, matching the other advisory Claude adapters.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
