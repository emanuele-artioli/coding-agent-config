# Claude Code harness rules

Claude-Code-specific mechanics. Imported by `~/.claude/CLAUDE.md` alongside
the tool-agnostic host rules in `../AGENTS.md`. Anything here that would also
be true for another agent belongs in `../AGENTS.md` instead; anything that
names a Claude tool (`Bash`, `Monitor`, `ScheduleWakeup`, `run_in_background`)
belongs here, because those names are wrong or absent in every other agent.

## Waiting for long-running commands — never hand-roll a waiter

⛔ **Never write `until ! pgrep -f <pattern>; do sleep N; done` (or any
self-written poll loop) to wait for a job.** The harness runs the loop via
`bash -c "<the whole command string>"`, and that string *contains* the
pattern — so `pgrep -f` matches the watcher's own process and the condition
can never become true. The job finishes, the watcher spins until timeout, and
the completion goes unnoticed. This has already burned >1h of wall clock.
Escaping tricks (`[p]attern`, `pgrep -P`) technically work but are still the
wrong answer: the harness already reports completion, so there is nothing to
poll for. `guard-wait-loop.py` blocks this pattern at the `PreToolUse` hook.

Pick by duration, not by habit:

- **Finishes in < 10 min** → foreground `Bash` with an explicit `timeout`
  (ms, max 600000). Output arrives in one piece and the harness kills it at
  the deadline, so it cannot hang forever.
- **Longer than that** (GPU restoration, full evaluation passes, big
  backfills) → `Bash` with `run_in_background: true`. It detaches, survives
  across turns, and **re-invokes Claude on exit** with the path to its
  output file. Read that file; do not poll for it.
- **Need progress while it runs** → `Monitor`, with a filter that matches
  failure signatures too (`Traceback|Error|FAILED|Killed|OOM`), not just the
  success marker — a success-only filter stays silent through a crash, and
  silence is indistinguishable from "still running."

`conda run -n <env> …` is not a solution to this. It is still a foreground
command subject to the same 10-minute cap, and without
`--no-capture-output` it buffers all output until exit — so on a long job it
shows nothing and then gets killed. Use it for env activation if convenient,
never as a completion-waiting strategy.

Note: `Monitor`'s progress-matching depends on the logging cadence described
in the shared "Long jobs must checkpoint" rule — a job that goes quiet for
more than ~10 minutes gives Monitor nothing fresh to match, which looks
identical to a hang.

Same trap, different tool: **`ScheduleWakeup` is not a wait-for-completion
mechanism.** It exists solely to self-pace `/loop` dynamic-mode iterations.
A background agent or background `Bash` job already triggers a notification
the moment it finishes — there is nothing to poll for. Don't call
`ScheduleWakeup` "just to wait" for one; it also fails outright when used
this way (it requires a `prompt` unless `stop: true`), so the mistake
surfaces immediately rather than silently wasting a turn — still worth not
repeating.

## Model family

Prefer **omitting `model` on `Agent`** so the subagent inherits the parent
session (Claude in-house). Do not pin versioned slugs — they go stale. If
you must pass a model, use only the Claude family (including stable aliases
like `sonnet` / `opus` / `haiku`).

Do not pass Grok, GPT, Gemini, or other off-family models unless the user
explicitly redirects the work. If Claude is clearly struggling on a task,
ask the user; prefer another platform/session over silently crossing family.
Live deny wiring: `../scripts/guard-model-family.py` (see
`../candidates/pending-verification/claude.md`).

## Where Claude's own config lives

- Prose: `~/.claude/CLAUDE.md` (this file's importer) and each project's
  `CLAUDE.md`, which is a thin wrapper importing that project's `AGENTS.md`.
- Skills: `~/.claude/skills/<name>/SKILL.md`, symlinked into
  `../skills/<name>/`. Claude Code follows symlinks out of the skills
  directory and reads the target's `SKILL.md`, which is what makes the
  symlink farm work.
- Subagents: `~/.claude/agents/<name>.md`, symlinked into `../agents/`.
- Hooks: `~/.claude/settings.json`, keyed by event name (`PreToolUse`,
  `PostToolUse`, `UserPromptSubmit`, `Stop`, `SessionStart`, …), invoking the
  Claude-dialect entry points in `../scripts/`. User- and project-level hooks
  both fire; the more specific level does not override.

## Knowledge loop (Claude Code)

- Shared queue and skills live under `../candidates/` and `../skills/`
  (`end-of-session`, `evaluate-candidates`, `handoff`).
- SessionStart / Stop / UserPromptSubmit / PreCompact wired in
  `~/.claude/settings.json` → `../scripts/claude/{session-start,stop,
  user-prompt-submit,pre-compact}.py`. All four are direct-executable
  (chmod +x, no `python3` prefix) so a missing file fails open rather than
  turning into an interpreter error; `stop.py` and `user-prompt-submit.py`
  always exit 0 regardless of nudge content, since Stop's exit 2 blocks
  Claude from stopping and would turn an advisory into a hang. Driven with
  sample payloads (see `../candidates/pending-verification/claude.md`) —
  true live-session firing still needs confirming from a fresh session.
- UserPromptSubmit soft task-change nudge stays log-only
  (`CONTEXT_NUDGE_BLOCK_SOFT` unset) per the locked decision in
  `HANDOFF-claude.md`.
- Model-family gate wired: `PreToolUse` matcher `Agent|Task` →
  `../scripts/guard-model-family.py` (`python3 <path>`, fail-closed). Note:
  the `Agent` tool's own schema already restricts `model` to the Claude
  family (`sonnet|opus|haiku|fable`), so an off-family spawn attempt is
  rejected before the hook even runs — the hook is defense-in-depth here,
  not the primary gate, at least until a spawn path with a looser schema is
  found.
- `end-of-session` commits on invoke and asks before push; handoff is a
  conditional step or a standalone skill.
- Prefer handoff before auto-compact; do not wait for full context.
