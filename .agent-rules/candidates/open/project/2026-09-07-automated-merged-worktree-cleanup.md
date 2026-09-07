---
id: 2026-09-07-automated-merged-worktree-cleanup
created: 2026-09-07
source_platform: antigravity
source_project: /home/itec/emanuele/pointstream
axis: project
status: open
summary: Automate safe post-merge cleanup of linked git worktrees whose commits are fully merged into origin/main across all harnesses and projects
suggested_action: lift to foundation host-wide tools via scripts/guardlib/worktree_cleanup.py, scripts/clean-merged-worktrees.py, and global git core.hooksPath
verify_platforms: [cursor, claude, codex, antigravity]
---

## Context and Problem

`AGENTS.md` (Plan mode: parallel-agent waves) establishes:
> "A wave is finished when its worktrees are gone, not when its PRs merge. A
> worktree outliving its branch is a silent-revert hazard: a resumed session
> re-applies its version of a file a later session already changed, and nothing
> about the output looks wrong. Remove per the git rules above, and ask the user
> first — a session may be paused in one."

Candidate `2026-08-31-clean-up-a-wave-when-it-merges` codified this rule, but cleanup remained manual.
In practice:
1. Subagents and multi-agent sessions across Cursor, Claude Code, Codex, and Antigravity frequently leave clean, merged worktrees behind after PRs merge (e.g. 4 stale worktrees found in `~/.claude/worktrees/` and `/var/tmp/`).
2. When a branch is checked out in a linked worktree, `git branch -d <branch>` fails (`error: Cannot delete branch ... checked out at ...`), leaving local branches and worktrees orphaned.
3. Over time, these accumulate, creating silent-revert hazards and wasting inodes.

## Solution

A tool-agnostic, fail-safe cleanup system implemented at the Git and host level:

1. **Policy core (`scripts/guardlib/worktree_cleanup.py`)**:
   - Compares commit ancestry strictly against `origin/main` (or `origin/master`).
   - **Hard invariant**: Refuses to touch any worktree with unstaged, staged, or untracked changes (`git status --porcelain`).
   - **Hard invariant**: Never touches worktrees with unmerged commits (`git log origin/main..<branch>` is non-empty).
   - Never removes the primary repository checkout root.
   - For 100% merged, clean worktrees: safely executes `git worktree remove`, `git branch -d` (safe delete only), `git worktree prune`, and `git remote prune origin`.

2. **Host-wide CLI entrypoint (`scripts/clean-merged-worktrees.py`)**:
   - Symlinked to `~/bin/git-clean-merged-worktrees`.
   - Accessible from any shell, IDE, or agent across all projects as native `git clean-merged-worktrees`.

3. **Global Git `post-merge` hook (`git-hooks/post-merge`)**:
   - Configured host-wide via `git config --global core.hooksPath ~/.agent-rules/git-hooks`.
   - Automatically executes whenever `git merge`, `git pull`, or `gh pr merge` completes in any repository on this host, regardless of which harness (Cursor, Claude, Codex, Antigravity, VS Code, or human) executed the merge.
   - Automatically chains to any repo-local `.git/hooks/post-merge` so project-specific hooks are preserved.
