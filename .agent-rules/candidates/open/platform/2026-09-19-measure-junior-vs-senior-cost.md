---
id: 2026-09-19-measure-junior-vs-senior-cost
created: 2026-09-19
source_platform: claude
source_project: .
axis: platform
status: open
summary: Measure senior-plus-juniors against parallel senior sessions on cost per accepted task
occurrences: 1
keywords: [junior, senior, cost, context, dispatch, measurement, worktree]
suggested_action: run the paired experiment, then confirm or revise the dispatch paragraph in AGENTS.md
verify_platforms: [claude]
---

The dispatch rule added to `AGENTS.md` on 2026-09-19 rests on a cost model,
not on a measurement. Settle it.

**Metric.** Cost per accepted task: tokens from dispatch until the senior's
own re-run of the check passes, rework included. Record wall clock and
first-time pass rate beside it.

**Arms.** A = senior plus juniors in one worktree. B = one senior session per
task, each in its own worktree and branch.

**Design.** Pair the tasks, each run in both arms, order alternated. Eight to
ten pairs settle cost: the predicted gap is about three times and the spread
per child is small. Quality cannot be settled at that size, since separating a
0.70 from a 0.90 first-time pass rate needs about sixty tasks per arm. Treat
quality as an alarm only, meaning a junior arm failing checks it should pass.

**Two facts to settle first.** The harness per-child token figure looks like
the child's final context, not summed traffic: a 0-tool probe reported 41.8k
while a 14-tool child reported 61.4k, where summed traffic would exceed 600k.
The whole model divides by that. And Claude subagent effort: an `effort:`
frontmatter field is documented, yet the same docs say subagents inherit the
main conversation's thinking configuration and have no per-subagent setting.
Drive both and measure which wins; `effort-models.json` marks the Claude rungs
`verified: false` for this reason.
