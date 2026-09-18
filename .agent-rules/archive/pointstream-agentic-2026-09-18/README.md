# PointStream agentic snapshot (2026-09-18)

Backup of PointStream’s agent-facing files, taken so they can be deleted
from the PointStream checkout and still restored from this coding-agent-config
branch: `archive/pointstream-agentic-2026-09-18`.

Paths under this directory match PointStream’s repo root
(`/home/itec/emanuele/pointstream/`), including the nested paper repo
`67a9ea6275d3d9785ce57026/`.

## Restore

```bash
SRC=/home/itec/emanuele/.agent-rules/archive/pointstream-agentic-2026-09-18
DST=/home/itec/emanuele/pointstream   # or a clone of PointStream
# copy tracked files back (skip this README and MANIFEST.txt)
rsync -a --exclude README.md --exclude MANIFEST.txt "$SRC"/ "$DST"/
```

Then commit **in the PointStream repo**, not here.

## Included

- Root `AGENTS.md`, `CLAUDE.md`, `PLAN.md`, `.agent-guards.json`
- Cursor agents + `host.mdc`, Antigravity `.agents/agents/`, Codex `config.toml`
- Copilot instructions (not CI workflows)
- `docs/workflow/` (session skill and dispatch notes)
- `docs/setup.md`, `docs/areas/infrastructure.md` (INFRA-ACT-01 / cleanup)
- Paper `AGENTS.md` / `CLAUDE.md`
- `scripts/cleanup_merged_worktrees.sh` (still unsafe; INFRA-ACT-01)

## Not included

Science area docs, evaluation-campaign *results*, paper TeX, GitHub Actions
CI/deploy workflows, datasets. Host SoT stays in `.agent-rules/` outside
this folder.

See `MANIFEST.txt` for the file list.
