---
name: escalate
description: The senior's procedure for putting one decision in front of the human. Use when a second child is stuck, when a check still fails after the escalation rung, when a design or scope question the senior cannot settle appears, or when the budget the senior would need is larger than the one given. Produces a short fixed-shape chat reply with one question, the evidence behind it, and a recommendation. Not a handoff document.
---

# Escalating one decision to the human

You are the senior and you have run out of authority, not out of
context. The reader has the full picture and very little time. Give them
one question, the evidence, and your recommendation.

This is not a `handoff`. A handoff is written for a receiver with zero
memory of the work; use the `handoff` skill for that case. Escalation is
written for someone who already knows the project.

## When to run this

A second child is stuck. A check still fails after the escalation rung in
the `session` skill. A design or scope question you cannot settle. A
budget you would have to exceed.

## Procedure

1. Confirm the rung is spent. A first `STUCK` is not an escalation.
2. Settle on the one question. If you have two, pick the one that blocks
   the other and hold the second back.
3. Write the reply in chat, using these headings and nothing else, at
   most 40 lines in total.

```
## Decision needed
## What the junior tried
## What the senior tried
## Evidence
## Options
## Recommendation
## Blocked meanwhile
```

4. Fill them as follows.
   - **Decision needed**: one question, answerable.
   - **What the junior tried**: the child's goal, check, and result.
   - **What the senior tried**: your own attempts after intake.
   - **Evidence**: paths, pasted output, numbers with their sources. No
     summaries of output you did not paste.
   - **Options**: two or three, each with its cost and its risk.
   - **Recommendation**: which option you would take, and why.
   - **Blocked meanwhile**: what cannot proceed, and what still can.
5. Write a file only if the human asks for one. The default is the chat
   reply.
6. After the decision, file a candidate under
   `.agent-rules/candidates/open/` when the cause was a missing rule
   rather than a hard task.

## Never

- Escalate a first `STUCK` without trying the escalation rung.
- Bury the question under narrative.
- Ask more than one question.
