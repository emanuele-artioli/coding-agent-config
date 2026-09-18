# E03 — AV1, VVC, neural anchors and representative timing

Owner: Cursor. Area: [evaluation](../../../../areas/evaluation.md).
Depends: E01 accepted. Scope: anchor adapters/drivers, benchmark manifests,
profiling/plot ingestion, minimal job allocation safeguards and corresponding
tests. No generator/background algorithm edits. First probe budget from campaign;
return costed extension if slow/native anchors exceed it.

## Work

Reuse/rescore eligible conventional anchor streams and timings before encoding.
Implement or validate one recent published neural baseline, starting with
DCVC-UF (official https://github.com/microsoft/DCVC); verify current paper,
checkpoints, runtime dependencies and real entropy-coded standalone round trip.
Pin release/commit/weights; if unavailable, return the compatibility blocker and
costed DCVC-RT or other published fallback rather than silently claiming SOTA.
This is integration/profiling, not a neural-baseline retraining campaign.

Start at E01's low resolution/fps. Sweep high/low preprocessing axes with shared
input/timebase controls, then native endpoints for promising regimes. Use slowest
supported AV1 and VVC implementation presets, recording resolved encoder and
decoder paths/builds, threads/GOP/chroma/range/latency, and actual bitstream bytes.
Do not call VVenC the VTM reference encoder or invent a codec-wide bitrate floor.
Train-free native codec points still require identical source frame identities.
When PointStream demonstrates a speed advantage, add bounded faster-preset arms
and compare measured computation budgets. Keep offline/low-delay comparisons
separate and include rescaling/restoration and neural chunk startup latency.

Use available hosts opportunistically with the campaign's per-host aggregate
CPU cap, GPU recheck/claims and idempotent job IDs. Verify current monitor and
resume behavior before introducing any new helper. Profile independent repeats
on named hardware; reuse matching timing strata for other RD points with visible
evidence links. Show confidence intervals, p95/cold/steady times and incomplete
strata; do not present heavily contended measurements as intrinsic speed.

Implement reusable RD plus quality/client-time plotting from the accepted index,
PDF/SVG exports and source tables, with optional log-time-coloured RD overview.
Keep encoding costs visible, and label unmatched/missing timing honestly. Do not
mix native quality with common-display/timebase quality in one curve.

## Acceptance

Actual paired coded/decoded points with metric/wire controls and adequate overlap;
complete tool/format provenance; a profile-evidence table and timing reuse proof;
plots reproducible by one recorded command, with explicit exclusions. Return
missing intervals and cost of filling them instead of extrapolating a win.

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
