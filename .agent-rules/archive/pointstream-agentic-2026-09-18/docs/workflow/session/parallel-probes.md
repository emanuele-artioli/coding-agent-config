# Parallel probes after the overlap ladder — 2026-09-11

Prepared for the user's request to clean up and dispatch efficient experiments to
Cursor or Antigravity. No jobs are launched by this document update. Give the
whole file plus the chosen lane to a worker; execution of that lane is authorized
when the user dispatches it. All scientific outputs are development-only.

## Shared contract and state

Main baseline at preparation: `dc4a0cd` (PR #94 policy). PR #93 head:
`ba5a9a8d6bda8430603cf36f7e0764b5b1fcce0b`, CI green but held for lane A fixes.
PR #92 carries this reconciled status and dispatch. Re-fetch before work; use the
merged documentation revision and record the exact code revision actually run.
Do not resume the old eight-hour or Wave 2 plans or their GPU assignments.

Read AGENTS.md, docs/setup.md, the assigned area and
[experiment design](../experiment-design.md). Each worker owns a fresh branch and
worktree; no shared mutable checkout. Use the relevant harness rules. Cursor or
Antigravity can own any lane; suggested allocation is Cursor A, Antigravity B/C
as independent subagents. Choose inexpensive agents for bounded evidence work.
The coordinator alone updates PLAN/area status and integrates changes.

External data root on this host: `/home/itec/emanuele/pointstream-data`.
Set PS_DATA_ROOT or a worktree marker; never create assets/outputs symlinks.
All lanes pin the same scene/frame/mask/object identities before pairing results.
The saved overlap run used 48 frames each of `alcaraz_highlights/scene_000` and
`federer_djokovic/scene_007`; do not infer their global frame IDs from scene names.
Recover actual frame indices from the run/loader manifest and reject missing data.
Confirmation sources remain forbidden. No training, downloads, Gate B or paper edits.

This session launched no experiment jobs. Process visibility here is sandbox-local
and cannot certify gpu5/gpu6 idle. Check host/job logs and GPU/CPU users before
launch. Never kill an existing process. B is read-only/CPU; C is CPU-first; A's
regressions use fake backends unless a native round trip is required. Serialize
native encodes on a shared host or allocate measured free cores explicitly.
Concurrent contention timings cannot establish runtime frontiers. Old fixed
CUDA_VISIBLE_DEVICES=1 assignments are expired.

## Wave 1: three independent decisions

### Lane A — make evidence reusable and client reconstruction trustworthy

IDs: `EVAL-ACT-09`, `GEN-ACT-08`. Branch `cursor/probe-validity` or
`antigravity/probe-validity`, fresh worktree `/tmp/pointstream-probe-validity`,
starting from #93 head. Implementation/check budget: 90 minutes; zero experiment
sweeps. Stop with a smaller remaining patch if that cap is insufficient.

Own `src/runner/generation_identity.py`, diagnostic report/driver and focused tests.
Avoid background implementation. Four concrete blockers from static review:

1. `generation_identity.py:209–212` returns a registry-built generator without
   matching its actual checkpoint to the transmitted digest. Resolve a client
   checkpoint explicitly and verify it, or fail closed. A path on the encoder
   is not a client checkpoint registry. Test A requested/B available rejection
   and a valid separate-process client without an injected encoder generator.
2. `diagnostic_report.py:154–173` selects only part of the config for reuse;
   `run_diagnostic_matrix.py:570` uses it. Identity must cover the complete
   effective config, device, masks, placements and conditioning, checkpoint and
   source hashes. Disable dirty-code reuse or hash the actual changes. Test
   changes to background quality, device, pose/mask and code independently;
   identical complete identities may reuse. No guessed cache hits.
3. `diagnostic_report.py:431–438` checks generation failures but can accept missing
   paste controls/hashes. Require successful declared controls and complete,
   finite required outputs. Test failed paste corners with successful generation;
   validity must remain false. Do not turn a no-op/null into a model benefit.
4. `run_diagnostic_matrix.py:119,134–135` hardcodes frame offset 38 and substitutes
   black skeletons. Resolve actual source coordinates using verified metadata;
   fail on missing/misaligned conditioning. Test two scenes with distinct frame
   offsets plus absent pose. No synthetic fallback in real-data paths.

Line numbers refer to reviewed #93 and will move. Selected behavioral regression
cases above are part of the dispatched task; no further test-approval round is
needed. Follow setup's lint/type/layer/appropriate integration checks. Update #93
by a forward commit, retain its useful repairs, and obtain green CI before merge.
Do not rewrite its old history or claim the fixes validate prior metrics.

Acceptance: the four failure cases fail closed and intended positive paths work,
plus a concise provenance contract B/C can use. Return changed commands and exact
commit. Correctness is the deliverable; no model ranking.

### Lane B — which bytes prevent a matched-quality win?

ID: `EVAL-ACT-08`. Fresh branch/worktree `cursor/byte-diagnosis` or
`antigravity/byte-diagnosis`, `/tmp/pointstream-byte-diagnosis`, from current main.
Own a narrowly scoped analysis helper under `scripts/` if necessary and external
artifacts; no runner/background changes. Cap: ten-minute provenance triage plus
30 minutes analysis/scoring, zero new candidate encodes. Stop at missing evidence
rather than rebuild the whole ladder. Helper implementation has a separate
30-minute cap; reuse existing comparison helpers first.

Input: `outputs/development-recovery/wave2-overlap-20260910/`, with hashes in
[evaluation](../../areas/evaluation.md). Read bounds.json before headline metrics;
carry its bands forward and record any revision before fresh measurement.
Report identity/evidence flags and reconcile recorded bound alarms first.

Hypothesis: fixed background/metadata costs consume most of the anchor budget.
Alternative: correction dominates, so foreground/background prediction is the
lever. For each saved Federer point, reconcile disjoint B+F+M+R+H to serialized
bytes. Against each anchor at supported final quality, report remaining budget
A(q)-B-M-H, required total-byte saving and each component's maximum recoverable
contribution. No global BD-rate for Alcaraz; no extrapolation or relaxed overlap
floor. Use the project's comparison helper, same-anchor zero and doubled-byte
arithmetic controls; these validate arithmetic only, not source scoring.

If saved decodes and actual masks exist, locate error in visible background,
foreground and boundaries; otherwise explicitly record unavailable spatial
attribution. Runtime scope must accompany size/quality, including any known
missing preprocessing. Do not manufacture speed evidence by dividing partial
stage time. Source-level n is two at most; no population ranking or fabricated SE.

Output: machine-readable component budget plus one waterfall/compact table,
provenance and validity limitations, and the ranked next intervention. Promote
background coding only if its plausible saving is relevant; if metadata or
residual dominates, redirect the next card. Preserve all originals. This lane
can read #93-era files without checking out or executing its unsafe reuse path.

### Lane C — does background representation explain enough error to matter?

ID: `CODEC-ACT-06`. Fresh branch/worktree `antigravity/background-probe` or
`cursor/background-probe`, `/tmp/pointstream-background-probe`, from current main.
Own a component-only probe under `scripts/` and focused tests. Do not edit shared
config, runner or production background contracts during Wave 1. Preparation cap
60 minutes, then at most six candidate configurations and 30 minutes execution
including controls/scoring. Reserve ten minutes of that run for diagnosis.

Current capabilities: `build_plate(frames, masks, register=True, ...)` excludes
foreground in temporal median compositing and fills holes. `register=False` is
an unregistered temporal median, not a first-frame still. Config has panorama
full/delta/stream/none; no true first-frame/video/removal selector exists.
`panorama-stream` codes plates, not full background video. Do not invent CLI flags.

Hypothesis: camera coverage/registration is the limiting background error;
video improves it but must earn its byte/time cost. Alternative: a still is
already sufficient and geometry/metadata or correction causes the deficit.
Use the exact saved 48-frame Federer interval after verifying inputs. Build a
common foreground-removed frame stack: preserve each original frame's visible,
unmasked background pixels and use the observed temporal background warped back
ONLY inside foreground masks; explicitly fill any still-uncovered holes. Never
replace entire frames with panorama renders, which would erase the dynamics
under test. Hold that stack/fill fixed. Compare the first cleaned frame repeated
with identity rendering (no camera warp), a registered panorama with charged
per-frame mappings, and cleaned per-frame video.
The temporal fill is offline and may use future frames; charge its construction
and label it. This isolates representation, not a claim about causal streaming.

Start with an uncompressed render sanity check (identity geometry, source frame
alignment and visible-pixel coverage). If wrong, fix the probe or stop before
encoding. Then up to three representations × two qualities under the same
available native codec/build (provisional VVC QP 47 and 32; estimate one case
against the cap first). Same QP is screening, not matched-quality equivalence.
If codec availability or cost prevents six cases, return fewer honest points.
Charge encoded payload plus necessary geometry/dimensions/timing side data and
label this a component package, not PointStream wire format. Decode and render
at original display size. A named fixed foreground overlay is an integration
preview only; include a no-overlay full-video anchor and its overlay conflict
control when saved decodes are available. Missing saved controls get a costed
follow-up, not an unbounded anchor sweep.

Before measurement fill numeric size/time bounds from the saved run and one-case
cost estimate; quality is measured on visible background with declared masks,
plus whole-frame/foreground/boundary diagnostics where the overlay is valid.
Temporal/perceptual plots require appropriate controls; PSNR screening alone
cannot promote a VMAF claim. Track startup/lookahead, preprocessing, encode,
decode/render time. If no usable geometry or verified masks, stop as unready.

Output: coverage/error maps and a small rate/quality/time table with implementation
limitations. Pair its plausible savings with B's ledger before production work.
Do not spend this stage implementing every fill method. No neural inpainting.

## Wave 2: integrate only the intervention supported by Wave 1

Coordinator joins A/B/C. Merge #93 only after A passes. Freeze the chosen fill
policy, representation, source/config identities and output contract; then assign
one narrowly scoped production integration, not three separate agents editing
runner/config. If B shows background is already cheap, switch to the evidenced
metadata or correction lever. Keep the losing prototype record.

A subsequent representation card may test three representations × two qualities
through the real byte-only client, with fixed foreground and matched-quality
correction. A separate fill card compares off/current/local mean/Telea only on
the chosen representation. Both cards need their own cost estimate and cap;
neither is automatically launched by Wave 1 completion.

Foreground resource screening is the next independent lane only after correct
inputs/client identity are established: pasted reference, an installed small
model and one installed diffusion backend; no training. Existing readiness CLI:
`scripts/smoke_generator.py --arch pix2pix --checkpoint <verified-path> --device <device> --num-frames 3 --seed 42 --json-out <external-file>`.
Run with the pinned Python environment. Its smoke controls are readiness tests,
not an end-to-end resource frontier. A later card must measure synchronized
client latency/throughput/peak memory and total wire/correction at matched quality.
Unavailable weights or OOM are deferred/infeasible at the setting, not inferior.

## Return contract

Each worker returns its exact commit/command, immutable artifact paths/hashes,
spent budget, controls and alarms, supported/contradicted/inconclusive verdict,
and one next decision. Notify only on completion, failed validity or needed user
action; scripts handle progress logs. No polling agent. Coordinator updates the
owning area and current plan without overwriting the other lanes' evidence.
