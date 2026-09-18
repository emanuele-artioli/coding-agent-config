# E03A — One result boundary, then anchor preparation

Owner: Cursor. Continue #104 at `7e4da6ecda16d93263f0e6c785a0213a9bb41ab6`.
Acquisition is accepted complete: all three media files plus report/log hashes
were independently checked; their eligible count remains zero and no scoring is
reported. Keep those assets reserved. Now close the result boundary instead of
another acquisition/inventory pass. Budget: two active worker hours initially.

## Ownership handoff

Cursor now owns BOTH `experiments/tier/campaign_result.py` and the generation
result adapter boundary. Read/port only needed adapter changes from Antigravity's
E02R `b7c4d16` into your branch; Antigravity stops editing that adapter. Do not
merge its trainers wholesale. Put translation in the experiment layer where
appropriate; avoid runner importing experiments. Use one canonical schema and
actual producer-shaped tests. Coordinate the specific file/commit handoff in PRs.

## Remaining acceptance failures (reproduced)

- `_finite_number(float('inf'))` returns True. `_rd_arms` trusts caller flags
  instead of checking values. A `validated_claim` producer example with total
  bytes -1, infinite quality and all three controls `{'status':'failed'}` is
  admitted by default validated RD ingestion. Normalize string/dict controls,
  require positive evidence of their success, finite domain-valid values and
  complete eligible metric/rate references. Missing, partial or not-applicable
  is not verified. Preserve valid RD without timing. Apply appropriate evidence
  requirements to standalone/runtime/trajectory too, without forcing quality
  controls on timing-only evidence. Do not expand to unrelated validator cases.
- The stored E02R campaign result fails the CURRENT contract (missing
  contract_revision, record_class, trajectory, invalid control statuses and a
  dict where code revision is expected). Structure-only acceptance against an
  old contract is not current integration proof.
- E02R adapter reads flat metrics, while actual rows put quality in `scores`,
  timing in `timing`, and payload components in `parts`. Missing objective
  quality is a mapping bug, not a consequence of a single scene. Single-scene
  measured RD may be diagnostic; it cannot establish generalization.
- Stored artifact_sha256 hashes canonicalized JSON rather than the referenced
  file bytes. Its declared 1080p shape disagrees with the artifact's 4K frames.
  Populate provenance from actual inputs; retain checkpoint digest separately.
  Do not infer decode/calibration/ledger success from hash/score/byte presence.

## Exact reuse inputs and deliverable

External data root is `/home/itec/emanuele/pointstream-data`:
`outputs/evaluation-campaign/e02r/diagnostic_matrix_pix2pix_scene028.json`
SHA `cec034102a3e00c2073158807278312ea3f7ccf56221918331e86dc308af7426`;
old campaign result SHA
`296dc0c98dc441ab85676cf3d4950b58ff35b6e2ce61f3ae97c2e9db9151df84`.
Regenerate a NEW derived record from that saved diagnostic, leaving originals
unchanged. Run it through CURRENT structure and claim ingestion. Report kept and
excluded scopes with correct reasons; do not force a success when actual control
evidence is missing. Add actual failure-case regressions, not tests that only
assert a schema label. Pin the agreed contract hash/revision for Antigravity.

Keep the pending source eligibility separate from acquisition. The independent
media hashes match; remaining eligibility work is frame/time origin after
stream-copy cuts, source/event overlap and content-based scene bounds selected
without codec scores. Do not reacquire the media merely to obtain exact cuts:
inspect local timestamps and record offsets/keyframe preroll. That can proceed
CPU-only alongside schema fixes under available resource accounting.

Then perform E03 CPU tool/environment and source-transform preparation. Deliver
the exact smallest low-resolution paired anchor card and existing-results reuse
map; generation is not a prerequisite. Measured anchor batches wait for tested
R0 and this boundary's acceptance here. Target next release: one scene, two rate
points per conventional codec, slowest supported presets, size/quality/timing
with controls, within the pre-existing six-setting/30-minute budget or a costed
extension. Neural codec setup can proceed separately without delaying that card.

Follow [campaign](../plan.md), [session workflow](../../SKILL.md), setup verification
and the existing bounded budgets. Pin exact branch/input/contract identities;
keep raw artifacts immutable. Run focused behavior regressions, project checks
and CI before requesting code merge. Return actual evidence and one next decision
here. No E05 campaign, test-source scoring, blanket rerun or broad rewrite.
