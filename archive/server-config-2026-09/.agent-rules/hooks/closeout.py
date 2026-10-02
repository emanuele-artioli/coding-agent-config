#!/usr/bin/env python3
"""Deterministic completion-boundary capture.

This module is the storage primitive used by lifecycle adapters.  It does not
interpret model output, run an evaluator, commit files, or push anything.

The public entry point is :func:`closeout` (also exported as
``record_closeout`` and ``close_out``).  It takes a state root, a stable
boundary/event identity, an explicit :class:`BoundaryKind` and
:class:`BoundaryState`, and a sequence of proposed observations.  Operational
receipts live in ``<state-root>/.closeout/receipts``.  Candidate files live in
``<state-root>/candidates`` when that directory exists (or directly below the
state root when it already looks like a candidates directory).

The receipt is a small, deterministic JSON record.  A pending receipt is
written before any candidate mutation and is checkpointed after every ledger
observation.  A retry can therefore reconcile a receipt that was interrupted
before or after a candidate write.  ``lessons.py`` owns occurrence counting and
event deduplication; this module never increments those counters itself.

CLI exit codes:

* 0 — a close-out was completed, or an explicitly non-boundary event was
  recorded as ignored;
* 1 — a pending close-out needs retry after an operational failure;
* 2 — invalid input or an identity/storage collision.

Example::

    closeout.py --root /tmp/state --boundary-id turn-7 --event-id stop-7 \
      --kind session --state completed \
      --observation '{"candidate_id":"lesson-1","axis":"project",\n+                      "summary":"A repeatable failure","evidence":"test"}'
"""

import argparse
import contextlib
import dataclasses
from datetime import date
from enum import Enum
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence

try:  # POSIX is the supported host; the fallback keeps imports portable.
    import fcntl
except ImportError:  # pragma: no cover - only for non-POSIX users
    fcntl = None


class CloseoutError(ValueError):
    """An input, identity, or recoverability invariant was violated."""


class BoundaryKind(str, Enum):
    """The caller's explicit lifecycle event.

    ``PROGRESS`` and ``QUESTION`` are deliberately represented here instead of
    being guessed from prose.  They always produce an ignored receipt and do
    not mutate the lesson queue.
    """

    SESSION = "session"
    HANDOFF = "handoff"
    REPORT = "report"
    PROGRESS = "progress"
    QUESTION = "question"

    # Readable aliases for callers that prefer the plan's wording.
    COMPLETED_SESSION = "session"
    COMPLETED_REPORT = "report"


class BoundaryState(str, Enum):
    """The state asserted by the caller at the boundary."""

    COMPLETED = "completed"
    BLOCKED = "blocked"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    ABRUPT = "abrupt"


# Short aliases make the public contract convenient without introducing a
# second set of accepted values.
CloseoutKind = BoundaryKind
CloseoutState = BoundaryState


@dataclasses.dataclass(frozen=True)
class Observation:
    """One candidate observation proposed by the semantic parent.

    ``candidate_id`` and ``summary`` are required only when a new candidate
    must be created.  Existing candidates may leave ``summary`` empty; the
    ledger then supplies the existing content.  An explicit ``event_id`` is
    preferred when several independent observations share one boundary.  If
    it is omitted, a stable ID is derived from the close-out event and the
    observation's position/candidate ID.
    """

    candidate_id: str
    axis: str = "project"
    summary: str = ""
    project: str = "."
    platform: str = ""
    evidence: str | None = None
    event_id: str | None = None
    keywords: tuple[str, ...] = ()
    created: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "Observation":
        """Build an observation from a JSON-like mapping.

        ``id`` and ``candidate`` are accepted as ergonomic aliases for
        ``candidate_id``.  Unknown fields are rejected so a typo cannot turn
        into an unrecorded lesson.
        """

        aliases = {"id": "candidate_id", "candidate": "candidate_id"}
        normalized: dict[str, Any] = {}
        allowed = {field.name for field in dataclasses.fields(cls)}
        for key, item in value.items():
            key = aliases.get(str(key), str(key))
            if key not in allowed:
                raise CloseoutError(f"unknown observation field {key!r}")
            normalized[key] = item
        if "candidate_id" not in normalized:
            raise CloseoutError("observation requires candidate_id")
        keywords = normalized.get("keywords", ())
        if isinstance(keywords, str):
            keywords = tuple(part.strip() for part in keywords.split(",") if part.strip())
        elif isinstance(keywords, Sequence) and not isinstance(keywords, (bytes, bytearray)):
            keywords = tuple(str(item) for item in keywords)
        else:
            raise CloseoutError("observation keywords must be a string or list")
        normalized["keywords"] = keywords
        return cls(**normalized)


@dataclasses.dataclass(frozen=True)
class ObservationResult:
    """Durable outcome for one proposed observation."""

    candidate_id: str
    event_id: str
    status: str
    path: str | None = None
    created_candidate: bool = False
    occurrences: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class CloseoutResult:
    """Result returned by :func:`closeout`."""

    receipt_path: Path
    status: str
    captured: bool
    replay: bool
    no_lessons: bool
    observations: tuple[ObservationResult, ...] = ()
    error: str | None = None
    reason: str | None = None

    @property
    def pending(self) -> bool:
        return self.status == "pending"

    def as_dict(self) -> dict[str, Any]:
        return {
            "receipt_path": str(self.receipt_path),
            "status": self.status,
            "captured": self.captured,
            "replay": self.replay,
            "no_lessons": self.no_lessons,
            "observations": [item.as_dict() for item in self.observations],
            "error": self.error,
            "reason": self.reason,
        }


def _load_lessons() -> Any:
    """Load the sibling ledger even when this file is imported by a test."""

    module_name = "_closeout_lessons"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    path = Path(__file__).resolve().with_name("lessons.py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load lesson ledger at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


lessons = _load_lessons()


_SAFE_ID = re.compile(r"^[^/\\\x00\r\n]+$")
_KIND_ALIASES = {
    "completed_session": BoundaryKind.SESSION,
    "session_end": BoundaryKind.SESSION,
    "end": BoundaryKind.SESSION,
    "end_session": BoundaryKind.SESSION,
    "completed_report": BoundaryKind.REPORT,
}
_STATE_ALIASES = {
    "complete": BoundaryState.COMPLETED,
    "done": BoundaryState.COMPLETED,
    "working": BoundaryState.IN_PROGRESS,
}


def _safe_text(value: Any, name: str, *, filename: bool = False) -> str:
    if not isinstance(value, str) or not value or any(ord(char) < 32 for char in value):
        raise CloseoutError(f"{name} must be a non-empty single-line string")
    if filename and (value in {".", ".."} or not _SAFE_ID.fullmatch(value)):
        raise CloseoutError(f"{name} is not a safe file identifier")
    return value


def _coerce_kind(value: BoundaryKind | str) -> BoundaryKind:
    if isinstance(value, BoundaryKind):
        return value
    raw = _safe_text(value, "boundary kind").lower().replace("-", "_")
    try:
        return BoundaryKind(raw)
    except ValueError:
        if raw in _KIND_ALIASES:
            return _KIND_ALIASES[raw]
        raise CloseoutError(
            "boundary kind must be session, handoff, report, progress, or question"
        ) from None


def _coerce_state(value: BoundaryState | str) -> BoundaryState:
    if isinstance(value, BoundaryState):
        return value
    raw = _safe_text(value, "boundary state").lower().replace("-", "_")
    try:
        return BoundaryState(raw)
    except ValueError:
        if raw in _STATE_ALIASES:
            return _STATE_ALIASES[raw]
        raise CloseoutError(
            "boundary state must be completed, blocked, pending, in_progress, "
            "waiting, or abrupt"
        ) from None


def _coerce_observation(value: Observation | Mapping[str, Any]) -> Observation:
    if isinstance(value, Observation):
        return value
    if isinstance(value, Mapping):
        return Observation.from_mapping(value)
    raise CloseoutError("observations must contain Observation values or mappings")


def _candidate_root(state_root: Path) -> Path:
    nested = state_root / "candidates"
    if nested.exists():
        return nested
    project_nested = state_root / ".agent-rules" / "candidates"
    if project_nested.exists():
        return project_nested
    if any((state_root / part).is_dir() for part in ("open", "done")):
        return state_root
    return nested


def _receipt_dir(state_root: Path) -> Path:
    return state_root / ".closeout" / "receipts"


def _receipt_path(state_root: Path, boundary_id: str, event_id: str) -> Path:
    # Keep normal IDs legible, while retaining a bounded filename for callers
    # that use long but otherwise safe IDs.
    stem = f"{boundary_id}--{event_id}"
    if len(stem) > 180:
        digest = hashlib.sha256(stem.encode("utf-8")).hexdigest()[:24]
        stem = f"closeout-{digest}"
    _safe_text(stem, "receipt identity", filename=True)
    return _receipt_dir(state_root) / f"{stem}.json"


@contextlib.contextmanager
def _state_lock(state_root: Path):
    lock_dir = state_root / ".closeout"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "closeout.lock"
    with lock_path.open("a+") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _atomic_write(path: Path, text: str) -> None:
    """Write a receipt/candidate atomically and fsync its containing folder."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temporary = handle.name
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass


def _write_json(path: Path, document: Mapping[str, Any]) -> None:
    _atomic_write(path, json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True) + "\n")


def _read_receipt(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CloseoutError(f"receipt {path} is unreadable; preserve it for recovery: {exc}") from exc
    if not isinstance(value, dict):
        raise CloseoutError(f"receipt {path} is not a JSON object")
    return value


def _eligible(kind: BoundaryKind, state: BoundaryState) -> bool:
    if kind in {BoundaryKind.PROGRESS, BoundaryKind.QUESTION}:
        return False
    if kind is BoundaryKind.HANDOFF:
        return True
    if kind is BoundaryKind.SESSION:
        return state in {BoundaryState.COMPLETED, BoundaryState.BLOCKED, BoundaryState.ABRUPT}
    return state is BoundaryState.COMPLETED


def _normalized_observation(
    observation: Observation,
    index: int,
    event_id: str,
    default_project: str,
    default_platform: str,
    when: str,
) -> dict[str, Any]:
    candidate_id = _safe_text(observation.candidate_id, "candidate id", filename=True)
    axis = _safe_text(observation.axis, "observation axis")
    if axis not in {"project", "platform"}:
        raise CloseoutError("observation axis must be project or platform")
    summary = observation.summary
    if not isinstance(summary, str) or any(ord(char) < 32 for char in summary):
        raise CloseoutError("observation summary must be a single-line string")
    project = _safe_text(observation.project or default_project, "project")
    platform = _safe_text(observation.platform or default_platform, "platform")
    evidence = observation.evidence
    if evidence is not None:
        _safe_text(evidence, "evidence")
    explicit_event = observation.event_id
    if explicit_event is not None:
        obs_event = _safe_text(explicit_event, "observation event id")
    elif index == 0:
        obs_event = event_id
    else:
        obs_event = f"{event_id}:{index}:{candidate_id}"
        _safe_text(obs_event, "observation event id")
    keywords: list[str] = []
    for item in observation.keywords:
        keywords.append(_safe_text(item, "keyword"))
    created = observation.created or when
    _safe_text(created, "created date")
    return {
        "candidate_id": candidate_id,
        "axis": axis,
        "summary": summary,
        "project": project,
        "platform": platform,
        "evidence": evidence,
        "event_id": obs_event,
        "keywords": keywords,
        "created": created,
        "status": "pending",
    }


def _identity(
    boundary_id: str,
    event_id: str,
    kind: BoundaryKind,
    state: BoundaryState,
    repo_id: str,
    task_id: str,
    observations: Sequence[Mapping[str, Any]],
) -> str:
    value = {
        "boundary_id": boundary_id,
        "event_id": event_id,
        "kind": kind.value,
        "state": state.value,
        "repo_id": repo_id,
        "task_id": task_id,
        "observations": [
            {key: item[key] for key in (
                "candidate_id", "axis", "summary", "project", "platform",
                "evidence", "event_id", "keywords", "created",
            )}
            for item in observations
        ],
    }
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _find_candidate(candidate_root: Path, candidate_id: str) -> list[Any]:
    return [entry for entry in lessons.load(candidate_root) if entry.id == candidate_id]


def _candidate_text(item: Mapping[str, Any]) -> str:
    keywords = json.dumps(item["keywords"], ensure_ascii=True)
    summary = item["summary"]
    # YAML frontmatter values are kept on one line.  The summary was already
    # checked for control characters, and JSON quoting keeps punctuation safe.
    summary_yaml = json.dumps(summary, ensure_ascii=True)
    return (
        "---\n"
        f"id: {item['candidate_id']}\n"
        f"created: {item['created']}\n"
        f"axis: {item['axis']}\n"
        "status: open\n"
        f"summary: {summary_yaml}\n"
        "occurrences: 0\n"
        f"keywords: {keywords}\n"
        f"source_project: {json.dumps(item['project'], ensure_ascii=True)}\n"
        f"source_platform: {json.dumps(item['platform'], ensure_ascii=True)}\n"
        "---\n\n"
        f"{summary}\n"
    )


def _ensure_candidate(candidate_root: Path, item: Mapping[str, Any]) -> tuple[bool, Path | None]:
    """Create a first-observation candidate if no candidate with this ID exists."""

    existing = _find_candidate(candidate_root, str(item["candidate_id"]))
    if existing:
        return False, None
    if not item["summary"]:
        raise CloseoutError(
            f"candidate {item['candidate_id']} does not exist; summary is required to create it"
        )
    destination = candidate_root / "open" / str(item["axis"]) / f"{item['candidate_id']}.md"
    if destination.exists():
        # A file that lessons.load could not parse must not be overwritten.
        raise CloseoutError(f"candidate destination collision at {destination}")
    _atomic_write(destination, _candidate_text(item))
    return True, destination


def _record_observation(candidate_root: Path, item: Mapping[str, Any]) -> ObservationResult:
    created, created_path = _ensure_candidate(candidate_root, item)
    try:
        destination, occurrences, already = lessons._record_with_lock(
            str(item["candidate_id"]),
            str(item["project"]),
            str(item["platform"]),
            candidate_root,
            str(item["created"]),
            str(item["event_id"]),
            item["evidence"],
        )
    except Exception:
        # The newly-created source remains in place.  The next invocation can
        # reconcile it through the ledger's own atomic/replay logic.
        raise
    return ObservationResult(
        candidate_id=str(item["candidate_id"]),
        event_id=str(item["event_id"]),
        status="already_recorded" if already else "recorded",
        path=str(destination),
        created_candidate=created,
        occurrences=occurrences,
    )


def _result_from_receipt(path: Path, receipt: Mapping[str, Any], *, replay: bool) -> CloseoutResult:
    results: list[ObservationResult] = []
    for item in receipt.get("observations", []):
        if not isinstance(item, Mapping):
            continue
        results.append(
            ObservationResult(
                candidate_id=str(item.get("candidate_id", "")),
                event_id=str(item.get("event_id", "")),
                status=str(item.get("status", "pending")),
                path=item.get("path"),
                created_candidate=bool(item.get("created_candidate", False)),
                occurrences=item.get("occurrences"),
            )
        )
    return CloseoutResult(
        receipt_path=path,
        status=str(receipt.get("status", "pending")),
        captured=bool(receipt.get("captured", False)),
        replay=replay,
        no_lessons=bool(receipt.get("no_lessons", not results)),
        observations=tuple(results),
        error=receipt.get("error"),
        reason=receipt.get("reason"),
    )


def closeout(
    root: str | Path,
    boundary_id: str,
    kind: BoundaryKind | str,
    state: BoundaryState | str,
    observations: Iterable[Observation | Mapping[str, Any]] | None = (),
    *,
    event_id: str | None = None,
    repo_id: str = "",
    task_id: str = "",
    project: str = ".",
    platform: str = "codex",
    when: str | None = None,
) -> CloseoutResult:
    """Record one explicit completion boundary and proposed observations.

    ``root`` is an operational state location, never an instruction file.  A
    receipt is keyed by ``boundary_id`` + ``event_id``; ``event_id`` defaults
    to ``boundary_id``.  Replaying the same identity and request is a true
    no-op.  A different event ID is an independent ledger event, including
    when it occurs in the same task.

    The function returns a ``pending`` result after an operational mutation or
    receipt failure so callers can retry.  Invalid input and identity
    collisions raise :class:`CloseoutError` before candidate mutation.
    """

    state_root = Path(root).expanduser().resolve()
    state_root.mkdir(parents=True, exist_ok=True)
    boundary_id = _safe_text(boundary_id, "boundary id", filename=True)
    event_id = _safe_text(event_id or boundary_id, "event id", filename=True)
    repo_id = _safe_text(repo_id, "repo id") if repo_id else ""
    task_id = _safe_text(task_id, "task id") if task_id else ""
    project = _safe_text(project, "project")
    platform = _safe_text(platform, "platform")
    when = _safe_text(when or date.today().isoformat(), "date")
    boundary_kind = _coerce_kind(kind)
    boundary_state = _coerce_state(state)
    if observations is None:
        observations = ()
    normalized = [
        _normalized_observation(_coerce_observation(value), index, event_id, project, platform, when)
        for index, value in enumerate(observations)
    ]
    identity = _identity(
        boundary_id, event_id, boundary_kind, boundary_state, repo_id, task_id, normalized
    )
    receipt_path = _receipt_path(state_root, boundary_id, event_id)
    candidate_root = _candidate_root(state_root)
    capture = _eligible(boundary_kind, boundary_state)

    with _state_lock(state_root):
        existing = _read_receipt(receipt_path)
        if existing is not None:
            if existing.get("identity") != identity:
                raise CloseoutError(
                    f"receipt identity collision at {receipt_path}; use a new boundary/event ID"
                )
            if existing.get("status") in {"completed", "ignored"}:
                return _result_from_receipt(receipt_path, existing, replay=True)
        else:
            existing = {
                "schema": 1,
                "boundary_id": boundary_id,
                "event_id": event_id,
                "kind": boundary_kind.value,
                "state": boundary_state.value,
                "repo_id": repo_id,
                "task_id": task_id,
                "identity": identity,
                "captured": capture,
                "status": "pending",
                "no_lessons": not normalized,
                "observations": normalized,
            }
            try:
                _write_json(receipt_path, existing)
            except OSError as exc:
                # No candidate mutation was attempted; return a retryable
                # result even if the fault happened after os.replace.
                return CloseoutResult(
                    receipt_path, "pending", capture, False, not normalized, error=str(exc)
                )

        if not capture:
            existing["status"] = "ignored"
            existing["captured"] = False
            existing["no_lessons"] = True
            existing["reason"] = "explicit progress/question or incomplete report boundary"
            try:
                _write_json(receipt_path, existing)
            except OSError as exc:
                return CloseoutResult(
                    receipt_path, "pending", False, False, True, error=str(exc),
                    reason=existing["reason"],
                )
            return _result_from_receipt(receipt_path, existing, replay=False)

        # Reconcile every observation whose ledger write is not durably marked
        # in the receipt.  The ledger event ID makes this safe after a crash
        # between its write and this checkpoint.
        for index, item in enumerate(existing.get("observations", [])):
            if item.get("status") in {"recorded", "already_recorded"}:
                continue
            try:
                result = _record_observation(candidate_root, item)
            except Exception as exc:  # operational failure is retryable
                item["status"] = "pending"
                existing["error"] = str(exc)
                try:
                    _write_json(receipt_path, existing)
                except OSError:
                    pass
                current = _result_from_receipt(receipt_path, existing, replay=False)
                return dataclasses.replace(current, status="pending", error=str(exc))
            item.update(result.as_dict())
            existing.pop("error", None)
            try:
                _write_json(receipt_path, existing)
            except OSError as exc:
                # The observation is already idempotently durable in lessons;
                # retrying will replay it and reconcile this checkpoint.
                return CloseoutResult(
                    receipt_path, "pending", True, False, False,
                    tuple(
                        ObservationResult(
                            candidate_id=str(value.get("candidate_id", "")),
                            event_id=str(value.get("event_id", "")),
                            status=str(value.get("status", "pending")),
                            path=value.get("path"),
                            created_candidate=bool(value.get("created_candidate", False)),
                            occurrences=value.get("occurrences"),
                        ) for value in existing.get("observations", [])
                    ),
                    error=str(exc),
                )

        existing["status"] = "completed"
        existing["captured"] = True
        existing["no_lessons"] = not bool(existing.get("observations"))
        existing.pop("error", None)
        try:
            _write_json(receipt_path, existing)
        except OSError as exc:
            # The candidate/ledger writes are complete.  The pending receipt
            # is enough for a later invocation to finish without recounting.
            return CloseoutResult(
                receipt_path, "pending", True, False, not normalized,
                error=str(exc),
            )
        return _result_from_receipt(receipt_path, existing, replay=False)


# Names used by lifecycle adapters and older callers.
record_closeout = closeout
close_out = closeout
capture_closeout = closeout


def _parse_observations(values: Sequence[str], filename: str | None) -> list[dict[str, Any]]:
    raw_values = list(values)
    if filename:
        try:
            loaded = json.loads(Path(filename).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CloseoutError(f"cannot read observations file {filename}: {exc}") from exc
        if not isinstance(loaded, list):
            raise CloseoutError("observations file must contain a JSON list")
        raw_values.extend(json.dumps(item) for item in loaded)
    parsed: list[dict[str, Any]] = []
    for raw in raw_values:
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CloseoutError(f"invalid observation JSON: {exc}") from exc
        if not isinstance(item, dict):
            raise CloseoutError("each observation must be a JSON object")
        parsed.append(item)
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point; see the module docstring for exit behavior."""

    raw = list(argv if argv is not None else sys.argv[1:])
    if raw and raw[0] in {"closeout", "record"}:
        raw = raw[1:]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", "--state-root", required=True, help="operational state location")
    parser.add_argument("--boundary-id", "--boundary", required=True)
    parser.add_argument("--event-id", "--event", default=None)
    parser.add_argument(
        "--kind", "--boundary-kind", required=True,
        choices=[item.value for item in BoundaryKind] + sorted(_KIND_ALIASES),
    )
    parser.add_argument(
        "--state", "--boundary-state", required=True,
        choices=[item.value for item in BoundaryState] + sorted(_STATE_ALIASES),
    )
    parser.add_argument("--repo-id", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--project", default=".")
    parser.add_argument("--platform", default="codex")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--observation", action="append", default=[])
    parser.add_argument("--observations-file", "--observation-file")
    args = parser.parse_args(raw)
    try:
        observations = _parse_observations(args.observation, args.observations_file)
        result = closeout(
            args.root, args.boundary_id, args.kind, args.state, observations,
            event_id=args.event_id, repo_id=args.repo_id, task_id=args.task_id,
            project=args.project, platform=args.platform, when=args.date,
        )
    except (CloseoutError, OSError) as exc:
        print(f"closeout: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if result.status in {"completed", "ignored"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
