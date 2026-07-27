---
name: handoff
description: Prepare a handoff document so another agent/tool (Cursor, Codex, Copilot, a fresh Claude session, a human) can pick up in-progress work with no shared memory. Use when approaching a rate limit, session limit, or context rot, when a resource this session depends on becomes unavailable (a GPU host is full, an API is down), when progressive context nudges are accepted, or whenever the user says "hand off", "continue in cursor/codex/etc", or "prepare a handoff". Prefer this before harness auto-compact — context rot starts around ~50% fill. Also used as a step inside end-of-session when work remains.
---

# Preparing a handoff

The receiving agent has **zero memory of this conversation** — no chat
history, no task list, no sense of what's been tried. Everything it needs
must live in one self-contained document plus the state already committed to
disk (branches, commits, files). Treat this the same way you'd brief a
teammate taking over your desk while you're on a flight with no wifi: assume
nothing carries over except what you write down and what's already saved.

Do **not** wait for context to be full or for auto-compact. Prefer a clean
handoff at a natural boundary once nudges say the session is warm. Mid-task
forced handoff at ~50% is still wrong — finish the current unit of work, then
hand off.

## Where it goes

Write `HANDOFF.md` at the root of the primary repo the work is in (or a
clearly-named file next to related ones if multiple repos are involved —
name each `HANDOFF-<repo-or-area>.md` and cross-link them). Don't bury it in
a scratchpad the other agent won't know to look for. If the project already
has a memory/log convention (a `RESEARCH_LOG.md`, a reviewer-response
checklist, a `CLAUDE.md`), link to those rather than duplicating their
content — the handoff doc is the entry point, not a copy of everything.

## What triggered this handoff (always state explicitly, first)

Name the actual constraint causing the handoff — rate limit, session length,
context rot / nudge, a resource outage — and anything the receiving agent
needs to know about it operationally: e.g. "the shared GPU server is fully
occupied by another user's job as of `<timestamp>`, unrelated to anything we
launched — don't assume it's our own stalled process; check `nvidia-smi`'s
process list before concluding the GPU is free" or "this session's rate
limit resets at `<time>`, so if you're a fresh Claude session resuming
later rather than a different tool, check whether waiting is simpler than a
cross-tool handoff." If the receiving agent is expected to work around the
constraint (e.g. "try a different server"), say so directly rather than
letting it discover the problem itself.

## Required sections

1. **One-paragraph summary of the overall task** — what's being built/fixed
   and why, in plain language, as if explaining to someone who has never
   seen this project. Link the original request/plan if one exists (a saved
   plan file, an issue, a design doc).
2. **Current state, verified not assumed** — for every repo/branch/worktree
   involved: exact branch name, whether it's merged/pushed/still open, and
   the *last verified* state (re-run a quick check — `git status`, `git log
   -1`, a test command — while writing this section; don't transcribe a
   stale belief from earlier in the conversation). Distinguish clearly
   between "done and verified", "done but unverified", and "in progress".
3. **What's actually running or queued right now** — any background job,
   GPU process, or long-running task that will still be alive when this
   session ends. Give the receiving agent a command to check its live
   status (not just "it should still be running") and explicitly say
   whether killing it is safe or would lose work.
4. **Open questions / decisions not yet made** — anything a human or the
   receiving agent needs to weigh in on before proceeding, phrased as an
   actual question with the options you'd considered, not just a vague
   "TBD". If the user raised specific questions this session didn't finish
   answering, carry them over verbatim rather than paraphrasing away detail.
5. **Immediate next steps, in order** — a short, concrete list of what to do
   first, second, third. Prefer "run X, expect Y" over abstract goals.
6. **Landmarks** — the small set of files/directories the receiving agent
   will need repeatedly (config, the main entry point, the test command, the
   log/memory file, any relevant skill). A few lines, not a directory tree.

## Tone and scope

Err toward over-including operational gotchas (a flaky command, an
environment quirk, a wrong assumption already corrected this session) over
re-explaining things the receiving agent can read for itself in the code —
its own exploration is cheap, re-discovering a gotcha that already cost this
session time is not. Keep the summary/next-steps sections tight; let the
"landmarks" section point at detail rather than inlining it.

## After writing it

Tell the user where the file is and, in one or two sentences, what the
receiving agent should do first. Do not act as though the handoff is
authorization to stop mid-task on your own initiative — only produce one
when the user actually asks for it, accepts a nudge, or the triggering
constraint (rate limit, outage, compaction) is genuinely imminent.

When called as a step of `end-of-session`, return to that skill for commit /
push after the handoff file exists.
