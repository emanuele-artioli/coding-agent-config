# Claude Code — pending verification

Items that were authored or documented from another platform. Close each only
from a Claude Code session after live verification.

- [ ] Wire SessionStart reminder: `candidate-reminders.py` (or Claude adapter) in `~/.claude/settings.json`
- [ ] Wire Stop nudge toward `end-of-session` (fail-open, direct executable)
- [ ] Wire UserPromptSubmit task-change detection (optional; log or rare block)
- [ ] Wire PreCompact strong handoff / end-of-session nudge
- [ ] Confirm progressive-nudge messages appear in Claude's hook output channel
- [ ] Confirm global skills `end-of-session`, `evaluate-candidates`, `handoff` resolve via symlink farm
