#!/usr/bin/python3
"""Codex Stop adapter — closeout capture and plan-waves advisory.

Does not set followup_message. Never auto-runs handoff.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

_HOST = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_HOST / "hooks"))

from closeout_adapter import capture_payload, emit_diagnostics  # noqa: E402

_SCRIPTS = _HOST / "scripts"
_LINT_SPEC = importlib.util.spec_from_file_location(
    "lint_plan_waves", _SCRIPTS / "lint_plan_waves.py"
)
_lint = importlib.util.module_from_spec(_LINT_SPEC)
assert _LINT_SPEC and _LINT_SPEC.loader
_LINT_SPEC.loader.exec_module(_lint)


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
                f"codex/stop: saw {key}={payload[key]!r}",
                file=sys.stderr,
            )
    try:
        probe = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "stop-probe.log"
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
    notices: list[str] = []

    # Explicit boundary signals only; the Stop hook itself is not completion
    # evidence.  The adapter is fail-open so it cannot hold up Codex.
    try:
        emit_diagnostics(capture_payload(payload, "codex"), "codex")
    except Exception as exc:  # pragma: no cover - defensive hook fail-open
        print(f"codex/closeout: adapter exception ({type(exc).__name__}); skipped", file=sys.stderr)

    # Soft plan-waves advisory (recent plans only — avoid nagging on history).
    try:
        roots: list[Path] = [Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "plans"]
        for raw in payload.get("workspace_roots") or []:
            if isinstance(raw, str) and raw:
                roots.append(Path(raw) / ".codex" / "plans")
        plans = _lint.filter_mtime(_lint.iter_plan_files(roots), mtime_days=7.0)
        for path, reason in _lint.check_paths(plans)[:5]:
            notices.append(f"plan-waves soft: {path.name}: {reason}")
    except Exception:
        pass

    print(json.dumps({"systemMessage": "\n".join(notices)}) if notices else "{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
