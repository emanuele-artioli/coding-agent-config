#!/usr/bin/env python3
"""Cursor preCompact adapter — strong handoff / end-of-session nudge."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from context_nudge import strong_precompact_message  # noqa: E402


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    msg = strong_precompact_message(payload)
    print(json.dumps({"user_message": msg}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
