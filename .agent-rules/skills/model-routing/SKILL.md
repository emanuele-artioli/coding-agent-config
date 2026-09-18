---
name: model-routing
description: Dispatch bounded subagents with a success check, keep parent context high-level, and escalate only when a child is stuck. Use before the first Task/Agent/invoke_subagent spawn, when a child reports STUCK, or when tempted to re-read every child diff with a smarter model.
---

# Model routing

Read `.agent-rules/effort-models.json` before the first spawn (this author's
map — edit for your subscriptions). Interactive models are set in the
product UI; this skill is **children only**. A project need not ship
subagent files: omit `model` to inherit, or pass the mapped slug. If the
project *does* name profiles, spawn those and omit inline `model`.

## Parent

Gather context, form a plan, dispatch children. Each child prompt must
contain: goal, allowed paths, success check the child can run alone, and
the stuck rule below. Keep high-level state plus short reports. Do not
hold the child's whole trace. Do not spawn a second agent whose only job
is to re-read the first child's diffs.

## Children

Mapped slugs (volume work): Cursor Grok 4.6, Antigravity Flash, Claude
Opus, Codex Luna extra-high. Omit `model` when the child should match the
parent. Spawn by `subagent_type` / profile name when a project file
exists, and omit inline `model` so frontmatter wins.

Existing task classes: `explore` / lookup, bounded edit (generic child),
`gpu-job-runner`, `paper-editor`. All use the mapped volume slug unless
the project profile says otherwise.

## Stuck

If the child cannot meet the check and has no next idea, it stops and
returns exactly:

`STUCK: out of ideas.`

then what it tried and why the check failed. The parent starts a **fresh**
child (do not resume to change model):

- Codex: Astra low or medium, rarely (often dies mid-prompt). Ask the user
  first if the quota is already thin.
- Cursor: Grok 4.6 high slug, or ask the user to take the question to Codex
  Astra / another platform.
- Antigravity: Flash high effort.
- Claude: stay on Opus; ask the user before switching platform.

## Harness spawn notes

- Cursor `Task`: `subagent_type` for named agents; live slugs
  `cursor-grok-4.6-medium` / `cursor-grok-4.6-high`. No Composer rung.
- Claude `Agent`: `opus`. Schema still allows haiku/sonnet (off-tier nudge).
- Antigravity `invoke_subagent`: `Model: flash`, medium effort default.
  No 3.8 Pro.
- Codex: TOML `[agents]` (Luna xhigh children). Shared `.agent.md` is not
  Codex-native.

Off-family spawns stay hard-denied. Dated API chart: repo README 2026-09-18.
