---
id: 2026-07-27-enforceable-rules
created: 2026-07-27
source_platform: cursor
source_project: .
axis: platform
status: open
summary: Prose-only "must" rules (e.g. plan-mode waves) are forgotten; need enforceable register + hooks/linters
suggested_action: Design foundation enforceable-rules register; Cursor plan-wave linter first; extend guardlib / .agent-guards.json pattern
verify_platforms: [claude, antigravity]
---

# Enforceable rules (deferred implementation)

## Problem

Foundation / platform / project "must" rules that are advisory-only get
forgotten. Example: "Plan mode: split complex plans into parallel-agent waves"
in `AGENTS.md` was in context and still skipped. The twice-wrong register in
`AGENTS.md` is necessary but insufficient for must-not-skip process rules.

## Layers to design

1. **Foundation:** which host rules are *enforceable* vs advisory; a small
   register listing rule id → enforcement mechanism (hook, skill gate, CI
   check, plan linter).
2. **Platform:** adapters — e.g. Cursor: lint `.cursor/plans/*.plan.md` for a
   waves section (or explicit "skipped: sequential/small" rationale). Claude /
   Antigravity equivalents. SessionStart can remind; Stop can nudge.
3. **Project:** extend `.agent-guards.json` for project-local musts rather than
   inventing a third config dialect.

## First concrete target

Plan-wave rule — detect complex plans missing a waves analysis. Soft vs hard
fail TBD per platform capability.

## Out of band until implemented

Human/agent reviewing plans checks for waves. Do not implement the register or
linter until this candidate is evaluated and scheduled.
