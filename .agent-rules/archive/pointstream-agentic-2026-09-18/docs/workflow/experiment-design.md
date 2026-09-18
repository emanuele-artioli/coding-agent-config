# Hypothesis-driven experiment design

This is the default policy for new PointStream development probes. It replaces
broad overnight sweeps as the next-action default, not historical evidence or
[submission gate criteria](../roadmap.md). A useful probe changes a decision:
which component to build, which regime to test, or which explanation to abandon.
A clean run or wider quality overlap alone is not progress toward a codec claim.

## 1. Write the decision before the command

Put a short experiment card in the owning area or linked run manifest before
launching. Fill every field; do not create a separate permanent session report.

| Field | Required content |
|---|---|
| Decision and hypothesis | One causal question, expected mechanism, and competing explanation. |
| Evidence reused | Immutable run/config/source/checkpoint identities; what existing evidence cannot answer. |
| Operating regime | Development sources, duration, motion/occlusion, target rate and quality interval, client hardware, latency and memory limits. |
| Smallest discriminating probe | Paired controls, one changed axis, concrete configurations, required implementation gaps. |
| Bounds and instrument | Two-sided size/quality/time expectations with rationale; calibration, null and wire/decode checks needed for this path. |
| Budget | Maximum new configurations, elapsed CPU/GPU budget including setup/scoring, per-job timeout, checkpoint/reuse plan. |
| Decision rule | What promotes, stops, or makes the result inconclusive; action for each outcome. |
| Artifact and narrative | Exact output location, byte/error/time breakdown, plot intended, and sentence that confirmation or contradiction would justify. |

Before every new experiment, inspect the existing index/classification and output
folders, prior manifests and saved decodes. Record a coverage/reuse decision by
source interval, transforms, component/removal settings, code/tool identity and
claim scope. Reuse compatible evidence, rescore saved decodes or repair the
specific missing measurement before scheduling fresh encodes/training. A folder
name or a newer code fix does not certify old evidence. The September campaign
may link representative timing with sample counts/uncertainty and compatible
hardware/workload identity; a timing gap alone does not invalidate valid RD data.

Default first probe: at most six new candidate configurations and 30 minutes of
execution including scoring, with a ten-minute evidence/instrument triage first.
These are planning caps, not claims about encoder speed. Estimate one case from
existing timing first; if the cap cannot answer the question, stop with a costed
smaller alternative or a proposed larger card. Do not silently expand the run.
Implementation is a separately bounded task, not time hidden inside a probe.
Reserve at least one third of the run budget for controls, scoring and diagnosis.
Larger stages need an explicit new budget within the user's authorized scope;
an old eight-hour dispatch is not standing authorization for repeated campaigns.

Reuse only artifacts with matching source frames, code/config/tool identities,
metric path and timing scope. Re-score saved decodes when possible instead of
re-encoding. Re-run controls affected by a changed path; unrelated calibration
need not force another whole ladder. Record setup, encoding, decoding and scoring
time separately so the next session can avoid the actual bottleneck.

Stop immediately on invalid input, wire mismatch, ineffective option or failed
metric controls. Stop an axis when its declared useful range is exhausted or its
best plausible benefit cannot close the measured gap. One bounded refinement is
allowed only if it fits the card and resolves a named ambiguity. Failed overlap
means unscorable; use paired local points for diagnosis without relaxing the
registered curve floor, extrapolating, or calling them a gate pass.

## 2. First explain the total-rate deficit

At a common final quality q and a declared client budget, let A(q) be the lower
measured rate of the eligible AV1 and VVC anchors. Count disjoint actual bytes:

`T = B + F + M + R + H`

B is background payload, F appearance/foreground payload including any transmitted
model updates, M masks/motion/geometry, R correction, and H remaining envelope,
container and fallback bytes. Assign each byte once and reconcile T to the wire.
Then `A(q) - B - M - H` is the budget remaining for F + R to beat both anchors.
Use rates or bytes consistently for identical source duration and display size.

If B alone exceeds A(q), that operating point cannot win on total rate even with
free foreground. B below A(q) is necessary but insufficient: metadata and
correction can consume the entire saving. This is a rejection test for that
point, not a proof that the representation cannot win at another quality or
clip duration. For each losing point, record component bytes, whole-frame and
foreground/background/boundary error, and encode/client time. Rank the next
intervention by plausible recoverable bytes at final quality per probe cost.
Do not infer the cause of Federer's deficit from total transport alone.

## 3. Background first: removal and representation are separate axes

Extend existing mask-aware compositing rather than introducing a duplicate
background pipeline. Current code in `src/components/background/plate.py`
excludes foreground during a registered temporal median and fills remaining
holes from finite neighbours. `panorama-stream` transports plates; its name is
not evidence of a full per-frame background-video implementation.

Proposed configurable axes (capabilities must be verified before use):

| Axis | Controls and candidates |
|---|---|
| Foreground removal/filling | Off; local mean colour with defined neighbourhood; current temporal observation/median plus hole fill; Telea; one neural inpainter only after cheap methods expose a consequential gap. |
| Representation | First-frame still with declared render/warp policy; registered panorama; foreground-removed per-frame video. |
| Coding | Codec/quality, spatial scale, refresh interval; refine only promising combinations. |

For the September 14 campaign, first reuse or measure removal OFF across all
three representations at two coarse operating points on a development scene.
Then compare paired removal-on methods at the same settings.
Do not run the Cartesian product. Inspect a second, different camera-motion or
occlusion regime before broad promotion. Then refine removal on promising
representations while retaining paired no-removal and current-method controls
across modes. If an arm is missing, inventory the gap and implement only what the immediate card needs.

A conventional full video without an overlay is the anchor. The same decoded
video plus the proposed overlay is a conflict control: inspect old actor
positions, moving mask boundaries, disocclusions and double silhouettes. Removal
must address foreground over time, not just the current paste region. Hidden
background need not be perceptually perfect if never exposed, but its coding
cost and subsequent exposed pixels matter. Neural filling may add detail that
costs bytes or temporal inconsistency; test rather than assuming improvement.

Still < panorama < video in bytes and quality is an initial hypothesis, not a
required ordering. Camera motion, canvas extent, temporal prediction, refresh
and correction can reverse it. Compare decoded renderings at original display
resolution and eventually the complete codec at matched final fidelity.
Background-only error on visible background pixels diagnoses the component;
it does not establish full-frame competitive quality. Hold foreground fixed
for integration checks, including residual absent and matched-quality correction.

Charge panorama dimensions, per-frame homographies/camera mappings, crop/coverage
and refresh metadata. Intrinsics alone do not specify each rendered view. Charge
segmentation, registration, filling and encoding on the sender, rendering and
decoding on the client, plus startup delay and lookahead. Label offline panoramas
as offline; do not derive live-stream claims from their steady-state FPS.

Promotion requires measured room for foreground/correction and a useful total
rate–distortion–computation tradeoff. If background is already cheap, redirect
to the measured metadata/residual/foreground bottleneck rather than polishing it.

## 4. Foreground models: test resource-dependent frontiers

The motivating foreground area/bitrate disparity is a scoped observation.
Verify its source, codec settings and attribution method before quoting it;
foreground and background costs in an inter-coded stream need not be additive.
It motivates a hypothesis, not a guaranteed budget recoverable by generation.

Low-resolution learning/readiness may proceed alongside background evaluation;
whole-codec selection uses its fixed backgrounds. Compare pasted references, a
ready small model and a ready diffusion model under declared rate, client memory
and latency budgets. Broad training needs a specific foreground error/correction
burden worth reducing. The September campaign authorizes readiness and staged
training under its costed cards; shared training cannot start before a valid
evaluator and split. Existing invalid rankings do not justify exclusion.

Hypotheses: small models may offer useful low-rate quality on weak clients;
diffusion may exchange greater computation for quality at higher resource
budgets. Neither parameter count nor model family guarantees speed, fidelity or
quality ceiling. Test native temporal inference, conditioning, step count,
precision, resolution and fitting/training budget. Perceptual realism and source
fidelity are distinct; keep object, temporal and whole-frame measurements.

Report total wire rate including references/conditioning/model updates and
residual demand at matched final quality. State the shared pretrained-weight
assumption and separate cold download/storage/startup from steady-state cost.
Measure end-to-end client latency, throughput and peak memory on named hardware;
no weak-client or real-time claim extrapolated from a server GPU. OOM means
infeasible under that tested budget; an unavailable backend is untested, not
inferior. Model rankings require adequate model-specific training and uncertainty.

Keep nondominated candidates per resource regime. Call a model dominated only
within tested conditions with comparable quality and reliable timing; keep the
full search record and place well-supported negative comparisons in an appendix
if they do not explain the main claim. Do not hide reversals to preserve a story.

## 5. Evidence becomes the narrative

For each card record: supported, contradicted, inconclusive, invalid, or deferred;
what was learned; cost spent; and the single next decision. Preserve immutable
old artifacts and append interpretations with provenance. Development selection
never turns exposed sources back into confirmation data.

Planned background figure: rate versus reconstructed quality, with separate
panels for camera regime/duration and accompanying encode/client time and memory.
Planned foreground figure: quality versus total rate within named client budgets,
plus quality versus client time and feasibility/VRAM. Show controls, measured
points, uncertainty and tested dominated arms; avoid a composite score that hides
tradeoffs. Generate paper plots only from validated artifacts. Component findings
can support explanatory figures without a codec win, but cannot substitute for
Gate A/B. Manuscript edits remain a separate task in the paper repository.
