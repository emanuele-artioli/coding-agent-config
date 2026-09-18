# Probe return and focused continuation — 16 September 2026

Return to Codex task **Clean project state and dispatch**,
`01a0a923-4c5e-71c3-8993-5c68f2a76bb4`. This replaces the old return address.
Read this brief with the [campaign](../plan.md), [setup](../../../../setup.md),
and [session workflow](../../SKILL.md). Preserve existing worker edits and the
active demo checkout; use the named isolated worktrees below.

## Acceptance decision

Reviewed main `c47684071daaea8921b2302b6c2971f11b070e0b`, Cursor #114
`c1c68ec71d804d42d774daa50700e93c1a7f8aee`, and Antigravity #109
`c9c4dede6afb4506cedd1f1fbf24b3416c39f826`. Both open PRs have passing
lint, typecheck and tests. Neither is accepted yet. #113 is already merged;
that does not certify its recommendation or every evidence arm.

The E03B four encodes and E04A six encodes exist. All ten recorded bitstream
hashes match. All eight E03B decoded containers (ordinary and standalone)
independently contain 48 frames at 640x360. The two reports identify the same
prepared RGB stack, SHA-256
`1f02475a5bbc3d94e4bae2e904dc29c3af3082be0c0c160e027b706a6950f6f8`.
These checks support artifact reuse; do not repeat those encodes.

Saved reports are under
`/home/itec/emanuele/pointstream-data/outputs/evaluation-20260914/{e03b,e04a}/run-20260916-federer007/`.
E03B report SHA-256:
`62ac0b15228001f7598958d501df133003d8c6faea0b5b6947670a3839fc45f7`.
E04A report SHA-256:
`e65ec04dedda40cdc472ace90fcce31e26b10218c15060097c6ca39f5010251d`.

E03B's VMAF lower-bound alarm has supporting calibration: severe blur reaches
the floor too. Keep the original bounds/report immutable and link a separate
alarm disposition. The measured point need not be re-encoded for this alarm.
One scene and single-run timings do not establish a general winner or a speed
ranking. Conventional anchor quality intervals do not overlap; no BD-rate.

### Reproduced code gaps

1. **#114 decode gate:** `e03b_persist._rgb_dump` pads short decodes and trims
   excess/partial data before validation. A two-frame raw buffer returned shape
   `(48, 8, 8, 3)` in a coordinator reproducer. The existing files pass independent
   frame counts, but future truncated output can be falsely certified.
2. **#109 reference shortcut:** `TennisSkeletonDataset._select_reference_path`
   uses `colors[idx % len(colors)]`. For the first track, each deterministic
   reference is its target image. The four-sample CLI regression uses this
   situation. Determinism is useful progress, but training must use a reference
   policy consistent with what the receiver receives.
3. **#109 candidate validity:** a row with `total_bytes=1000`, `psnr_mean=NaN`,
   `ssim_mean=0.9`, `client_seconds=1` dominates a row with bytes 2000,
   PSNR 30, and the same SSIM/time. NaN is treated as neither better nor worse.
   Incomplete/invalid measurements must not eliminate a valid candidate.

#109 now contains an actual fresh-CLI continuation regression and restored
Python RNG/isolated DataLoader RNG. Do not repeat the earlier accusation that
only a same-process test exists. Its assertions use numerical tolerance, not
bitwise equality, and the test disables CUDA. State that scope accurately.
The supplied diagnostic and adapter JSON hashes match their pointers in #109;
that authenticates the old artifacts, without upgrading their claim eligibility.

## Cursor — E03B acceptance repair in #114

Resume `/home/itec/emanuele/worktrees/pointstream-e03b-20260916`, branch
`codex/e03b-20260916`, after checking clean state and fetching/integrating main.
Keep ownership of `experiments/tier/e03b_*`, the reader/adapter boundary,
related tests/manifests, and evaluation/data state. Do not edit the E04 runner.

Within **two active preparation hours**, fail on empty, partial, short, or
extra decoded frames before reshaping/padding can hide the actual count. Record
actual decode dimensions/count and compare ordinary versus standalone pixels;
validate the charged stream, not a manufactured output shape. Add focused
regressions under the test-design workflow. Check the existing eight decoded
containers and four streams; derive new verification records in a new directory.
No new candidate encode is authorized by this repair.

Make run directories immutable: a repeated invocation must refuse to overwrite
bounds, reports, streams, or prepared data, or verify explicit compatible reuse.
Validate prepared-array hash and source/seek/filter identity before reuse.
For native PTS, verify selected PNGs against the mapped decoded source frames;
nearest timestamp assignment alone is not proof of pixel provenance. Preserve
the old mapping if a correction is needed and write a derived mapping.

Keep score-free eligibility separate from authorization to score. Correct the
reversed ancestry wording in evaluation.md (`df9f945` descends from `8eb045a`)
and the stale CI checkbox in #114. Return exact verification paths/hashes,
remaining source-mapping uncertainty, and the updated PR/CI. Pause for review.

## Antigravity — E04A evidence completion and common-scope comparison

Start a fresh worktree
`/home/itec/emanuele/worktrees/pointstream-e04a-evidence-20260916`, branch
`codex/e04a-evidence-20260916`, from fetched main containing `c476840` and this
brief. Scope: `scripts/run_e04a_probe.py`, background probe transport helpers,
related tests, codec state and external derived evidence. Leave Cursor files
and generator training untouched.

The current six rows are a background component diagnostic. Their ledger counts
background payload and side data; fixed-overlay foreground references/masks are
not a complete charged codec. The region SSIM path is global masked SSIM, while
the saved calibration calls whole-frame windowed SSIM. The campaign rows omit
that metric scope and assert transport/runtime eligibility unconditionally.
Complete these evidence gaps before promoting a representation:

- Calibrate the actual visible/object/boundary scorers on identity, mild/severe
  noise and blur, and unrelated structured content; report empty-mask behavior.
  Reuse inputs and decoded outputs. Register two-sided bounds before new scores.
- Decode each representation from only saved bitstream and serialized side
  data. The client must use unpacked dimensions/count/fps/homographies, with no
  original geometry available. Reject truncated/extra video frames; the new
  runner currently pads video too. This is decode-only validation.
- Produce derived records naming background-only bytes, metric definition and
  region, omitted foreground costs, exact encoder/decoder argv, binary
  identities, and provenance of host/timing. Do not hardcode host or lookahead.
  Separate common preparation from necessary per-arm work and clarify whether
  compositing is inside the client timing. Reprofile only missing timing strata.
- Rescore saved E03B decodes through those same background and whole-frame
  scopes. Compare adjacent measured rates, with all three size/quality/time
  dimensions. Do not equate whole-frame windowed SSIM to masked global SSIM or
  background-only bytes to a whole-codec budget. Preserve hardware differences.
- Replace the broad "Pareto-optimal below 20 KB" / "eliminating ghosting"
  recommendation with a one-scene conditional observation. The cheap still arm
  remains a rate tradeoff; measured ghost-region error is nonzero. Ghost-region
  MAD also includes ordinary reconstruction error and alone cannot certify
  disappearance of silhouettes. Inspect saved reconstructions for that claim.

Budget: **two active preparation hours**, **30 minutes total decode/rescoring
and missing timing**, **zero new candidate encodes**. Use a new directory under
`outputs/evaluation-20260914/e04a/` and preserve every existing artifact. Return
a scoped PR/CI, derived evidence, and the smallest costed second-camera plus
paired-removal experiment needed next. That larger experiment awaits review.

## Antigravity — E02S correction in #109, separate session

Resume `/home/itec/emanuele/worktrees/pointstream-eval-e02r`, branch
`codex/eval-e02r`, from the reviewed head after fetching/integrating main.
Scope: selected trainers, `src/shared/tennis_dataset.py`, campaign selection,
related tests, generation state. Keep the accepted Cursor adapter unchanged.

Within **two active preparation hours**, replace the deterministic target-copy
shortcut with an explicit stable reference policy matching transmitted reference
availability. A fixed first reference is a possible policy: its own reference
frame can legitimately match the target, but subsequent targets must not all be
fed themselves. Test different track lengths/offsets and record selected
source/reference IDs. Preserve prior checkpoints and flag any training that used
the shortcut; do not discard families on that invalid evidence.

Reject or mark incomparable NaN and domain-invalid measurement fields. Preserve
quality/resource tradeoffs, missing evidence and legitimate identity-score
semantics. Test actual producer-shaped rows through promotion, not only a helper.
Reconcile documentation with actual bands (current code: 2% rate, 0.1 dB PSNR,
0.005 SSIM, 5% relative client time; the prior report said 1% and 0.05 seconds).

Rerun only the tiny selected-trainer CLI continuation case with the corrected
reference policy, under explicit one-device/worker constraints, within the
existing **30-minute execution cap**. Prove which steps and references execute;
compare G, D, both optimizers and relevant RNG state. Use exact equality if
claiming bit-identical continuation; otherwise report the tolerance and observed
difference. No seven-corner matrix rerun merely because its pointers were late.
Describe CUDA/multiworker/multidevice modes only to the extent actually verified.
Prepare an E05 first-stage decision card from existing artifacts, but do not
launch E05 or confirmation scoring. Return updated #109, checks and evidence.

## Cost and shared gate

The existing conventional/background probes finished in minutes, not hours;
their reruns are not the critical path. This correction wave permits at most
six active preparation hours across three independent workers and one hour of
bounded execution across the two Antigravity lanes. It has no candidate-encode
budget. Run lanes concurrently only when the per-host aggregate CPU allowance
fits; recheck devices, use accepted local-host claims, detach longer jobs, and
report actionable events only. Cross-host claim deployment remains unverified.

Neural-anchor compatibility, a baseline-clearing trained foreground model,
full-codec comparisons, source-level confirmation and a second domain remain
uncompleted. Their runtime cannot be inferred from these component probes.
The E05 protocol's 1/4/12 GPU-hour stages are conditional caps, not a completed
cost estimate or automatic release. At return, provide compatibility status
and a measured pilot cost before committing the rest of the critical path.
The 20 September freeze remains at risk; the 30 September target and required
neural-winner/secondary-domain evidence are unchanged. E05 and confirmation
scoring remain unreleased. No new experimental jobs were launched by this review.
