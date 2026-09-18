# R0R — Repair actual claim ownership and child lifecycle

Owner: Antigravity subagent, continuing R0 `d39893c963f787691dc83dcbf9e2240016627c45`
in its own worktree. Scope claims/monitor and focused tests only. Two active
worker hours initially; no GPU workload required to reproduce these defects.
R0 is NOT accepted or merge-ready; publish a PR and full CI after correction.

## Reproduced CPU-only blockers

1. `claims.py:242` removes the CPU mutex after 30 seconds with no verified owner
   death. Aging a held lock's timestamp to 31 seconds permits a second process
   into the same critical section. No TTL-only takeover; token-safe release and
   conservative verified-liveness recovery apply to mutexes as well as devices.
2. `run_supervised` releases claims in finally after an interrupted wait while
   its child survives (`claims.py:887`). The reproduction leaves a live child
   and empty CPU allocations. On interruption terminate/reap only the owned
   process group before release, or retain the claim as unresolved if death
   cannot be verified. Cover spawn failure and successful completion too.
3. `is_claim_active` trusts an interrupted/failed status before process liveness
   (`:175`); monitor writes interrupted before child shutdown (`monitor.py:322`).
   A live local PID with interrupted status is classified inactive. Store/check
   child/group and process start identity, conservatively handle remote unknown
   liveness and supervisor restart, and never let status text release a live job.
4. Missing UUID or failed occupancy query is treated as free (`:345,393,481`).
   `acquire_device_claim(device_uuid='GPU-NOT-PRESENT', probe_fn=lambda: [])`
   succeeds. Missing/failed/unknown query must defer. Recheck immediately before
   Popen, after CPU allocation and other setup, with claimed-only child visibility.
5. CPU availability omits quota/load (`:536`) and environment pool limits alone
   do not account for concurrent codec/loader children. Require an explicit
   aggregate per-job budget and all campaign jobs, including GPU jobs, to take
   a CPU allowance; enforce worker/codec/pool settings within it. Document the
   limits of accounting rather than claiming env vars enforce arbitrary children.

## Acceptance and handoff

Add the actual CPU-only reproductions and verify one winner, non-owner release,
interrupted child lifecycle, invalid queries and combined CPU allocation. No
killing colleague processes; test children only. Verify cross-host filesystem
claims with two bounded contenders where available, otherwise state unverified
scope and keep that deployment disabled. Existing gpu6 availability inspection
is useful but not cross-host atomicity/lifecycle proof. Pass a tested commit and
actual monitor launch command to the coordinator and E02S. No E02 GPU probe using
bare CUDA_VISIBLE_DEVICES selection while claim support remains broken.

Follow [campaign](../plan.md), [session workflow](../../SKILL.md), setup verification
and the existing bounded budgets. Pin exact branch/input/contract identities;
keep raw artifacts immutable. Run focused behavior regressions, project checks
and CI before requesting code merge. Return actual evidence and one next decision
here. No E05 campaign, test-source scoring, blanket rerun or broad rewrite.
