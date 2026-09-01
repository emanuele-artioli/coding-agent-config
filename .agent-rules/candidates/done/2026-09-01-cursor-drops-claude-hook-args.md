---
id: 2026-09-01-cursor-drops-claude-hook-args
created: 2026-09-01
source_platform: cursor
source_project: .
axis: platform
status: needs_verification
summary: Cursor loads Claude Code hooks but drops the args array, so command /usr/bin/env with args becomes a bare env that fail-closes every Shell call
suggested_action: keep Claude PreToolUse command as a single /usr/bin/python3 /path string; never command+args through env
verify_platforms: [claude]
---

Evaluated 2026-09-01 from Cursor. Applied to shared SoT and to the live
Claude config (the latter because it was breaking every Cursor Shell call).
Not claimed verified on Claude.

**Applied**

- `harness/claude.md` and `harness/cursor.md`: do not wire Claude
  PreToolUse as `"command": "/usr/bin/env"` plus `args`. Use one string,
  `/usr/bin/python3 /path/script.py`. Set `PYTHONPYCACHEPREFIX` inside
  the script.
- `~/.claude/settings.json`: four PreToolUse entries converted to that
  shape.
- `scripts/guard-{wait-loop,git,rm,model-family}.py`:
  `os.environ.setdefault("PYTHONPYCACHEPREFIX", "/var/tmp/emanuele-pycache")`
  before importing guardlib.
- Live Cursor: `echo ping` returned, `/tmp` commit allowed, standalone
  `git push --force` denied. Did **not** put this in `AGENTS.md`; it is a
  Cursor-import quirk, not a host-wide rule.

**Needs Claude**

Confirm from a Claude Code session that Bash PreToolUse (wait-loop,
irreversible git, protected rm) and `Agent|Task` still fire with the
python3 command strings. Ticket:
`candidates/pending-verification/claude.md`. Do not restore
`command`+`args` through `/usr/bin/env`.
