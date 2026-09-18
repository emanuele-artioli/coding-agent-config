---
name: session
description: Route a task, dispatch a bounded child, or report/close work when no project session skill exists. Use at the start of multi-step work, before spawning subagents, and when finishing a unit of work. Ordinary one-file edits do not need it.
---

# Session (no project files required)

If the project has its own session skill, follow that instead.

## Dispatch

1. Extract the outcome and constraints.
2. Read what exists: README, `pyproject.toml`, tests. If `PLAN.md` or
   `docs/areas/` is present, use the one relevant area. Do not invent a
   project docs tree.
3. Child prompt (when you spawn): goal, allowed paths, success check the
   child can run alone, stuck rule (`STUCK: out of ideas.`). Worktree and
   branch if the child writes in parallel.
4. Parent keeps integration and hard judgment. Children report short.

Reuse existing evidence before new runs. A folder name or a newer patch
does not certify old numbers. Missing timing is not a reason to rerun a
finished rate/quality measurement. Smallest probe that fills the gap.
`verify-measurement` before claiming a ranking. `model-routing` before
the first spawn. Check the child's reported model before accepting.
Long jobs: checkpoints and progress lines, not a periodic agent poll.

## Report

What changed, how you checked it, what is still open. For experiments:
command, config identity, size/quality/time if those axes exist.

## Close

`end-of-session` when the user is done or the session should hand off.
Do not retire worktrees without asking.
