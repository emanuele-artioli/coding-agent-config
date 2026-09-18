# Antigravity dispatch: repair PR #88, then search the full codec

> Superseded as the default next dispatch on 2026-09-11 by
> [hypothesis-driven experiment design](../experiment-design.md). Repair status
> below is historical. Reconcile current code and evidence before reusing any
> section; this file does not authorize another automatic eight-hour search.

Execute when the user gives this file as a prompt. Initial budget: eight wall-clock hours including validation, experiment time and reporting. Follow AGENTS.md, docs/setup.md, the session workflow, the Antigravity harness rules and docs/workflow/long-jobs.md. This dispatch supersedes overnight-recovery.md for new work after PR #88.

## Baseline and outcome

Read the PR #88 audit in docs/areas/evaluation.md and the generator audit in docs/areas/generation.md. Reviewed PR #88 head: d1d24b7d091e4cb725cb5956863ba2bc1d54769e. Main at review: 6b04eae plus the commit delivering this dispatch. Fetch current heads and reconcile changes before proceeding. PR #88 is open and unready: tests pass, lint/type checks fail, and scientific blockers remain. Preserve its useful residual-stream and resolution-adaptive implementation; fix its integration before merging or ranking models. Do not merge the old claims unchanged.

Objective: a trustworthy full-codec development comparison and a resumable, budgeted search for at least one competitive configuration. A generator-free win is not a prerequisite for training, and each generator need not beat AV1/VVC. The final selected codec must support its scoped paper claim. Gate A remains open, Gate B incomplete, Gate C formal ablations preparation only.

The user authorizes the scoped repairs, the behavioral tests below, bounded development runs and training within the eight-hour cap when this dispatch is supplied. State the selected tests, then implement without another confirmation. No multi-day job is authorized by this prompt. Preserve unrelated jobs, environments, uncommitted work and all previous artifacts.

## Wave 1 — independent repairs and readiness work

Use Antigravity subagents in isolated branch/share workspaces, with lighter models for bounded checks and the coordinator handling architectural decisions and integration. Never share a mutable checkout between workers. Establish the result/transport/manifest interfaces first; coordinator owns shared contracts, area updates and PR integration. Parallelize implementation and read-only inventories; serialize GPU-heavy work unless measured spare resources and explicit device assignment make concurrent runs safe.

### A. Client, residual and accounting — CODEC-ACT-05 / EVAL-ACT-06

Own src/runner/, src/pipeline/residual/ and focused tests; coordinate shared contracts.

- Make the public delivered_frames and delivered_quality originate from the actual client reconstruction for one and multiple chunks. Current properties still read ART_DELIVERED/ART_QUALITY from the encoder DAG. A controlled client-output perturbation must change the public arrays, scores and experiment reports.
- Generation-enabled decoding must use a serialized, source-free contract: decoded reference bytes, pose/motion/masks, placement schedule, model/config identity and seeds. It currently bypasses the byte-only client using in-memory view/client_objects/ref. Do not pass original appearance or conditioning arrays for free. Avoid duplicate pasted/generated placements. Test a fresh process without source paths and compare its prediction against the actual encoder prediction.
- Count the complete serialized wire format, including repeated or deduplicated references, masks, residual metadata and envelope headers. Reconcile the actual bytes to the ledger. Checking only residual stream length is insufficient. The audit's tiny non-generative run produced 1,219 envelope bytes while its ledger claimed 631 with no raw_parts.
- Preserve the true predictor and full-range residual work. Declare the full-range 8-bit mapping's additional quantization (it is not lossless), chroma loss, gating/downscaling and supported determinism. Enforce compressed-evidence requirements and reject incompatible/corrupt payloads. Measure client decode and serialization costs consistently.

Authorized behavioral checks: changed-client-output propagation; fresh-process decode with generation absent/present and residual absent/present; full wire reconciliation and disabled-stage zero calls/bytes; +/-255 and zero residuals; mismatched seed/checkpoint/config rejection or explicit invalidity; non-identical predictor detection; truncated/corrupt stream rejection; native codec roundtrip. No scientific score from a source fallback.

### B. Dataset and checkpoint evaluation — GEN-ACT-05

Own scripts/train_campaign.py evaluator/data selection and its tests. Agree the campaign scheduling boundary with C; C proposes scheduler changes but does not edit this file until B hands it over.

- Resolve the probe manifest's local versus global frame coordinates correctly for source crops and skeletons. On the audited full-dataset layout, nine of twelve probe tracks lack every source filename the current evaluator requests. Missing frames must fail, never become grey images or synthetic sequences. Synthetic data belongs only in explicitly injected test fixtures.
- Keep crop diagnostics explicitly crop-scoped. Replace the central-quarter synthetic placement with real full-frame clips, masks and actual bounding boxes for whole-codec ranking. Verify RGB/channel order, resize/letterbox alignment and source/pose correspondence visually and numerically.
- Enforce declared training/development-validation separation by source/scene and exposure manifest. Do not fall back from empty held-out selection to all probes. Track-held-out clips from development videos may be used for labeled development selection; they are not independent confirmation. Reject empty clips, partial evaluations, missing required scores, invalid wire accounting or missing provenance.
- Evaluate the actual immutable checkpoint hash and exact configuration. Apply device, seed and inference-step arguments rather than merely accepting them. Record per-clip outcomes and source grouping, not aggregates alone. Remove the alias that calls a temporal frame-difference proxy FVD.
- Re-run all four diagnostic matrix controls on the same input/configuration, or reuse only immutable results whose complete identity matches. Remove unconditional numeric controls in scripts/run_diagnostic_matrix.py (coordinate ownership with coordinator). A fixed residual QP is not matched final fidelity.

Authorized checks: correct local/global frame lookup; missing source/pose failure; empty split/metrics cannot succeed or promote; real geometry retained; no overlap with forbidden confirmation sources; selected checkpoint/device/seed actually reaches inference; corruption of client output affects ranking; configuration-matched control reuse only.

### C. Model inventory and experiment protocol — GEN-ACT-06 / EVAL-ACT-07

Initially own a machine-readable candidate/configuration inventory and bounded read-only probes. Own experiments/tier/ protocol/calibration repairs and tests; use coordinator review for statistical policy. Do not run training until A/B integration is validated.

- Inventory every registered backend, collapsing aliases. For each record actual checkpoint hashes, training exposure, adapter readiness, native temporal support, conditioning requirements, memory/time pilot and train/resume support. Include pix2pix, SPADE4Tennis-lite, pose/reference ControlNet, true IP-Adapter-conditioned options and Animate-Anyone where assets exist. Other registered backends receive an explicit ready/blocked/deferred decision; no implicit exclusion because only two training wrappers are convenient.
- Close the calibration alarm correctly: check identity > mild > severe and mild > unrelated separately; do not force unrelated below every severe distortion. Calibrate absolute scales and natural unrelated controls. Do not weaken thresholds to accept desired outcomes. Verify the actual metric path used by each experiment.
- Require full frozen identity and evidence before confirmation, including expected identity (currently optional), independent match grouping (scene IDs do not identify independent matches), complete per-rung configuration, actual presets, uncertainty and verified output/wire artifacts. Status booleans supplied by a caller are not proof. Keep pilot mode fail-closed.
- Keep AV1 and VVC native and resolution-adaptive arms at the same display grid; report both. Recompute stored BD-rate as an arithmetic check only, not a newly valid experiment. Keep the measured-overlap threshold and no-extrapolation rule. Refine sampling where overlap is insufficient; do not relax it after seeing scores.

Authorized checks: required identity absent/mismatched fails; several scenes from one match count once; null calibration ordering is correctly partial; known identical/+10% curves reproduce 0/+10%; insufficient overlap stays unscorable; runtime/bytes for spatial scaling are charged.

## Wave 2 — integration and full-codec pilots

Coordinator integrates repairs onto the PR #88 branch without overwriting other sessions, corrects its PR description/status claims, and runs required lint, typing, layer checks, relevant integration tests and native roundtrips. Fix CI before merging. Preserve raw old reports and register their superseded interpretations. Existing passing unit tests do not substitute for the new behavioral checks.

Before reading new metrics, write two-sided plausible bounds and null expectations. Run tiny development pilots first. The diagnostic matrix is generation off/on × residual off/on, with an actually loaded candidate and same-scene pasted-reference controls. Reconstruct from bytes in another process, score that output, save frame checksums, all component byte counts and synchronized runtimes. Validate real-frame/pose contact sheets and fail on missing inputs before paying for model inference.

Then produce whole-frame and object-scoped rate–quality curves for the complete codec. Predeclare display-fidelity targets and sweep residual rate to match them; keep total wire bytes and runtime as selection criteria. Include residual absent controls, multiple residual codecs (AV1 and VVC where supported; current AVC is a baseline), background representation/scale/refresh, appearance compression/refresh, pose/motion precision, and longer eligible scenes for amortization. Start with one axis at a time around a verified configuration, then test promising interactions. Choose durations based on actual eligible footage; never pad/repeat frames to manufacture amortization.

Prioritize levers from a measured byte/error profile. Background/metadata may dominate even with a better foreground model. Maintain a no-generation control so an expensive model is selected only if it earns its cost. Distinguish low-rate perceptual regimes from high-fidelity correction; report both honestly. No fallback-only conventional codec result may be labeled a semantic codec win.

## Wave 3 — staged training, only after trustworthy ranking

Use a multi-fidelity search inspired by [Hyperband](https://jmlr.org/papers/v18/16-558.html), not automatic architectural elimination after one epoch. The schedule below is a planning budget, not a claim of convergence.

1. Run existing checkpoints and no-model controls first. Test intended conditioning and native temporal sequence inference; readiness/sensitivity is not proof of quality or cross-process determinism. Compare fine-tuned checkpoints with their actual initialization.
2. Within each ready architecture, declare a small search (for example three configurations) over learning rate and the fidelity/adversarial/perceptual/temporal loss tradeoff. Use model-appropriate defaults as baselines, not identical losses for unlike models. Verify nonzero optimizer updates, gradients and training/inference preprocessing before promotion.
3. Use bounded resource rungs, for example 15, 60 and 180 cumulative GPU minutes, recording steps, examples and wall time. Expensive models need a meaningful minimum update budget; if a bracket cannot afford that, mark deferred rather than inferior. These rungs share the remaining eight-hour budget; do not multiply it by candidate count. Allocate at most half the remaining experiment budget to initial screening so promotion remains possible.
4. Promote configurations on total bytes at predeclared matched final fidelity with a runtime constraint/Pareto comparison. Recheck promising or ambiguous candidates with another seed and several independent development sources; preserve uncertainty and a slower-starting candidate until its learning curve is informative. Do not optimize fixed-QP residual bytes alone, or prune on a tiny composite-score difference.
5. A single surviving candidate must continue training to its authorized final budget: the current campaign stops when alive has length one. Save/resume optimizer, scheduler, RNG and training progress at least hourly independently of epoch count; verify exact continuation. Store immutable checkpoint hashes and per-trial hyperparameters. Restore SPADE to the candidate pool; the old ranking does not justify pruning it.

Wire scheduler changes only after B hands off train_campaign.py. If training cannot start within the eight hours, finish the repaired harness and readiness registry, and give the exact next command rather than launching an unbounded continuation. All-model readiness screening is useful; equal expensive training for every model is not required.

## Reporting and submission decisions

Launch long jobs detached with ten-minute progress logs, hourly checkpoints, verified resume and an overall eight-hour deadline. Ordinary progress is quiet; provide an end-of-budget digest and actionable blocker notifications if the harness supports them. Do not poll with an agent loop. Stop launching new trials before the final 30-minute validation/report window.

Morning output: PRs/CI; repair acceptance evidence; complete/failed/deferred trials; exact model/config identities and splits; per-source total-byte/quality/runtime tables with controls; curves only where valid; winner status (including no winner); and a bounded continuation command. Update PLAN and owning areas after each accepted wave.

Protect still-unexposed confirmation sources. Previously evaluated Gate B pilots are already exposed even if untouched this night. Once a credible Gate A configuration is selected, freeze the full procedure and confirm on an audited reserved split; then execute formal Gate C ablations. Baseline setup, ablation plumbing and paper preparation may run earlier. Review submission feasibility against the provisional 20 September evidence freeze and 30 September target; missing evidence stays missing, regardless of deadline. Fold validated findings into the separate paper repository; do not clear result HOLEs with pilots or the old PR #88 ranking.
