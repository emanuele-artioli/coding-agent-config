# HANDOFF — coding-agent-config (Cursor follow-up, 2026-07-27)

## What triggered this handoff

User asked to continue after commit/push of the prior knowledge-loop work:
finish remaining **Cursor** tasks; prepare Claude/Antigravity handoffs for
other-platform tickets.

## One-paragraph summary

Knowledge loop is live on Cursor. This session verified SessionStart + stop
fill-% probe, implemented the soft plan-wave linter + enforceable-rules
register, and wrote platform handoffs. Remaining live wiring for Claude /
Antigravity is **out of band** — use the sibling handoff files.

## Current state (re-verify with `git status` / `git log -1` before acting)

| Item | State |
|---|---|
| Branch | `master` (prior tip `2dbf2a8`); **this session’s SoT edits may be uncommitted** |
| Cursor pending-verification | **all checked** |
| Open candidates | none (enforceable-rules → `done/`) |
| Claude / Antigravity pending-verification | still open — see sibling handoffs |

## What’s running

Nothing.

## Open questions / decisions

All prior decisions still locked (soft task-change log-only; plan-wave soft
first; architecture `--check` standalone). Optional later: enable
`--strict` plan-wave gate; model-family enforcement plan under
`.cursor/plans/model_family_enforcement_*.plan.md` is **separate** work (not
started).

## Immediate next steps

1. **User:** commit/push Cursor SoT changes if desired.
2. **Claude Code:** open `HANDOFF-claude.md` and wire SessionStart/Stop/….
3. **Antigravity:** open `HANDOFF-antigravity.md` and create `hooks.json`.
4. Optional: add `skipped: sequential/small` (or waves) to recent plans that
   soft-fail (`model_family_enforcement_*`, `env_restorers_queue_*`).

## Landmarks

| Path | Why |
|---|---|
| `HANDOFF-claude.md` | Claude pickup |
| `HANDOFF-antigravity.md` | Antigravity pickup |
| `.agent-rules/enforceable-rules.md` | Must-rule register |
| `.agent-rules/scripts/lint_plan_waves.py` | Soft linter |
| `~/.cursor/session-start.log` / `stop-probe.log` | Live Cursor proofs |
| `.agent-rules/candidates/pending-verification/cursor.md` | Clear |

---

## Retired — 2026-08-31

Spent. Every "immediate next step" it lists has landed, checked against the
checklists rather than assumed:

| Its next step | State today |
|---|---|
| Commit/push Cursor SoT changes | done; `pending-verification/cursor.md` shows the live proofs |
| Claude Code: wire SessionStart/Stop/… | done — all 10 rows in `pending-verification/claude.md` are checked, including two closed as N/A-by-design with reasons |
| Antigravity: create `hooks.json` | done — all 10 rows in `pending-verification/antigravity.md` are checked |
| Add `skipped: sequential/small` to soft-failing plans | optional then, moot now |

Its "Current state" table was also the exact hazard `AGENTS.md` warns about in
the git section: it claimed **"Open candidates: none"** while the queue in fact
sat at 11 open items, the oldest from 2026-07-29 — a status line that stayed
plausible for five weeks after it stopped being true. Kept here as the audit
record; it is not a live document and nothing should be picked up from it.

