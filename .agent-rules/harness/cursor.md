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
`subagent_type` and omit `model` so the file's frontmatter `model` applies;
an inline Task `model` currently wins over Explore-settings and can fight
the profile. Custom subagent files use YAML frontmatter; bracket options
(`composer-2.5[fast=false]`) work there, while the Task `model` enum only
accepts exact live slugs. Cursor has no separate subagent `effort` field —
the slug is the effort (`cursor-grok-4.6-medium` or `-high`). Escalate with
a fresh `stuck-escalation` child after `STUCK: out of ideas.` or a failed
check, not by resuming the previous child.

Global SoT agents live in `../agents/<name>.agent.md` and are linked into
`~/.cursor/agents/<name>.md` by `../scripts/install.py`. Shared project
agents stay real under `.claude/agents/` with `.cursor/agents` → symlink
when that tree exists. A project-only ladder may be real files in
`.cursor/agents/` (Cursor's native path; no `.claude` copy required).
Claude-oriented `tools:` frontmatter on those files is ignored here —
Cursor uses its own tool set; keep the prompt body tool-agnostic.

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
rung table. A `subagentStop` adapter `scripts/cursor/subagent-stop.py`
exists for the report contract; its wiring in `~/.cursor/hooks.json` and
the payload field name are pending verification from a Cursor session.

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

- Prose: project `AGENTS.md` (root and nested, always-on) and project
  `CLAUDE.md` (also always applied, for Claude Code compatibility).
  `.cursor/rules/*.mdc` adds frontmatter control — `alwaysApply`, `globs`,
  description-based selection — that plain `AGENTS.md` cannot express.
- Skills: Cursor reads `.cursor/skills/`, `.agents/skills/`, `.claude/skills/`
  and `.codex/skills/` per project, and the same four under `~/`. The host's
  global skills therefore already reach Cursor through `~/.claude/skills/` —
  no Cursor-specific skill copy is needed.
- Subagents: `~/.cursor/agents/` and `.cursor/agents/` are the native paths;
  `.claude/agents/` is also read as a compatibility path.
- Commands: `~/.cursor/commands/` and `.cursor/commands/`.
- MCP: `~/.cursor/mcp.json` and `.cursor/mcp.json`. Shared servers come from
  `../mcp/catalog.json` via `install.py`; marketplace plugin MCPs stay local.
- Hooks: `~/.cursor/hooks.json` (paths relative to `~/.cursor/`) and
  `.cursor/hooks.json` (paths relative to the project root). Events are
  lowerCamel (`beforeShellExecution`, `afterFileEdit`, `preToolUse`, `stop`,
  …). A command hook reads JSON on stdin and answers with JSON on stdout —
  `{"permission": "allow" | "ask" | "deny", "user_message": …,
  "agent_message": …}` — which is a *different contract* from Claude's
  `hookSpecificOutput` block, so each platform needs its own thin adapter over
  the shared guard logic in `../scripts/guardlib/`. Verified: `ask` works on
  `beforeShellExecution`; live 2026-07-28 it is **not** implemented for
  `preToolUse` / `subagentStart` (Cursor errors — use allow/deny only there).
  Verified payload fields for `beforeShellExecution`: top-level `command`,
  empty `cwd`, project root in `workspace_roots`. Live 2026-08-31: this hook
  is the agent Shell tool only. `vscode.git` called `/usr/bin/git` itself
  (Git.log); `git.pushForce` is that extension's command, not this hook.
  Default `git.allowForcePush` is false, so Force Push is hidden until a
  human enables it. Opening this folder, vscode.git finds a **parent**
  repo at `/home/itec/emanuele`; `git status` there over NFS is why the
  Source Control panel hangs. Workspace setting
  `git.openRepositoryInParentFolders: never` (`.vscode/settings.json`)
  stops that. `Read` of a file over 100,000 characters is refused and
  must be paginated with `offset`/`limit`; there is no must-read-before-edit
  rule and no 2000-line default page (unlike Claude Code).
  The irreversible-git guard is a boundary for agent shell commands.
  Commit, push, merge, rebase, `reset --hard` are allowed by that guard
  (live 2026-08-31 and again 2026-09-01). A standalone `git push --force`
  is denied with "Blocked a git operation that cannot be undone."
  Cursor also loads Claude Code hooks from `~/.claude/settings.json` when
  third-party skills are on. Claude's PreToolUse entries used
  `"command": "/usr/bin/env"` plus an `args` array. Cursor takes `command`
  and drops `args`, so it ran bare `env`, which dumps the environment to
  stdout. That is not JSON, and Cursor fail-closes the action as
  `Hook "/usr/bin/env" returned invalid JSON`. That blocked every Shell
  call, including `echo` and `git commit`, and it is not the git guard.
  Claude's `command` must be a single string Cursor can exec
  (`/usr/bin/python3 /path/script.py`). Do not use `command`+`args` with
  `/usr/bin/env` to set `PYTHONPYCACHEPREFIX`; instead assign
  `sys.pycache_prefix` inside the script (an `os.environ` write there does
  nothing — the variable is read at interpreter startup).
  `beforeShellExecution` timeout is 45s for NFS. Scripts use
  `#!/usr/bin/python3`. The Source Control panel bypasses this hook.
- `~/.cursor/skills-cursor/` is Cursor's own managed directory. Never edit or
  vendor anything into it.

## Knowledge loop (Cursor)

- Host SoT: `../candidates/`, skills `end-of-session`, `evaluate-candidates`,
  `handoff`. SessionStart runs `scripts/cursor/session-start.py` (pending-
  verification + open candidates reminders via `additional_context` + stderr;
  side-channel `~/.cursor/session-start.log` because Cursor may drop
  `additional_context` on a known IDE race).
- Progressive nudges (never force mid-task handoff): `beforeSubmitPrompt`
  (soft/log), `stop` (medium/stderr), `preCompact` (`user_message` strong).
  Shared policy in `../scripts/context_nudge.py`. Prefer handoff before
  auto-compact; context rot often starts ~50% fill. Live probe: `stop` does
  **not** carry `context_usage_percent` (see `~/.cursor/stop-probe.log`);
  medium nudges use the stop-count proxy. `stop` still appends payload keys
  to the probe log in case that changes.
- PreCompact also writes a resume stub under `../var/precompact/` (template
  only — the hook has no transcript). SessionStart re-surfaces a recent stub
  or project `HANDOFF.md`. Keep always-on rules session-stable; put volatile
  reminders in hook `additional_context` only (see README).
- Architecture diagrams: `../scripts/render_architecture.py` (`--check`
  freshness gate, standalone from `install.py`).
- Enforceable rules register: `../enforceable-rules.md`. Soft plan-wave
  linter: `../scripts/lint_plan_waves.py` (CLI + advisory from `stop` for
  plans touched in the last 7 days). Soft task-change stays log-only.
- `end-of-session`: invoke = commit consent; ask before push. Conditionally
  runs handoff as a step.
- Platform write-ownership: do not claim Claude/Antigravity hooks verified
  from here; leave tickets under `../candidates/pending-verification/`.
  Pickup docs: `HANDOFF-claude.md`, `HANDOFF-antigravity.md` at repo root.
