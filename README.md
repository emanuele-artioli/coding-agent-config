# coding-agent-config

Shared fleet rules, skills, and hooks for coding agents across projects
and harnesses (Claude Code, Cursor, Antigravity, Codex, Copilot).

**Projects do not need their own AGENTS.md, skills, or agents.** Install
this repo, point the harness at it, and work in a normal git checkout.

**This GPU/NFS host is optional.** Portable rules live in
[`.agent-rules/AGENTS.md`](.agent-rules/AGENTS.md). Lab facts live in
[`.agent-rules/host.md`](.agent-rules/host.md) — other machines skip that
file. Edit [`effort-models.json`](.agent-rules/harness/effort-models.json) for
your own bill; the checked-in map is the author's.

The source of truth is [`.agent-rules/`](.agent-rules/): `AGENTS.md`,
`host.md`, `harness/`, `hooks/`, and `scripts/`. Edit portable content there, never
in a per-agent copy.

## Install

```bash
python3 .agent-rules/scripts/install.py
python3 .agent-rules/scripts/install.py --check
```

`install.py` only links into agent directories that already exist and
reports conflicts instead of clobbering real files.

## Skills

Four hats. The senior is the session.

| Skill | When |
|---|---|
| `session` | dispatch, intake, escalation, when to ask |
| `engineer` | plan as signatures plus three-group tests |
| `paper` | markers, literature, figures, measurement |
| `end-of-session` | closeout, `HANDOFF.md`, candidates, commit |

Juniors: `implementer`, `paper-screener`, `data-condenser`, `paper-editor`,
`referee`, `gpu-job-runner`, `stuck-escalation`.

## Layout

On the author's machine this git repo is the home directory, with an
allowlist [`.gitignore`](.gitignore). Clone `.agent-rules/` (or the whole
repo) anywhere convenient if you adapt the idea elsewhere.
