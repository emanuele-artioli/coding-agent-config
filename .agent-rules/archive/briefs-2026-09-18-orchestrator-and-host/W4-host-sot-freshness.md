# W4 — Host SoT vs current harness docs and the ablation suite

Read `README.md` in this folder first. Do not open other W*.md files.
Do not rewrite the SoT in this pass except tiny factual corrections you
would otherwise lose; the deliverable is a **cut/keep/move list**.

## Job

coding-agent-config grew while models were weaker and while each vendor’s
subagent story was thinner. It may now be over-specified. Check that
against **current** vendor documentation and against the ablation catalog
we already designed.

The question is not “can we delete rules because models are smart”. The
catalog’s own scoring: keep anything whose without-arm still fails the
job. Token savings that also fail the task are not a win.

## The existing test suite (this is it)

Not pytest. `.agent-rules/CONCEPTS.md`:

- Delivery hierarchy: hook → skill/subagent → AGENTS last
- Each atomic has one ablation test
- “Recommended first ablation batch” when a new default model lands
  (items 1–7: tooling-meant-to-evolve, coding-style volume, paper thin vs
  stack, bound-before-believing, context nudges, effort-tier-nudge, AGENTS
  lines that already have hooks)
- Hard hooks and git promotion are **do not diet first**

Run that batch **on paper** against 2026-09-18 models first (which items
are now likely dead vs still load-bearing). Then pick at most two atomics
and actually run the 5–15 min recipe if a session can afford it. Do not
pretend a thought experiment is a completed ablation.

## Vendor docs to fetch (current, not harness memory)

Read the live docs; quote version/date. Harness `*.md` files are **our**
notes and may be wrong.

- Claude Code: https://docs.anthropic.com/en/docs/claude-code (subagents,
  hooks, CLAUDE.md vs AGENTS.md, skills)
- Cursor: https://cursor.com/docs (Agent/Task, hooks.json, rules vs
  AGENTS.md, subagent model field)
- Codex: https://developers.openai.com/codex (CODEX_HOME, AGENTS.md cap,
  hooks, `[agents]` TOML)
- Antigravity / Gemini: current VS Code extension docs for
  `invoke_subagent`, GEMINI.md vs AGENTS.md, hooks.json shape

For each platform record: what the product now does natively that our SoT
still explains at length; what we still must keep because the product
does not.

## Likely stale vs likely still needed (hypotheses — verify)

Stale / shrink candidates:

- Prose that only Cursor could parallel-subagent (candidate
  `2026-09-10-cross-harness-parallel-subagents` already disputes this)
- Effort-tier tables that encode Composer/Haiku/Sonnet savings the user
  rejected (W1 is already rewriting the numbers; you judge whether the
  *nudge hook* still earns its keep)
- Long harness essays that duplicate vendor docs (waiting for jobs,
  slash-command paths)
- `review-fix` / cheap-then-review (already retracted in the index)

Still needed regardless of IQ:

- NFS / login-shell / sqlite-before-torch host facts (not discoverable)
- Destructive git + `rm` guards (judgement-free)
- Wait-loop self-match (harness still wraps `bash -c`)
- Pointer-not-inline host rules (cloud agents still do not see `~`)
- Knowledge loop candidates queue (process, not model quality)

## Deliverable

Write
`W4-findings.md` (now beside this file under
`.agent-rules/archive/briefs-2026-09-18-orchestrator-and-host/`)
(create it) with:

- Per-platform: native vs SoT overlap (short)
- Per CONCEPTS first-batch item: keep / move / delete / run-ablation
- Ordered apply list for a **later** coding-agent-config session
- What you did **not** verify

Do not apply a large diet in the same context that researched it. That is
how this repo got both over-specified and internally inconsistent.

## Done when

`W4-findings.md` exists and a later agent can apply it without reading
vendor docs again. Host SoT is not rewritten beyond a typo/date fix.
