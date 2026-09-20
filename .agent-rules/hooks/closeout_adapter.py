#!/usr/bin/env python3
"""Conservative lifecycle adapters for the deterministic closeout core.

The stop hooks receive different, partly undocumented payloads.  This module
therefore accepts only fields that explicitly describe a completion boundary;
it never infers completion from a normal Stop, a dirty worktree, a status
string, or model prose.  A missing or unsupported field is reported as a
diagnostic and is a no-op.

Operational state defaults to a harness-owned directory below the user's home
directory.  It is intentionally separate from a repository's ``.agent-rules``
tree.  Tests and callers may pass ``state_root`` or set ``CLOSEOUT_STATE_ROOT``
to an isolated location.

The public functions are deliberately small:

``normalize_payload``
    Return a normalized event, or ``None`` when the payload is not an
    explicit boundary.
``capture_payload``
    Normalize and call :mod:`closeout`; all errors fail open and become
    diagnostics.
``emit_diagnostics``
    Print diagnostics in a hook-safe way without changing the hook result.
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import sys
from typing import Any, Mapping


_SCRIPTS = Path(__file__).resolve().parent
_CORE_SPEC = importlib.util.spec_from_file_location("_closeout_core", _SCRIPTS / "closeout.py")
if _CORE_SPEC is None or _CORE_SPEC.loader is None:  # pragma: no cover - packaging failure
    raise ImportError(f"cannot load closeout core from {_SCRIPTS / 'closeout.py'}")
_core = importlib.util.module_from_spec(_CORE_SPEC)
sys.modules.setdefault("_closeout_core", _core)
_CORE_SPEC.loader.exec_module(_core)


def closeout(*args: Any, **kwargs: Any) -> Any:
    """Indirection kept patchable for hook-level fail-open tests."""

    return _core.closeout(*args, **kwargs)


_HARNESS_DIRS = {
    "claude": ".claude",
    "cursor": ".cursor",
    "antigravity": ".gemini",
    "codex": ".codex",
}

# These are the only semantic boundary names emitted by this adapter.  The
# values on the right are the closeout core's explicit kind/state pair.
_BOUNDARY_KINDS: dict[str, tuple[str, str]] = {
    "completed_session": ("session", "completed"),
    "handoff": ("handoff", "pending"),
    "completed_report": ("report", "completed"),
    "blocked_transfer": ("handoff", "blocked"),
    "no_lessons": ("session", "completed"),
}

_KIND_ALIASES = {
    "session_end": "completed_session",
    "end": "completed_session",
    "end_session": "completed_session",
    "completed": "completed_session",
    "report_complete": "completed_report",
    "final_report": "completed_report",
    "blocked": "blocked_transfer",
    "blocked_handoff": "blocked_transfer",
    "no_lesson": "no_lessons",
}

_CORE_KIND_NAMES = {"session", "handoff", "report", "progress", "question"}
_NON_BOUNDARY_NAMES = {"progress", "question", "approval_wait", "waiting", "in_progress"}


@dataclass(frozen=True)
class NormalizedBoundary:
    """One explicit lifecycle boundary understood by the closeout core."""

    harness: str
    # ``boundary_kind`` is the readable adapter enum.  ``kind`` and ``state``
    # are the exact values passed to closeout.py.
    boundary_kind: str
    kind: str
    state: str
    boundary_id: str
    event_id: str
    observations: tuple[Mapping[str, Any], ...] = ()
    repo_id: str = ""
    task_id: str = ""
    project: str = "."
    platform: str = ""
    when: str | None = None
    signal: str = ""


@dataclass(frozen=True)
class CaptureResult:
    """Fail-open result returned by :func:`capture_payload`."""

    event: NormalizedBoundary | None = None
    result: Any | None = None
    diagnostics: tuple[str, ...] = ()
    skipped: bool = False

    @property
    def captured(self) -> bool:
        return bool(self.result is not None and getattr(self.result, "captured", False))

    @property
    def replay(self) -> bool:
        return bool(self.result is not None and getattr(self.result, "replay", False))


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _flag(value: Any) -> bool:
    """Accept only unambiguous boolean spellings from hook JSON."""

    if value is True:
        return True
    return isinstance(value, str) and value.strip().lower() in {"true", "yes", "1"}


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _safe_identifier(value: Any) -> str | None:
    """Validate an ID without rewriting it and accidentally causing a collision."""

    value = _clean_text(value)
    if value is None or value in {".", ".."}:
        return None
    if any(ord(char) < 32 or char in "/\\\x00" for char in value):
        return None
    return value


def _nested_fields(payload: Mapping[str, Any]) -> tuple[dict[str, Any], str | None]:
    """Merge an explicit closeout event object over top-level hook fields."""

    merged = dict(payload)
    source: str | None = None
    # These names are explicit event containers.  A generic event string is
    # never treated as a boundary, but a mapping under ``event`` is safe.
    for key in ("closeout", "completion_boundary", "boundary", "event"):
        value = payload.get(key)
        if _is_mapping(value):
            merged.update(value)
            source = key
            break
    return merged, source


def _explicit_child_or_wait(fields: Mapping[str, Any]) -> str | None:
    if any(_flag(fields.get(key)) for key in ("child_report", "is_child_report", "subagent_report")):
        return "child report is not a user completion boundary"
    report_type = fields.get("report_type") or fields.get("event_type")
    if isinstance(report_type, str) and report_type.strip().lower() in {
        "child_report", "subagent_report", "child", "subagent",
    }:
        return "child report is not a user completion boundary"
    if any(_flag(fields.get(key)) for key in (
        "awaiting_input", "awaiting_approval", "waiting_for_user",
        "approval_wait", "question_wait",
    )):
        return "question or approval wait is not a completion boundary"
    if isinstance(report_type, str) and report_type.strip().lower() in {
        "progress", "question", "approval_wait", "waiting",
    }:
        return "progress/question event is not a completion boundary"
    return None


def _raw_boundary_kind(fields: Mapping[str, Any]) -> tuple[str | None, str | None]:
    """Return semantic kind and the field/flag that supplied it."""

    for key in (
        "boundary_kind", "boundaryKind", "closeout_kind", "completion_kind",
        "boundary_type", "kind", "event_type", "lifecycle_event",
    ):
        raw = fields.get(key)
        if raw is None:
            continue
        if not isinstance(raw, str):
            return None, f"{key} must be a string"
        normalized = raw.strip().lower().replace("-", "_").replace(" ", "_")
        normalized = _KIND_ALIASES.get(normalized, normalized)
        if normalized in _NON_BOUNDARY_NAMES:
            return normalized, key
        if normalized in _BOUNDARY_KINDS:
            return normalized, key
        if normalized in _CORE_KIND_NAMES:
            return normalized, key
        return None, f"unsupported boundary kind {raw!r}; harness event support is not established"

    # Boolean flags are accepted only when they name the boundary directly.
    flags = (
        ("end_of_session", "completed_session"),
        ("endOfSession", "completed_session"),
        ("session_end", "completed_session"),
        ("handoff_requested", "handoff"),
        ("handoff", "handoff"),
        ("completed_report", "completed_report"),
        ("closing_report", "completed_report"),
        ("final_report", "completed_report"),
        ("blocked_transfer", "blocked_transfer"),
        ("no_lessons", "no_lessons"),
    )
    for key, kind in flags:
        if _flag(fields.get(key)):
            return kind, key
    return None, None


def _stable_ids(
    fields: Mapping[str, Any],
    boundary_kind: str,
    signal: str | None,
) -> tuple[str | None, str | None, str | None]:
    explicit_boundary = fields.get("boundary_id", fields.get("boundaryId", fields.get("id")))
    explicit_event = fields.get("event_id", fields.get("eventId"))
    boundary_id = _safe_identifier(explicit_boundary) if explicit_boundary is not None else None
    event_id = _safe_identifier(explicit_event) if explicit_event is not None else None
    if explicit_boundary is not None and boundary_id is None:
        return None, None, "boundary_id must be a safe non-empty string"
    if explicit_event is not None and event_id is None:
        return None, None, "event_id must be a safe non-empty string"

    session_id = None
    for key in (
        "session_id", "sessionId", "conversation_id", "conversationId",
        "composer_id", "composerId",
    ):
        session_id = _safe_identifier(fields.get(key))
        if session_id:
            break
    if boundary_id is None:
        # A stable session ID is an explicit identity signal.  Include the
        # semantic boundary to keep a handoff and final session distinct.
        if event_id is not None:
            boundary_id = event_id
        elif session_id is not None:
            boundary_id = f"{session_id}:{boundary_kind}"
        else:
            return None, None, "missing stable boundary/event identity (boundary_id, event_id, or session_id)"
        if _safe_identifier(boundary_id) is None:
            return None, None, "stable event identity cannot form a safe boundary identity"
    if event_id is None:
        event_id = boundary_id
    return boundary_id, event_id, None


def _observations(fields: Mapping[str, Any]) -> tuple[tuple[Mapping[str, Any], ...] | None, str | None]:
    raw = fields.get("observations", ())
    if raw is None:
        return (), None
    if not isinstance(raw, (list, tuple)):
        return None, "observations must be a JSON list; closeout skipped"
    items: list[Mapping[str, Any]] = []
    for index, item in enumerate(raw):
        if not _is_mapping(item):
            return None, f"observation {index} must be a JSON object; closeout skipped"
        items.append(dict(item))
    return tuple(items), None


def _normalize_payload(payload: Any, harness: str) -> tuple[NormalizedBoundary | None, list[str]]:
    diagnostics: list[str] = []
    harness_name = _clean_text(harness) or "unknown"
    if not _is_mapping(payload):
        return None, ["payload is not a JSON object; closeout skipped"]
    if _flag(payload.get("stop_hook_active")):
        return None, ["stop_hook_active re-entry; closeout skipped"]

    fields, nested_source = _nested_fields(payload)
    wait_reason = _explicit_child_or_wait(fields)
    if wait_reason:
        return None, [f"{wait_reason}; closeout skipped"]

    semantic, signal = _raw_boundary_kind(fields)
    if signal is not None and semantic in _NON_BOUNDARY_NAMES:
        return None, [f"{semantic} event is not a completion boundary; closeout skipped"]
    if semantic is None:
        if signal and (signal.startswith("unsupported boundary kind") or signal.endswith("must be a string")):
            return None, [f"{signal}; closeout skipped"]
        return None, [
            "no explicit completion boundary signal in payload; ordinary Stop is not captured",
        ]
    if semantic not in _BOUNDARY_KINDS:
        # ``session``, ``handoff`` and ``report`` are accepted core names only
        # when their state is explicit.  This avoids treating a generic kind
        # field as a completed task.
        if semantic not in _CORE_KIND_NAMES:
            return None, [f"unsupported boundary kind {semantic!r}; closeout skipped"]

    state_raw = fields.get("boundary_state", fields.get("state", fields.get("status")))
    state = _clean_text(state_raw)
    if state:
        state = state.lower().replace("-", "_")
        state = {"complete": "completed", "done": "completed", "working": "in_progress"}.get(state, state)

    if semantic in _BOUNDARY_KINDS:
        core_kind, default_state = _BOUNDARY_KINDS[semantic]
        if state is None:
            state = default_state
        elif semantic in {"completed_session", "completed_report", "no_lessons"} and state != default_state:
            return None, [
                f"boundary kind {semantic!r} conflicts with boundary_state {state!r}; closeout skipped",
            ]
    else:
        core_kind = semantic
        if state is None:
            return None, [f"boundary kind {semantic!r} requires an explicit boundary_state; closeout skipped"]
        if core_kind not in _CORE_KIND_NAMES:
            return None, [f"unsupported boundary kind {semantic!r}; closeout skipped"]

    if core_kind == "progress" or core_kind == "question":
        return None, [f"{core_kind} event is not a completion boundary; closeout skipped"]
    if core_kind == "report" and state != "completed":
        return None, ["report boundary is not completed; closeout skipped"]
    if core_kind == "session" and state not in {"completed", "blocked", "abrupt"}:
        return None, [f"session boundary state {state!r} is not complete; closeout skipped"]

    boundary_id, event_id, id_error = _stable_ids(fields, semantic, signal)
    if id_error:
        return None, [f"{id_error}; closeout skipped"]
    assert boundary_id is not None and event_id is not None

    observations, observation_error = _observations(fields)
    if observation_error:
        return None, [observation_error]
    assert observations is not None
    if semantic == "no_lessons" and observations:
        return None, ["no_lessons boundary must not contain observations; closeout skipped"]

    def optional_text(*keys: str, default: str = "") -> str:
        for key in keys:
            value = _clean_text(fields.get(key))
            if value:
                return value
        return default

    # A malformed optional metadata field is left for the core to reject and
    # be caught as a fail-open diagnostic.  The boundary decision itself is
    # based only on explicit kind/identity fields above.
    normalized_boundary_kind = semantic
    if semantic == "session" and state == "completed":
        normalized_boundary_kind = "completed_session"
    elif semantic == "session" and state == "blocked":
        normalized_boundary_kind = "blocked_transfer"
    elif semantic == "report" and state == "completed":
        normalized_boundary_kind = "completed_report"

    return NormalizedBoundary(
        harness=harness_name,
        boundary_kind=normalized_boundary_kind,
        kind=core_kind,
        state=state,
        boundary_id=boundary_id,
        event_id=event_id,
        observations=observations,
        repo_id=optional_text("repo_id", "repository_id"),
        task_id=optional_text("task_id", "task"),
        project=optional_text("project", default="."),
        platform=optional_text("platform", default=harness_name),
        when=optional_text("when", "date", default="") or None,
        signal=(f"{nested_source}.{signal}" if nested_source and signal else signal or ""),
    ), diagnostics


def normalize_payload(payload: Any, harness: str = "unknown") -> NormalizedBoundary | None:
    """Return an explicit normalized boundary, or ``None`` for a no-op."""

    event, _ = _normalize_payload(payload, harness)
    return event


def diagnose_payload(payload: Any, harness: str = "unknown") -> tuple[str, ...]:
    """Return the fail-open diagnostics that normalization would produce."""

    _, diagnostics = _normalize_payload(payload, harness)
    return tuple(diagnostics)


def state_root_for(
    payload: Mapping[str, Any] | None = None,
    harness: str = "unknown",
    state_root: str | Path | None = None,
) -> Path:
    """Resolve isolated operational state without using a project rule tree."""

    fields, _ = _nested_fields(payload) if _is_mapping(payload) else ({}, None)
    explicit = state_root
    if explicit is None:
        explicit = fields.get("closeout_state_root") or fields.get("state_root")
    if explicit is None:
        explicit = os.environ.get("CLOSEOUT_STATE_ROOT")
    if explicit is not None:
        value = _clean_text(str(explicit))
        if value is None:
            raise ValueError("closeout state root must be a non-empty path")
        return Path(value).expanduser().resolve()

    harness_dir = _HARNESS_DIRS.get((_clean_text(harness) or "").lower())
    if harness_dir is None:
        return (Path.home() / ".closeout-state").expanduser().resolve()
    if harness_dir == ".codex":
        base = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    else:
        base = Path.home() / harness_dir
    return (base / "closeout-state").expanduser().resolve()


def capture_payload(
    payload: Any,
    harness: str = "unknown",
    *,
    state_root: str | Path | None = None,
) -> CaptureResult:
    """Normalize and capture a payload; every failure is fail-open."""

    try:
        event, diagnostics = _normalize_payload(payload, harness)
        if event is None:
            return CaptureResult(None, None, tuple(diagnostics), skipped=True)
        root = state_root_for(payload, harness, state_root)
        result = closeout(
            root,
            event.boundary_id,
            event.kind,
            event.state,
            event.observations,
            event_id=event.event_id,
            repo_id=event.repo_id,
            task_id=event.task_id,
            project=event.project,
            platform=event.platform,
            when=event.when,
        )
        return CaptureResult(event, result, tuple(diagnostics), skipped=False)
    except Exception as exc:  # hooks must never block the harness
        return CaptureResult(
            None,
            None,
            (f"adapter exception ({type(exc).__name__}): {exc}; closeout skipped",),
            skipped=True,
        )


# Names useful to lifecycle adapters and tests.
record_from_payload = capture_payload
adapt_payload = normalize_payload
handle_payload = capture_payload


def emit_diagnostics(result: CaptureResult | None, harness: str = "unknown") -> None:
    """Write diagnostics to stderr while preserving the hook's exit contract."""

    if result is None:
        return
    for diagnostic in result.diagnostics:
        print(f"{_clean_text(harness) or 'lifecycle'}/closeout: {diagnostic}", file=sys.stderr)


__all__ = [
    "CaptureResult",
    "NormalizedBoundary",
    "adapt_payload",
    "capture_payload",
    "diagnose_payload",
    "emit_diagnostics",
    "handle_payload",
    "normalize_payload",
    "record_from_payload",
    "state_root_for",
]
