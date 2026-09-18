# Worker B — credible anchors and experiment verdicts

Assignment: EVAL-ACT-06 evaluator portion and EVAL-ACT-07. Follow overnight-recovery.md. Own experiments/tier/ evaluation drivers and their focused tests; coordinate shared metric/contracts changes. Worker A owns runner transport and scoring integration.

Read docs/areas/evaluation.md and the PR #86 audit. The new fail-closed verdict is only a guard: full confirmation protocol enforcement remains unfinished. Preserve immutable old reports and label new runs development pilots.

Make experiment identity include the full configuration, exact codec builds/presets, model hashes when used, manifest, metric versions and runtime policy. Require evidence of actual client-output scoring, measured full wire cost, calibrated metrics/nulls, source eligibility and uncertainty before confirmation can pass. Missing evidence must fail closed. Coordinate the runner interface with A rather than duplicating it.

Provide both AV1 and VVC native-resolution curves and separately labeled resolution-adaptive curves. Drive settings and verify that actual outputs change. Search practical low-rate controls and spatial scaling without calling a sampled QP endpoint a universal floor. Restore all decoded arms to the same original display grid for scoring and include rescaling time. Include a residual-on high-fidelity ladder after A integrates; do not restrict the experiment to C0–C3. Predeclare the local search and quality targets, use development material only, and prohibit BD-rate extrapolation outside measured common quality support.

Authorized tests: missing protocol evidence fails; incomplete/duplicate sources cannot satisfy independent-source count; mismatched configuration/model/anchor identity fails; no-overlap curves are unscorable; known synthetic curves give the expected comparison sign; rescaled outputs have the original dimensions and declared timing/byte treatment; pilot completion cannot imply confirmation. Calibrate actual metrics with known anchors before ranking outputs. Do not write tests merely asserting report wording.

Deliver runnable bounded development commands, exact manifests and an integration checklist for A. Keep any early diagnostics explicitly provisional until runner validation passes. Coordinator runs integrated experiments and updates areas.
