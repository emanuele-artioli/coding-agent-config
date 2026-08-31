"""Shared progressive context-nudge policy (platform-agnostic).

Cursor/Claude adapters call these helpers. Fill-% is only reliably available
on preCompact today; earlier tiers use a per-conversation stop-count proxy.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

STATE_DIR = Path(__file__).resolve().parent.parent / "var"
STATE_PATH = STATE_DIR / "context-nudge-state.json"

# Soft / medium thresholds on agent stop count (proxy for context fill).
SOFT_STOPS = 12
MEDIUM_STOPS = 20
COOLDOWN_SEC = 30 * 60

TASK_CHANGE = re.compile(
    r"(?i)\b("
    r"now let'?s|new task|switch to|unrelated|ignore previous|"
    r"different (?:task|topic)|instead\b|forget (?:that|the previous)"
    r")\b"
)

MSG_SOFT = (
    "Warm session + possible new task — context may already be stale. "
    "Consider `handoff` or a fresh chat; otherwise continue."
)
MSG_MEDIUM = (
    "Session is getting long (context rot often starts ~50% fill). "
    "A mid-task handoff will hurt — plan `handoff` or `end-of-session` "
    "at the next natural boundary."
)
MSG_STRONG = (
    "Compaction imminent — prefer `end-of-session` / `handoff` now over "
    "relying on auto-summary. Do not wait for full context."
)


def load_state() -> dict[str, Any]:
    try:
        return json.loads(STATE_PATH.read_text())
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def save_state(state: dict[str, Any]) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")
    except OSError:
        pass


def conversation_id(payload: dict) -> str:
    for key in ("conversation_id", "session_id", "composerId", "composer_id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return "unknown"


def record_stop(payload: dict) -> int:
    """Increment stop count; return new count."""
    cid = conversation_id(payload)
    state = load_state()
    entry = state.get(cid) or {"stops": 0, "last_nudge": {}, "started": time.time()}
    # Prefer real fill % if an undocumented field appears.
    for key in ("context_usage_percent", "contextUsagePercent"):
        raw = payload.get(key)
        if isinstance(raw, (int, float)):
            entry["last_fill_percent"] = float(raw)
    entry["stops"] = int(entry.get("stops", 0)) + 1
    entry["updated"] = time.time()
    state[cid] = entry
    save_state(state)
    return int(entry["stops"])


def stops_for(payload: dict) -> int:
    cid = conversation_id(payload)
    entry = load_state().get(cid) or {}
    return int(entry.get("stops", 0))


def fill_percent(payload: dict) -> float | None:
    for key in ("context_usage_percent", "contextUsagePercent"):
        raw = payload.get(key)
        if isinstance(raw, (int, float)):
            return float(raw)
    cid = conversation_id(payload)
    entry = load_state().get(cid) or {}
    raw = entry.get("last_fill_percent")
    return float(raw) if isinstance(raw, (int, float)) else None


def _cooldown_ok(payload: dict, tier: str) -> bool:
    cid = conversation_id(payload)
    entry = load_state().get(cid) or {}
    last = (entry.get("last_nudge") or {}).get(tier, 0)
    return (time.time() - float(last or 0)) >= COOLDOWN_SEC


def _mark_nudge(payload: dict, tier: str) -> None:
    cid = conversation_id(payload)
    state = load_state()
    entry = state.get(cid) or {"stops": 0, "last_nudge": {}}
    nudges = dict(entry.get("last_nudge") or {})
    nudges[tier] = time.time()
    entry["last_nudge"] = nudges
    state[cid] = entry
    save_state(state)


def looks_like_task_change(prompt: str, attachments: list | None = None) -> bool:
    if prompt and TASK_CHANGE.search(prompt):
        return True
    for item in attachments or []:
        if not isinstance(item, dict):
            continue
        path = str(item.get("file_path") or "")
        if path.endswith(".plan.md") or "/plans/" in path:
            return True
    return False


def soft_task_change_message(payload: dict, prompt: str, attachments: list | None = None) -> str | None:
    """Return a soft message, or None. Caller decides whether to block."""
    if stops_for(payload) < SOFT_STOPS and (fill_percent(payload) or 0) < 50:
        return None
    if not looks_like_task_change(prompt, attachments):
        return None
    if not _cooldown_ok(payload, "soft"):
        return None
    _mark_nudge(payload, "soft")
    return MSG_SOFT


def medium_aging_message(payload: dict) -> str | None:
    stops = record_stop(payload)
    fill = fill_percent(payload)
    warm = stops >= MEDIUM_STOPS or (fill is not None and fill >= 50)
    if not warm or not _cooldown_ok(payload, "medium"):
        return None
    _mark_nudge(payload, "medium")
    return MSG_MEDIUM


def strong_precompact_message(payload: dict) -> str:
    """Strong nudge plus a resume-stub path the agent can fill before compact."""
    from precompact_stub import write_stub  # local import: avoid cycle with tests

    _mark_nudge(payload, "strong")
    fill = fill_percent(payload)
    base = MSG_STRONG
    if fill is not None:
        base = f"{MSG_STRONG} (context_usage_percent={fill:.0f})"

    stub = write_stub(conversation_id(payload))
    if stub is None:
        return (
            f"{base} Fill a `HANDOFF.md` now if you can; after compact, resume "
            "from that file rather than auto-summary alone."
        )
    return (
        f"{base} Resume stub (empty template — fill it, or write `HANDOFF.md`): "
        f"{stub}. After compact, read that file first before re-exploring."
    )
