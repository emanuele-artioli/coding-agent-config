# E01R — Correct evidence eligibility and acquire reserved sources

Owner: Cursor. Continue PR #104 from `b87daf51b88a27ed7ee1c8ad9858131eef2fe5db`;
incorporate shared main `2f63ae1` plus these coordinator docs without overwriting
Antigravity's work. Keep your existing clean E01 worktree; record its head.
Areas/scope: E01-owned contracts, manifests, evaluation/data docs and tests;
acquisition metadata outside the code tree. Do not edit E02 adapter/trainers or
job claims. Budget: four active worker hours for contract correction; source
acquisition is a separate bounded stage below. Report partial progress early if
an external acquisition block arises.

## Coordinator decisions — 14 September

Accept **three fresh independent matches** as the prospective target (six still
preferred) and reserve the proposed primary IDs:
`conf_cand_01_sinner_medvedev_ao2024`,
`conf_cand_04_medvedev_djokovic_usopen2023`,
`conf_cand_05_swiatek_sabalenka_madrid2024`.
This accepts a target/shortlist, not their acquisition, eligibility or scientific
confirmation. On-disk untouched count is zero. Verify event identities, overlap
with development compilations, provenance and actual accessibility before freeze.
No test score access. Acquisition failures require a prospective substitute and
updated manifest, never substitution of the two exposed Gate B sources as fresh.
Remove `fallback_if_unacquired.uses_exposed_sources=true`: those remain development
or historical observations, not restricted held-out confirmation.

Accept low display 360-short-edge/12 fps versus native, crop size separately,
valid colour arms, and 250 ms as a declared working latency target. VMAF 20 can
be a diagnostic exclusion threshold; it is not an established practical quality
floor. Before final selection, propose an interpretable quality criterion using
calibrated development anchors and inspectable reconstructions, recording the
rationale. This does not block exploratory low-resolution probes. Eight seconds
is a live smoke check, not strong sustained-operation evidence: finalists need
at least 30 seconds after startup AND four refresh cycles AND more than temporal
context, with backlog and latency by window. If this cannot be staged on suitable
source material, return the missing test instead of declaring sustained live.

## Corrections required before E01 acceptance

1. Separate historical/exploratory observations, recoverable evidence, and
validated claim eligibility. Current examples mark old unverified reconstruction,
calibration and ledger paths `rd=true`; missing timing is not their only defect.
Retain them in inventory and separately labelled diagnostic plots, but block them
from validated RD curves until the relevant metric/output/byte validity has been
established. Validate per metric/arm where only some evidence is salvageable;
do not require wholesale re-encoding. Reconcile reuse notes with actual chronology
(e.g. the overlap run is after #88; name the actual unresolved path).

2. Tighten the ingestion boundary without building a new general framework.
On the reported E01 head, clearing artifact path/hash/code, source/frame IDs and
setting `controls=None` still yields zero blockers and `n_kept=1` for RD. The
unrun timing example also enters runtime ingestion. Require meaningful identities,
correct control types and claim-specific evidence; distinguish synthetic examples
from eligible actual artifacts, finite metric/byte values and their referenced
sources, and verified timing strata from placeholder IDs. A valid RD row with
no timing must remain valid for RD. A malformed runtime claim must not silently
certify runtime; preserve independently established RD eligibility where possible.
Structural validation alone may exist, but production ingestion must also check
eligibility/provenance. Add these actual misuse cases to tests.

3. Finalize the adapter interface with Antigravity early. Its merged adapter
currently uses a different schema; publish exact producer-shaped examples and
require real E02 output to pass through `validate_campaign_record` and
`ingest_for_claim`. Full-trajectory evidence is not automatically `generalization`;
that claim requires independent-source/frozen-procedure evidence. Define trajectory
coverage separately. Do not make single-scene readiness depend on a generalization
flag. Pin the agreed contract revision before downstream runs.

4. Freeze usable source/time manifests, not just video labels. Validation blocks
must be explicitly excluded by training selectors, with match grouping/replay
checks. Specify deterministic sampling of native timestamps, colour/range handling
for missing tags, and decoded-frame hold for common-timebase scoring; never use
untransmitted source frames to restore missing output frames or compare reduced
fps against a conveniently reduced reference without labelling that scope.
Prospective confirmation policy must reject pending/unaccepted policy for final
confirmation, invalid counts (including booleans), and wrong stage names. Record
the chosen policy identity in experiment provenance.

## Acquisition lane — start now, independent of schema repairs

Inventory existing acquisition scripts/manifests and access; reuse verified media
if discovered. Download only the reserved sources or bounded qualifying windows
needed for manifests/confirmation, external to code; preserve provenance and
checksums, expose no confirmation quality scores or tuning. A CPU-only isolated
subagent may handle this lane using a separate output path and manifest ownership;
root Cursor owns merging its metadata. Initial cap: two hours wall time and one
attempt per source, then report acquired/inaccessible, storage/time estimates and
substitute options. Respect colleagues and the aggregate 90% CPU cap; no new
server-wide crawler or full unrelated dataset download. Access failures are
reported rather than bypassed.

## Completion

Update #104 with corrections and exact regressions; report accepted-target versus
actually acquired/eligible count. No E03/E04 measured batch yet on the proposed
contract. Their CPU environment/tool inventory may proceed without touching
active E02/R0 files. Return corrected contract for review, then coordinator
releases the first low-resolution anchor/background probe.

## Execution and return

Follow the [campaign](../plan.md) and [session workflow](../../SKILL.md).
Pin actual code/inputs; retain immutable outputs. Run meaningful behavior tests
and setup checks for changed code, plus CI. No expensive campaign expansion.
Return exact commands, artifact identities, controls, spent budget, unresolved
issues and one next decision to the coordinating Codex task; do not self-dispatch.
