# Claude Code harness rules

Claude-Code-specific mechanics. Imported by `~/.claude/CLAUDE.md` alongside
the tool-agnostic host rules in `../../AGENTS.md`. Anything here that would also
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

`Edit` refuses unless the file was read in this conversation. A partial
read satisfies the precondition. Prefer an index plus per-section body
files over monoliths. Dated cost: `lessons/`. Unverified whether other
platforms couple read-before-edit the same way; see the
pending-verification checklists.

## Rungs (subagent spawns only)

The interactive model is whatever the user set in the Claude UI; that
session is the senior. Mapped rungs (`../effort-models.json`): junior
Opus low, escalation Opus xhigh. The `Agent` tool has no effort
parameter, so spawn a junior by agent name and omit `model` — effort
comes from the agent file's frontmatter, `effort: low` plus a
`maxTurns:` budget on juniors and `effort: xhigh` on `stuck-escalation`.
Hook entries in `settings.json` are snapshotted at session start, so a
new hook needs a fresh session. Dated spawn delay: `lessons/`. Do not
pin versioned slugs — the file uses stable aliases (`haiku` / `sonnet` /
`opus`). Haiku and Sonnet are in-family but off the rung table (soft
ask). This never overrides the user's session model.

Junior and escalation files also restrict `tools:`, set `omitClaudeMd:
true`, and carry the `agents/JUNIOR-FACTS.md` block in place of the
imported rules.

Do not pass Grok, GPT, Gemini, or other off-family models unless the user
explicitly redirects the work. If Claude is clearly struggling on a task,
ask the user; prefer another platform/session over silently crossing family.
Live deny wiring (hard, family mismatch only): `../../hooks/guard-model-family.py`.
The same script also asks for confirmation (soft — never blocks) when a
requested model is in-family but off the rung table, so a deliberate
off-rung pick still goes through once you confirm. A `SubagentStop` hook,
`subagent-stop.py` beside this file, checks the child's last message against
the report contract in skill `session` and warns the senior as a system
message; advisory, fail-open. See
`../../candidates/pending-verification/claude.md`.

## Knowledge loop (Claude Code)

Queue layout and how to file a candidate: `../../candidates/README.md`. The
procedure is the `end-of-session` skill; this platform's live-wiring status is
`../../candidates/pending-verification/claude.md`.
