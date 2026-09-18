# Wave: orchestrator, models, host freshness (2026-09-18)

Coordination index for five independent briefs. Edit this file only to mark a
workstream done or to record a decision that more than one brief must see.
Do not put vendor-doc dumps or PointStream file lists here.

**Human canvas:** `.cursor/projects/home-itec-emanuele/canvases/host-routing-waves.canvas.tsx`

## Locked by the user (do not re-litigate)

- Artificial Analysis **API** Pareto on this date is GPT-heavy. This host
  pays **subscriptions**. Quota, not list price, is the ranking.
- Chart to use: `../assets/2026-09-18-intelligence-index-vs-cost-simplified.png`
  (replaces the earlier full-catalog PNG). Timestamp stays 2026-09-18.
- **Do not** publish a “session defaults to pick in the UI” table. Set the
  interactive model once in each product UI. Host docs do not nag the human
  to re-pick it.
- **Do not** list “avoid as daily driver” models. Unused models stay unused.
- **Do not** review every cheap child’s work with a smarter model. That
  duplicates the task. The parent plans and dispatches; children own a
  bounded task, self-check, and return a short report. Escalate to a
  smarter model only when the current one is stuck.
- 2026-09-18 session that added `review-fix` + “cheap doer then capable
  review” encoded the wrong architecture. Retract it.

## Model facts (locked)

| Harness | Interactive (set in UI, not in README tables) | Subagents / volume | Escape hatch |
|---|---|---|---|
| Codex | Sol medium — analyze, dispatch, review reports | Luna extra-high for general / well-specified child work | Astra low or medium, rarely; often dies mid-prompt |
| Cursor | Grok 4.6 medium | Grok 4.6 always. Medium default; high is optional, unknown payoff. No Composer rung. | none named |
| Antigravity | Gemini 3.8 **Flash** medium (there is no 3.8 Pro) | Flash medium; high optional, same caveat as Grok high | none named |
| Claude | Opus 5 medium | Opus 5 medium. Sonnet is on the chart to show it is bad; do not use it. | people dislike Opus’s voice; Claude is not the long-session default |

## Orchestrator shape (locked)

The first prompt hits the UI default model. That parent: gathers context,
forms a plan, dispatches children with high-level instructions plus a
self-contained success check, and keeps only high-level state plus child
reports. Children gather their own extra context, do the work, assess
themselves, report. Parent then dispatches more children or returns to the
human. A child that is out of ideas must say so and ask to move up (Astra
on Codex; otherwise the parent’s judgment / another platform).

## Waves

**Wave 1** (parallel, separate worktrees): W1, W3, W4.

**Wave 2** (after W1 has landed the model map): W2, W5.

W5 may *read* PointStream in wave 1 but must not rewrite PointStream ladders
until W1+W2 have a host policy to align to.

## Briefs (one worktree each)

| Id | File | Writes | Must not |
|---|---|---|---|
| W1 | `W1-model-map.md` | README chart, `effort-models.json`, harness model sections, kill session-default tables | design the subagent roster; PointStream; vendor-doc diet |
| W2 | `W2-orchestrator-subagents.md` | `model-routing` skill, shared agents, spawn rules | re-pick models; git worktrees; CONCEPTS ablation |
| W3 | `W3-multi-harness-git.md` | git/worktree practice + existing cleanup tools | models; PointStream science |
| W4 | `W4-host-sot-freshness.md` | findings + cut/keep list against vendor docs and `CONCEPTS.md` | ship SoT rewrites in the same pass as the research |
| W5 | `W5-pointstream-alignment.md` | PointStream vs host delta; apply only after W1+W2 | invent a third model ladder |

## Shared files (serialize)

- `README.md`, `effort-models.json`, `harness/*.md`, `skills/model-routing/`,
  `agents/review-fix.agent.md`, host `AGENTS.md` model paragraph: **W1 then W2**.
- PointStream `AGENTS.md`, `.cursor/agents/`, `.agents/agents/`,
  `.codex/config.toml`, `docs/workflow/session/SKILL.md`: **W5 only**.
- `scripts/guardlib/worktree_cleanup.py` and git hooks: **W3 only**.
- `CONCEPTS.md`: W4 proposes; apply in a follow-up, not inside W4’s research
  context.

## Done when

Each brief’s “Done when” is checked. This index lists the five ids as done.
W1 W2 W3 W4 W5 done 2026-09-18 (Cursor parent + W4 subagent findings).
No single agent re-reads all five bodies to “merge” them.
