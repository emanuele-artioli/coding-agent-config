# E02R — Finish actual generator readiness before E05

Owner: Antigravity. Base: merged #105 `2f63ae1` plus coordinator follow-up docs.
E02 is partial, despite merged CI-green code. Keep useful trajectory/pose changes;
repair only the selected readiness/training path. Scope: E02 adapter, evaluator,
trainers, tests, truthful generation area/cards. R0 is a separate subagent/worktree
on job support; E01R remains Cursor-owned. Budget: four active worker hours plus
one real-backend probe of at most six settings / 30 minutes including scoring.
No E05 training campaign until acceptance; report the smallest unresolved failure.

## Reproduced integration blockers

- `src/runner/generation_adapter.py` emits `rd_claim`/`speed_claim`, no E01 schema,
  artifact/source/frame/op identities, and expects top-level normal/shuffled rows
  whereas diagnostic producer output has `matrix`. Passing the adapter output
  into E01 validator yields missing fields and all claim-scope errors.
- Calling `adapt_campaign_eval_result({'aggregate': {'success': True}}, ...)`
  without any control or checkpoint evidence marks all four conditioning/seed
  controls true plus RD, standalone and temporal claims. Missing hashes become
  `injected`; `filename:sha` is not a SHA-256 digest. These are not fail-closed.
- New tests in `test_e02_readiness.py` compare constant arrays and NumPy RNG;
  request counts are useful loader checks but none prove real neural control,
  temporal inference, tiny learning or loaded-checkpoint resume.
- Pix2Pix and SPADE test the hourly deadline only after an epoch. A long epoch
  still cannot checkpoint hourly. Resume must preserve the needed optimizer,
  scheduler/RNG/step state and declare partial-epoch replay/skip semantics.
- `train_campaign.evaluate_checkpoint` always enables STAGE_RESIDUAL; passing
  None through `--no-residual-bytes` still creates default residual settings.
  Foreground residual-OFF evaluation is therefore not established.
- SPADE lite/full instantiate the same ResNet9 generator (only discriminator
  count changes). The reported UNet/local enhancer is future work. Pretrained
  generator load is overwritten by `weights_init_normal` unless resume is active.

## Work and acceptance

1. Agree E01R's exact result contract and connect actual producer output through
it. Keep generic runner records inside the architectural layer boundary; the
experiment adapter may live in experiments and consume runner output, rather
than making `src/runner` import `experiments`. Reject absent/nonfinite identity,
metric and required control evidence; no placeholder success defaults. Use
source-grouped uncertainty, no zero-width certainty from n=1 or correlated frame
replicates. Keep synthetic examples separate from real claim eligibility.
Add integration tests using real producer-shaped rows, missing controls, wrong
loaded checkpoint, missing pose and failed/zero-call generation. Tests should
exercise the boundary, not simply check new labels exist.

2. Add explicit residual-off configuration with zero residual bytes AND calls.
For E05 residual-off compare actual total wire rate at matched quality/client
budget with foreground/temporal guards; residual bytes alone cannot rank it.
For residual-on, fixed residual QP does not establish matched final quality.
Remove the changing min-max composite as a promotion basis. A fixed 2%/0.1 dB
indifference band can be a declared practical tolerance, but is not measured
uncertainty; preserve close/incomparable candidates and use grouped uncertainty
or report it unavailable. Correct cards to staged aggregate budgets, not 1/4/12
GPU-hours for each model/setting. Slow models remain on the offline quality
frontier; latency failure alone does not terminate a family.

3. Check checkpoint deadlines inside training progress, save atomically, and
verify interrupt/resume on the selected tiny learning path. Correct SPADE
initialization/pretrained loading order if using that path, with evidence that
loaded values survive before the first update. Label actual architecture and
checkpoint/environment availability honestly. Do not build a new full SPADE
architecture merely to make the old report true. Full hashes and load evidence
replace truncated hashes/estimated memory presented as verified readiness.

4. After R0 works and the E01R schema is agreed, execute one tiny learning and
standalone multi-frame control on a real available small backend (Pix2Pix is a
reasonable first choice). Pin inputs/weights, verify proper conditioning/indexing,
normal/shuffled/no-condition and repeated same-seed controls on actual generator
outputs, not manufactured arrays. Show per-frame call/placement coverage and
inspect motion/identity sensitivity at object scale. Check temporal models use
native sequence inference before calling them ready; defer them honestly if not
probed. Include both paste and generated residual-off controls and a tiny actual
checkpoint interruption/resume. Record provenance, wire reconciliation, delivered
hashes, invocation/coverage, metric calibration and timing scope in external run
artifacts. If 30 minutes cannot answer it, return the costed smaller next probe.

## Completion

Qualify the old `02-generator-readiness-report.md` as superseded where necessary;
put detailed new evidence in PR/run artifacts rather than another permanent
completed-session report. Mark candidates implemented, available, loaded, or
validated according to evidence. Return revised cards, R0 revision, E01 adapter
roundtrip proof and bounded real-backend readiness evidence. E03/E04 remain
independent once E01R is accepted; do not wait for every neural family to train.

## Execution and return

Follow the [campaign](../plan.md) and [session workflow](../../SKILL.md).
Pin actual code/inputs; retain immutable outputs. Run meaningful behavior tests
and setup checks for changed code, plus CI. No expensive campaign expansion.
Return exact commands, artifact identities, controls, spent budget, unresolved
issues and one next decision to the coordinating Codex task; do not self-dispatch.
