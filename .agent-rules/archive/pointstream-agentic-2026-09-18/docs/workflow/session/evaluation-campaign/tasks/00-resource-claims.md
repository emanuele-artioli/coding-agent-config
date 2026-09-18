# R0 — Minimal atomic resource claims for campaign jobs

Owner: Antigravity, preferably an independent bounded subagent while E02R fixes
training/evidence. Scope: `experiments/jobs/` claim/launcher support and focused
tests, infrastructure area; no shared adapter/trainer/schema files. Start from
current main in a separate worktree/branch. Budget: two active worker hours;
CPU-only process tests. Return immediately if existing site scheduler support
solves the requirement; do not build a cluster scheduler.

## Required behavior

Use a verified shared jobs location accessible from all participating hosts.
Key claims by canonical hostname and GPU UUID (not local ordinal alone). Atomic
acquire must give exactly one owner when competing processes request one device;
record a random ownership token, job ID, host, device, process identity and start
identity. Check existing processes/free memory before selection and recheck under
the claim immediately before launch. Claims coordinate our workers only; colleagues
are unaffected and may still make a device busy. Recheck and defer rather than
kill or preempt. Any visible GPU not explicitly claimed must be hidden from the
child using CUDA_VISIBLE_DEVICES; the trainers currently auto-spawn over all
visible devices. Record UUID to child ordinal mapping.

Release only by the owning token after the supervised child actually exits.
Interruptions/stale claims cannot be reclaimed just because a TTL expires or a
remote PID is not visible locally: verify owner/job liveness, otherwise leave it
pending and report. Claim acquisition and failed launch must be recoverable;
a long-running child must retain its claim through the monitor lifecycle.
Use one consistent cross-host atomic primitive on the actual filesystem, with a
local-process contention check and a bounded two-host check when access allows.
Do not advertise cross-host protection based solely on per-host /tmp locks.

Account all our simultaneous codec/BLAS/loader CPU threads per host under the
campaign's available-core cap (affinity/quota/load aware). Host-level allocation
updates must be atomic, and CPU-only acquisition workers must participate or
reserve an explicit allowance. Busy/unsupported host: defer or move an unstarted
job, never duplicate a running shard. Integrate with existing detached monitor,
not a persistent model polling loop.

## Acceptance and handoff

Demonstrate competing acquisition (one winner), distinct device independence,
non-owner release rejection, busy-device rejection after recheck, failed-launch
cleanup, and retained claims while a supervised child runs; verify CPU allocations
cannot oversubscribe our cap. Document one actual launch command and safe recovery.
No GPU workload needed for process tests. Send the tested helper revision to E02R
and the coordinator. Real-backend readiness can use it only after these checks;
return any unavailable real-host verification explicitly.

## Execution and return

Follow the [campaign](../plan.md) and [session workflow](../../SKILL.md).
Pin actual code/inputs; retain immutable outputs. Run meaningful behavior tests
and setup checks for changed code, plus CI. No expensive campaign expansion.
Return exact commands, artifact identities, controls, spent budget, unresolved
issues and one next decision to the coordinating Codex task; do not self-dispatch.
