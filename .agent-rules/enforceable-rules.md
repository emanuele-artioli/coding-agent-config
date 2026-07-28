# Enforceable rules register

Maps host “must” rules (prose in `AGENTS.md` / harness) to a real mechanism.
Prose alone is not enforcement — agents forget rules that are already in
context. Soft first; harden only after the advisory path proves useful.

| Rule id | Prose source | Mechanism | Mode | Notes |
|---|---|---|---|---|
| `plan-waves` | `AGENTS.md` — Plan mode: parallel-agent waves | `scripts/lint_plan_waves.py` (+ Cursor `stop` advisory) | **soft** | Pass = waves heading *or* explicit `skipped: sequential/small`. Hard fail later (Cursor `.cursor/plans/`). |
| `soft-task-change` | progressive nudges | `scripts/context_nudge.py` via `beforeSubmitPrompt` | **log-only** | Do not enable `CONTEXT_NUDGE_BLOCK_SOFT=1` until soft plan-wave nudges are proven. |
| `architecture-freshness` | living diagrams | `scripts/render_architecture.py --check` | **standalone gate** | Not folded into `install.py --check`. |
| `model-family` | `harness/{cursor,claude,antigravity}.md` — Model family | `scripts/guardlib/model_family.py` + Cursor `scripts/cursor/before-task.py` (`preToolUse`/`Task`, `subagentStart`) + Claude `PreToolUse`/`Agent\|Task` → `scripts/guard-model-family.py` | **hard** (family) on Cursor Task path and Claude `PreToolUse`; soft on Antigravity until pending-verification closes. **soft** (effort tier, added 2026-07-28) everywhere | Prefer omit/inherit; family prefixes only (no versioned slugs). Distrust pstack multi-family defaults. Claude wired 2026-07-28 (script-level verified; the `Agent` tool's own schema already blocks off-family models before the hook runs, so live hook-deny proof is N/A-by-design — see `candidates/pending-verification/claude.md`). Antigravity adapter shipped in SoT. Effort-tier data: `effort-models.json` maps low/medium/high → model per platform for **subagent spawns only** (never the user's own session model); `model_family.tier_nudge()` fires only once the family check already passed. Claude surfaces it as `permissionDecision: "ask"`. Cursor cannot — live 2026-07-28 confirmed `{"permission":"ask"}` on `preToolUse`/`subagentStart` is rejected ("not yet implemented"); stays allow + log (+ `agent_message`). Antigravity is exit-code only (0/2), log-only-by-design for the soft tier. |

## Adding a rule

1. Put the must in `AGENTS.md` (or harness) if it isn’t there.
2. Add a row here with a concrete mechanism (script, hook, CI gate).
3. Prefer soft advisory until the fix message is clear and false positives are rare.
4. Platform live wiring for non-Cursor agents → `candidates/pending-verification/<platform>.md`.
