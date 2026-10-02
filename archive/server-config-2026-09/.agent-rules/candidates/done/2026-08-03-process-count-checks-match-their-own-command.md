---
id: 2026-08-03-process-count-checks-match-their-own-command
created: 2026-08-03
source_platform: claude
source_project: /home/itec/emanuele/presley
axis: platform
status: applied
summary: A pgrep/ps/pkill from a harness Bash call matches the call's own command line — a count reads wrong, and a pkill -f kills its own shell
suggested_action: extend the harness wait-loop rule to cover counting and killing, not just waiting
verify_platforms: []
---

# Counting processes from a harness Bash call matches the check itself

**Surfaced:** 2026-08-03, PRESLEY operating-map Wave 2B (Claude Code subagent).
**Axis:** platform. **Status:** open, not yet applied to any rule file.

## What happened

An agent about to launch a metric backfill checked first whether another
backfill was already running — the project has a hard rule that two concurrent
backfills will write the same `result.json`, which is a corruption risk on a
gitignored, hours-expensive artifact.

The check reported **2 backfill processes**. The true count was **zero**. Both
"hits" were the checking command matching its own command string.

The agent noticed, re-checked with `ps ... | grep -v grep | wc -l`, got zero,
and proceeded correctly. But a less careful reading would have abandoned a
legitimate launch — or, in the opposite direction, a check written to confirm
something *is* running would have reported success against nothing.

## Why the existing rule does not cover it

`harness/claude.md` already forbids `until ! pgrep -f <pattern>; do sleep N;
done` wait-loops, for exactly this self-match reason. Two gaps:

1. **The existing rule is about *waiting*.** This was **counting** — a
   precondition check before launching, not a poll. Someone applying the rule
   as written would not think it applies, because there is no loop.
2. **The documented escape hatch does not work here.** The rule notes
   `[p]attern` "technically works". It does not, when the harness runs the
   whole command string through a wrapper that `eval`s it: the bracket trick
   defeats a literal `pgrep -f`, but the pattern still appears inside the
   wrapper's own command line, so the wrapper is matched instead.

## Proposed rule text

> **Any `pgrep`/`ps`/`grep` over the process table from a harness `Bash` call
> matches the call itself.** This is not only a wait-loop problem — it corrupts
> *counting* checks ("is something already running?") just as badly, and the
> `[p]attern` trick does not save you, because the pattern also sits in the
> wrapper's `eval` string. Filter the checker out explicitly
> (`| grep -v grep | wc -l`) and **sanity-check the count against a state you
> can see** — a log mtime, a lock file, a results directory — before acting on
> it. A count of zero that should be one is as dangerous as the reverse.

## Where it would go

`~/.agent-rules/harness/claude.md`, extending the existing waiting-for-long-
running-commands section rather than adding a new one — but note the rule
itself is tool-agnostic in substance (any agent shelling out hits this), so it
may belong in `AGENTS.md` with only the `Bash`-tool naming left in the harness
file. **That split is the judgement call to make when applying this.**

---

## Second occurrence, 2026-08-23, pointstream (Claude Code) — and it destroyed work

Same root cause, one step worse: the command **acted** on the self-match instead
of reporting it.

    pkill -f "pytest tests/invariants/test_metric_calibration" 2>/dev/null; sleep 1; \
      conda run ... python - <<'PYEOF' ...edit a test file... PYEOF

The harness runs this via `bash -c "<the whole string>"`, so the shell's own
command line contains the pattern. `pkill -f` matched it and **killed its own
shell**, taking the queued heredoc edit with it. The edit silently did not land.
The only symptom was exit code 144 — no error text, and the file looked
untouched for reasons that had nothing to do with the file.

`pgrep -f` returns a wrong number and you get a chance to notice. `pkill -f`
sends a signal, and what it kills may be the work you had lined up behind it.

**Rule this suggests, covering both occurrences:**

> A process check or kill issued from an agent's shell matches its own command
> line. Never pass `-f` a pattern that appears in the command you are typing.
> To inspect, use `ps -eo pid,args | grep -F <pattern> | grep -v grep`. To kill,
> take the PID from that listing, or use the harness's own task-stop mechanism
> for anything the harness started. Never chain other work behind a pattern
> kill in the same call.

This is now twice, on two projects and two axes (a count that was read, a kill
that was executed), which by the host's own standard makes it a rule rather than
a story.

---

## Resolution — 2026-08-31

**Applied** to `harness/claude.md`, extending the existing wait-loop section
("The same self-match ruins checks that are not loops"), covering both
occurrences: the count that read 2 against a true 0, and the `pkill -f` that
killed its own shell and swallowed a queued heredoc edit behind exit 144.

On the judgement call the candidate flagged: it stayed in the harness file
rather than moving to `AGENTS.md`. The substance is tool-agnostic, but the
mechanism is not — it is specifically that *this* harness runs the whole
command string through `bash -c`, so the pattern sits in the wrapper's own
command line. An agent whose shell-out does not work that way does not have the
bug. Splitting one short rule across two files to separate substance from
mechanism would cost more than it buys, and `AGENTS.md` is under length
pressure.
