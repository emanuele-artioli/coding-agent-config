---
name: update-paper
description: Fold new findings (run/experiment results, diagnoses, retractions, dead ends) into a project's paper, guided by its marker convention, and into its research log. Use after runs complete and results are committed and tested, or when a conclusion changes.
---

# Folding findings into the paper

This assumes the project's paper repo uses (or should use) a marker
convention in the manuscript source — comments like
`STATUS/GOAL/HOLE/NOTE/NEXT/CLAIM(anchor):` — that record, per element, what
it's waiting for and where its data came from. If the project's paper repo
has its own `CLAUDE.md`, that's the authoritative spec for the exact marker
syntax and any revision-tracking convention (e.g. `\rev{}`/`\del{}`); read it
before editing. The paper is the primary living document — anything a
reader needs goes there; a secondary research log holds what can't live in
reader-facing text (hard methodology rules, standing results, dead-end and
superseded registries).

## Before writing anything

**Check the run's own citability verdict before citing it.** Projects on
this host record whether a run/result satisfies their methodology rules
directly in that run's own output record (an `invariant_failures`-style
field, or equivalent) — a non-empty/failing verdict means the run isn't
citable, even though it may look like a perfectly well-formed result. A
result with **no** verdict at all predates the check and has never been
evaluated — treat a missing verdict as unverified, not as clean, and backfill
if the project has a command for that.

Then check the research log's dead-end/superseded registry, if one exists —
it exists to stop a disproven conclusion from being re-landed.

## Procedure

1. **Find what the paper is waiting for.** Grep the manuscript for the
   project's marker convention (e.g. `grep -n '^% *\(STATUS\|GOAL\|HOLE\|
   NOTE\|NEXT\|CLAIM\)(' *.tex`). A `HOLE(id)` names the exact data an
   element is missing — only land a number where the paper actually has a
   hole for it.
2. **Write the text**, and in the same edit clear the `HOLE` and add the
   provenance line (`CLAIM(id): src=<path> date=YYYY-MM-DD`, or whatever the
   project's marker spec calls for). A `HOLE` may only be cleared by the edit
   that lands its data — never in advance. If the project tracks
   reviewer-visible revisions (`\rev{}`/`\del{}` or similar), follow that
   convention for the same edit.
3. **Update the research log**: add the finding to standing results, or to
   the dead-end registry if something was disproved. If a queued result just
   landed in the paper text, remove it from the queue.
4. **Cross-update the reviewer checklist**, if one exists and a referee item
   advanced. "Done" means the text or experiment is actually in place — never
   a plan.
5. **If a component's contract changed,** update the project's architecture
   doc in the same session, if it has one.
6. **Verify and commit.** If there's no local TeX toolchain, verify
   structurally (balanced braces/environments in the edited file) and let the
   remote build (Overleaf, CI) confirm. If the paper lives in a separate
   nested git repo, commit it separately from the code, naming the anchor ids
   and the run/result identifiers in the message.

## Rules of evidence

- Every number cites a real path: a specific run/result directory and its
  output record. No path, no claim.
- **Name the config that produced it.** A smoke-test-sized result must be
  labeled as one — check whether the project's default config caps some
  dimension (frame count, iteration count) that would make a partial result
  look like a full one.
- Distinguish a single-run observation from a swept or confirmed result, in
  the text, not just in your head.
- A conclusion that's now wrong is marked superseded in place, never
  rewritten or silently deleted — the registry is what stops it being
  rediscovered.
- Invalidated run outputs get moved to a `_superseded/` (or equivalent)
  location, never deleted outright — check whether a guard-rm-style hook
  would block the delete anyway.
