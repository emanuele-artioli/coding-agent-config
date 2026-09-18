# E08 — Evaluation manuscript and reproducible figures

Owner: Antigravity. Area: [paper](../../../../areas/paper.md).
Setup/structure starts early; accepted component evidence permits corresponding
prose; final headline claims require E06/E07. Scope: plot/table tools and code-side
evidence package; manuscript edits only in its separate git repository, after
reading that repo's AGENTS.md. Do not duplicate manuscript text in the code repo.

## Work

Read the current manuscript and map its evaluation to setup and the campaign's
five-part narrative. Allocate main/appendix space before inserting every figure.
Write setup and verified method/training protocol while experiments run; preserve
explicit placeholders for unconfirmed numbers. Once a generator clears baseline,
prioritize this work over optional family improvements.

Use E03's shared plot reader rather than a competing script. Produce RD and
client-time panels for anchors/final system, paired removal deltas, foreground
resource frontiers, residual curves and disjoint byte/time tables. Include
encoder time and justified representative timing references without requiring
fresh profiles for every RD row. Show sample counts/uncertainty and offline,
non-real-time, missing or inconclusive points. Put full search axes, budget,
learning curves, negative results and failures in a compact appendix/artifact.

Audit each numerical claim to immutable run IDs, eligible metric scope and
hardware/timing evidence. Rebuild all figures/tables from the accepted index in
one documented command; export vector PDF/SVG and machine-readable source tables.
Package minimal reproduction commands, configs, native binaries/build identities,
checkpoint references and source acquisition instructions without redistributing
restricted footage. Clear result placeholders only with actual evidence.

## Acceptance

Paper builds; main+references and appendix meet the repository's verified venue
budget; citations/figures agree with accepted evidence and domain boundaries;
code and paper changes have separate commits/PR provenance. Run the paper
structure workflow for page/section balance and final artifact reconstruction.
Report submission readiness and unresolved requirements here. Do not submit to
the venue or silently rewrite the scientific gates to fit the remaining time.

## Start, validation and return

Read [campaign plan](../plan.md), your named area, and the project
[session workflow](../../SKILL.md). Follow its worktree, ownership, reuse-first,
bounds, per-stage budget, scheduling and return contract. Output root is
`$PS_DATA_ROOT/outputs/evaluation-20260914/<task-id>/<unique-run-id>/`; job records
are under `$PS_DATA_ROOT/jobs/`. These paths are proposed destinations, not
existing evidence. Commit code/docs, run relevant behavior tests and setup
verification plus CI; native paths require a real encode/decode control.
Documentation-only work uses link checks and `git diff --check`. Report exact
validation commands actually run; do not invent working CLI flags in dispatches.
Return here after the bounded assignment; wait for the coordinator's next task.
