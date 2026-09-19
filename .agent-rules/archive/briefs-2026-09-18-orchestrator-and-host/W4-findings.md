# W4 findings — host SoT vs vendor docs (access date 2026-09-18)

Research only. **Do not apply this diet in the same session that wrote it.**
A later coding-agent-config session applies the ordered list at the bottom.

Locked facts from this folder’s `README.md` were treated as policy, not
vendor docs: subscription quota not API Pareto; no session-default UI
tables; no cheap-doer-then-smarter-review; `review-fix` retracted.

**No live 5–15 min ablation was run.** Scores below are paper scores
against CONCEPTS.md’s catalog and 2026-09-18 locked models. A thought
experiment is not a completed ablation.

---

## Per platform — native vs SoT overlap

### Claude Code

Docs (fetched 2026-09-18):

- Memory / CLAUDE.md: https://code.claude.com/docs/en/memory
- Alias: https://code.claude.com/docs/en/claude-md
- Subagents: https://code.claude.com/docs/en/sub-agents
- Hooks: https://code.claude.com/docs/en/hooks
- Skills: https://code.claude.com/docs/en/skills
- `.claude/` layout: https://code.claude.com/docs/en/claude-directory

**Native now**

- Persistent instructions are **`CLAUDE.md`**, not `AGENTS.md`. Quote:
  “Claude Code reads `CLAUDE.md`, not `AGENTS.md`.” Import with a
  `CLAUDE.md` body that is `@AGENTS.md` (plus Claude-only lines below),
  or a symlink. `/init` with `CLAUDE_CODE_NEW_INIT=1` also reads
  `AGENTS.md`. `/import` (v2.1.213+) can copy `AGENTS.md` into CLAUDE.md.
- `.claude/rules/*.md` with optional `paths` frontmatter: path-gated
  rules load when matching files enter context. CLAUDE.md is guidance,
  not enforcement — **PreToolUse hooks** enforce.
- Subagents: Markdown + YAML in `.claude/agents/` and `~/.claude/agents/`.
  Built-ins: Explore, Plan, general-purpose, plus helpers. Explore/Plan
  **skip CLAUDE.md and git status**. Custom fields include `model`,
  `tools`, `skills`, `hooks`, `background`, `isolation`, `effort`.
  As of v2.1.198 Explore inherits the parent model (API cap Opus);
  background is the default; `Agent` tool spawns children; parallel
  research is documented. Forked skills with Explore/Plan skip CLAUDE.md.
- Hooks in `settings.json` (and plugins/skill/subagent frontmatter):
  SessionStart/End, PreToolUse (can deny), PostToolUse, SubagentStart/Stop,
  Stop, PreCompact, UserPromptSubmit, and many more. Matcher on tool name.

**Product does not replace**

- Host NFS / login-shell / sqlite-before-torch / no-sudo facts.
- `bash -c` wait-loop **self-match** (our `guard-wait-loop`). Vendor
  documents Monitor / background Bash; it does not document this failure.
- Destructive git / protected `rm` (our guardlib).
- Pointer-not-inline: cloud Claude on another machine still will not see
  `~/.claude` host files unless the project imports them.

**SoT overlap to cut later (harness essays, not host AGENTS facts)**

- Long “how to wait / slash-command paths / built-in subagent catalog”
  that now lives in vendor docs. Keep only host-specific waiter +
  self-match + tool names (`Bash`, `Monitor`, `run_in_background`).
- Effort text that still talks Haiku/Sonnet savings. Locked: Opus 5
  medium parent and child; Sonnet is not used. Vendor still mentions
  Haiku for cost routing — ignore for this host.

### Cursor (Agent / Task / hooks / rules)

Docs (fetched 2026-09-18):

- Agent overview: https://cursor.com/docs/agent/overview
- Subagents (Task): https://cursor.com/docs/subagents
- Hooks: https://cursor.com/docs/hooks
- Rules + AGENTS.md: https://cursor.com/docs/rules
- CLI also reads AGENTS.md and CLAUDE.md: https://cursor.com/docs/cli/using

**Native now**

- **Agent** is the parent. **Task** is the subagent spawn tool. Docs:
  “Agent sends multiple Task tool calls in a single message, so
  subagents run simultaneously.” Foreground vs `is_background`.
  Built-ins: Explore, Bash, Browser. Custom: `.cursor/agents/*.md` with
  `name`, `description`, `model` (`inherit` default or a model ID plus
  `[effort=…]` brackets), `readonly`, `is_background`. Also discovers
  `.claude/agents/` and `.codex/agents/` (`.cursor/` wins on name clash).
  Isolated copies: git worktree or cloud VM. Cloud subagents do not see
  local MCP / `~/.cursor`.
- **hooks.json `version`: 1** at `.cursor/hooks.json` (project) and
  `~/.cursor/hooks.json` (user). Events include `sessionStart`,
  `beforeShellExecution`, `subagentStart` / `subagentStop` (can
  allow/deny Task), `preCompact`, `stop`. **User hooks are not available
  to cloud agents.** Project `.cursor/hooks.json` is. `ask` on
  `subagentStart` is treated as deny (forum; not re-tested here).
- **AGENTS.md** at repo root and nested dirs; more specific nested file
  wins. Alternative: `.cursor/rules/*.mdc` with `alwaysApply` / globs /
  description. Plain `.md` in `.cursor/rules` is ignored. User Rules live
  in Settings (account), not `~/.cursor/rules/`. Team Rules (dashboard)
  take precedence when present.

**Product does not replace**

- Same host facts; wait-loop self-match on `beforeShellExecution`.
- Pointer-not-inline is **stronger** for Cursor cloud: user hooks and
  home AGENTS are invisible; only committed project pointers/hooks run.
- Locked child model is Grok 4.6 inherit. Vendor Explore still “uses a
  faster model by default” — our family hook must keep Explore on Grok
  if the product would otherwise pick Composer.

**SoT overlap to cut later**

- Prose that “only Cursor can parallel-subagent.” False in 2026-09-18
  vendor docs for all four harnesses.
- Re-explaining Task/worktree isolation / hooks.json schema.
- Composer/Haiku/Sonnet effort ladders (locked: no Composer rung).

### Codex (`CODEX_HOME`, AGENTS cap, hooks, `[agents]`)

Docs (fetched 2026-09-18):

- AGENTS.md discovery: https://developers.openai.com/codex/guides/agents-md
- Subagents + custom TOML: https://developers.openai.com/codex/subagents
- Hooks: https://developers.openai.com/codex/hooks
- Config reference: https://developers.openai.com/codex/config-reference
- Sample `[agents]`: https://developers.openai.com/codex/config-sample

**Native now**

- **`CODEX_HOME`** defaults to `~/.codex`; override for a profile. Global
  instructions: `$CODEX_HOME/AGENTS.override.md` else `$CODEX_HOME/AGENTS.md`
  (first non-empty only). Then project root → cwd: per directory
  `AGENTS.override.md` then `AGENTS.md` then `project_doc_fallback_filenames`.
  Concatenate root→cwd. **`project_doc_max_bytes` default 32 KiB**
  cumulative; stop adding files at the cap. Raise the knob or nest files.
- Subagents are first-class: spawn on request or when AGENTS/skills ask;
  built-ins `default` / `worker` / `explorer`. Custom agents:
  `~/.codex/agents/*.toml` or `.codex/agents/*.toml` with required
  `name`, `description`, `developer_instructions`. Optional `model`,
  `model_reasoning_effort`, sandbox, MCP, skills.
- **`[agents]` in config.toml** (config-reference, 2026-09-18):
  `agents.max_depth` (default 1), `agents.max_threads` (default 6),
  `agents.job_max_runtime_seconds`. The narrative subagents page also
  lists `agents.enabled`, `agents.max_concurrent_threads_per_session`
  (legacy alias `max_threads`), `agents.default_subagent_model`,
  `agents.default_subagent_reasoning_effort`. Sample config comments
  match the narrative names. Treat **both names as live until a local
  Codex version is checked** (not verified on this host).
- Hooks: `hooks.json` or inline `[hooks]` in config.toml; user
  `~/.codex/` and project `.codex/`. Events: PreToolUse, PostToolUse,
  SessionStart, SubagentStart/Stop, Stop, PreCompact, PermissionRequest,
  etc. Non-managed hooks need `/hooks` trust. `features.hooks`.
- Vendor model names in that page (`gpt-5.6`, terra, luna) are **API
  catalog**. This host uses subscription Sol / Luna / Astra per locked
  README — do not copy vendor slug tables into host AGENTS.

**Product does not replace**

- Setting `CODEX_HOME=/var/tmp/emanuele-codex` so sockets/SQLite stay
  off NFS (host-only). Docs only say “set CODEX_HOME for a profile.”
- 32 KiB cap vs a large host AGENTS.md: **product will truncate**; SoT
  must stay short or nest. That is a reason to diet AGENTS, not a reason
  to delete host facts.
- Wait-loop / destructive git / rm guards (our adapters).
- Locked child: Luna extra-high; Astra only as escape. Vendor defaults
  (terra/luna API names) are not our map.

**SoT overlap to cut later**

- Re-teaching AGENTS discovery / `[agents]` schema / hook event lists.
- `harness/codex.md` line that custom agents are “TOML roles under
  `[agents]`, not … markdown” is **half-stale**: custom agents are
  standalone `agents/*.toml`; `[agents]` is global limits + optional
  role pointers (`config_file`). Keep the “not Claude markdown” warning;
  fix the path when applying.

### Antigravity / Gemini (`invoke_subagent`, GEMINI.md, hooks)

Docs (fetched 2026-09-18):

- Subagents: https://www.antigravity.google/docs/subagents/
- CLI subagents / tasks: https://www.antigravity.google/docs/cli/subagents/
- Hooks: https://www.antigravity.google/docs/hooks/
- IDE hooks: https://antigravity.google/docs/ide/hooks/
- Rules: https://antigravity.google/docs/rules-workflows/
- GEMINI.md + AGENTS.md: https://www.antigravity.google/docs/cli/best-practices/
- Same pair on migrate: https://www.antigravity.google/docs/cli/gcli-migration/
- VS Code marketplace (invoke_subagent, inherit/branch/share):
  https://marketplace.visualstudio.com/items?itemName=Google.GoogleAntigravity

**Native now**

- Parent tool **`invoke_subagent`**: array of `{Prompt, Role, TypeName,
  Workspace?}`. Workspace: `inherit` | `branch` (git worktree) | `share`.
  Clean child context. Also `define_subagent`, `send_message`,
  `manage_subagents`. Built-ins: `research`, `browser`, `self`. Custom
  Markdown + YAML: `.agents/agents/*.md` or `~/.gemini/config/agents/`.
  Frontmatter: `name`, `description`, `tools`, `subagent`/`mainAgent`,
  `model` (`inherit` | `flash` | `pro`), skills. Nesting depth cap **10**.
  `/boost` and `/teamwork-preview` are product orchestrators (plan-gated).
- **GEMINI.md and AGENTS.md** at the active directory / workspace root
  are both parsed. Global: `~/.gemini/GEMINI.md`. Additional rules:
  `.agents/rules/` (12 000 characters **each**); modes always / model /
  glob / manual. Skills: `.agents/skills/` (workspace),
  `~/.gemini/antigravity-cli/skills/` (CLI global).
- **hooks.json**: workspace `.agents/hooks.json`, global
  `~/.gemini/config/hooks.json`. Events: PreToolUse, PostToolUse,
  PreInvocation, PostInvocation, Stop. Matcher on tool name including
  `run_command` and `invoke_subagent`. PreToolUse can `allow` / `deny` /
  `ask`. Hook examples still show `modelName` like
  `gemini-3.6-flash-medium` — example only; locked interactive is
  Gemini 3.8 Flash medium (no 3.8 Pro). Do not pass `pro` expecting 3.8 Pro.

**Product does not replace**

- Host facts; wait-loop if `run_command` still wraps `bash -c` (not
  re-verified on Antigravity this pass — keep the hook).
- Locked: children Flash medium; `pro` in vendor frontmatter is the
  wrong rung here.
- Conflict rule “GEMINI.md wins vs AGENTS.md” is **our harness claim**,
  not quoted from the two pages above (they only say both are parsed).

**SoT overlap to cut later**

- `harness/antigravity.md` restating invoke_subagent / Workspace enum /
  manage_subagents — vendor-complete. Keep host Flash mapping and the
  “no 3.8 Pro” line.
- Sequential-thinking / GitHub MCP essays unless they failed twice
  (AGENTS.md register-of-failures test). They look like product tutorials.

---

## CONCEPTS first ablation batch — paper scores

Scoring rule (CONCEPTS): keep if the without-arm still fails the job.
Token savings that fail the task are not a win. Hierarchy: hook →
skill/subagent → AGENTS last. **Do not diet first:** hard hooks, git
promotion, host-machine atomics without hooks, `project-env-and-deps`,
thin paper facts, project hard science.

| # | Atomic | Paper score | Why (2026-09-18 models) |
|---|---|---|---|
| 1 | `tooling-meant-to-evolve` / `where-to-look-for-more` | **delete** | Catalog already says delete. Grok 4.6 / Opus 5 / Flash / Sol can glob paper and skill paths. Meta “config will change” indexes are not a failure-mode guard. |
| 2 | MoQSplat `coding-style` volume | **delete** essay; **keep** gaps one-liner | Style prose is linter work (Cursor rules docs say the same). Gaps (no unbidden CI) still fail without a one-liner. Project AGENTS, not host. |
| 3 | `paper` thin AGENTS vs skills/agent/Stop stack | **move** | Keep thin facts (Overleaf path, markers). Demote paper-editor / update-paper / reviewer-response / sync-hook until thin AGENTS fails. Catalog already expects thin wins. **run-ablation later** on one paper repo (“What next?” → HOLE/NEXT). |
| 4 | `bound-before-believing` | **delete** from always-on AGENTS | Catalog: prefer omit; invented bounds are theater. Still a long host AGENTS section today. Adjacent “Control the instrument” is the same family — **move** to `verify-measurement` skill when a ranking is claimed, not always-on. Do not restore a generic compare skill. |
| 5 | `context-nudge` / `candidate-reminders` / `precompact-stub` | **keep** as hooks; **tune** | Already the right layer. Not an AGENTS diet. Quiet reminders if they never get acted on. **run-ablation later** on candidate-reminders (acted on ≥1 across N sessions, else drop reminder, keep queue). |
| 6 | `effort-tier-nudge` | **move** (drop review-fix; shrink hook) | Locked architecture retracts cheap-then-review. Cursor/Claude/Antigravity locked children **inherit the in-house model**; vendor default is already `inherit`. The soft map earns keep mainly on **Codex** (Luna child vs Sol parent, Astra escape). JSON table stays W1’s job. CONCEPTS current text still names `review-fix` — fix that on apply. **run-ablation later** (15 min): Cursor spawn without the nudge — does Explore stay Grok? |
| 7 | AGENTS lines that already have working hooks | **delete** duplicates | Wait-loop and destructive `rm`/`git` belong in hooks; AGENTS at most a one-line pointer. **Keep** git-dev judgement (read before delete, origin/main, dirty worktree) — catalog says do not diet first. **Keep** NFS/login-shell/sqlite (no hook). Trim `long-jobs` AGENTS body to pointer + skill/`gpu-job-runner`. Trim `knowledge-loop` AGENTS if SessionStart + end-of-session already fire. Trim `plan-waves` AGENTS if `lint_plan_waves.py` is enough — **run-ablation later**, do not cut on paper alone. |

**Do not diet first (reconfirmed):** `guard-destructive-rm`, `wait_loop`,
`guard-model-family`, `git-dev`/`git-test`/`git-prod` (except MoQSplat CI
gap), host-machine atomics, `project-env-and-deps`, thin paper facts,
fixed-QP / Residual Guarantee / MoQ mapping.

### Hypotheses from the brief — verdict

| Hypothesis | Verdict |
|---|---|
| Prose that only Cursor could parallel-subagent | **Stale.** Claude background Agent, Cursor multi-Task, Codex spawn, Antigravity `invoke_subagent` arrays are all vendor-native. |
| Effort-tier tables / nudge | Tables: W1. Nudge: keep Codex-shaped; drop review-fix; likely drop on inherit-only harnesses after ablation. |
| Long harness essays duplicating vendor docs | **Cut later** (wait-loop self-match and NFS CODEX_HOME stay). |
| `review-fix` / cheap-then-review | **Delete** (locked retract). |

### Still needed regardless of model IQ

- NFS open-cost, `/var/tmp` per-host, login-shell rc tax, sqlite-before-torch, no-sudo/headless.
- Destructive git + `rm` hard hooks (judgement-free).
- Wait-loop self-match (harness still wraps `bash -c`).
- Pointer-not-inline (Cursor cloud docs: no `~/.cursor/hooks.json`; Claude/Codex cloud similarly miss home).
- Knowledge-loop candidates queue (process, not IQ).

---

## Ordered later-apply list

For a **later** coding-agent-config session. Stop after each wave if
inconsistent. Do not combine with another research dump.

1. **Retract leftover review-fix / cheap-then-review** in CONCEPTS
   `effort-tier-nudge` Current line, any remaining skill/agent file, and
   indexes. Policy already locked; docs must match.
2. **Host AGENTS.md trim (item 4 + 7), keep host facts:** remove always-on
   `bound-before-believing` and shrink “Control the instrument” to a
   pointer at `verify-measurement`. One-line pointers for wait-loop / rm
   (hooks exist). Do not touch NFS, sqlite-before-torch, git-dev
   judgement, gh, project-env, thin orchestrator paragraph (locked
   parent/child shape can stay once W1/W2 land).
3. **Harness diet (duplicate vendor docs only):** Claude/Cursor waiter
   *catalog* of product waiters → link out; keep self-match. Cursor:
   delete “only we can parallel.” Antigravity: delete invoke_subagent
   tutorial; keep Flash / no-3.8-Pro. Codex: fix custom-agent path
   (`agents/*.toml` + `[agents]` limits); keep `CODEX_HOME` NFS note
   and 32 KiB cap warning.
4. **Project AGENTS:** delete `tooling-meant-to-evolve` / where-to-look
   blobs; shrink MoQSplat coding-style; leave science one-liners.
5. **Paper stack demotion (item 3):** thin AGENTS-only on paper repos;
   stop loading paper-editor/sync-hook by default. Then run the 5–15 min
   recipe on one repo.
6. **Effort nudge (item 6):** after W1 JSON exists, disable or no-op the
   soft nudge on Cursor/Claude/Antigravity if inherit already matches
   locked children; keep Codex default_subagent / spawn map. Then run
   the Cursor Explore-family ablation.
7. **Hook tune (item 5):** measure candidate-reminders action rate; quiet
   or drop the reminder, never the queue. Leave hard hooks untouched.

Optional eighth (only if 2 made host AGENTS still huge vs Codex 32 KiB):
split by nested directory files Codex can concatenate, or raise
`project_doc_max_bytes` in `$CODEX_HOME/config.toml` — measure first.

---

## What this pass did **not** verify

- Installed CLI/IDE versions on this host vs the docs above (Claude
  v2.1.198+ claims, Cursor 3.3+ Explore picker, local Codex build).
- Any 5–15 min CONCEPTS ablation (no Arm A/B, no token counts).
- Whether this host’s concatenated AGENTS chain actually hits Codex
  32 KiB (byte count not measured).
- Codex config key aliases (`max_threads` vs
  `max_concurrent_threads_per_session`; `default_subagent_model` in
  narrative vs config-reference table) against the binary here.
- Antigravity “GEMINI.md wins on AGENTS.md conflict” (harness-only).
- Antigravity `run_command` `bash -c` self-match (keep hook anyway).
- Cursor `subagentStart` `"ask"` → deny (forum only).
- Cursor Explore still switching off-family despite `model: inherit`
  (forum; that is why `guard-model-family` stays).
- Whether `lint_plan_waves.py` is enough without AGENTS plan-waves
  prose.
- Whether candidate-reminders are acted on.
- VS Code Google Antigravity extension vs Antigravity 2.0 vs CLI vs
  standalone IDE — docs were read for all surfaces; behavior was not
  clicked through.
- Hook payload field names against our adapters (no adapter audit;
  W3 owns git hooks).
- Candidate `2026-09-10-cross-harness-parallel-subagents` body (brief
  forbade other W*.md; this candidate was not opened).

---

## Keep vs cut (one screen)

**Keep:** host NFS/login-shell/sqlite/no-sudo/headless; hard hooks
(rm, wait-loop, model-family, destructive git); git-dev/test/prod
judgement; project-env; thin paper facts; project science; knowledge
queue; pointer-not-inline; Codex `CODEX_HOME` on `/var/tmp` + AGENTS
size cap awareness; Claude `@AGENTS.md` import.

**Cut / move later:** always-on bound-before-believing; tooling-meant-
to-evolve; MoQSplat style essays; review-fix; Cursor-only-parallel
prose; vendor-duplicating harness tutorials; paper skills/hooks until
thin AGENTS fails; effort-tier nudge on inherit-only harnesses (after
ablation); AGENTS duplicates of working hooks.
