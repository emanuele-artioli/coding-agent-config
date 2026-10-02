# 2026-09-20 — subagentStop payload

`subagentStop` fires and logs keys to `~/.cursor/subagent-stop.log`. The
native payload has no child-final-text field, so the adapter cannot flag
a broken report. Same as Antigravity here. `task` in that payload is the
prompt, not the child's last message.
