# E02 — Full-trajectory generation and training readiness

Owner: Antigravity. Area: [generation](../../../../areas/generation.md).
Ready in parallel with E01; use its schema once accepted.
Scope: `experiments/long_scenes/loader.py`, `scripts/run_diagnostic_matrix.py`,
`src/runner/generation_identity.py`, training/evaluator adapters and corresponding
tests. Coordinate E01-owned `experiments/tier/protocol.py` and result schema edits.
Budget: 4 worker hours, then smallest readiness probe (six configs / 30 minutes).

## Work

Before any GPU probe, verify existing atomic host/device claims and recheck
availability under the campaign policy. If allocation safeguards are absent,
return this narrow prerequisite for coordinator assignment; do metadata/CPU work
in parallel, without waiting on all of E03 or launching an unclaimed GPU job.

Inventory actual model backends, checkpoint paths/hashes, training histories,
input sizes/temporal context and available environments. Reuse #102 repairs;
verify their integration with real backends rather than blanket reimplementing.
Current saved 16-frame diagnostics exercise first-frame placements, so they
cannot rank full-sequence synthesis. Keep all model families available pending
valid readiness and training; a failed load is untested, not inferior quality.

Restore full visible-track placement/conditioning over time, with explicit
pose/frame indexing and native temporal inference. Verify decoder receives only
charged state, invokes the selected loaded weights and changes appropriate
frames. Require normal versus shuffled/no conditioning plus repeated same-seed
controls and meaningful foreground/temporal sensitivity, not hash inequality
alone. Exercise both reference paste and generated modes with residual off.

Inspect `scripts/train_campaign.py` against the retired evaluator noted in
long-jobs.md. Replace the legacy per-rung min-max composite ranking with the campaign's
frozen metrics and uncertainty-aware promotion; do not use its uncalibrated
LPIPS-like distance or automatically halve candidates with tiny differences.
Restore the smallest supported low-resolution training/evaluation
path; verify train/validation/test separation, resume from an actual checkpoint,
hourly wall-clock checkpointing and ten-minute progress. Code imported must come
from this worktree, not the editable main install. No package mutation in the
shared pinned environment; incompatible models use separately declared envs.

Prepare E05 candidate cards (ready small model and temporal/diffusion candidate
where available), including native training recipe, low-resolution crop/sequence
compatibility, hyperparameter endpoints, three-stage aggregate cost and stop
rules. Existing one-epoch failures do not prove model-family failure.

## Acceptance

A small real clip produces correctly aligned multi-frame standalone outputs;
checkpoint mismatch, missing pose and incomplete reports fail clearly; controls
show actual conditioning effect or return an explicit unresolved diagnostic.
Tiny learning sanity and checkpoint resume work before ranking/training budgets
are released. Deliver commands, supported backend roster, E01 schema adapter,
readiness evidence and the costed first E05 stage. No broad training here.

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
