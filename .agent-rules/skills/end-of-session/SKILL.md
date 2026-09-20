---
name: end-of-session
description: Close out a coding session — surface knowledge candidates on project and platform axes, re-check repo/job state, optionally hand off, commit (invoke = consent), then ask before push. Use when the user says end/close/wrap up session, accepts a context or Stop nudge, or needs a clean boundary before a new task.
---

# End of session

Close-out orchestrator. Not gated on “context is full” (that is already too
late). Progressive context hooks may *nudge* toward this skill; they never
auto-run it.

## Procedure (in order)

### 1. State check

Re-verify (SessionStart output is stale):

- `git status -sb`, branch, ahead/behind, dirty files
- other worktrees (`git worktree list`): dirty vs merged into `origin/main` or `origin/master` vs unmerged. List only; do not remove
- unmerged local branches vs that origin default (`git log --oneline origin/main..` or `origin/master..`; do not delete)
- if this tree is dirty, do not `git checkout` another branch here — add a worktree
- background / GPU jobs that will outlive this session

### 2. Surface on both axes

*Consider* project and platform independently. Write a candidate **only when
there is something to surface**:

- Project → this checkout's `.agent-rules/candidates/open/project/`
- Platform → this checkout's `.agent-rules/candidates/open/platform/`

Follow the schema in `candidates/README.md`. Do not create “nothing to
surface” files. A one-line verbal note (“nothing on either axis”) is enough
if useful.

**Before writing, check whether this already happened once.** Run
`python3 <config>/.agent-rules/scripts/lessons.py match "<your one-line
summary>"`. Scores are a recall aid — a restatement in other words scores
zero, so read the printed list too.

- Earlier entry found → do **not** file a new candidate. Run `lessons.py
  record <id> --project <path> --platform <name>`, fill the appended
  occurrence stub (what happened this time, and why the earlier entry did
  not prevent it), and name the delivery you would pick. Twice is a rule.
- Nothing matches → new candidate, **with `keywords:`** so the next session
  can find it.

### 3. Other close-out checks (advisory)

- If the project has outputs + paper dirs (or a wired paper-sync hook),
  re-check whether outputs are newer than the paper’s last commit; *mention*
  `update-paper` / `results-report` when relevant — do **not** run them.
- Unfinished user questions; long jobs still running.
- If cwd is coding-agent-config and `candidates/open/` is non-empty, remind
  about `evaluate-candidates` — do not auto-evaluate on every project close.
- Mention `test-design` / `reviewer-response` only if clearly in play.

### 4. Handoff when needed

If work remains, or the user accepted a context/task nudge aimed at transfer:
run the **handoff** skill procedure as a step (write/update `HANDOFF.md`).
Clean close with nothing to transfer → skip `HANDOFF.md`. Do not wait for
auto-compact. Handoff alone remains valid mid-session without this skill.

### 5. Commit

**Invoking this skill is consent to commit.** Stage relevant work + any new
candidate / handoff files; commit with a clear message. Do **not** push yet.

### 6. Push

Show `git status` / ahead count and **ask once**. Push only after the user
confirms.

### 7. Summary

Tell the user what was committed, whether candidates were filed, and which
platforms (if any) have new `pending-verification` items.
