# E05 — Bounded foreground training and baseline-clearing model

Owner: Antigravity. Area: [generation](../../../../areas/generation.md).
Depends: E02 readiness and E01 split/schema. Low-resolution crop learning can
start before E04; final whole-codec selection uses E04's fixed backgrounds.
Scope: training/model configs, adapters and checkpoints in external storage,
foreground campaign evaluator and tests; no concurrent background-core edits.

## Work

Use existing valid training/results first. Compare paste and supported warped
reference baselines against ready small and temporal/diffusion methods. Main
comparison residual off; defer matched residual-on baselines to E06. Charge
reference refresh, motion/pose/masks, per-video weights/adapters and container
costs. Shared pretrained weights need an explicit installation/download and
startup assumption, applied equally to the neural anchor.

Write per-model cards with valid hyperparameter endpoints (e.g. learning rate,
capacity, sequence/crop size, diffusion steps), native architecture use and
training budget. First fit a tiny scene to prove learnability; then disjoint
same-video validation; cross-video development validation; finally fit promoted
configurations under the frozen recipe. Increase resources progressively with
aggregate round caps 1/4/12 GPU-hours, not these amounts per grid cell. Report
learning curves, examples/steps, seeds, wall/GPU cost and promotion criteria.
Do not eliminate slowly learning candidates on one tiny run or tiny differences;
reserve a bounded ambiguity extension. Use coarse endpoints then targeted
refinement, not every hyperparameter combination.

Start low-resolution to reduce cost, then evaluate/fine-tune finalists at higher
resolution/fps and one or two intermediate points. Distinguish crop/model input
size from full video output. A low-resolution ranking need not transfer; test
one plausible reversal before permanently deferring a family. Use actual full
trajectories and native temporal context, preserving pose and identity fidelity.

Baseline-clearing criterion: reproducible foreground improvement at matched
actual total rate and declared client budget, satisfying whole-frame quality
floor and temporal/identity controls. Freeze the metric, effect size/uncertainty
rule and rate interval on development data before final ranking. A full-codec
residual-on advantage may strengthen the result but cannot silently replace the
required residual-off foreground comparison; return here if only that works.

## Acceptance

At least one validated neural finalist clears declared baselines, with source
uncertainty and a cost/quality/latency frontier; otherwise return the precise
roadblock. Once achieved, freeze that candidate for writing/confirmation and
queue optional improvements separately. Label remaining methods failed under
recorded budget, invalid, untested or deferred as appropriate. Deliver training
appendix data, reproducible recipes/checkpoints and E06 generator configs.

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
