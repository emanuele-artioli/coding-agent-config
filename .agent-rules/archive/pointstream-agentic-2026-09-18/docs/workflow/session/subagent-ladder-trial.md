# Demo subagent-ladder trial

Run this trial only for real, low-risk tasks in `demo/` that change the public
demo's documentation, static report, or small non-GPU tooling. Do not use it
for the PointStream codec, evaluation campaign, paper claims, GPU jobs,
generated benchmark outputs, merges, or shared contracts.

## Goal and duration

Compare two escalation ladders for the next 24 completed eligible demo cards.
Review after two days if at least 20 cards completed; otherwise report the
sample as insufficient and continue until 20 cards arise naturally. Stop early
only if an arm causes material damage. Never invent work merely to fill the
sample.

### Arm A — picker-style

Codex (three rungs):

1. `trial_a_start`: Terra / low
2. `trial_a_retry_1`: Sol / low
3. `trial_a_retry_2`: Sol / medium

Cursor (two rungs; Grok effort is the model slug):

1. `trial-a-start`: Grok 4.6 low
2. `trial-a-retry`: Grok 4.6 high

Antigravity (two rungs):

1. `trial-a-start`: Gemini 3.8 Flash / low
2. `trial-a-retry`: Gemini 3.8 Flash / high

### Arm B — cost-first

Codex (three rungs):

1. `budget_default`: Luna / medium
2. `balanced_retry`: Terra / medium
3. `expert_retry`: Sol / medium

Cursor (two rungs):

1. `budget-default`: Composer 2.5
2. `expert-retry`: Grok 4.6 low

Antigravity (two rungs):

1. `budget-default`: Gemini 3.8 Flash / low
2. `expert-retry`: Gemini 3.8 Flash / high

## Automatic session procedure

When a session receives an eligible demo task with a concrete acceptance check:

1. Create `docs/history/subagent-ladder-trial/<card-id>.md` before dispatch.
   Use a stable card ID: `YYYYMMDD-short-task-name`.
2. Count completed records by arm. Choose the arm with fewer completions. If
   tied, draw A or B with `shuf -n 1 -e A B` and record the draw. Do not change
   the selected arm after seeing its result.
3. State the task, allowed files, acceptance check, arm, and first profile in
   the record. Dispatch a fresh child with that profile.
4. Accept a result only when its predeclared check passes. On failure, record
   the failure and escalate once within the selected arm only if the retry is
   safe and the same task remains well-scoped. Otherwise mark the card failed.
5. Add the final result before closing the session. The coordinator integrates
   successful work and reports the record path.

The coordinator must verify child runtime metadata. On Codex: model, effort,
and permission mode. On Cursor: the model actually used (Composer vs
`cursor-grok-4.6-low` / `-high`); there is no separate effort field. On
Antigravity: model (Flash) and effort tier (low vs high). A missing or
mismatched field invalidates that attempt.

## Card record

Use this format; one record per card prevents concurrent sessions from editing a
shared ledger.

```markdown
# <card-id>

- Started/completed: <UTC timestamps>
- Demo task and allowed files: <actual task>
- Acceptance check: `<command>` or <objective review condition>
- Arm / allocation: A|B / <count-based or tie draw>
- Attempts: <profile, model, effort or slug, pass/fail, elapsed time for each>
- Final result: pass | fail | invalid
- Coordinator integration time: <minutes>
- Evidence: <commit, command output, or review notes>
- Escalation reason: <none or concrete failed check>
```

At the end, compare final pass rate, elapsed time, escalation rate, and total
model usage or cost where the harness exposes it. Include coordinator review
time. Keep the cost-first ladder for PointStream only when it preserves final
acceptance and does not create unacceptable integration cost.
