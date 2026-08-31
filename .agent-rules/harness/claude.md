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

**The same self-match ruins checks that are not loops.** Any `pgrep`/`ps`/`pkill`
over the process table from a `Bash` call matches the call itself, because the
harness runs the whole string through `bash -c`. A *count* comes back silently
wrong — a "is a backfill already running?" check read 2 when the true answer was
0 — and `pkill -f` is worse: one killed its own shell and took a queued heredoc
edit with it, surfacing only as exit 144 with the file looking untouched.
Inspect with `ps -eo pid,args | grep -F <pattern> | grep -v grep`, kill by PID
or by the harness's own task-stop, sanity-check any count against a state you
can see (a log mtime, a lock file, a results directory), and never chain other
work behind a pattern kill in the same call.

Pick by duration, not by habit:

- **Finishes in < 10 min** → foreground `Bash` with an explicit `timeout`
  (ms, max 600000). This means the **tool parameter**, not the shell binary: a
  `timeout 900 …` inside the command still dies at the tool's 120 000 ms
  default, reporting `Command timed out after 2m 0s` as though the shell
  timeout misfired. A shell `timeout` can only shorten, never extend. Output
  arrives in one piece and the harness kills it at the deadline, so it cannot
  hang forever.
- **Longer than that** (GPU restoration, full evaluation passes, big
  backfills) → `Bash` with `run_in_background: true`. It detaches, survives
  across turns, and **re-invokes Claude on exit** with the path to its
  output file. Read that file; do not poll for it. **A "stopped" notification
  with no completion record does not mean the work failed** — check the
  artifacts (output dirs, log mtimes) before relaunching anything. One such
  notification described a ~6-hour GPU campaign that had finished all of its
  work and died during a later step.
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

## Reading a file is a precondition for editing it — so size matters

`Edit` refuses unless the file was read in this conversation, and a plain `Read`
pulls up to 2000 lines, so **appending one line to a big doc pays for the whole
doc, again after every compaction** (a 1008-line / 67 KB markdown file cost ~17k
tokens per session that touched it). Past ~25k tokens `Read` truncates and makes
you paginate. A partial read satisfies the precondition fine, but nobody
paginates a monolith because there is no way to know the right offset — so the
fix is structural: an index carrying entry *titles* plus per-section body files,
and pointers that name the specific body file. Unverified whether other
platforms couple read-before-edit the same way; see the pending-verification
checklists.

## Model family and effort tier (subagent spawns only)

Before spawning a subagent via `Agent`, assess the effort its task needs
(simple/bounded lookup vs. substantial multi-step work vs.
architecture-level judgment ≈ low/medium/high) and pass the `model` value
mapped for that tier in `../effort-models.json`. Omitting `model` (which
inherits the parent session) is still correct specifically when the
subagent's task is roughly the same effort as the parent's own — that's the
"no strong opinion" case, not the universal default. Do not pin versioned
slugs — they go stale; the file uses stable aliases (`sonnet` / `opus`).
None of this ever applies to your own top-level session model, which the
user picks freely.

Do not pass Grok, GPT, Gemini, or other off-family models unless the user
explicitly redirects the work. If Claude is clearly struggling on a task,
ask the user; prefer another platform/session over silently crossing family.
Live deny wiring (hard, family mismatch only): `../scripts/guard-model-family.py`.
The same script also asks for confirmation (soft — never blocks) when a
requested model is in-family but off the tier table, so a deliberate
off-tier pick still goes through once you confirm. See
`../candidates/pending-verification/claude.md`.

## Where Claude's own config lives

- Prose: `~/.claude/CLAUDE.md` is the **only** Claude user-level rules file
  (there is no `~/CLAUDE.md`). It `@`-imports this file and `../AGENTS.md`.
  Each project's `CLAUDE.md` is a thin wrapper importing that project's
  `AGENTS.md` only — host rules are already loaded from the user-level file.
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
  PreCompact writes a resume stub under `../var/precompact/` and names it in
  the injected message; SessionStart re-surfaces a recent stub or project
  `HANDOFF.md`. Always-on rule files stay session-stable — volatile reminders
  go through hook stdout only (see README).
