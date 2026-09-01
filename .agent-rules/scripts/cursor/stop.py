#!/usr/bin/python3
"""Cursor stop adapter — medium aging nudge + dirty-tree end-of-session hint.

Medium tier prints to stderr (Hooks channel). Does not set followup_message
(reserved for rare strong loops). Never auto-runs handoff.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from context_nudge import medium_aging_message  # noqa: E402

_SCRIPTS = Path(__file__).resolve().parent.parent
_LINT_SPEC = importlib.util.spec_from_file_location(
    "lint_plan_waves", _SCRIPTS / "lint_plan_waves.py"
)
_lint = importlib.util.module_from_spec(_LINT_SPEC)
assert _LINT_SPEC and _LINT_SPEC.loader
_LINT_SPEC.loader.exec_module(_lint)


def _git_dirty() -> bool:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return bool(out.stdout.strip()) if out.returncode == 0 else False
    except (OSError, subprocess.SubprocessError):
        return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}

    # Live fill-% probe: documented on preCompact only; log keys once so we
    # can confirm whether stop ever carries an undocumented field.
    fill_keys = ("context_usage_percent", "contextUsagePercent")
    for key in fill_keys:
        if key in payload:
            print(
                f"cursor/stop: saw {key}={payload[key]!r}",
                file=sys.stderr,
            )
    try:
        probe = Path.home() / ".cursor" / "stop-probe.log"
        probe.parent.mkdir(parents=True, exist_ok=True)
        with probe.open("a") as handle:
            handle.write(
                json.dumps(
                    {
                        "keys": sorted(payload.keys()),
                        "has_fill": any(k in payload for k in fill_keys),
                        "status": payload.get("status"),
                        "loop_count": payload.get("loop_count"),
                    }
                )
                + "\n"
            )
    except OSError:
        pass

    msg = medium_aging_message(payload)
    if msg:
        print(f"context-nudge medium: {msg}", file=sys.stderr)

    if _git_dirty():
        print(
            "Knowledge loop — dirty tree; consider end-of-session "
            "(commit on invoke, ask before push).",
            file=sys.stderr,
        )

    # Soft plan-waves advisory (recent plans only — avoid nagging on history).
    try:
        roots: list[Path] = [Path.home() / ".cursor" / "plans"]
        for raw in payload.get("workspace_roots") or []:
            if isinstance(raw, str) and raw:
                roots.append(Path(raw) / ".cursor" / "plans")
        plans = _lint.filter_mtime(_lint.iter_plan_files(roots), mtime_days=7.0)
        for path, reason in _lint.check_paths(plans)[:5]:
            print(f"plan-waves soft: {path.name}: {reason}", file=sys.stderr)
    except Exception:
        pass

    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
