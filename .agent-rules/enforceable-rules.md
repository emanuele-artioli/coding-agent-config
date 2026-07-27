# Enforceable rules register

Maps host “must” rules (prose in `AGENTS.md` / harness) to a real mechanism.
Prose alone is not enforcement — agents forget rules that are already in
context. Soft first; harden only after the advisory path proves useful.

| Rule id | Prose source | Mechanism | Mode | Notes |
|---|---|---|---|---|
| `plan-waves` | `AGENTS.md` — Plan mode: parallel-agent waves | `scripts/lint_plan_waves.py` (+ Cursor `stop` advisory) | **soft** | Pass = waves heading *or* explicit `skipped: sequential/small`. Hard fail later (Cursor `.cursor/plans/`). |
| `soft-task-change` | progressive nudges | `scripts/context_nudge.py` via `beforeSubmitPrompt` | **log-only** | Do not enable `CONTEXT_NUDGE_BLOCK_SOFT=1` until soft plan-wave nudges are proven. |
| `architecture-freshness` | living diagrams | `scripts/render_architecture.py --check` | **standalone gate** | Not folded into `install.py --check`. |

## Adding a rule

1. Put the must in `AGENTS.md` (or harness) if it isn’t there.
2. Add a row here with a concrete mechanism (script, hook, CI gate).
3. Prefer soft advisory until the fix message is clear and false positives are rare.
4. Platform live wiring for non-Cursor agents → `candidates/pending-verification/<platform>.md`.
