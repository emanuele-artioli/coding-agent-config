# Antigravity — pending verification

Items that were authored or documented from another platform. Close each only
from an Antigravity session after live verification. Hook commands must be
**absolute paths**.

- [x] Wire SessionStart reminder in `~/.gemini/config/hooks.json` (absolute paths)
  (entry point: `/home/itec/emanuele/HANDOFF-antigravity.md`)
- [x] Wire Stop / PreInvocation nudge toward `end-of-session`
- [x] Wire progressive context nudges if event payloads support them
- [x] Confirm global skills resolve under `~/.gemini/config/skills/`
- [x] Confirm `pending-verification` SessionStart reminder is visible
- [x] Wire model-family gate in `~/.gemini/config/hooks.json` with an **absolute** path, e.g.
  `python3 /home/itec/emanuele/.agent-rules/scripts/antigravity/guard-model-family.py`
  on `PreToolUse` for the spawn tool that carries `model` (verified in Antigravity session;
  tools do not expose `model` parameter in schema, so subagents omit `model` and inherit Gemini parent session by construction)
- [x] Live deny test: off-family model → non-zero exit / blocked; omit or `gemini-*` → allow
  (script-level direct payload test verified exit code 2 on off-family model string as defense-in-depth)
- [x] **Tiered rule delivery (added 2026-07-28 from a Claude session — verified live in Antigravity).**
  Each project's `AGENTS.md` now marks some sections `<!-- scope: <globs> -->`.
  Antigravity reads `AGENTS.md` natively and in full; the `<!-- scope: ... -->`
  comments are inert HTML comments and all rules remain fully present in
  context. Verified live that generated `.claude/` files are not double-read,
  and host rules in `GEMINI.md` / `AGENTS.md` load cleanly without missing lines.
- [x] **Effort-tier nudge (added 2026-07-28 from a Claude session — verified live in Antigravity).**
  `scripts/antigravity/guard-model-family.py` logs (stderr, non-blocking) an
  effort-tier nudge when a model is in-family but off the tier table.
  Confirmed live: stderr is captured in harness logs on exit 0. Antigravity's
  hook API supports binary exit status (0 = allow, non-zero = block) without an
  interactive "ask" soft-confirm contract, so stderr logging is the exact
  intended behavior.
- [x] **Effort-settability for subagents (added 2026-07-28 from a Claude session — verified live in Antigravity).**
  Inspected Antigravity subagent tool schemas (`browser_subagent`). Subagent
  tools do not expose an `effort` parameter. Effort level is controlled at the
  harness/session level, so `effort` in `effort-models.json` is confirmed as
  informational metadata rather than an invocable tool parameter.
- [ ] **Read-before-edit cost of large files (added 2026-08-31 from a Claude session — not verified here).**
  On Claude Code, `Edit` refuses unless the file was read this conversation and a
  plain `Read` pulls up to 2000 lines, so appending one line to a 67 KB doc cost
  ~17k tokens per session, again after each compaction; past ~25k tokens `Read`
  truncates. Recorded in `harness/claude.md`, deliberately **not** promoted to
  `AGENTS.md` until this is checked elsewhere. What to confirm here: (a) does
  this platform's edit tool require a prior read of the file, (b) does a default
  read pull the whole file, (c) is there a per-call result cap that forces
  pagination. If all three hold on every platform, promote the rule to
  `AGENTS.md`; if it is Claude-only, it stays in `harness/claude.md`.
  Candidate: `done/2026-07-29-claude-read-edit-cost-of-big-files.md`.
- [ ] **Shell guard `antigravity/before-shell.py` (added 2026-08-31 from a Claude
  session — not verified here).** New adapter applying the shared `guardlib`
  shell policies in Antigravity's dialect: denies irreversible git
  (`destructive_git`), `rm` against protected trees (`destructive_rm`) and
  hand-rolled wait loops (`wait_loop`); advises on long runs and on committing
  straight to `main`. Its payload keys and the exit-status contract were
  inferred from `antigravity/guard-model-family.py`, not observed. Wire with an
  **absolute** path in `~/.gemini/config/hooks.json` (`python3 <abs-path>`), then
  confirm live: (a) `git push --force` is denied and the stderr reason is
  visible, (b) `git push -u origin <branch>` is allowed, (c) `git commit -m "do
  not push --force"` is allowed — the string must not trigger the guard. Until
  wired, this hook denies nothing.
