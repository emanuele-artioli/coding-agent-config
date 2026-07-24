---
name: reviewer-response
description: Work a reviewer-driven item for a paper resubmission or revision — scope the required experiment/code/text change, implement it, and update the reviewer checklist. Use when the user references a reviewer comment, asks what's left for a revision, or wants to close a checklist item.
---

# Working a reviewer-response checklist

Assumes the paper repo keeps (or should keep) an authoritative, living
checklist — one entry per reviewer theme, with something like
Reviewer(s) / Status / Evidence / Owed(or Plan) / Resolution fields — plus
the raw reviews themselves, and a research log with hard rules and standing
results. If the paper repo has its own `CLAUDE.md`, it's the source of truth
for exactly where these live and what the marker/revision-tracking
conventions are; read it, and the checklist itself (it moves — don't trust a
stale mental model of what's open), before scoping anything.

## Workflow

1. Read the specific review section and the matching checklist entry — its
   "Owed"/"Plan" field is the scoped task.
2. Check the paper's markers for where the work lands (the same
   `GOAL/HOLE/NOTE/NEXT/CLAIM` grep as the `update-paper` skill). Several
   reviewer answers typically map onto a `HOLE` naming a whole missing
   section or table.
3. Classify the work:
   - **Experiment** → hand off to the project's run/experiment skill or
     agent, then summarize with the project's results-reporting skill.
   - **Code change** → normal repo rules (lint/type-check/tests + real-input
     verification, commit before kicking off any long run).
   - **Paper text** → the `paper-editor` agent (or this project's own
     paper-editing convention), for substantive edits.
4. For any paper claim about the implementation, verify against the source
   and real output before writing — and check the research log's superseded
   registry, because a previously-cited result may have already been
   retracted.
5. When done, update the checklist in the same pass: Status plus one
   concrete Resolution line (what changed, where — a section added, a table
   added, the run/result identifier). "Done" only when the change is
   actually in place, never from a plan alone.
6. Fold new evidence into the paper via the `update-paper` skill — clearing
   the relevant `HOLE` and writing the `CLAIM` line in the same edit.
