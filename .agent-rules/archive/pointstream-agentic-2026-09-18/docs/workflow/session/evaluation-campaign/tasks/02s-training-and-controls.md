# E02S — Actual training resume and missing controls only

Owner: Antigravity, continuing E02R `b7c4d16e19758dc27064006e1129c0996d6bebbd`.
Scope selected trainer/evaluator and their tests. Cursor E03A exclusively owns
result adapter/contract from now on; do not reimplement it in parallel. Delegate
R0R separately. Initial budget two active worker hours plus one bounded
30-minute real-backend acceptance stage after R0R is verified.

## Accepted progress

The reported diagnostic hashes match. Full-trajectory defaults True, so the
reported CLI is valid despite omitting that flag; metadata contains 32 placements
across 16 frames. Intra-epoch atomic writes and SPADE initialization before
pretrained loading are implemented. Slow model families remain available.
This is useful real execution evidence; preserve and reuse it.

## Remaining specific gaps

- Saved evidence explicitly has `same_seed_tested=false` and
  `no_conditioning_tested=false`. A five-corner normal/shuffled matrix does not
  include those controls. Distinct frame hashes establish pixel changes, not
  useful motion/identity adherence; object-scale control inspection remains.
- The reported resume test reloads generator weights and compares a forward
  pass. It does not interrupt and resume an actual trainer optimizer update.
  Current trainers restore post-step RNG, create a new shuffled DataLoader then
  skip saved positions: this can skip unseen examples and repeat old ones.
  Restore/reconstruct sampler/epoch order and declared cursor semantics, including
  worker randomness, or use explicit safe epoch replay with recorded extra work.
  RNG state tensors loaded with map_location=device may be CUDA tensors when
  torch.set_rng_state requires CPU state; exercise actual selected-device resume.
  Do not add imaginary schedulers just to match the old report's sched_G/D claim.
- Ranking still orders raw bytes without matching fidelity/client budgets, retains
  per-rung min-max tie-breaking, and promotion uses zero residual bytes for
  residual-off candidates. Fix only the selection path to use the declared
  total-rate/quality/resource comparison, preserving incomparable candidates.
  Fixed tolerances may be practical indifference bands; do not label them
  measured uncertainty. Before that works, no automated model pruning.

## Bounded real acceptance stage

First get corrected R0R launch evidence and Cursor's pinned adapter contract.
Reuse the existing diagnostic instead of rerunning its entire scored matrix.
Run the smallest normal/repeated-same-seed/no-conditioning comparison needed on
one actual loaded small backend; reuse normal/shuffled outputs only when exact
conditions/code/inputs permit. If a new normal is necessary, use a shorter
low-resolution paired probe within the cap, with enough trajectory to exercise
conditioning. Record actual invocation and scoped controls, not made-up arrays.
Missing objective mapping is fixed by Cursor, not by another GPU run.

Run a tiny actual training CLI: observe learning on development-only examples,
interrupt at a known batch boundary, resume in a fresh process, and complete an
optimizer update. Verify weights AND optimizer/RNG/sample-order continuation
against an uninterrupted control within the declared numerical tolerance. Capture
real command/checkpoint schema/step IDs and source sample IDs. Use accelerated
checkpoint interval in the test to exercise the hourly mechanism without waiting
an hour. No confirmation media or full campaign training. Identify unsupported
backends as deferred; one valid small backend is sufficient for this gate.

Final output: new immutable derived/control/resume artifacts through the exact
E03A contract with honest scopes. The fixed-QP residual-byte difference from the
old matrix is not a matched-final-quality improvement; no model ranking is
accepted from it. Record server and client generation calls separately even when
residual is off, before predicting that residual-on doubles generation cost.
Publish E02R trainer corrections as a PR with CI, excluding adapter files now
owned by Cursor (agree transfer through explicit commits, never discard changes).
Return evidence here; E05 remains unreleased until the real acceptance stage passes.

Follow [campaign](../plan.md), [session workflow](../../SKILL.md), setup verification
and the existing bounded budgets. Pin exact branch/input/contract identities;
keep raw artifacts immutable. Run focused behavior regressions, project checks
and CI before requesting code merge. Return actual evidence and one next decision
here. No E05 campaign, test-source scoring, blanket rerun or broad rewrite.
