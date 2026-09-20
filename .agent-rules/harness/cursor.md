# Cursor harness rules

Cursor-specific mechanics, to sit alongside the tool-agnostic host rules in
`../AGENTS.md`.

**How this file reaches Cursor.** Cursor has no user-level rules file —
`~/.cursor/rules/` is not read. User Rules live in Settings as plain
text. Projects **need not** ship a pointer file. On this lab, paste the
User Rule in `../host.md`. Elsewhere, point a User Rule at this clone's
`AGENTS.md` and `harness/cursor.md`. Opening this repo also loads them.
A project `.mdc` that only points here is optional, never a copy.

NFS timings, `/var/tmp` editor-server paths, and parent-repo git-panel
hangs in this file apply **only when `host.md` is loaded**. Skip them on
a local disk. Wait-loop, subagent, and model-family rules still apply.

## Shell calls still pay a per-call tax — prefer the file tools

Observed 2026-07-25: three unrelated `Shell` calls each took 480–500 s.
That was the editor server on NFS. After moving it to `/var/tmp`, a
no-op `echo` from this session (2026-08-31) returned in ~5 s, of which
5.1 s was `before-shell.py` starting on NFS (guardlib import 2.4 s).
Ten one-liners are about a minute of hook overhead, not an hour. File
tools still win for anything that is just a read or an edit.

Consequences worth internalising:

- Use `Read`, `Glob`, and `Grep` instead of `cat`, `head`, `tail`, `ls`,
  `find`, and `rg`. They are fast here and are the documented preference
  anyway.
- Use `StrReplace`/`Write` instead of `sed`/`awk`/heredocs.
- When shell is genuinely required (git, conda, running a job), **batch
  every command into a single call** chained with `&&`.
- Budget `block_until_ms` accordingly: a call that "should" take two
  seconds still needs ~5 s of hook tax plus the work itself.
- `Read` refuses a file over 100,000 characters and must be paginated with
  `offset`/`limit`. There is no must-read-before-edit rule and no 2000-line
  default page here, unlike Claude Code.

## Waiting for long-running commands — never hand-roll a waiter

⛔ **Never write `until ! pgrep -f <pattern>; do sleep N; done` (or any
self-written poll loop) to wait for a job.** The command runs via
`bash -c "<the whole command string>"`, so the string *contains* the pattern
and `pgrep -f` matches the watcher's own process — the condition never becomes
true, the job finishes unnoticed, and the loop spins until timeout. This has
burned over an hour of wall clock on this host more than once, under more than
one agent. `guard-wait-loop.py` blocks the pattern at the
`beforeShellExecution` hook.

There is nothing to poll for, because Cursor already reports completion:

- **Finishes inside the block window** → plain `Shell` with `block_until_ms`
  sized to the expected runtime plus a generous buffer (see the slow-shell
  note above).
- **Longer than that** → `Shell` with `block_until_ms: 0`. It detaches,
  streams into a terminal file, and **notifies on completion at the end of the
  turn**. Do one status check afterwards to confirm it actually started, then
  get on with other work.
- **Need to block on the result because nothing else can proceed** →
  `AwaitShell` with that `shell_id`, sizing `block_until_ms` to the expected
  remaining runtime, optionally with `pattern` to return early on a known
  success or failure line.
- **Need progress while it runs** → `notify_on_output` with a pattern that
  matches failure signatures too (`Traceback|Error|FAILED|Killed|OOM`), not
  just the success marker. A success-only pattern stays silent through a crash,
  and silence is indistinguishable from "still running."

Do **not** poll a backgrounded job reflexively. `AwaitShell` is for the case
where the next step is genuinely blocked, or where the job needs close
monitoring (training runs, long migrations) — not as a habit.

Terminal files under `.cursor/projects/<workspace>/terminals/<id>.txt` carry
the live output plus a header (`pid`, `cwd`, `running_for_ms`) and, once
finished, a footer (`exit_code`, `elapsed_ms`). Read that file rather than
re-running the command.

`conda run -n <env> …` is not a completion-waiting strategy. Without
`--no-capture-output` it buffers everything until exit, so a long job shows
nothing and then hits the block deadline. Use it for env activation only.

## Subagents

`Task` subagents each get their own context window. Use `explore` for
broad codebase questions and a named agent for the job it was written
for: `implementer`, `paper-screener`, `data-condenser`, `paper-editor`,
`referee`, `gpu-job-runner`, `stuck-escalation`, plus whatever a project
adds. A background subagent notifies on completion — never `AwaitShell`
or sleep waiting for one.

Split genuinely independent workstreams across parallel subagents in one
message, per the host-wide plan-mode rule; keep sequential work in one agent.

Read skill `session` before the first `Task` spawn. If the project
`AGENTS.md` names its own ladder, follow that. Spawn juniors by
`subagent_type`. Generated `~/.cursor/agents/<n>.md` files carry the
in-family slug (`cursor-grok-4.6-medium`, escalation `-high`). Do **not**
rely on the shared source `model: opus` — live 2026-09-20 that value is
resolved to `claude-opus-5-thinking-high` at `subagentStart` even when the
Task call passed `inherit`, and the family gate denies the spawn. An
inline Task `model` currently wins over Explore-settings for built-in
types, but a custom agent's file model still wins at `subagentStart`.
Custom subagent files use YAML frontmatter; bracket options
(`composer-2.5[fast=false]`) work there, while the Task `model` enum only
accepts exact live slugs. Cursor has no separate subagent `effort` field —
the slug is the effort (`cursor-grok-4.6-medium` or `-high`). Escalate with
a fresh `stuck-escalation` child after `STUCK: out of ideas.` or a failed
check, not by resuming the previous child.

Global SoT agents live in `../agents/<name>.agent.md`. `../scripts/install.py`
writes Cursor-native copies into `~/.cursor/agents/<name>.md` (ownership
markers, in-family `model`, Claude-only fields omitted). Shared project
agents stay real under `.claude/agents/` with `.cursor/agents` → symlink
when that tree exists. A project-only ladder may be real files in
`.cursor/agents/` (Cursor's native path; no `.claude` copy required).
Claude-oriented `tools:`, `omitClaudeMd`, `maxTurns`, and `effort`
frontmatter is unsupported here — Cursor uses its own tool set and the
slug is the effort; keep the prompt body tool-agnostic.

## Rungs (subagent spawns only)

The interactive model is whatever the user set in the Cursor UI; that
session is the senior. Mapped rungs (`effort-models.json`): junior and
senior are `cursor-grok-4.6-medium`, escalation is the `-high` slug. There
is no effort field here — the slug is the effort, and `-high` is optional
thinking, not a different model family. Omit `model` when the junior should
match the senior. Do not pin versioned slugs in host prompts. This never
overrides the user's session model.

Never pass Claude / GPT (or other off-family) models because a skill table
said so. The Cursor marketplace **pstack** plugin’s multi-family defaults
(`/setup-pstack`, arena / interrogate panels) ignore which IDE you are on
and are **untrusted** here — do not follow them. `before-task.py` on
`preToolUse`/`Task` and `subagentStart` hard-denies off-family spawns; when
a model is in-family but off the rung table it still returns
`{"permission": "allow"}` and logs the nudge to
`~/.cursor/model-family-hook.log` (also echoed as `agent_message`). Live
2026-07-28: `{"permission": "ask"}` on this hook is rejected by Cursor
("ask … for preToolUse hooks is not yet implemented") — so do not use ask
here until that lands. `ask` remains valid for `beforeShellExecution`.
Rung matching accepts Cursor’s live slugs (`cursor-grok-4.6-medium` ≡
`grok-4.6`); product variants like `composer-2.5-fast` / `grok-4.6-fast`
still nudge. Composer stays in-family for the hard gate but is off the
rung table. Cursor also loads Claude's `~/.claude/settings.json` hooks:
`guard-model-family.py` must no-op on Cursor-shaped payloads
(`cursor_version` or `preToolUse`/`subagentStart`), otherwise an explicit
`cursor-grok-4.6-high` spawn is denied as off-family for Claude. A
`subagentStop` adapter `scripts/cursor/subagent-stop.py` is wired in
`~/.cursor/hooks.json`; the payload field for the child's final message
is logged to `~/.cursor/subagent-stop.log` until the first live payload
is trimmed.

If in-house models are clearly struggling, ask the user; prefer switching
platform/session over silently crossing family. Settings hygiene: Explore
subagent model → inherit or in-house; Fast mode can force cheaper variants.

## Slash commands

Plain markdown under `~/.cursor/commands/<name>.md` (global) or
`.cursor/commands/<name>.md` (project). Filename = `/name`. Host-wide prompts
are authored once in `../workflows/` and linked by `install.py`. Project
prompts live in `.agents/workflows/` with `.cursor/commands` → symlink so
Antigravity and Cursor share one tree. Prefer a skill over a command when the
workflow should also auto-trigger from a description match.

## Where Cursor's own config lives

Every path, hook event name and payload shape: `../README.md`, sections
"Global tool locations per platform" and "Hooks".

## Knowledge loop (Cursor)

Queue layout and how to file a candidate: `../candidates/README.md`. The
procedures are the `end-of-session`, `evaluate-candidates` and `handoff`
skills; this platform's live-wiring status is
`../candidates/pending-verification/cursor.md`.
