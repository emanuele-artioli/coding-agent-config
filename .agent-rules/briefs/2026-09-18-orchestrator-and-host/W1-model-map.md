# W1 — Model map and dated chart

Read `README.md` in this folder first. Do not open the other W*.md files.

## Job

Put the 2026-09-18 **subscription** ranking into the SoT, and take out the
wrong artifacts from the previous session (API-as-cost table, session-default
UI table, “avoid as daily driver”, Gemini Pro, Sonnet-as-default, Composer as
the cheap Cursor rung, `review-fix` as a mandatory second pass).

You implement file edits. You do not design the subagent catalog (W2).

## Locked inputs

- Chart: `/home/itec/emanuele/.agent-rules/assets/2026-09-18-intelligence-index-vs-cost-simplified.png`
- Replace `.agent-rules/assets/2026-09-18-intelligence-index-vs-cost.png` with
  that simplified file (or point README at the simplified name and delete the
  unused PNG). Caption must keep the date **2026-09-18** and say the chart is
  API list price, while this host follows subscription quota.
- Model facts: the table in this wave’s index README. Codex Sol / Luna xhigh /
  rare Astra; Cursor Grok 4.6 only; Antigravity Flash 3.8 medium; Claude Opus 5
  medium.
- No README/harness table of “pick this in the UI”. The human sets the
  interactive model once. Docs talk about **subagent** slugs and escalation
  only.

## Touch these

- `/home/itec/emanuele/README.md` — dated chart section: image + short
  “API ≠ subscription” note. Delete the session-defaults table and the
  avoid-list. One sentence pointing at `effort-models.json` is enough.
- `/home/itec/emanuele/.agent-rules/effort-models.json` — rewrite
  `platforms` to the locked slugs. Drop `session_defaults` (that was the UI
  table in JSON form). Keep a `snapshot.date` of 2026-09-18.
- Harness **model** sections only: `harness/cursor.md`, `antigravity.md`,
  `claude.md`, `codex.md`. Cursor: Grok 4.6 medium/high, no Composer ladder.
  Antigravity: Flash, not Pro; “pro is missing” not “pro is stale, do not
  select” unless you verify the spawn enum. Claude: Opus not Sonnet/Haiku.
  Codex: Sol parent / Luna xhigh children / Astra escape.
- Host `AGENTS.md` paragraph “Match model capability to the task” — rewrite
  to orchestrator + escalate-when-stuck, not cheap-then-review. Keep it
  short. Then `python3 .agent-rules/scripts/sync_host_rules.py`.
- `scripts/guardlib/model_family.py` + `test_model_family.py` — match the
  new JSON. Cursor family is still Grok/Composer (Composer may remain
  *allowed* by the hard family gate even if the tier table no longer maps
  it). Claude family still allows sonnet; it should **nudge** if off-tier.
- Do **not** delete `skills/model-routing/` or `agents/review-fix.agent.md`
  here. Leave a one-line stub in each pointing at W2, or leave them broken
  with a TODO that W2 owns. Do not invent replacement agent files.

## Do not

- Fetch vendor documentation (W4).
- Edit PointStream (W5).
- Change git/worktree scripts (W3).
- Argue whether Grok high or Flash high “pays off”. Record both as optional
  thinking, default medium.

## Tests

- `python3 -m unittest guardlib.test_model_family` from
  `.agent-rules/scripts`.
- `python3 .agent-rules/scripts/sync_host_rules.py --check`
- `python3 .agent-rules/scripts/render_architecture.py --check` if you
  touched `.agent-rules/README.md`.

## Done when

README shows the simplified dated chart and no UI-defaults table.
`effort-models.json` matches the locked map. Harness model sections and
tests agree. The previous session’s review-everything wording is gone from
files you were allowed to touch.
