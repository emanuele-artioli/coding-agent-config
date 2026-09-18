# W3 — Multi-harness git, branches, worktrees

Read `README.md` in this folder first. Do not open other W*.md files.

## Job

Several harnesses work the same machine and the same repos at once. They
step on each other: cannot checkout because of pending changes, worktrees
and branches go stale, unmerged work sits unnoticed. Write the **practice**
and check whether the **tools we already have** cover it, then fill the
real gap only.

## What is already true (do not re-derive from scratch)

Host `AGENTS.md`:

- Work on a branch; reversible vs irreversible.
- Isolation needs a **worktree and a branch**, not a branch in a shared
  checkout. Two agents in one checkout share HEAD.
- A wave is finished when its worktrees are gone.
- Ask the user before removing a worktree that might be a paused session.
- Compare against `origin/main`, not a stale local `main`.
- Read a branch before deleting; tag `archive/<branch>` if not empty.

Already built (2026-09-07):

- `scripts/guardlib/worktree_cleanup.py`
- `scripts/clean-merged-worktrees.py` → `git-clean-merged-worktrees`
- global `core.hooksPath` `post-merge` cleanup of **clean, fully merged**
  worktrees
- PointStream `AGENTS.md` currently **forbids**
  `scripts/cleanup_merged_worktrees.sh` until `INFRA-ACT-01` (deletion
  fallback can discard uncommitted work). Host cleanup claims it refuses
  dirty trees. W3 must reconcile that warning with the host tool, not
  ignore it.

## Problems the merge-cleanup tool does **not** solve

1. Two live sessions, one checkout: dirty tree, checkout blocked.
2. Two worktrees on the **same** branch (git usually refuses; agents try
   anyway).
3. Unmerged branches nobody is looking at (cleanup will not touch them;
   they need listing, not deletion).
4. Coordination docs that should have been on the shared branch but lived
   only in a worktree.

## Work to do

1. Inventory live worktrees on this host for coding-agent-config and
   PointStream (`git worktree list`, including `/var/tmp` and
   `~/.claude/worktrees/` if present). Report dirty vs merged vs stale.
   Do not delete anything without asking.
2. Read the cleanup policy and PointStream `INFRA-ACT-01` / area
   infrastructure notes. Either close the conflict (host tool is safe and
   PointStream should point at it) or document why PointStream must keep
   the ban.
3. Propose a **small** practice, highest delivery that works:
   - Hook/advisory if an agent is about to `git checkout` a dirty tree or
     open the primary checkout for a second harness? Only if you can match
     it reliably.
   - Else a short host `AGENTS.md` addition (isolation rule already exists
     — do not duplicate; add only the missing operational step).
   - A session skill step in `end-of-session` (list this repo’s extra
     worktrees / unmerged branches) is better than another always-on
     essay if the failure is “forgot to clean up”.
4. Best practice to recommend (refine with evidence from step 1):

   One live session → one worktree → one branch. The project’s primary
   checkout is for the human / a single orchestrator, not for parallel
   children. Children use `git worktree add` (or Antigravity
   `Workspace: "branch"`). Never share a dirty tree. Unmerged work is
   listed at close-out. Merged+clean worktrees are the existing CLI, not
   `git worktree remove --force`.

## Touch these (only if the inventory justifies it)

- `AGENTS.md` plan-mode / git isolation — one or two sentences max
- `end-of-session` skill — optional worktree/branch checklist
- PointStream cleanup ban: **file a note for W5**, do not edit PointStream
  unless the only fix is a one-line pointer and W5 is not started; prefer
  leaving W5 the edit
- Cleanup scripts: bugfix only if you find a dirty-tree deletion path

## Do not

- Force-delete worktrees
- Redesign model routing
- Treat “many harnesses” as a reason to serialize all work onto one branch
  without worktrees

## Done when

A written recommendation that names the failure modes you actually saw on
disk, maps each to an existing tool or a small new step, and does not add
a second source of truth for git safety.
