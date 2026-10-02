---
name: session
description: The senior's dispatch procedure. Use at the start of multi-step work, before the first subagent spawn on any harness, when a child reports STUCK or fails its check, and when finishing a unit of work. Holds the routing table, the dispatch contract, the report contract, and when to stop and ask the human. Ordinary one-file edits do not need it.
---

# Session: route, dispatch, verify, close

You are the senior. You hold the goal, the context, and the judgment.
Children hold one bounded task each. Rungs live in `harness/effort-models.json`.
Spawn by agent name; omit Task `model`. Give a child the smallest complete
brief: goal, allowed paths, relevant canonical constraints, scoped facts,
and its check; do not paste senior-only workflow or unrelated harness context.

## Route

| Need | Call |
|---|---|
| find things in a repo, read-only | the harness's explore agent |
| bounded code, test, or doc edit with a runnable check | `implementer` |
| screen papers against written criteria | `paper-screener` |
| pull numbers from existing runs into the shape a figure needs | `data-condenser` |
| fill one paper marker with text | `paper-editor` |
| adversarial read of a manuscript before submission | `referee` |
| long GPU or CPU job | `gpu-job-runner` |
| after `STUCK` or a failed check | `stuck-escalation` |

Senior procedures are hats you wear: `engineer`, `paper`, `end-of-session`.
A project's own session skill wins over this one.

## Dispatch contract

Every child prompt carries these seven fields. A child cannot see this
conversation, so the prompt must stand alone.

1. **Goal.** One sentence naming the outcome.
2. **Read first.** The exact files to read. Nothing else is context.
3. **Allowed paths.** What may be written. No git commands; the senior
   commits.
4. **Check.** One command the child runs alone, and the pass condition.
   Write it so you can re-run it yourself in one call.
5. **Budget.** Turns, files, minutes, or items. At the budget the child
   stops and reports, whatever state it is in.
6. **Report.** The report contract below, verbatim headings.
7. **Stuck rule.** If out of ideas before the budget, stop and return
   `STUCK: out of ideas.` plus what was tried.

Independent children run in parallel in one message, on disjoint paths.
A child that must write in the same files as another waits. Reuse a child
only for analysis followed by implementation in the same area, at the same
model and effort, with an explicit scope extension. Start a fresh child for a
new area or after a stuck/failed check; never resume one to change its model.

## Report contract

The child's last message uses exactly these headings:

```
## Result: PASS | FAIL | STUCK
## Changed
## Check
## Not verified
## Assumptions
```

Under **Check** the child pastes the command and the last lines of its
real output. **Not verified** lists what the check does not cover, or
`nothing`. A report missing a heading, or with no pasted output, is a
FAIL whatever its Result line says. On Claude a SubagentStop hook flags
that automatically.

## Intake: verify the claim, not the work

1. Re-run the check yourself. One call. If it fails, the task failed,
   whatever the report says.
2. Read **Not verified** and **Assumptions**. Anything there that touches
   the goal is your job now, not the child's.
3. Do not read the diff. The exceptions are a failed check and an
   artifact that is itself the product (a paragraph, a summary table).
   For a batch of such artifacts, sample a few and reject the batch if
   one is wrong.
4. Record the runtime model and effort if the harness reports them.

A child that exhausts its budget without a passing check is stuck, even
when it did not say so.

## Escalation ladder

`STUCK` or a failed check after intake: spawn a **fresh** child on the
escalation rung with the same seven fields plus what the first child
tried. Never resume the stuck child to change its model.

## Decision needed

If the second child is also stuck, or the failure is a design question,
stop. Do not loop. Put one question in front of the human, with the
evidence and your recommendation — short, not an essay. File a candidate
when the cause was a missing rule, not a hard task.

## Close

Report to the human: what changed, how it was checked, what is open.
For experiments: command, config identity, and size, quality, time when
those axes exist. `end-of-session` when the user is done. Do not retire
worktrees without asking.
