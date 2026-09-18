# E06 — Residual contribution and complete-system frontier

Owner: Cursor. Area: [evaluation](../../../../areas/evaluation.md).
Depends: E03 anchors + E04 backgrounds; E05 finalist for final neural comparison.
Scope: residual/runner integration, paired system experiments, profiling and
plots/tests. Shared generator internals require a handoff from Antigravity.

## Work

Reuse existing residual ladders only where predictor, source, wire/decode and
quality identities match. Pair residual off/on for fixed paste and neural
predictors/backgrounds. Sweep coarse residual QPs, refine near useful matched
quality intervals. Full-system residual correction must use the same decoded,
quantized conditioning/references/weights and generator state at server and client.
Verify reconstructed predictors agree; freeze seeds/state for stochastic models
and test actual delivered residual-corrected output.

Decompose time: residual-off sender preprocessing/encoding + client generation;
residual-on adds server generation, residual encoding and client residual
decode/application, while client generation remains. Expensive generation may
roughly double generation work across endpoints; measure its share and total
wall time instead of enforcing a 2x result. Account residual payload separately
from additional metadata, including its QP/format, and reuse matching profiles.

Combine E04/E05 frontier candidates and perform bounded joint refinement
(background QP/removal/refresh, reference cadence, model settings, residual QP).
Keep components fixed for causal ablations, then label joint-search results
separately. Include generation/appearance/motion/background ablations required by
roadmap, testing zero calls/bytes for disabled optional stages. Do not assume
component winners compose into the best codec.

Search low/native and mixed resolution/fps corners, then at most two intermediate
points around feasibility. Report nondominated resolution/fps pairs for live
sender and playback separately, causal lookahead/startup and p95 latency, queue
stability and memory. Run E01's registered sustained-duration check only for
real-time finalists, beyond startup/context and multiple refresh cycles; short
scene probes are screening evidence only. Native fps/resolution may fail; preserve the measured
boundary. Offline panorama/fitting cannot become live solely through resizing.
If faster than slow anchors, request E03 faster-preset points before speed claims.
Compare matched input/timebase, colour paths, quality floors and resource regimes.

## Acceptance

Residual contribution plots with measured/representative stage timing; actual
standalone full-wire comparisons against AV1/VVC/neural codec in overlapping
quality/rate intervals; source-level uncertainty; selected joint frontier and
live/playback feasibility classification. SOTA claim only where comparisons to
all declared baselines support it. Freeze config selection/adaptation/metrics and
pass a manifest to E07; otherwise return the measured gap and next bounded choice.

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
