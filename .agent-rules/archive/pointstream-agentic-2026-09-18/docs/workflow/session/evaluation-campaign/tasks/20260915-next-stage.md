# Next evaluation stage — coordinator dispatch, 15 September 2026

Return to the Codex task **Coordinate submission evaluation**, task ID
`01a0a488-257a-7b93-ab8c-2ac2a590f29c`. Read the current campaign entry point
for accepted code revisions before starting. This assignment supersedes the
older repair prompts only where stated below.

Reviewed code heads: #104 `0bbf3fb66091b35cbb6642fe6667da6431e4a602` and
#108 `af3e5dba78befd533962ff47ae63181a34753961`. Workers fetch main containing
both accepted changes and this dispatch, then record that actual commit.
Accepted main code baseline: `3896da6d69547b206a8455dae6a4b13f24cdc649`
(#104, following #108 `30d02552e60e1d390c82f879ab99ae61ae55fd27`).
The contract manifest's `code_head=d99d527183dea84e3db9b2923f4fc94d33957897`
names the code-bearing commit; its subsequent pin commit only records those
bytes. Verify the two module and two example digests before producing records.

## Cursor — E03B anchors and score-free confirmation eligibility

Area/action: evaluation, E03. Continue from accepted #104 and #108
on a fresh branch/worktree; record the exact merged code revision and contract
module hashes. Cursor retains exclusive ownership of the campaign reader and
generation result adapter.

Execute the four-setting card in
`manifests/evaluation_20260915_e03a_anchor_card.json`: Federer scene 007,
48 aligned source frames, short edge 360, 12 fps, AV1 preset 0 and VVC slower,
QP 63 and 47 each. First resolve and save effective source transforms, colour
metadata, full native encoder/decoder argv, and CPU allocation. Use existing
codec adapters and preserved artifacts. The reuse map identifies why archived
native points cannot replace this low-resolution comparison. Share the exact
selected frame/PTS manifest with E04; neither experiment depends on generator
readiness. The card's 24 fps cache positions are target-grid indices, not native
PTS. Before reuse, verify its source/seek/filter identity, then resolve original
frame PTS for those positions. The old helper tests only file count and may
write into a historical cache: do not call its extraction fallback there. If
identity or PTS cannot be recovered, materialize only the same four-second
window in a new run directory using the existing extraction primitive and save
the exact mapping. Never overwrite BP46/BP21 frames. The earlier native interval
[68:116] is not this scene-start interval and must not be relabeled.

Implementation/preparation allowance: two active worker hours. Measured probe:
at most 30 minutes including decode, calibration and scoring, four candidate
settings (maximum six if an explicitly documented refinement fits the cap).
Reserve at least one third for controls/scoring. Register numerical two-sided
size/quality/time bounds before reading the new scores. Calibrate the selected
metric path with identical, mild/severe noise and blur, and unrelated structured
content. Run only the missing calibration, or cite compatible calibrated data
with its exact identity. Record absolute scales and the null.

Persist actual streams, decodes, byte ledger, source IDs, frame PTS, commands,
binary versions/hashes and separate preparation/encode/decode/scoring time under
`/home/itec/emanuele/pointstream-data/outputs/evaluation-20260914/e03b/` in a new
run directory. Validate all four rows through the accepted contract. Missing
runtime does not remove otherwise valid RD; profile only the missing compatible
stratum. One scene gives a development diagnostic, not a confirmed advantage.
Two points per codec may have insufficient overlap; return that gap rather than
extrapolating. Pause with measured cost if the card cannot finish in budget.

Separately complete the reserved trio's score-free event/overlap, timestamp
origin and content-based scene eligibility. Use acquired files and acquisition
hashes; preserve `scores_computed=false`. Freeze eligible scene boundaries before
codec selection and scoring. All three sources are 1080p; they cannot confirm a
native 4K claim. Neural anchor environment/checkpoint setup can proceed within
the preparation allowance; its compatibility issues do not delay this card.

Return exact code/PR/CI, job and artifact paths/hashes, produced/requested cases,
controls/alarms, three-axis evidence and one proposed next decision here.

## Antigravity — E04A removal-off background probe

Area/action: codec, E04 / CODEC-ACT-07. Use an isolated branch/worktree based on
accepted #104/#108, independent of #109. Scope the existing background probe,
its component/transport adapters, related tests and codec area. Coordinate any
shared runner edit before changing it.

Preparation allowance: two active worker hours. Inspect the reuse map and the
saved `outputs/development-recovery/wave2-background-probe/probe_report.json`,
BP30 reference-policy comparison and BP52 rate search. Preserve their original
files and validity labels. The three-mode artifact ran removal ON; BP30 modes
are reference policies. Reuse compatible mappings/decodes/timing, and list the
specific evidence gaps in the E04 card.

Implement the smallest missing removal-OFF path and verify actor pixels are
unchanged in its input stack and optional removal/fill calls are zero. Record
any inherent actor suppression by panorama aggregation separately. Use the
E03B timestamp/transform recipe (or independently materialize the same recipe)
on Federer scene 007 at 360-short-edge/12 fps, 48 frames. Keep all foreground
references, placements and compositing fixed, with residual and generation OFF.
Run still, panorama and per-frame video at two coarse QPs, six candidate
settings in at most 30 minutes including controls/scoring. The initial QPs are
47 and 32, as in the earlier background screening; pin the actual codec/preset
and validate the budget before launch. A changed preset or source interval
prevents treating old removal-ON rows as paired measurements.

Register two-sided size/quality/time bounds and rationale before scores. Require
the actual serialized decode, all geometry/mask/metadata bytes reconciled,
calibrated visible-background/object/boundary/composed quality, and separate
sender/client timings and lookahead. Reuse the full decoded video for both
no-overlay and fixed-overlay conflict controls; inspect old actor positions,
boundaries and double silhouettes without extra encoding. Preserve outputs in a
new directory under
`/home/itec/emanuele/pointstream-data/outputs/evaluation-20260914/e04a/`.

Return the six cases, controls, alarms and reuse ledger here. A contrasting
camera scene and paired removal-ON follow in the next costed stage before
promotion. This first probe cannot establish a whole-codec win or select a
background for all regimes.

## Antigravity — E02S acceptance completion, separate lane

PR #109 remains open; E05 is unreleased. Preserve reported seven-corner and
optimizer artifacts and provide their execution host, exact paths, commands,
input/checkpoint IDs and SHA-256 before deciding whether any run is missing.
The existing test reinstantiates a model within one process, uses prepared
tensors and omits the trainer DataLoader/discriminator path. It is insufficient
evidence of CLI continuation. Python `random.choice` selects reference images;
sampler order alone does not restore that randomness or worker state.
Creating a new DataLoader iterator also consumes global Torch RNG unless it
uses an isolated generator, shifting dropout after the saved checkpoint.

Within two active worker hours, repair and verify the actual selected trainer's
fresh-process continuation, including source/reference IDs, sampler cursor,
Python/Torch/CUDA/NumPy randomness and both optimizers. A deterministic
per-sample reference policy or explicitly constrained verified worker mode is
acceptable; describe unsupported modes honestly. Use a development-only tiny
CLI and accelerated checkpoint interval. Real execution is limited to the
existing 30-minute acceptance allowance through accepted resource support.
Reuse completed evidence wherever compatible.

Verify selection against actual producer fields (`total_bytes`, `psnr_mean`,
`ssim_mean`, `measured_client_seconds`/`client_seconds`) and preserve candidates
whose quality/resource evidence is missing or incomparable. The current
comparison ignores SSIM and treats missing PSNR/time as equal: a rate-only row
can dominate a measured row. Use declared per-metric indifference bands and
retain quality/resource tradeoffs. Explicit residual
OFF must remain off. Feed the actual control rows through Cursor's accepted
adapter; report missing/failed controls faithfully. The repeat corner
`gen_on_res_off_same_seed` must be recognized by the combined adapter, which
previously accepted only an explicit repeat flag or `_repeat` suffix.
Hash changes alone establish
pixel sensitivity, not useful motion or identity adherence. Return the specific
remaining evidence and code correction to #109; do not edit Cursor-owned files
or self-release E05. E04A proceeds concurrently in its own scope.

## Shared launch and return policy

Use accepted claims/monitor code, an explicit per-job CPU allowance and a
per-host aggregate <=90% of currently available cores, accounting for codec,
BLAS and loader workers. Recheck device availability immediately at launch.
Initially run both lanes on one verified host using shared local-host claims,
or queue them if the aggregate allowance is unavailable. Parallel assignments
do not require concurrent encodes. Untested cross-host contention and
takeover/recovery remain disabled; additional hosts need a bounded two-host
claim test before deployment. Never preempt colleagues or treat this
coordinator's limited device visibility as evidence that a host is idle.

Jobs detach, write progress every ten minutes, checkpoint resumable work hourly,
and notify this task on completion, failure or a required decision. No periodic
agent polling. If automatic return delivery is unavailable, provide the user a
paste-ready report addressed to this task. Pause after each bounded assignment.
Keep confirmation scores untouched and all old artifacts immutable.

The provisional 20 September freeze is at risk until anchor/background results,
generator readiness, neural anchor compatibility and full-codec comparisons
return. At the next probe return, cost the remaining critical path explicitly;
keep the 30 September submission target and the neural-winner/secondary-domain
requirements unless the user changes them.
