---
id: 2026-09-10-cross-harness-parallel-subagents
created: 2026-09-10
source_platform: antigravity
source_project: /home/itec/emanuele/pointstream
axis: platform
status: open
summary: Antigravity, Claude, and Codex support parallel subagents alongside Cursor when configured with weaker models
suggested_action: update harness files and session skills to reflect that parallel wave execution is supported across all major harnesses using cheaper model tiers
verify_platforms: [antigravity, cursor, claude, codex]
---

Prior documentation stated or implied that only Cursor was suitable for parallel
subagent workstreams, and labeled other harnesses as sequential.

Investigation confirmed that Antigravity natively provides `invoke_subagent`
with concurrent multi-agent dispatch, isolated workspaces (`Workspace: "branch"`
or `"share"`), and model selection (`Model: "flash_lite" | "flash" | "pro"`).
Likewise, Claude Code supports subagents via `Agent`/`Task` (with `haiku`/`sonnet`),
and Codex supports TOML roles and subagents.

Key rule for parallel subagent execution across all harnesses:
Always configure subagents running parallel lanes or multi-agent waves to use
weaker/cheaper models (e.g. `flash_lite`/`flash` on Antigravity, `composer-2.5`
on Cursor, `haiku`/`sonnet` on Claude) to conserve token budgets and avoid
runaway context costs.
