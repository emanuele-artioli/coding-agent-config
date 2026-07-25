# Repo hygiene check

Inspect the current git repository the way a careful human would before
deleting anything or assuming work is lost:

1. Print `git status -sb` and `git branch -vv`.
2. List other worktrees with `git worktree list`.
3. If there are unpushed commits or other worktrees, say so plainly — do not
   delete a branch or worktree without reading it first (`git log main..<branch>`
   and `git diff main...<branch> --stat`). Tag non-empty branches with
   `archive/<branch>` before deleting.
4. Summarize in a few lines: current branch, dirty vs clean, ahead/behind,
   other worktrees worth knowing about.

Do not modify the repository. Report only.
