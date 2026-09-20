#!/usr/bin/env python3
"""Check that every shared skill and agent honours the role contracts.

Code checks what prose would only suggest. Run after editing anything under
`skills/` or `agents/`:

    python3 verify_roles.py            # exit 1 on any failure
    python3 verify_roles.py --list     # also print what passed

Rules enforced:

* Every `skills/<name>/SKILL.md` has frontmatter `name` equal to its
  directory and a non-empty `description`. Senior hats are engineer,
  paper, end-of-session. Dispatch hats (engineer, paper) name the
  `session` skill, so the dispatch contract is reached from them, and
  stay under MAX_SKILL_LINES.
* Every `agents/<name>.agent.md` has frontmatter `name` equal to its stem,
  a non-empty `description`, and the five report headings verbatim in its
  body, so a child cannot be spawned without the report contract. A junior
  (one listed in JUNIOR_AGENTS) also carries its portable `rung: junior`,
  `effort:` and `maxTurns:`; the escalation role carries `rung: escalation`.
* Every junior and escalation agent restricts `tools:`, sets
  `omitClaudeMd: true`, and carries the `agents/JUNIOR-FACTS.md` text
  verbatim in its body. Those three go together: a child that does not
  load the imported host rules must be handed the host facts instead.
* The `session` skill's routing table names every agent file, and every
  agent it names exists. Same for the senior skills it lists.
* No file under skills/ or agents/ still names a retired tool
  (RETIRED_NAMES).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HOST = Path(__file__).resolve().parents[1]
SKILLS = HOST / "skills"
AGENTS = HOST / "agents"

REPORT_HEADINGS = (
    "## Result: PASS | FAIL | STUCK",
    "## Changed",
    "## Check",
    "## Not verified",
    "## Assumptions",
)
SENIOR_SKILLS = (
    "engineer",
    "paper",
    "end-of-session",
)
JUNIOR_AGENTS = (
    "implementer",
    "paper-screener",
    "data-condenser",
    "paper-editor",
    "referee",
    "gpu-job-runner",
)
ESCALATION_AGENTS = ("stuck-escalation",)
ROLE_RUNGS = {agent: "junior" for agent in JUNIOR_AGENTS} | {
    agent: "escalation" for agent in ESCALATION_AGENTS
}
RETIRED_NAMES = (
    "model-routing",
    "budget-default",
    "review-fix",
    "expert-retry",
    "evaluate-candidates",
    "implementation-plan",
    "test-design",
    "literature-review",
    "figure-first",
    "paper-outline",
    "paper-structure",
    "update-paper",
    "reviewer-response",
    "results-report",
    "verify-measurement",
)
MAX_SKILL_LINES = 120
MAX_AGENT_LINES = 100
JUNIOR_FACTS = AGENTS / "JUNIOR-FACTS.md"

_FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def frontmatter(text: str) -> dict[str, str]:
    match = _FM.match(text)
    if not match:
        return {}
    out: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            out[key.strip()] = value.strip()
    return out


def check_skill(path: Path, failures: list[str], passed: list[str]) -> None:
    text = path.read_text()
    fm = frontmatter(text)
    name = path.parent.name
    label = f"skills/{name}"
    if fm.get("name") != name:
        failures.append(f"{label}: frontmatter name {fm.get('name')!r} != {name!r}")
    if not fm.get("description"):
        failures.append(f"{label}: empty description")
    if name in SENIOR_SKILLS:
        if "`session`" not in text:
            failures.append(f"{label}: senior skill does not name the `session` skill")
        lines = len(text.splitlines())
        if lines > MAX_SKILL_LINES:
            failures.append(f"{label}: {lines} lines > {MAX_SKILL_LINES}")
    for retired in RETIRED_NAMES:
        if retired in text:
            failures.append(f"{label}: names retired tool {retired!r}")
    passed.append(label)


def _stripped(text: str) -> str:
    """The text with trailing whitespace removed from every line."""
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def check_agent(path: Path, failures: list[str], passed: list[str], facts: str) -> None:
    text = path.read_text()
    fm = frontmatter(text)
    stem = path.name.removesuffix(".agent.md")
    label = f"agents/{stem}"
    if fm.get("name") != stem:
        failures.append(f"{label}: frontmatter name {fm.get('name')!r} != {stem!r}")
    if not fm.get("description"):
        failures.append(f"{label}: empty description")
    for heading in REPORT_HEADINGS:
        if heading not in text:
            failures.append(f"{label}: missing report heading {heading!r}")
    if stem in JUNIOR_AGENTS:
        if fm.get("rung") != ROLE_RUNGS[stem]:
            failures.append(
                f"{label}: role frontmatter rung {fm.get('rung')!r} "
                f"!= {ROLE_RUNGS[stem]!r}"
            )
        for key in ("effort", "maxTurns"):
            if key not in fm:
                failures.append(f"{label}: junior without frontmatter {key}:")
    if stem in ESCALATION_AGENTS:
        if fm.get("rung") != ROLE_RUNGS[stem]:
            failures.append(
                f"{label}: role frontmatter rung {fm.get('rung')!r} "
                f"!= {ROLE_RUNGS[stem]!r}"
            )
        if "effort" not in fm:
            failures.append(f"{label}: escalation agent without frontmatter effort:")
    if stem in JUNIOR_AGENTS + ESCALATION_AGENTS:
        if not fm.get("tools"):
            failures.append(f"{label}: child without frontmatter tools:")
        if fm.get("omitClaudeMd") != "true":
            failures.append(f"{label}: child without frontmatter omitClaudeMd: true")
        if facts and _stripped(facts) not in _stripped(text):
            failures.append(f"{label}: body does not carry the JUNIOR-FACTS.md text")
    lines = len(text.splitlines())
    if lines > MAX_AGENT_LINES:
        failures.append(f"{label}: {lines} lines > {MAX_AGENT_LINES}")
    for retired in RETIRED_NAMES:
        if retired in text:
            failures.append(f"{label}: names retired tool {retired!r}")
    passed.append(label)


def check_routing(failures: list[str]) -> None:
    session = SKILLS / "session" / "SKILL.md"
    if not session.is_file():
        failures.append("skills/session: missing")
        return
    text = session.read_text()
    agents = {p.name.removesuffix(".agent.md") for p in AGENTS.glob("*.agent.md")}
    for agent in sorted(agents):
        if f"`{agent}`" not in text:
            failures.append(f"skills/session: routing table does not name agent `{agent}`")
    for name in re.findall(r"`([a-z][a-z0-9-]*)`", text):
        if name in JUNIOR_AGENTS + ESCALATION_AGENTS and name not in agents:
            failures.append(f"skills/session: names agent `{name}` that has no file")
    for skill in SENIOR_SKILLS:
        if f"`{skill}`" not in text:
            failures.append(f"skills/session: does not list senior skill `{skill}`")
        if not (SKILLS / skill / "SKILL.md").is_file():
            failures.append(f"skills/{skill}: missing (listed as a senior skill)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--list", action="store_true", help="print what passed")
    args = parser.parse_args()

    failures: list[str] = []
    passed: list[str] = []
    for skill in sorted(SKILLS.glob("*/SKILL.md")):
        check_skill(skill, failures, passed)
    facts = ""
    if JUNIOR_FACTS.is_file():
        facts = JUNIOR_FACTS.read_text()
    else:
        failures.append(f"agents/{JUNIOR_FACTS.name}: missing")
    for agent in sorted(AGENTS.glob("*.agent.md")):
        check_agent(agent, failures, passed, facts)
    check_routing(failures)

    if args.list:
        for label in passed:
            print(f"ok   {label}")
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"{len(passed)} files checked, {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
