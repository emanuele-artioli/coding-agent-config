# E04 — Background representation and paired removal

Owner: Antigravity. Area: [codec](../../../../areas/codec.md).
Depends: E01 reuse map/input contract; independent of E03 measurements and E05
training after interface freeze. Scope: `scripts/background_probe.py`, background
components and their transport/render adapters, probe tests/configs. Coordinate
shared runner edits with E02/E06. Subagent requires its own worktree/output path.

## Work

First resolve existing three-mode evidence, especially
`outputs/development-recovery/wave2-background-probe/probe_report.json` under the
external data root. The #96 probe builds foreground-removed frames with temporal
observations and Telea fill; #101 serializes geometry/charges float32 precision.
Do not relabel that as removal-off or rerun it merely because it is old. Reuse the
parts justified by E01, rescore saved decodes where possible, and run only gaps.

Verify separate config axes: still (declared static/warp behavior), panorama,
per-frame video; and removal off, temporal fill/current heuristic, cheap spatial
fill, optional neural inpainting only after a consequential cheap-method gap.
Removal off must leave actor pixels untouched in the input stack and execute
zero optional removal/fill calls; verify this, not flag names. Panorama
aggregation can itself suppress transient actors: record that inherent behavior
and do not confuse it with an explicit foreground-removal preprocessor.
First compare all three modes off, two coarse quality settings on a low-resolution
development scene. Add a contrasting camera/occlusion scene before promotion.
Then pair removal off/on at the same settings across the modes, initially cheap
methods, preserving comparisons rather than only selecting the apparent winner.
Expand coverage to selected videos/scenes using E01's manifest, native endpoints
and duration contrasts under a separately accepted batch budget.

Hold foreground reconstruction fixed and residual off. Include full decoded
video/no-overlay and same video/overlay conflict controls; consider a warped
single-frame control to separate geometry from panorama coverage. Score visible
background, object/boundary and final composed frames. Explain the motivating
background bitrate observation with its original attribution limits; it is not
a recoverable fraction promised for every inter-coded sequence.

Charge actual independently decoded payloads and all consumed mappings,
dimensions, masks, crop/refresh/timing metadata exactly once. Intrinsics alone
are insufficient panorama transport. Still/video headers may already carry some
fields. No original untransmitted float64 geometry/state at the decoder. Report
preprocessing/filling/registration/encode versus client costs and lookahead;
full-scene future context remains offline. Reuse defensible timing strata.

## Acceptance

Reuse/new-run ledger and paired results answer which representation/removal
choices remain useful by camera regime, duration and resource budget. Actual
wire roundtrip, calibrated scoped quality, time evidence and control outcomes
are present. Deliver a background frontier and fixed integration configs for
E05/E06, plus paired-change/byte plots; no required still < panorama < video
ordering and no background-only claim of full-codec superiority.

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
