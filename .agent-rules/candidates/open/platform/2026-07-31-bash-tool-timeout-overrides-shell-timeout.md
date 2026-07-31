---
id: 2026-07-31-bash-tool-timeout-overrides-shell-timeout
created: 2026-07-31
source_platform: claude
source_project: /home/itec/emanuele/presley
axis: platform
status: open
summary: Claude Code's Bash tool caps at its own 120s default regardless of a `timeout 900` inside the command — and a completed background job can report "stopped" with no completion record
suggested_action: add both to harness/claude.md's waiting-for-long-commands section
verify_platforms: [claude]
---

Two distinct traps, both hit in one session, both in the same area the existing
"never hand-roll a waiter" rule covers.

## 1. Shell `timeout` does not raise the Bash tool's ceiling

```
timeout 900 python long_thing.py     # <- killed at 120s, not 900s
```

The `timeout` binary bounds the *command*; the harness independently bounds the
*tool call* at its **120 000 ms default**. The smaller wins, so a command wrapped
in a generous shell `timeout` still dies at two minutes, and the error reads
`Command timed out after 2m 0s` — which looks like the shell timeout misfiring
rather than a separate limit.

**Rule:** to allow more than 2 minutes, pass the tool's own `timeout` parameter
(ms, max 600 000). A shell `timeout` is then still useful as an inner bound, but
it can only ever shorten, never extend.

The existing harness rule already says "foreground `Bash` with an explicit
`timeout` (ms, max 600000)" — worth making explicit that this means the **tool
parameter**, and that the shell builtin does not substitute for it, because the
natural reading is that either works.

## 2. "stopped" in a background-task notification does not mean the work failed

A background `Bash` job was reported as:

> No completion record was found for this background shell command... It may have
> been stopped... or it may have been running when the previous Claude Code
> process exited.

The job had in fact **completed all of its work**; it died afterwards, during a
later step. Treating "stopped" as "did not finish" would have relaunched a
finished ~6-hour GPU campaign.

**Rule:** on a `stopped` notification, check the *artifacts* before concluding
anything — output files, result directories, log timestamps. Do not infer
progress from the notification, and do not infer it from `pgrep` either: the
harness runs the command via `bash -c "<whole string>"`, so `pgrep -f <pattern>`
matches the checking command itself and reports a live process that is only ever
the check. (`ps -eo cmd | grep "[p]attern"` or checking artifact mtimes both
avoid this; the existing wait-loop rule covers the same self-match hazard from a
different angle.)

Corollary worth stating alongside the existing hourly-checkpoint rule: the reason
the finished work survived a process death at all is that the job wrote **one
output directory per unit of work as it completed**, so the crash cost only the
in-flight item. That is what makes "check the artifacts" a reliable recovery path
rather than a guess.
