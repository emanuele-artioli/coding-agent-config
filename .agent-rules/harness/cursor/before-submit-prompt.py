#!/usr/bin/python3
"""Cursor beforeSubmitPrompt — always continue.

Documented outputs: continue. Fill-% probe stays on stderr if an
undocumented field appears.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({"continue": True}))
        return 0
    if not isinstance(payload, dict):
        print(json.dumps({"continue": True}))
        return 0

    # Probe for undocumented fill %.
    for key in ("context_usage_percent", "contextUsagePercent"):
        if key in payload:
            print(
                f"cursor/before-submit-prompt: saw {key}={payload[key]!r}",
                file=sys.stderr,
            )

    print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
