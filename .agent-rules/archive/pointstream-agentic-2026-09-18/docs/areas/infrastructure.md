# Infrastructure Area

## Current acquisition / integration review

R0R repairs the CPU-only blockers identified in R0 `d39893c`: eliminates TTL-only
takeover on mutexes and claims, guarantees child process group termination and reaping
prior to claim release (retaining claim if death unverified), checks local PID liveness
and process start identity before status text, fails closed on absent or unqueried GPUs
with pre-Popen rechecks, and accounts for cgroup quotas, load, and mandatory per-job CPU
thread allowances. Cross-host NFS contention and lifecycle behavior have not yet been
tested by two real hosts, so multi-host deployment remains disabled; run monitored jobs
on one verified host until that check is recorded.

## Coordinator follow-up — E01/E02

Atomic resource claims are completed under [R0](../workflow/session/evaluation-campaign/tasks/00-resource-claims.md):
minimal atomic filesystem claims in `experiments/jobs/claims.py`, GPU UUID and canonical host keying,
pre-launch recheck under claim (no preemption/killing), child device isolation (`CUDA_VISIBLE_DEVICES`),
conservative stale-owner verification (never steal solely on TTL), aggregate per-host CPU cap
(`floor(0.90 * available_cores)`), and seamless integration with `experiments/jobs/monitor.py`.

## Current campaign — 14 September 2026

The [campaign](../workflow/session/evaluation-campaign/plan.md) may use any GPU
free at experiment launch across accessible servers. Recheck/claim resources;
aggregate all campaign CPU/codec/BLAS threads per host under 90% of currently
available cores, respecting affinity/quota and colleagues. Busy hosts defer or
move unstarted shards; profile hardware strata separately. Existing monitor and
checkpoint tooling should be reused. INFRA-ACT-01 is unresolved; cleanup helper
remains prohibited. No fixed GPU reservation carries into this campaign.

**Evidence Revision**: Reconciled through PR #68 (`956ad3c277`), PR #73, and R0 resource claims.
**Owned Scope**: Environments, CI/GitHub Actions, worktree lifecycle, runner integration, local caches, hardware profiling.

---

## 1. Current State

### Atomic cross-host resource claims (R0 / R0R — PR branch `codex/eval-r0`)

`experiments/jobs/claims.py` implements filesystem resource claims for PointStream workers without cluster schedulers or colleague preemption. Single-host behavior is tested; cross-host deployment remains disabled pending a two-host NFS contention/lifecycle check:
- **Shared jobs location**: Keyed under `PS_DATA_ROOT/jobs/claims` (`src.contracts.paths.data_root() / "jobs" / "claims"`) or explicit `PS_CLAIMS_DIR`.
- **Atomic cross-host primitive**: Leverages POSIX atomic directory creation (`mkdir`) on shared filesystem for device claims and host CPU allocation mutex (`.lock`).
- **Device keying**: Canonical hostname (`socket.getfqdn()` / `platform.node()`) and GPU UUID (`nvidia-smi --query-gpu=uuid`), not ordinal alone.
- **Atomic acquire**: Exactly one process succeeds in acquiring a device claim directory; records ownership token, job ID, host, device UUID, process PID, and timestamp. Missing device UUID or failed occupancy query fails closed (`DeviceUnavailableError`).
- **Pre-selection and pre-launch recheck**: Inspects memory and running processes before selection and immediately rechecks under the claim prior to child launch (pre-Popen). Defers/aborts on contention; never kills or preempts another user's work.
- **Device isolation**: Hides unallocated GPUs from child via `CUDA_VISIBLE_DEVICES` (and sets `PS_CLAIMED_GPU_UUID`), preventing multi-GPU trainers from auto-spawning across unallocated devices.
- **Token release & conservative stale owner handling (R0R)**: Released strictly by the owning random token. Eliminated TTL-only takeover in `atomic_dir_lock` and device claims. Stale claims verify liveness strictly via local PID liveness and process start time identity (detecting recycled PIDs). Stale remote claims or unverifiable local liveness are never stolen.
- **Child process group lifecycle & Interruption (R0R)**: `run_supervised` creates a new process session (`start_new_session=True`), catching all exceptions/interrupts and executing `terminate_and_reap_process_group` (SIGTERM -> timeout -> SIGKILL -> reap) before releasing claims. If child death cannot be verified, claims are retained as unresolved.
- **Claim activity vs status ordering (R0R)**: `is_claim_active` checks local PID liveness before trusting terminal status text; `monitor.py` stops and reaps child process groups before writing terminal status.
- **Aggregate CPU allowance & Cgroup accounting (R0R)**: Refuses declared allocations above `floor(0.90 * available_cores)`; `get_available_cores()` accounts for cgroup v1/v2 quota and system load. Sets `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `TORCH_NUM_THREADS`, `RAY_NUM_CPUS`, `POLARS_MAX_THREADS`, `PS_CPU_ALLOWANCE`, etc. in the child environment. These are cooperative limits and cannot enforce a cap on arbitrary children that ignore them. Explicit positive `cpu_threads` is mandatory for all monitored jobs.
- **Integration**: Integrated into `experiments.jobs.monitor` (`start --claim-gpu ... --cpu-threads ...` and `supervise` lifecycle), standalone context manager `claim_resources`, and CLI `python -m experiments.jobs.claims launch`.
- **Validation**: CPU-only focused tests cover local claim and monitor behavior. Real GPU query and auto-selection were checked on gpu5 (RTX 6000 Ada). No two-host contention/lifecycle result is recorded, so this is not yet evidence for cross-host deployment.

### Quiet long-job monitoring (PR #82)

`experiments/jobs/monitor.py` implements detached command supervision, ten-minute
file logging, explicit work-progress tracking, quiet hours, one-shot/repeating
digests, and a durable event queue with a Codex CLI adapter. Due events are
batched into one wakeup; unchanged health does not invoke the agent. Repeated
publication of the same stage decision is deduplicated independently of timestamps.

Validation: host `/usr/bin/true` launch reached complete; the installed Codex CLI
accepted a self-addressed queue check. Ruff, full mypy, import-layer validation,
and 91 selected tests (30 new monitoring/campaign cases plus 61 existing
runner/low-rate/heartbeat cases) pass against main through #81 with a host-local
Torch cache. The new job modules have 81% targeted statement coverage.
Regression scope was approved; no GPU experiment was needed for these checks. No existing overnight job was reconfigured.
See [the workflow](../workflow/long-jobs.md) for usage and delivery limitations.

### Environment & Startup Performance
PointStream runs on a shared remote Linux GPU server with an NFS-backed home directory. On **gpu6** (commit `bc09184`, September 2026), process startup and import latency were measured under clean conditions (`PYTHONNOUSERSITE=1`, explicit `PYTHONPATH`):

| Operation | n | Mean ± SE (s) | Range (s) | Notes |
|---|---:|---:|---:|---|
| `git status --short` | 5 | 0.057 ± 0.034 | 0.020–0.195 | Fast metadata walk |
| `git ls-files` | 5 | 0.0051 ± 0.0001 | 0.0046–0.0053 | Memory cached |
| `rg --files` (source dirs) | 5 | 0.0147 ± 0.0006 | 0.0134–0.0168 | Fast local traversal |
| System Python no-op | 5 | 0.0227 ± 0.0006 | 0.0215–0.0243 | Base interpreter overhead |
| PointStream Python no-op | 5 | 0.0455 ± 0.0113 | 0.0330–0.0905 | Conda env startup |
| `import sqlite3` | 3 | 0.0440 ± 0.0074 | 0.0353–0.0587 | Enforces ABI compliance |
| `import sqlite3` then `torch` | 3 | 2.101 ± 0.620 | 1.350–3.331 | PyTorch import tax |
| `import sqlite3` then `src.runner` | 3 | 0.529 ± 0.117 | 0.406–0.764 | Runner does **not** load Torch |

### Worktree Cleanup Audit
PR #68 introduced `scripts/cleanup_merged_worktrees.sh`. The documentation audit in PR #73 flagged critical safety hazards in this helper:
- Suppresses error codes from `git fetch`, `status`, and `log`.
- Falls back from `git worktree remove` to `rm -rf` when git refuses to delete a dirty worktree.
- Performs irreversible remote-ref pruning (`git remote prune origin`).

**Operational Directive**: Do **not** execute `scripts/cleanup_merged_worktrees.sh` in automated workflows until `INFRA-ACT-01` is completed.

---

## 2. Key Decisions & Evidence Anchor

| Topic | PR / Commit | Decision & Status |
|---|---|---|
| External data separation | #32 (`d436b02`), #35 (`420c3bec4a`) | `paths.py` resolver routes data to `.ps-data-root`; zero symlinks in repo. |
| Worktree recovery | #53 (`ec581e957d`) | Strict branch-and-worktree isolation protocol established. |
| CI automation | #23, #44 | Integrated `ruff`, `mypy`, layer boundaries, and synthetic tier tests. |
| Host profiling | #73 | Measured process startup and import times; confirmed runner does not load Torch. |

---

## 3. Next Actions

| ID | Status | Dependencies | Source | Description & Acceptance Criteria |
|---|---|---|---|---|
| `INFRA-ACT-05` | Local-ready / cross-host disabled | Two-host NFS check | 00-resource-claims.md (R0) | **Atomic resource claims**: local claim ownership, GPU UUID keying, pre-launch recheck, device isolation, conservative stale-owner handling, declared CPU allowance, child process-group lifecycle, and monitor integration are implemented. Acceptance still requires two real hosts contending through the shared claim path and lifecycle verification before enabling multi-host deployment. |
| `INFRA-ACT-04` | Complete | None | PR #82 | Quiet monitor and approved scheduling/stall/restart/budget regression tests implemented. Use the workflow for new jobs; transport acceptance is verified, but automated idle wakeup timing is not a guaranteed service. |
| `INFRA-ACT-01` | Ready | None | #68, #73 | **Repair worktree cleanup helper**: Refactor `scripts/cleanup_merged_worktrees.sh` to halt on any git refusal, verify clean working tree against `origin/main`, remove the `rm -rf` fallback, and drop remote pruning. Acceptance: Script refuses to delete unmerged or dirty worktrees and passes unit test. |
| `INFRA-ACT-02` | Ready | None | Host rules | **Host-local cache enforcement**: Configure local caching (the checkout-specific cache paths in `docs/setup.md`) in CI and runner scripts. Acceptance: Zero mypy cache files written to NFS home. |
| `INFRA-ACT-03` | Closed / Archived (D1/D6) | None | `plans/DEFERRED.md` | **Static typing and test pollution**: Mypy passes cleanly across all 350 source files; tests isolated from global environment. |

### PR #73 review follow-up (2026-09-08)

Moved closeout procedures into the session skill and verification rationale into setup; corrected pytest cache configuration and the README output path that bypassed the data root. Replaced nonexistent area evidence commit hashes with verified PR merge references. Repaired the audit brief recovery row, which stored a commit abbreviation instead of a blob hash. Reconciled stale assignment state and qualified unverified codec claims. Gate B now distinguishes per-video encoding from shared-model training and source generalization; the existing six-match validator remains authoritative. Validation: relative-link and recovery-blob audit, documented CLI inspection, skill frontmatter validation, and diff whitespace checks; CI results are recorded in the follow-up PR. Next infrastructure action remains `INFRA-ACT-01`; this documentation review does not repair or authorize the unsafe cleanup helper.

### Worktree retirement — 2026-09-11

User approved removal of six clean worktrees; removed without force or the unsafe
helper. The following remote tags preserve their tips under `archive/20260911/`:

| Removed worktree under `/tmp/` | Archive tag suffix | Preservation evidence |
|---|---|---|
| `pointstream-pr88-audit` | `pr-88` | `d1d24b7` ancestor of PR #88 integrated head |
| `pointstream-probe-framework` | `codex/probe-framework` | Tree identical to merged `dc4a0cd` (#94) |
| `pointstream-recovery` | `antigravity/overnight-recovery` | Tree identical to merged `2b7c2b0` (#88) |
| `pointstream-submission-dispatch` | `pr-90` | Tree identical to merged `221aa14` (#90) |
| `pointstream-worker-b` | `antigravity/recovery-worker-b-verdict` | `ea4fee8` ancestor of preserved #88 head |
| `pointstream-worker-c` | `antigravity/recovery-worker-c-generator` | `1992878` ancestor of preserved #88 head |

Tracked and untracked state was clean; ignored output directories contained no
files. Cache directories were disposable. All local and remote branches remain.
The larger local-branch deletion proposal was rejected by automatic approval
review as beyond the six-worktree approval; it was not executed.

Retain `/tmp/pointstream-worker-a`: `artifacts/residual_smoke.json` is modified.
Retain `/tmp/pointstream-wave1-a`, `-b`, `-c` until #93 is repaired/integrated;
their commits are ancestors of #93, but that PR is still open. Retain
`/tmp/pointstream-pr92` as a possibly paused Cursor checkout; after #92 updates,
fetch and reconcile it before resuming. No process observed in this sandbox
proves another host/session idle. `INFRA-ACT-01` remains open.

### Handoff cleanup — 2026-09-12

With explicit user approval, retired all nine remaining stale worktrees and 32
local non-main branches after remotely archiving every tip. Preserved the dirty
worker-a residual-smoke artifact in archive-only commit `26a7555`; it is not new
mainline evidence. Exact refs, preservation proofs and removed paths are in
[cleanup inventory](../history/cleanup-2026-09-12.json). No remote branch, dataset,
experiment artifact or paper file was deleted. Only main and the current handoff
checkout remained immediately after this cleanup. Do not use the unsafe cleanup
helper; `INFRA-ACT-01` is still open.
