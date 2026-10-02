#!/usr/bin/env python3
"""Antigravity Stop adapter — closeout capture.

Always exits 0 for advisory hooks.
Logs side-channel probe under ~/.gemini/stop-probe.log to verify payload fields.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HOST = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_HOST / "hooks"))

from closeout_adapter import capture_payload, emit_diagnostics  # noqa: E402


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    try:
        probe = Path.home() / ".gemini" / "stop-probe.log"
        probe.parent.mkdir(parents=True, exist_ok=True)
        with probe.open("a") as handle:
            handle.write(
                json.dumps(
                    {
                        "keys": sorted(payload.keys()),
                        "context_usage_percent": payload.get("context_usage_percent")
                        or payload.get("contextUsagePercent"),
                    }
                )
                + "\n"
            )
    except OSError:
        pass

    # Capture only an explicit boundary; all adapter errors remain advisory.
    try:
        emit_diagnostics(capture_payload(payload, "antigravity"), "antigravity")
    except Exception as exc:  # pragma: no cover - defensive hook fail-open
        print(f"antigravity/closeout: adapter exception ({type(exc).__name__}); skipped", file=sys.stderr)

    print("{}", file=sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
