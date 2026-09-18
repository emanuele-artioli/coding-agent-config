---
name: pointstream-session
description: Route a PointStream task, prepare a scoped dispatch, or report/close a completed work session.
---

# PointStream Session Workflow

This skill standardizes task routing, execution reporting, and clean session boundaries across all AI coding assistants (Codex, Claude, Cursor, and VS Code + Antigravity).

---

## 1. Routing

Use the user's chosen harness and model. Otherwise select by task complexity and available resources; no harness has an exclusive scientific or implementation role. Ordinary edits need no dispatch ceremony.

### Harness capabilities & parallel subagents
Parallel workstreams and wave dispatches are supported across all coding harnesses on this host (not only Cursor):
- **VS Code + Antigravity**: Dispatches parallel subagents via `invoke_subagent`
  with isolated workspaces (`Workspace: "branch"` or `"share"`). PointStream
  work uses `.agents/agents/`: `budget-default` (Gemini 3.8 Flash / medium)
  then `expert-retry` (Flash / high) after `STUCK` or a failed check. The
  parent keeps integration and hard judgment.
- **Cursor**: Dispatches parallel subagents via `Task`. PointStream work uses
  `.cursor/agents/`: `budget-default` (Grok 4.6 medium) then `expert-retry`
  (Grok 4.6 high). Spawn by `subagent_type` and omit `model`. Trial profiles
  stay in [subagent-ladder-trial.md](subagent-ladder-trial.md).
- **Claude Code**: Dispatches subagents via `Agent`/`Task` with `opus`.
- **Codex**: `.codex/config.toml` `budget_default` (Luna extra-high) then
  `expert_retry` (Astra low) after stuck/failed check. Trial profiles remain
  trial-only.

When dispatching multi-lane workstreams, any of these harnesses can run independent lanes concurrently using weaker-model subagents; sequential execution (running lanes in order within a single session) remains the standard fallback when subagents are not used.

## 2. Modes of Operation

### Mode A: Route & Dispatch
When initiating or handing off a task:
1. **Extract Outcome**: Identify the requested goal, explicit constraints, and potential ambiguity.
2. **Consult Area Context**: Read [PLAN.md](../../../PLAN.md) and the single relevant area document in `docs/areas/`.
3. **Formulate Dispatch**:
   - **Objective & Area**: Name the functional area and stable action ID (e.g. `CODEC-ACT-01`).
   - **Revisions**: Pinned code commit and evidence baseline.
   - **Scope**: Allowed files, worktree path, and branch name.
   - **Inputs & Outputs**: Explicit configs, manifests, or interfaces.
   - **Acceptance Criteria**: Concrete commands and verification gates (see [setup verification](../../setup.md#4-verification)).
   - **Bounds & Controls**: Pre-run bounds for experiment runs; null controls.

For new research work, use [hypothesis-driven experiment design](../experiment-design.md).
Before scheduling any new run, inspect existing result indexes, folder classifications,
manifests, saved decodes and prior validity decisions. Record the exact question,
matching artifact IDs, what can be reused/rescored, and the remaining evidence gap
in the decision card. Check actual configs rather than filenames. Missing timing
alone does not require repeating a rate/quality experiment: link statistically
adequate representative timing for compatible workloads/hardware, or profile
only the missing stratum. Never upgrade old evidence merely because code was
repaired. Launch only the smallest probe that fills the documented gap. The
[older submission dispatch](submission-search.md) is historical repair context;
do not automatically rerun its waves or budget.

### Long jobs

Use [the long-job workflow](../long-jobs.md). Use an already supplied reporting
cadence; otherwise ask once. The September evaluation campaign uses actionable
events, without periodic chat digests. Delegate health checks and ten-minute
logging to the script;
wake the agent only for requested digests or actionable events. Use bounded
pilot/confirmation gates before expensive codec stages. Do not create a periodic
agent polling loop. Training subset stages remain a protocol until its evaluator
is restored.

### Mode B: Execute & Report
When executing work and reporting results:
- **For Documentation & Refactoring Tasks**:
  - Changed files and rationale.
  - Verification appropriate to the changed files; distinguish completed checks from unavailable checks.
  - Area document updates and next actions.
- **For Research & Experiment Tasks**:
  - Exact command, configuration manifest, and input sequence.
  - Encoder binaries, versions, and presets.
  - **Three-axis metrics**: Size (bytes/bitrate), quality (PSNR, SSIM, VMAF, LPIPS), and execution runtime (encode/decode FPS).
  - Pre-run bounds check: Report each alarm and its resolution or unresolved status; report uncertainty at the independent source level.
  - Explicit citable conclusion (label Gate A results exploratory; scope confirmed claims to the Gate B protocol).

### Mode C: Close & Continue
When completing a session:
1. **Record Result**: For completed repository work, commit onto the task branch, push, and open/update a PR with findings and validation. Keep one PR per independently revertible change, not per reply. Follow existing user authorization and any explicitly invoked closeout skill.
2. **Update Area State**: Update the owning area document in `docs/areas/` with current status and mark action completed/advanced.
3. **Check CI**: Watch GitHub Actions run via `gh run watch <id>` and inspect `gh run view <id> --log-failed` if failures occur.
4. **Clean Boundary**:
   - If work is finished: fetch fresh `origin/main`, verify merge ancestry plus unique commits/diff and clean tracked/untracked status before considering retirement. Ask before removing a worktree that may host a paused session. Never force removal or bypass Git refusal with `rm -rf`. Do not run `scripts/cleanup_merged_worktrees.sh` (`INFRA-ACT-01`). Host `git-clean-merged-worktrees` is allowed only on merged, clean trees.
   - If work remains: provide a concise continuation prompt in the chat response. State the unresolved decision and resume command. Do not create a standalone completed-session report or permanent root handoff document; keep decisions in the area and details in the PR.
