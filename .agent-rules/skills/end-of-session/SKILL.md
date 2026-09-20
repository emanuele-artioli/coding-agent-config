---
name: end-of-session
description: Close out a coding session — surface knowledge candidates, re-check repo/job state, write HANDOFF.md when work remains, commit (invoke = consent), and ask before push. Use when the user says end/close/wrap up session, or needs a clean boundary before a new task.
---

# End of session

Close-out hat after skill `session`. A verified adapter may create a
deterministic receipt at an explicit completion boundary, but it never
asks an LLM to infer a lesson or commits on its own.

## Procedure (in order)

### 1. State check

Re-verify (SessionStart output is stale):

- `git status -sb`, branch, ahead/behind, dirty files
- other worktrees (`git worktree list`): dirty vs merged into `origin/main`
  or `origin/master` vs unmerged. List only; do not remove
- unmerged local branches vs that origin default (`git log --oneline
  origin/main..` or `origin/master..`; do not delete)
- if this tree is dirty, do not `git checkout` another branch here — add a
  worktree
- background / GPU jobs that will outlive this session

### 2. Surface lessons at file time

Consider project and platform independently. Write a candidate only when
there is something to surface.

Before writing, run
`python3 <config>/.agent-rules/scripts/lessons.py match "<your one-line
summary>"`. Scores are a recall aid — a restatement in other words scores
zero, so read the printed list too.

- First time (nothing matches) → file under `candidates/open/` (`project/`
  or `platform/`), with `keywords:`, per `candidates/README.md`. Do not
  create “nothing to surface” files. A one-line verbal note is enough if
  there is nothing to file.
- Second time (an earlier entry matches) → promote into `AGENTS.md` or a
  hook and **remove** the candidate. Twice is a rule. Note what happened
  this time and why the earlier entry did not prevent it.

Use `scripts/closeout.py` for the boundary receipt and event-id bookkeeping;
a replay of the same boundary must be a no-op, and a close with no lesson
is still a valid receipt.

### 3. Other close-out checks (advisory)

- If the project has outputs + paper dirs (or a wired paper-sync hook),
  re-check whether outputs are newer than the paper’s last commit; mention
  skill `paper` when relevant — do not run it from close-out.
- Unfinished user questions; long jobs still running.

### 4. If work remains, write HANDOFF.md

If work remains, write `HANDOFF.md` at the repo root (or
`HANDOFF-<area>.md` when several repos are in play). Clean close with
nothing to transfer → skip it. Do not wait for auto-compact.

Required sections, short:

1. **Summary** — one paragraph of the overall task.
2. **Verified state** — branch, last check you re-ran, done vs in progress.
3. **What's running** — jobs that will outlive this session, and how to
   check them. Say whether killing them is safe.
4. **Open questions** — actual questions, not TBD.
5. **Next steps** — first, second, third.

Tell the user where the file is and what to do first.

### 5. Commit

**Invoking this skill is consent to commit.** Stage relevant work + any new
candidate / `HANDOFF.md` files; commit with a clear message. Do not push yet.

### 6. Push

Show `git status` / ahead count. **Ask before push** unless the session
already authorized it. Invoking close-out does not add new authority.

### 7. Summary

Tell the user what was committed, whether candidates were filed or promoted,
and what is still open.
