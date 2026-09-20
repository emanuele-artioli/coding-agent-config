#!/usr/bin/python3
"""Codex UserPromptSubmit adapter — pass-through."""

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
