---
id: 2026-07-27-enforceable-rules
created: 2026-07-27
source_platform: cursor
source_project: .
axis: platform
status: open
summary: Prose-only "must" rules (e.g. plan-mode waves) are forgotten; need enforceable register + hooks/linters
suggested_action: Soft-first plan-wave linter + foundation register; hard fail later per platform
verify_platforms: [claude, antigravity]
evaluated: 2026-07-27
---

# Enforceable rules (evaluated — scheduled)

## Evaluation (2026-07-27)

**Keep and schedule** — do not discard. Prose-only must-rules are a repeated
failure mode (plan-wave rule skipped while in context).

### Decisions

1. **Soft vs hard for plan-wave:** **soft first.** Missing waves section (or
   missing explicit `skipped: sequential/small`) → advisory stderr / SessionStart
   / stop nudge. Hard fail only after soft path is proven useful and the
   platform can surface a clear fix message (Cursor plan files under
   `.cursor/plans/`).
2. **Soft task-change (`beforeSubmitPrompt`):** keep **log-only** default;
   do not enable `CONTEXT_NUDGE_BLOCK_SOFT=1` until soft plan-wave nudges are
   in place (separate open question from HANDOFF; answered here as keep
   log-only).
3. **Shape:** foundation markdown register (rule id → mechanism) under
   `.agent-rules/`; Cursor plan-wave linter first; extend
   `guardlib` / `.agent-guards.json` for project-local musts later — no third
   config dialect.

### Next implementation slice

1. Add `.agent-rules/enforceable-rules.md` register with `plan-waves` →
   `cursor-plan-linter (soft)`.
2. Add `scripts/lint_plan_waves.py` scanning `.cursor/plans/*.plan.md` for a
   waves heading or `skipped: sequential/small`.
3. Wire advisory call from Cursor `stop` or a workflow; leave Claude /
   Antigravity as `needs_verification` tickets when adapters land.

Until then: human/agent reviewing plans checks for waves manually.
