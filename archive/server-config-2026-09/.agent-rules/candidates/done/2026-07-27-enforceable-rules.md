---
id: 2026-07-27-enforceable-rules
created: 2026-07-27
source_platform: cursor
source_project: .
axis: platform
status: applied
summary: Prose-only "must" rules (e.g. plan-mode waves) are forgotten; need enforceable register + hooks/linters
suggested_action: Soft-first plan-wave linter + foundation register; hard fail later per platform
verify_platforms: [claude, antigravity]
evaluated: 2026-07-27
applied: 2026-07-27
---

# Enforceable rules (applied — Cursor soft slice)

## What landed (Cursor)

1. `.agent-rules/enforceable-rules.md` register (`plan-waves` soft,
   `soft-task-change` log-only, `architecture-freshness` standalone).
2. `scripts/lint_plan_waves.py` — waves heading **or**
   `skipped: sequential/small`; soft exit 0; `--strict` reserved;
   `--self-test` fixtures.
3. Cursor `scripts/cursor/stop.py` calls the linter for plans mtime ≤ 7 days
   under `~/.cursor/plans` / workspace `.cursor/plans`.

## Still later

- Hard fail (`--strict` in CI / plan-mode gate) after soft path is useful.
- Claude / Antigravity: no plan-file dialect equivalent wired yet — their
  pending-verification tickets remain the knowledge-loop hook wiring first
  (see `HANDOFF-claude.md` / `HANDOFF-antigravity.md`). Revisit plan-wave
  soft nudge once SessionStart/Stop adapters exist on those platforms.
