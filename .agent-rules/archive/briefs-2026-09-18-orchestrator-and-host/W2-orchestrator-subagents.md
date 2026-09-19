# W2 — Orchestrator and task-class subagents

Read `README.md` in this folder first. Open W1 only if you need the landed
`effort-models.json`; do not reopen W3–W5.

## Job

Make the host tools implement the **orchestrator** shape, not “cheap model
writes, smart model re-reads everything”.

Parent (UI default model): context → plan → dispatch bounded children →
keep high-level state and reports → more children or answer the human.

Child: extra context for *its* bound, work, self-assess with the check the
parent wrote, short report. If out of ideas, say so and request a smarter
rung instead of looping.

## Why the last design is wrong

A mandatory `review-fix` pass on every cheap diff costs a second full
reading of the work. The parent might as well have done the task. Review
belongs in the parent’s **report intake** (short) or in a rare escalation
(Astra / stuck), not as a default second agent.

## What already exists (start here, do not reinvent)

Host:

- `skills/model-routing/SKILL.md` — rewrite the procedure.
- `agents/review-fix.agent.md` — repurpose or delete. A stuck-escalation
  profile is closer to the need than a reviewer of all diffs.
- `effort-models.json` — slugs only; W1 owns values.
- Hooks `model_family` — keep **family** deny. Soft tier nudge may still
  help. Hooks cannot force the parent to dispatch well.

PointStream already runs this shape (read after W1, copy *structure* not
old slugs):

- `pointstream/docs/workflow/session/SKILL.md` — extract outcome, scope,
  acceptance check, parent keeps integration.
- `pointstream/.cursor/agents/budget-default.md` and `expert-retry.md`
- `pointstream/.agents/agents/` same names
- `pointstream/.codex/config.toml` profiles
- `pointstream/AGENTS.md` § Subagents

Do not edit PointStream (W5). If host and PointStream must share a skill
body, W5 lands the project wrapper.

## Design questions this brief must answer in writing before editing

1. **Task classes, not price rungs.** Name 3–6 host-wide child types that
   are actually dispatched (explore/lookup, bounded edit, GPU job,
   paper-editor already exist). Map each to a slug from `effort-models.json`.
   Cursor maps every class to Grok 4.6; Codex maps ordinary children to Luna
   xhigh; Antigravity to Flash; Claude to Opus. Do not invent Composer/Haiku
   “savings” that the user rejected.
2. **Stuck protocol.** Exact phrase the child must return. Who it hands to
   (fresh child with Astra on Codex; ask the user before Astra; switch
   platform). Never resume the stuck child to change model (PointStream
   already says this — keep it).
3. **Spawn mechanics per harness** (read live tool schemas in that
   harness, not this Cursor session’s Task enum if you are documenting
   Claude/Antigravity/Codex):
   - Cursor `Task` / `subagent_type` vs inline `model`
   - Claude `Agent`
   - Antigravity `invoke_subagent` Model/effort
   - Codex TOML `[agents]` (shared `.agent.md` is not Codex-native)
4. **Whether a host `budget-default` / `expert-retry` pair still makes
   sense.** User said Cursor should always be Grok 4.6. Escalation on
   Cursor is thinking medium→high or “ask Astra on Codex”, not Composer→Grok.
   Do not preserve PointStream’s Composer rung on the host.

## Touch these

- `skills/model-routing/SKILL.md` — trigger: before first spawn, when a
  child reports stuck, when tempted to “just review the diffs with a
  smarter model”.
- Shared agents under `.agent-rules/agents/` — replace `review-fix` or add
  a `stuck-escalation` / task-class files. Frontmatter `model` must be
  platform-safe (omit and let parent pass slug, or per-platform copies if
  omit does not work).
- Harness **subagent** sections (not the whole file): how to dispatch, what
  to put in the child prompt (goal, allowed paths, success check, stuck
  rule).
- `enforceable-rules.md` / `CONCEPTS.md` `effort-tier-nudge` current line —
  only if the delivery changed. No ablation study (W4).

## Done when

A parent following `model-routing` dispatches bounded children with a
success check, does not spawn a default reviewer, and has a written stuck →
smarter-model path per harness. `review-fix` is gone or means something
that matches this brief. PointStream files are untouched.
