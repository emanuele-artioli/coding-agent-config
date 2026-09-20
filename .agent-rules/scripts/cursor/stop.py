#!/usr/bin/python3
"""Cursor stop adapter — closeout capture and plan-waves advisory.

Never auto-runs handoff. Does not set followup_message.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from closeout_adapter import capture_payload, emit_diagnostics  # noqa: E402

_SCRIPTS = Path(__file__).resolve().parent.parent
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
                        "model": payload.get("model"),
                        "model_id": payload.get("model_id"),
                        "model_params": payload.get("model_params"),
                        "input_tokens": payload.get("input_tokens"),
                        "output_tokens": payload.get("output_tokens"),
                        "cache_read_tokens": payload.get("cache_read_tokens"),
                        "cache_write_tokens": payload.get("cache_write_tokens"),
                    }
                )
                + "\n"
            )
    except OSError:
        pass

    # Only explicit closeout boundary fields can trigger capture.  Keep the
    # hook fail-open if an adapter or storage dependency is unavailable.
    try:
        emit_diagnostics(capture_payload(payload, "cursor"), "cursor")
    except Exception as exc:  # pragma: no cover - defensive hook fail-open
        print(f"cursor/closeout: adapter exception ({type(exc).__name__}); skipped", file=sys.stderr)

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
