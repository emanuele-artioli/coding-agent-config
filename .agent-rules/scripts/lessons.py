#!/usr/bin/env python3
"""Lesson ledger over the candidates queue — find the earlier entry, record a repeat.

`AGENTS.md` makes a rule out of anything that has gone wrong *more than once*,
but nothing read the queue back, so a second occurrence looked like a first.
This reads frontmatter only (bodies are long; NFS opens are slow) and never
touches git.

    lessons.py list
    lessons.py match "one-line summary of what just went wrong"
    lessons.py record <id> --project <path> --platform <name>
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sys
import tempfile
import threading
import uuid
from datetime import date
from pathlib import Path

try:
    import fcntl
except ImportError:  # pragma: no cover - the supported hosts are POSIX
    fcntl = None

ROOT = Path(__file__).resolve().parent.parent / "candidates"
FULL_LIST_UNDER = 60  # below this, printing every summary beats any matcher
VALID_AXES = frozenset(("project", "platform"))
EVENT_FIELDS = ("recorded_events", "event_ids", "events", "event_id")


class RecordError(ValueError):
    """A candidate cannot be safely recorded without changing its meaning."""

STOP = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "it", "its",
    "is", "are", "was", "were", "that", "this", "with", "from", "by", "at",
    "as", "be", "not", "but", "than", "then", "when", "while", "into", "over",
    "out", "up", "do", "does", "did", "can", "will", "so", "if", "no", "any",
    "one", "two", "also", "here", "there", "which", "what", "how", "you",
}


def _stem(word: str) -> str:
    for suf in ("ing", "ies", "ed", "es", "s"):
        if suf == "s" and word.endswith("ss"):
            continue
        if word.endswith(suf) and len(word) > len(suf) + 2:
            return word[: -len(suf)]
    return word


def _tokens(text: str) -> set[str]:
    words = re.split(r"[^a-z0-9]+", text.lower())
    return {_stem(w) for w in words if len(w) > 2 and w not in STOP}


def _frontmatter(path: Path) -> dict[str, str]:
    """Parse the leading `---` block. Scalars only; lists stay raw strings."""
    fields: dict[str, str] = {}
    try:
        with path.open() as handle:
            if handle.readline().strip() != "---":
                return fields
            for line in handle:
                if line.strip() == "---":
                    break
                m = re.match(r"^([a-z_]+):\s*(.*)$", line.rstrip("\n"))
                if m:
                    fields[m.group(1)] = m.group(2).strip()
    except OSError:
        return {}
    return fields


class Entry:
    def __init__(self, path: Path, root: Path) -> None:
        self.path = path
        self.fm = _frontmatter(path)
        self.id = self.fm.get("id") or path.stem.removeprefix("promote-")
        self.summary = self.fm.get("summary", "")
        self.axis = self.fm.get("axis", "project")
        self.status = self.fm.get("status", "open")
        self.where = "open" if root / "open" in path.parents else "done"
        try:
            self.occurrences = int(self.fm.get("occurrences", "1"))
        except ValueError:
            self.occurrences = 1
        # No `keywords:` on the 18 legacy files — derive from the slug + summary.
        raw = self.fm.get("keywords", "")
        self.keywords = _tokens(raw) | _tokens(path.stem)
        self.summary_tokens = _tokens(self.summary)

    def score(self, query: set[str]) -> int:
        """Slug and keyword hits count double; summary hits count once."""
        return sum(
            2 if t in self.keywords else 1
            for t in query
            if t in self.keywords or t in self.summary_tokens
        )

    def line(self) -> str:
        return (
            f"{self.id} | {self.where}/{self.status} | {self.axis} | "
            f"x{self.occurrences} | {self.summary}"
        )


def load(root: Path = ROOT) -> list[Entry]:
    paths: list[Path] = []
    for directory in (root / "open" / "project", root / "open" / "platform", root / "done"):
        if directory.is_dir():
            paths += sorted(p for p in directory.iterdir() if p.suffix == ".md")
    return [Entry(p, root) for p in paths]


def cmd_list(entries: list[Entry]) -> int:
    for entry in entries:
        print(entry.line())
    return 0


def cmd_match(entries: list[Entry], query: str) -> int:
    tokens = _tokens(query)
    ranked = sorted(
        ((e.score(tokens), e) for e in entries), key=lambda p: (-p[0], p[1].id)
    )
    hits = [(s, e) for s, e in ranked if s > 0][:5]
    if hits:
        print(f"Best matches for: {query}")
        for score, entry in hits:
            print(f"  [{score}] {entry.line()}")
    else:
        print(f"No keyword overlap for: {query}")
    print(
        "\nOverlap is a recall aid, not a verdict — a restatement in different "
        "words scores zero. Read the list before deciding this is new."
    )
    if len(entries) < FULL_LIST_UNDER:
        print(f"\nAll {len(entries)} candidates:")
        cmd_list(entries)
    return 0


def _split_document(text: str) -> tuple[list[str], str]:
    """Return frontmatter lines and body, or reject a malformed document."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise RecordError("has no frontmatter block")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[1:index], "".join(lines[index + 1:])
    raise RecordError("has an unterminated frontmatter block")


def _fields_from_lines(lines: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in lines:
        match = re.match(r"^([a-z_]+):\s*(.*?)(?:\r?\n)?$", line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return fields


def _safe_value(value: str, name: str) -> str:
    if not value or any(ord(char) < 32 for char in value):
        raise RecordError(f"{name} must be a non-empty single-line value")
    return value


def _safe_identifier(value: str) -> str:
    _safe_value(value, "candidate id")
    if value in {".", ".."} or "/" in value or "\\" in value:
        raise RecordError(f"candidate id {value!r} is not a safe file identifier")
    return value


def _parse_scalar_list(raw: str, field: str) -> list[str]:
    """Parse the small JSON/YAML scalar lists used in candidate metadata."""
    value = raw.strip()
    if not value:
        return []
    if value.startswith("["):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            # Existing candidate files use simple YAML lists without quotes.
            if not value.endswith("]"):
                raise RecordError(f"malformed {field} metadata")
            parsed = [part.strip().strip("'\"") for part in value[1:-1].split(",") if part.strip()]
        if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
            raise RecordError(f"malformed {field} metadata")
        result = parsed
    elif value.startswith(("{", "(")) or value.endswith(("}", ")")):
        raise RecordError(f"malformed {field} metadata")
    elif "," in value:
        result = [part.strip().strip("'\"") for part in value.split(",") if part.strip()]
    else:
        result = [value.strip("'\"")]
    for item in result:
        _safe_value(item, field)
    return result


def _event_ids(text: str, fields: dict[str, str]) -> list[str]:
    ids: list[str] = []
    for field in EVENT_FIELDS:
        if field in fields:
            ids.extend(_parse_scalar_list(fields[field], field))
    # The marker is also durable when a process dies after writing the body but
    # before the next metadata rewrite.  It is deliberately not read by load(),
    # so list/match remain frontmatter-only.
    ids.extend(re.findall(r"<!--\s*lessons-event:\s*([^\n]*?)\s*-->", text))
    result: list[str] = []
    for item in ids:
        if item not in result:
            result.append(item)
    return result


def _status_history(fields: dict[str, str], current: str) -> list[str]:
    history: list[str] = []
    if "status_history" in fields:
        history = _parse_scalar_list(fields["status_history"], "status_history")
    elif fields.get("previous_status"):
        history = _parse_scalar_list(fields["previous_status"], "previous_status")
    if not history:
        history = [current]
    return history


def _occurrences(fields: dict[str, str]) -> int:
    raw = fields.get("occurrences")
    if raw is None:
        return 1
    try:
        value = int(raw)
    except ValueError as exc:
        raise RecordError("occurrences metadata is not an integer") from exc
    if value < 0:
        raise RecordError("occurrences metadata cannot be negative")
    return value


def _validated_document(path: Path, root: Path) -> tuple[Entry, str, list[str], dict[str, str], list[str], list[str]]:
    try:
        text = path.read_text()
    except OSError as exc:
        raise RecordError(f"cannot read {path}: {exc}") from exc
    try:
        lines, _body = _split_document(text)
    except RecordError as exc:
        raise RecordError(f"{path} {exc}") from exc
    fields = _fields_from_lines(lines)
    entry = Entry(path, root)
    entry.fm = fields
    entry.id = fields.get("id") or path.stem.removeprefix("promote-")
    entry.summary = fields.get("summary", "")
    entry.axis = fields.get("axis", "project")
    entry.status = fields.get("status", "open")
    entry.occurrences = _occurrences(fields)
    if entry.axis not in VALID_AXES:
        raise RecordError(f"{path} has invalid axis {entry.axis!r}; expected project or platform")
    _safe_identifier(entry.id)
    _safe_value(entry.status, "status")
    events = _event_ids(text, fields)
    history = _status_history(fields, entry.status)
    return entry, text, lines, fields, events, history


def _canonical(root: Path, entry: Entry) -> Path:
    return root / "open" / entry.axis / f"promote-{_safe_identifier(entry.id)}.md"


def _same_candidate(left: Entry, right: Entry) -> bool:
    """Conservative identity check for an interrupted move or its collision."""
    for key in ("id", "axis", "summary", "created", "source_project", "source_platform"):
        if left.fm.get(key, "") != right.fm.get(key, ""):
            return False
    return True


def _has_recorder_marker(document: tuple[Entry, str, list[str], dict[str, str], list[str], list[str]]) -> bool:
    return "<!-- lessons-event:" in document[1]


def _replace_metadata(
    text: str,
    count: int,
    event_ids: list[str],
    history: list[str],
    previous_status: str | None,
    event_id: str,
    when: str,
    project: str,
    platform: str,
    evidence: str | None,
    append_occurrence: bool,
) -> str:
    lines, body = _split_document(text)
    output: list[str] = []
    seen_events = False
    seen_history = False
    seen_previous = False
    for line in lines:
        bare = line.rstrip("\r\n")
        key_match = re.match(r"^([a-z_]+):", bare)
        key = key_match.group(1) if key_match else ""
        if key == "status":
            output.append("status: recurring")
        elif key == "occurrences":
            output.append(f"occurrences: {count}")
        elif key == "recorded_events":
            output.append(f"recorded_events: {json.dumps(event_ids, ensure_ascii=True)}")
            seen_events = True
        elif key == "status_history":
            output.append(f"status_history: {json.dumps(history, ensure_ascii=True)}")
            seen_history = True
        elif key == "previous_status":
            if previous_status is not None:
                output.append(
                    f"previous_status: {json.dumps(previous_status, ensure_ascii=True)}"
                )
            else:
                output.append(bare)
            seen_previous = True
        else:
            output.append(bare)
    if not any(line.startswith("occurrences:") for line in output):
        output.append(f"occurrences: {count}")
    if not seen_events:
        output.append(f"recorded_events: {json.dumps(event_ids, ensure_ascii=True)}")
    if not seen_history:
        output.append(f"status_history: {json.dumps(history, ensure_ascii=True)}")
    if previous_status is not None and not seen_previous:
        output.append(
            f"previous_status: {json.dumps(previous_status, ensure_ascii=True)}"
        )

    updated_body = body
    if append_occurrence:
        if updated_body and not updated_body.endswith("\n"):
            updated_body += "\n"
        updated_body += (
            f"\n## Occurrence {count}, {when}, {project} ({platform})\n\n"
            f"<!-- lessons-event: {event_id} -->\n"
            "<!-- What happened this time, and why the earlier entry did not "
            "prevent it.\n     Then promote: evaluate-candidates, `recurring` "
            "branch. -->\n"
        )
        if evidence:
            updated_body += f"\nEvidence: {evidence}\n"
    return "---\n" + "\n".join(output) + "\n---\n" + updated_body


def _atomic_write(path: Path, text: str) -> None:
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


_LOCAL_LOCKS: dict[str, threading.RLock] = {}
_LOCAL_LOCKS_GUARD = threading.Lock()


@contextlib.contextmanager
def _queue_lock(root: Path):
    """Serialize writers with an advisory lock on the queue directory."""
    root.mkdir(parents=True, exist_ok=True)
    key = str(root)
    with _LOCAL_LOCKS_GUARD:
        local_lock = _LOCAL_LOCKS.setdefault(key, threading.RLock())
    with local_lock:
        if fcntl is None:  # pragma: no cover - only for non-POSIX users
            yield
            return
        fd = os.open(root, os.O_RDONLY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)


def _record_locked(
    ident: str,
    project: str,
    platform: str,
    root: Path,
    when: str,
    event_id: str,
    evidence: str | None,
) -> tuple[Path, int, bool]:
    entries = load(root)
    found = [entry for entry in entries if entry.id == ident]
    if not found:
        raise RecordError(f"no candidate with id {ident}")

    documents = [_validated_document(entry.path, root) for entry in found]
    axes = {document[0].axis for document in documents}
    if len(axes) != 1:
        raise RecordError(f"duplicate candidate id {ident} has conflicting axis values")
    axis = next(iter(axes))
    destination = root / "open" / axis / f"promote-{_safe_identifier(ident)}.md"

    # A source plus its canonical destination is the one duplicate that can be
    # safely recognized: it is the observable half-completed move. Every other
    # duplicate remains an error rather than selecting an arbitrary file.
    canonical_doc = None
    canonical_path = destination.resolve()
    for document in documents:
        if document[0].path.resolve() == canonical_path:
            canonical_doc = document
            break
    if canonical_doc is None and destination.exists():
        canonical_doc = _validated_document(destination, root)
        if canonical_doc[0].id != ident or canonical_doc[0].axis != axis:
            raise RecordError(f"destination collision at {destination}; refusing to overwrite it")
        documents.append(canonical_doc)

    if len(documents) > 1:
        if canonical_doc is None:
            raise RecordError(f"duplicate candidate id {ident}; refusing to choose a file")
        recoverable_move = False
        for document in documents:
            if document is canonical_doc:
                continue
            if not _same_candidate(canonical_doc[0], document[0]):
                raise RecordError(f"destination collision at {destination}; files are unrelated")
            # A canonical/source pair is only an interrupted move when their
            # durable state differs. Identical duplicates are still rejected;
            # otherwise a user-created duplicate would be silently deleted.
            if (
                set(canonical_doc[4]) != set(document[4])
                or canonical_doc[0].occurrences != document[0].occurrences
                or canonical_doc[0].status != document[0].status
            ):
                if not (_has_recorder_marker(canonical_doc) or _has_recorder_marker(document)):
                    raise RecordError(
                        f"destination collision at {destination}; no recorder state proves a recovery"
                    )
                recoverable_move = True
        if not recoverable_move:
            raise RecordError(f"duplicate candidate id {ident}; refusing to choose a file")

    # Select the canonical document as the base whenever it exists. This lets a
    # retry keep an already-written destination and fold in a source left behind
    # by an interrupted unlink.
    base = canonical_doc or documents[0]
    base_entry, base_text, _base_lines, _base_fields, base_events, base_history = base
    all_events: list[str] = []
    for document in documents:
        for item in document[4]:
            if item not in all_events:
                all_events.append(item)

    max_document = max(documents, key=lambda document: document[0].occurrences)
    max_events = set(max_document[4])
    max_count = max(document[0].occurrences for document in documents)
    before = set(all_events)
    already_recorded = event_id in before
    if not already_recorded:
        all_events.append(event_id)
    count = max_count + len(set(all_events) - max_events)

    # A replay against the already-canonical document is a true no-op. Apart
    # from being cheaper, this keeps mtimes and the body stable for callers that
    # use the result as a durable receipt.
    if already_recorded and canonical_doc is not None and len(documents) == 1:
        return destination, count, True

    current_status = base_entry.status
    history = list(base_history)
    if not history:
        history = [current_status]
    if current_status not in history:
        history.append(current_status)
    previous_status = base_entry.fm.get("previous_status")
    if current_status != "recurring" and previous_status is None:
        previous_status = current_status
    if not history or history[-1] != "recurring":
        history.append("recurring")

    # Preserve occurrence text from a source that has an event absent in the
    # canonical destination. This matters only for crash recovery; normal writes
    # run under the same lock and produce one complete document.
    merged_text = base_text
    base_event_set = set(base_events)
    for document in documents:
        if document is base:
            continue
        if set(document[4]) - base_event_set:
            _other_lines, other_body = _split_document(document[1])
            if other_body and other_body not in merged_text:
                if not merged_text.endswith("\n"):
                    merged_text += "\n"
                merged_text += other_body
            base_event_set.update(document[4])

    updated = _replace_metadata(
        merged_text, count, all_events, history, previous_status,
        event_id, _safe_value(when, "date"), _safe_value(project, "project"),
        _safe_value(platform, "platform"), evidence, not already_recorded,
    )
    try:
        _atomic_write(destination, updated)
    except OSError as exc:
        raise RecordError(f"could not atomically write {destination}: {exc}") from exc

    # The destination is durable before any source is removed. If cleanup is
    # interrupted, a later invocation recognizes this exact pair and retries it.
    cleanup_error: OSError | None = None
    for document in documents:
        source = document[0].path
        if source.resolve() == destination.resolve():
            continue
        try:
            source.unlink()
        except FileNotFoundError:
            continue
        except OSError as exc:
            cleanup_error = exc
    if cleanup_error is not None:
        raise RecordError(
            f"recorded {event_id} at {destination}, but source cleanup is pending: {cleanup_error}"
        )
    return destination, count, already_recorded


def cmd_record(
    entries: list[Entry], ident: str, project: str, platform: str,
    root: Path, when: str, event_id: str | None = None,
    evidence: str | None = None,
) -> int:
    del entries  # record reloads under the writer lock; the caller's snapshot may be stale
    try:
        event = _safe_value(event_id, "event id") if event_id is not None else uuid.uuid4().hex
        if evidence is not None:
            evidence = _safe_value(evidence, "evidence")
        destination, count, already = _record_with_lock(
            ident, project, platform, root, when, event, evidence
        )
    except RecordError as exc:
        print(f"lessons: {exc}", file=sys.stderr)
        return 1
    if already:
        print(f"lessons: {ident} event {event} already recorded; occurrences={count}, status=recurring")
    else:
        print(f"lessons: {ident} now occurrences={count}, status=recurring")
    print(f"lessons: {destination}")
    return 0


def _record_with_lock(
    ident: str,
    project: str,
    platform: str,
    root: Path,
    when: str,
    event_id: str,
    evidence: str | None,
) -> tuple[Path, int, bool]:
    root = root.resolve()
    with _queue_lock(root):
        return _record_locked(ident, project, platform, root, when, event_id, evidence)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT), help="candidates/ directory")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p_match = sub.add_parser("match")
    p_match.add_argument("summary")
    p_record = sub.add_parser("record")
    p_record.add_argument("id")
    p_record.add_argument("--project", default=".")
    p_record.add_argument("--platform", default="claude")
    p_record.add_argument("--date", default=date.today().isoformat())
    p_record.add_argument(
        "--event-id", "--event", "--capture-id", "--capture", "--observation-id",
        dest="event_id", help="stable identity for this observation",
    )
    p_record.add_argument("--evidence", help="short evidence note for the occurrence")
    args = parser.parse_args(argv)

    root = Path(args.root)
    entries = load(root)
    if args.cmd == "list":
        return cmd_list(entries)
    if args.cmd == "match":
        return cmd_match(entries, args.summary)
    return cmd_record(
        entries, args.id, args.project, args.platform, root, args.date,
        args.event_id, args.evidence,
    )


if __name__ == "__main__":
    raise SystemExit(main())
