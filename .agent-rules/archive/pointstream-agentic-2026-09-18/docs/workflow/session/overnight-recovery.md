> Superseded for new work after PR #88: use [submission search](submission-search.md). This file records the original recovery assignment.

# Overnight recovery: residual fidelity, credible evaluation, generator readiness

Execute this assignment when the user supplies this file as a prompt. Budget: eight hours from launch, including validation and reporting. Parallel subagents in separate worktrees (or isolated workspaces) can be dispatched across harnesses (Antigravity with `invoke_subagent`, Cursor with `Task`, Claude Code with `Agent`, or Codex), provided they are configured to use weaker/cheaper models for subagent lanes (such as Gemini Flash/Flash-Lite on Antigravity, Composer on Cursor, Haiku/Sonnet on Claude) to conserve token budgets; a harness without subagent support or running sequentially can execute lanes A, B, then C in order. This is development work, not a Gate B confirmation campaign.

## Starting point and authority

Read AGENTS.md, PLAN.md, docs/setup.md and the session workflow. Evidence baseline: PR #86, commit a3a2570; use current origin/main including this dispatch and reconcile later changes before editing. The main checkout was observed with a damaged Git index on 2026-09-09: use a clean worktree and codex/ branch; do not reset or repair another session's checkout. Read the corresponding harness rules.

The user authorizes implementation, the behavioral tests listed in the worker briefs, bounded development experiments and a bounded training pilot under the conditions below. State the selected test cases before writing them, then proceed without another confirmation. Commit, push, create PRs and merge after required checks under the host rules. Do not remove possibly occupied worktrees without permission. Do not launch a multi-day training campaign or spend confirmation sources to tune the method.

## Outcome and dependencies

The full codec, including residual correction and a useful generator if one exists, is the candidate that eventually needs competitive evidence. Generation-free and residual-free variants are controls; they do not each need to win before development can proceed.

1. Preflight: inspect active jobs, available hardware, dependencies and source exposure. Create a development manifest from already exposed material. Agree interfaces and ownership before dispatching workers.
2. In parallel, dispatch [A: residual and client transport](repair-residual-transport.md), [B: anchors and verdict integrity](anchor-and-verdict.md), and [C: generator readiness](generator-readiness.md). Reserve shared contracts/configuration changes and area/status documents for the coordinator; workers request interface changes through the coordinator. Give each worker its own worktree. Only one GPU-heavy job may run at a time; respect existing jobs and never kill unrelated processes.
3. Integrate A and B, run the required setup checks and native smoke tests. Then measure residual-off/on curves against both AV1 and VVC. Integrate C's working candidate only after the transport and measurement checks pass. Run the generation off/on × residual off/on diagnostic matrix where supported, with a pasted-reference control. Reject unsupported corners explicitly rather than scoring source-frame fallbacks.
4. A training pilot may proceed without a generator-free win, but only after a real checkpoint loads, native temporal inference works, and the current runner evaluates it correctly. Limit training to two hours and the remaining overall budget. Compare before/after on disjoint development validation scenes; preserve untouched confirmation sources. Account for fitting time and any transmitted video-specific weights. Do not optimize only isolated crop realism.
5. Reserve the final 30 minutes for checks, durable progress, PRs and a morning digest. If repairs take the night, deliver tested repairs and an exact resumable command; do not manufacture an experimental conclusion to fill the schedule.

## Scientific and runtime requirements

Before reading metrics or launching runs, record plausible two-sided quality, byte and runtime bounds with rationale. Calibrate metrics on identical, mildly degraded, severely degraded and unrelated inputs; include null controls. Score the actual standalone decoded frames. Count every transmitted byte, including residual, masks, headers, metadata and container overhead; distinguish shared installed model assumptions from per-video payload. Measure encoding, generation, rescaling and client decoding time.

Compare measured curves at common display resolution and matched quality/rate with no extrapolation. Include a high-fidelity residual-on ladder, not only the old starved C0–C3 corner. Predeclare quality targets and anchor settings before inspecting candidate results. Native-resolution and resolution-adaptive AV1/VVC arms stay separately labeled. Report per-source results and uncertainty; frames are not independent samples. No observed advantage is guaranteed, and no pilot flag certifies Gate B.

Use docs/workflow/long-jobs.md for detached jobs: ten-minute progress logs, hourly checkpoints, verified resume and an eight-hour wall-clock cap. Verify that a supervisor supports the actual command; do not assume its existing codec CLI exposes new arms. Reporting cadence is supplied: quiet during ordinary progress, a final eight-hour digest, and actionable failure notification through the current harness if supported. Do not create a periodic agent polling loop. Compare completed entries with submitted entries; exit zero alone is insufficient.

Record exact code/config/model hashes, seeds, source/frame manifests, native codec paths/builds/presets, environment and commands. Data and outputs stay outside the code tree. Update codec, evaluation and generation areas plus PLAN; change gate status only with its actual evidence. Paper changes require its separate repository and instructions, and should describe verified implementation or evidence, not predicted gains.

Morning digest: merged PRs and remaining branches, tests, runnable commands, artifact paths, what residual fidelity now supports, which generator actually ran, total rate/quality/runtime results with controls, unresolved blockers and the next bounded experiment. Keep Gate A open and Gate B incomplete unless their full documented criteria really become satisfied.
