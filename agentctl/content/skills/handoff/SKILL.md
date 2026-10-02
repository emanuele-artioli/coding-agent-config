---
name: handoff
description: Preserve a factual continuation record when transferring an agentctl task between sessions, harnesses or machines.
---

Use `agentctl handoff TASK` to collect the recorded revision, changes, native
session, checks, artifacts and unresolved state. Add only decision-relevant
context that the task record does not contain: objective, decisions, remaining
work, and limitations. Distinguish observed results from assumptions.

Resume the same harness with `agentctl continue TASK --prompt TEXT --seconds N`. For another
harness, collect the snapshot and create a fresh task using its revision and
the handoff. Preserve the old task and its evidence. An unknown connectivity
state requires inspection before starting replacement work.
