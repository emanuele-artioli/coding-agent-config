# Evaluation handoff — 2026-09-12

Historical handoff. The user supplied the full evaluation plan after this file
was written; PRs #100–#102 subsequently repaired audit findings. Active work
follows the [September 14 campaign](evaluation-campaign/plan.md), not the
first-decisions or training restrictions below. Preserve this file as history.

**Trigger:** the user explicitly requested a clean project boundary and handoff
to a new session to execute their evaluation plan. This is not a resource failure
or an instruction to resume the old Wave 2 campaign. Read this file from current
main before creating a new worktree. The session workflow's existing location is
used instead of a permanent root HANDOFF file.

## User's objective and scientific sequence

PointStream must find and explain useful rate–distortion–computation regimes for
the 30 September submission. The user's evaluation plan is:

1. Separate optional foreground removal/filling (off, local colour heuristic,
   temporal observations, Telea, later neural inpainting) from representation
   (first-frame still, panorama with charged rendering metadata, cleaned video).
   Establish their byte/quality/computation tradeoffs and remaining foreground
   budget against both AV1 and VVC. Compare actual reconstructed outputs.
2. Once validated, turn those tradeoffs into an explanatory paper plot. Static
   smaller/worse, panorama intermediate, video larger/better are hypotheses,
   not required outcomes. Preserve contrary observations and update the story.
3. Then compare foreground models across bitrate and actual client resource
   budgets: small models may serve weak/low-rate clients, diffusion may buy
   quality with more time/memory. Test rather than assume those orderings; retain
   paste controls, charge conditioning/model updates/correction, and preserve
   dominated trials for an appendix where appropriate.

Use [experiment design](../experiment-design.md): smallest discriminating probe,
explicit bounds, controls, cost and stop rule. Never automatically launch another
full ladder or train through an invalid evaluator. Confirmation data stay reserved.
The motivating foreground bitrate/area observation needs scoped attribution;
it is not a guaranteed recoverable fraction of an inter-coded stream.

## Verified current state

Code baseline audited: `4fa7cd3` (merged #93/#95/#96/#97/#98). The handoff/docs
commit follows it; fetch current main and record the actual experiment revision.
No open PRs existed at audit start. #98 CI was green; 26 focused existing tests
passed again in the audit. See [the audit](../../history/antigravity-audit-2026-09-12.md)
for exact artifact hashes, reproduced failures and interpretation boundaries.

- Byte accounting supports investigating the legacy background/metadata cost;
  the helper's hardcoded promotion and runtime prose are not reusable evidence.
- Background prototype is exploratory. Geometry bytes are estimated, not an
  independently decoded package; the 94% matched-quality saving is unestablished.
- Generator diagnostics have sparse first-frame effects and weak whole-frame
  null separation; no model-family ranking or real-time claim is established.
- Gate A stays open and Gate B incomplete. No new paper claim was validated.
- Paper repo `67a9ea6275d3d9785ce57026/` was clean at `55e4bc4`; do not write
  manuscript prose in the code repository. Paper edits are deferred until evidence.

Nine stale worktrees and 32 local branches were removed with the user's specific
approval. Every tip is remotely archived under `archive/20260912/<old-branch>`;
[cleanup inventory](../../history/cleanup-2026-09-12.json) gives exact tips/proofs.
The dirty worker-a smoke artifact was preserved in archive-only commit `26a7555`,
not promoted to main. Remote branches remain deliberately; do not check one out
and reapply its stale docs. New work starts from current main in a fresh worktree.

## What is running and what is available

This audit launched no experiments or training. Its tests finished. Process
visibility was sandbox-local and does not establish other hosts idle. Recheck
actual host GPU/CPU processes and `pointstream-data/jobs/` before any launch;
never kill a job on the assumption it is stale. No prior GPU 1 reservation carries
forward. Use `nvidia-smi` on the execution host and the long-job status files.

Pinned Python found at `/home/itec/emanuele/.conda/envs/pointstream/bin/python`.
Read docs/setup.md before running; import sqlite3 before torch, keep caches local,
and set PS_DATA_ROOT to `/home/itec/emanuele/pointstream-data`. No data symlinks.
Native binaries and versions must be verified on the actual execution host.

## First decisions and bounded work

**First decide what the background plot needs to establish.** A component-only
screen is cheaper; a codec claim requires full wire decoding and matched final
quality. Start by verifying the existing background strategy/config path, not by
adding a duplicate “compact panorama” implementation because of the prototype's
name. Identify which of geometry, coding settings, resolution and refresh caused
the old/new byte difference.

1. `EVAL-ACT-11`: correct only the evidence paths needed for the next probe.
   Make verdicts/alarms/timing analysis data-derived; keep missing values explicit.
   For model work, require actual augmented pose hashes, complete result schema,
   declared nulls and backend-loaded checkpoint verification. Add regressions for
   the audit's reproduced failures before claiming those guarantees. Budget a
   focused repair card, not an unlimited evaluator rewrite. Model repairs can
   proceed independently of generation-off background preparation.
2. `CODEC-ACT-07`: create one reviewable card for first-frame/panorama/video using
   a fixed fill and the same real clip. Serialize and decode all required geometry
   at charged precision, hash source/masks/config, and score the actual client
   output. Keep fixed foreground and residual-off controls, then spend a bounded
   correction search only where required to reach a declared final-quality target.
   Include full-video/no-overlay and overlay-conflict controls. Consider a warped
   single-frame control if the question is registration versus panorama coverage.
3. Start with at most six new candidate settings / 30 minutes execution including
   scoring; budget implementation separately and estimate one case first. Never
   reuse the background cache by filename alone or overwrite default output paths.
   Report visible-background, foreground/boundary and whole-frame scope separately;
   include preprocessing, startup/lookahead and encode/client time. If the small
   probe cannot distinguish choices, state the precise missing comparison.
4. Only after useful total-codec headroom is established, write the separate fill
   comparison card and a foreground resource card. Use actual per-frame placement
   and intended temporal inference, meaningful pose/fidelity checks and a repeated
   same-condition control before ranking models. Keep training, neural filling,
   large grids and paper result edits off until their specific card is justified.

Open questions the next session must resolve: Is a loss caused by camera geometry
or by coding settings? How much correction erases background savings? Is the
foreground benchmark intentionally sparse-keyframe synthesis or full pose-driven
video? Which actual client memory/latency budget is the intended claim? Resolve
from evidence and user priorities before allocating expensive runs. Do not require
all these answers to perform a cheap, generation-off background check.

## Landmarks and return contract

- PLAN.md and docs/areas/{codec,evaluation,generation}.md: current actions.
- scripts/background_probe.py, scripts/byte_diagnosis.py: prototypes with audit limits.
- scripts/run_diagnostic_matrix.py, experiments/long_scenes/loader.py,
  experiments/tier/diagnostic_report.py: sparse placement/pose/validity boundaries.
- src/runner/generation_identity.py: checkpoint factory boundary.
- docs/workflow/experiment-design.md and docs/setup.md: budgets and verification.
- docs/history/antigravity-audit-2026-09-12.md: findings and immutable artifact anchors.

Return exact config/command and identities, all three dimensions, controls/alarms,
cost spent, supported/contradicted/inconclusive verdict, and one next decision.
Preserve all old outputs. Update the owning area and current PLAN; do not restore
stale status from an old worktree or mark a gate passed because a job completed.
