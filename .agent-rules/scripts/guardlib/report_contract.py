"""Policy: check a subagent's final report against the report contract.

The contract lives in `skills/session/SKILL.md` ("Report contract"): the
child's last message uses five verbatim headings, and under **Check** it
pastes the command and the last lines of its real output. A report that
drops a heading, or that describes a check instead of pasting its output,
is a FAIL whatever its Result line says — the parent then has no evidence
and must re-run the check itself.

Pure functions only: no stdin, no stdout, no exit codes. The adapters in
`scripts/claude/subagent-stop.py` and `scripts/cursor/subagent-stop.py`
read their platform's payload and print in their platform's shape.

Wiring these adapters into a settings file is the senior's step, not this
module's — nothing here reads or writes any configuration. The Claude side
targets the documented `SubagentStop` event. **The Cursor side is pending
verification**: the `subagentStop` event's payload field for the child's
final message has not been observed live, so the adapter accepts more than
one field name (see its docstring).
"""

from __future__ import annotations

import re

RESULT_HEADING = "## Result: PASS | FAIL | STUCK"

#: The five headings of the report contract, in order. The Result entry is
#: the *template* line; a real report carries one of RESULT_VALUES instead
#: of the `PASS | FAIL | STUCK` placeholder.
REQUIRED_HEADINGS = (
    RESULT_HEADING,
    "## Changed",
    "## Check",
    "## Not verified",
    "## Assumptions",
)

RESULT_VALUES = ("PASS", "FAIL", "STUCK")

_RESULT_LINE = re.compile(r"^##\s*Result:\s*(.*?)\s*$", re.MULTILINE)
_ANY_HEADING = re.compile(r"^##\s+")
_FENCE = re.compile(r"^\s*```", re.MULTILINE)

MISSING = "missing heading: {}"
BAD_RESULT = "Result line is not PASS, FAIL, or STUCK"
NO_OUTPUT = "no output pasted under Check"


def _has_heading(text: str, heading: str) -> bool:
    return any(line.strip().startswith(heading) for line in text.splitlines())


def _check_section(text: str) -> str | None:
    """The body between `## Check` and the next `## ` heading, or None."""
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip().startswith("## Check"):
            start = index + 1
            break
    if start is None:
        return None
    body: list[str] = []
    for line in lines[start:]:
        if _ANY_HEADING.match(line.strip()) and line.strip().startswith("## "):
            break
        body.append(line)
    return "\n".join(body)


def problems(text: str) -> list[str]:
    """Human-readable problems with a child's final report, in order."""
    text = text or ""
    found: list[str] = []

    match = _RESULT_LINE.search(text)
    if match is None:
        found.append(MISSING.format(RESULT_HEADING))
    elif match.group(1) not in RESULT_VALUES:
        found.append(BAD_RESULT)

    for heading in REQUIRED_HEADINGS[1:]:
        if not _has_heading(text, heading):
            found.append(MISSING.format(heading))

    body = _check_section(text)
    if body is not None:
        non_blank = [line for line in body.splitlines() if line.strip()]
        if not _FENCE.search(body) and len(non_blank) < 2:
            found.append(NO_OUTPUT)

    return found


def message(found: list[str]) -> str:
    """One paragraph for the parent. Empty list means nothing to say."""
    if not found:
        return ""
    return (
        "Report contract: this subagent's report does not meet the contract — "
        + "; ".join(found)
        + ". Treat the report as FAIL whatever its Result line says, and "
        "re-run the check yourself before believing any of it."
    )
