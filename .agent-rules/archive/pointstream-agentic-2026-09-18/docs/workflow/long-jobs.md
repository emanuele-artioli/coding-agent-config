# Long jobs: quiet monitoring and bounded adaptation

## Launch and reporting policy

Use the September evaluation campaign
[allocation and reporting policy](session/evaluation-campaign/plan.md#shared-servers-and-timing-evidence)
for its jobs: opportunistic free GPUs, aggregate per-host CPU cap, bounded stages,
and actionable-event reporting. For other jobs, ask once at launch for reporting
preference unless it is already known. Reuse
that answer for the job. The fallback is file logging plus actionable events;
periodic chat reports require an explicit schedule. Ten-minute progress logging
is independent of chat reporting and hourly checkpointing.

Use `experiments.jobs.monitor`, a Python supervisor with no model calls in its
health loop. It writes `command.log`, timestamped `progress.log`, atomic
`status.json`, and durable `events/*.json`. A quiet heartbeat is not evidence of
work: only an explicit progress update changes `last_progress`. An uninstrumented
job therefore gets a suspected-stall event after the configured interval, not a
claim that it hung. The monitor checks child exit and a wall-time budget (ten-second polling plus delivery/termination grace);
it does not infer GPU health from utilization. The budget applies to the whole
command, not each subprocess or GPU separately.

Run from one checkout with its pinned Python environment activated. Put durable
job records under the configured external data root, outside the code tree.
For example, substitute an actual job directory and owning Codex task ID:

```bash
python -m experiments.jobs.monitor start /absolute/data/jobs/ladder-001 \
  --budget-hours 12 --thread TASK_ID \
  --report-in-hours 8 --quiet-hours 8 \
  --cpu-threads 8 --claim-gpu GPU-UUID \
  --claims-dir /absolute/data/jobs/claims \
  --command python -m experiments.jobs.codec run \
  /absolute/data/policies/ladder.json /absolute/data/campaigns/ladder-001
```

`--cpu-threads` is required for every monitored command, including CPU-only
jobs. Omit `--claim-gpu` only for a CPU-only job. The thread-related environment
variables are cooperative limits; they do not constrain an arbitrary external
binary that ignores them.

The launcher detaches the supervisor. A sandbox that kills descendants when a
shell call ends requires an authorized host launch; `setsid` alone cannot defeat
sandbox lifecycle cleanup. Inspect `supervisor.log` and `status.json` once after
launch. Do not leave an agent polling them. Use `--codex /absolute/path/to/codex`
when Codex is not on the supervisor's PATH. Omitting `--thread` writes events to
files without attempting to wake an agent.

Change cadence without restarting the command:

```bash
# One digest eight hours from now, then ask again; silence includes completion.
python -m experiments.jobs.monitor schedule /absolute/data/jobs/ladder-001 \
  --report-in-hours 8 --quiet-hours 8
# Hourly reports while the job runs.
python -m experiments.jobs.monitor schedule /absolute/data/jobs/ladder-001 --every-hours 1
# Stop periodic reports; retain actionable events.
python -m experiments.jobs.monitor schedule /absolute/data/jobs/ladder-001
```

Deadlines are persisted UTC Unix timestamps. Quiet hours defer actionable events
as well as routine reports; `schedule --urgent-during-quiet` opts into immediate
event delivery. No answer to a one-shot digest means no recurring reports.
Completion ends the supervisor after pending delivery and any requested first
digest. To report on an already-finished job later, read its saved status.

The Codex adapter calls the installed `codex queue --thread ... --message ...`
only for due events. It needs an available app server and authenticated CLI on
the execution host. It writes an acknowledgement only after successful queueing;
this is transport acceptance, not proof that the agent read the message. Failed
delivery stays on disk for retry. Delivery is at least once: a crash between
queueing and acknowledgement can duplicate a message. Stable event IDs let the
receiving task suppress duplicate reports. Repeated publication of the same
decision in a stage does not create another wakeup merely because its timestamp
changed. A digest should read current status
and new results, not reread the full log or restart ten-minute agent checks.

`serve JOB_DIRECTORY` retries undelivered events after supervisor restart. It
never relaunches a command recorded as running: its exit status is then unknown,
so it reports interruption for inspection. It does not adopt or kill a process
by an unverified saved PID. The monitor does not manufacture training checkpoints;
the launched trainer must still provide and verify hourly checkpoint/resume.

## Bounded paired codec ladders

`python -m experiments.jobs.codec run POLICY_JSON CAMPAIGN_DIRECTORY` wraps the
existing paired ladder, including PointStream's QP and joint JPEG/QP payload
sweeps. Both arms retain the existing matched encoder preset and pixel format.
The cheap axis is clip length; this avoids assuming a fast preset predicts a
slower preset. Choose representative scenes, not only the easiest static scene.

The execution order is short pilots across all selected scenes, optional bounded
spacing changes and another pilot, longer confirmation across all scenes, then
final-length runs. A short-clip success is not a long-clip compression claim.
Amortization and temporal context can change the ordering at longer durations.

Supply these policy fields explicitly:

| Fields | Meaning |
|---|---|
| `codec`, `tier`, `sweep` | Existing codec/tier names; `qp` or `payload` |
| `scenes` | Unique `[video, scene]` pairs from the existing TierClip cache |
| `dataset_revision` | Immutable dataset/manifest revision |
| `pilot_frames`, `confirmation_frames`, `final_frames` | Integers, `2 <= pilot < confirmation <= final`; must fit cached clips |
| `qps`, `qp_min`, `qp_max`, `qp_step` | At least three increasing QPs, allowed interval and widening step |
| `jpegs`, `jpeg_min`, `jpeg_max`, `jpeg_step` | Payload only: decreasing JPEG quality aligned with increasing QP, bounds in 1–100 |
| `min_gap_db`, `max_adjustments` | Minimum adjacent Y-PSNR spacing and maximum pilot revisions |
| `budget_seconds`, `pair_timeout_seconds` | Cumulative worker wall-time budget; per-pair timeout at most 3500 seconds |
| `bands` | Two-sided `[low, high]` bands for `psnr_dB`, `coded_bytes`, `seconds` |
| `bounds_basis`, `controls_evidence` | Pre-measurement rationale and absolute path to control evidence JSON |

There is deliberately no ready-to-run policy with invented scientific bounds.
The control record must contain `calibrated: true` and `null_checked: true`, plus
the evidence establishing those assertions: identical/mild/severe/unrelated
anchors, absolute metric scale, source identities, and a no-generator or shuffled
control as appropriate. These flags attest reviewed evidence; the controller
cannot verify that prose or a control experiment is truthful.

Every scene must return the full requested point count on both arms. Missing,
nonfinite, out-of-band, nonmonotone, uncoded, or failed results pause the campaign.
Close qualities cause wider endpoints and redistributed intermediate points,
within the approved QP/JPEG bounds. Exhausted bounds or failed longer-clip
confirmation pause for a decision rather than launching the expensive stage.
Similar quality can coexist with useful size/speed differences: this gate asks
for usable quality coverage and does not declare a model inferior.

The controller saves inputs, pair outputs, elapsed cost, decisions and inflight
state. Resuming requires the same policy, control record and code identity. A
completed pair is reused; an interrupted worker requires inspection and is not
silently replayed. An attention verdict is terminal for that campaign: change the
plan in a new directory and preserve the original evidence. No worker is allowed
more than 3500 seconds without a campaign checkpoint; jobs needing longer pairs
need finer-grained runner checkpoint integration before increasing that limit.

Exploratory completion always has `citable: false`. Final paper evidence still
requires frozen settings, held-out evaluation, full quality metrics, size and
encode/decode timing, calibrated controls, and uncertainty across independent
scenes/videos. Do not count correlated frames as independent samples.

## Training candidates: proposed evaluation protocol

This is the protocol for a future training campaign, not a repaired training
launcher. `scripts/train_campaign.py` still calls the retired evaluator and must
be rewired to the runner before real training. Do not enable its unattended mode
as a substitute for the gates below.

For ten videos, first freeze two as the test set and use the other eight for
training/validation development. Group by original source/match/camera where
necessary; different excerpts of the same source are not independent videos.

| Stage | Data and task | Decision it supports |
|---|---|---|
| Reconstruction sanity | Fit a tiny scene and reconstruct the training scene using the intended decoder conditioning | Can the implementation learn, use conditioning, and reproduce motion? Repair failures before ranking models. |
| Same-video validation | Train on other scenes of one video; validate on a disjoint scene with no overlapping frames | Does it work beyond memorized frames within this domain? |
| Cross-video screening | Train on small, diverse subsets of development videos; validate on a held-out development video | Which candidates transfer to new content? Rotate held-out development videos for finalists if affordable. |
| Full development training | Choose configuration and training schedule using development validation; refit on all eight videos if appropriate | Freeze finalists and operating points. |
| Final evaluation | Evaluate once on the two untouched test videos | Evidence for the scoped generalization claim, with the limitation of only two independent test videos. |

Use nested, fixed subsets across candidates. Increase data diversity, training
steps and temporal sequence length deliberately; reducing all of them at once
can hide why rankings change. Compare model families at meaningful minimum
budgets, record examples/steps and wall time, and reserve an extension budget for
ambiguous or slowly improving candidates. Do not automatically halve the field
on tiny score differences. A scene-overfit checkpoint can warm-start later stages
only if that curriculum is recorded and applied consistently; finalists should
confirm the intended full training recipe.

For PointStream, judge the whole codec: actual total delivered bytes at a quality
target (or quality at matched bytes), encoding/decoding runtime, and temporal
fidelity. Include model updates/adapters in transmission accounting when adapted
per content. A better-looking generator may require more residual bits. Compare
against the no-generator/reference reconstruction path, validate conditioning
with a shuffled/null control, and use temporal models on sequences. Preserve
Pareto tradeoffs rather than averaging unrelated metrics into a changing score.

There is no established single best candidate selector for this exact task.
Multi-fidelity allocation is the relevant method family:

- [Hyperband](https://www.jmlr.org/beta/papers/v18/16-558.html) allocates increasing budgets through successive halving.
- [BOHB](https://proceedings.mlr.press/v80/falkner18a.html) combines budget allocation with Bayesian configuration search.
- [FABOLAS](https://proceedings.mlr.press/v54/klein17a.html) explicitly models validation error and cost as dataset size changes.
- [In-context freeze-thaw BO](https://proceedings.mlr.press/v235/rakotoarison24a.html) is a more recent learning-curve-based approach; its benchmark claims do not establish superiority on PointStream.
- [DCVC-UF's training recipe](https://github.com/microsoft/DCVC/blob/main/training.md) progressively increases sequence length and patch size. This supports retaining temporal context in later stages, not using one-scene replication as final codec evaluation.

For ten heterogeneous models, begin with the transparent staged protocol above.
Only adopt a learned search controller after checking that cheap-stage evidence
predicts the deployment objective on this candidate population.
