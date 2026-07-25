#!/usr/bin/env bash
# Vendors the canonical sync_agent_rules.py into each project's tools/
# directory. sync_agent_rules.py can't be referenced centrally by absolute
# path like the hooks in this directory are -- it's invoked by CI in both
# projects (and pre-commit in pointstream), and CI runners have no access to
# ~/.agent-rules/ at all. So each project keeps a real, physical copy, and
# this script is the propagation step: edit
# ~/.agent-rules/scripts/sync_agent_rules.py, then run this, and every
# project's copy is updated in one step instead of four hand-edits.
#
# Migration guard: the current script treats AGENTS.md as the hand-edited
# source and CLAUDE.md as a wrapper that imports it. Copying it into a project
# still laid out the old way round -- CLAUDE.md canonical, AGENTS.md generated
# -- would make the next run rewrite that project's AGENTS.md over its own
# generated content and delete files it still depends on. So a project is
# skipped, loudly, until its CLAUDE.md imports AGENTS.md.
#
# Not runnable in CI and not meant to be.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/sync_agent_rules.py"
PROJECTS=(
  /home/itec/emanuele/pointstream
  /home/itec/emanuele/presley
  /home/itec/emanuele/moq3dgs
  /home/itec/emanuele/TIGAS
)

for repo in "${PROJECTS[@]}"; do
  dst="$repo/tools/sync_agent_rules.py"
  if [[ ! -f "$dst" ]]; then
    echo "skip (no tools/sync_agent_rules.py found): $repo" >&2
    continue
  fi
  if ! grep -q '@AGENTS\.md' "$repo/CLAUDE.md" 2>/dev/null; then
    echo "SKIP (not migrated: CLAUDE.md does not import AGENTS.md): $repo" >&2
    continue
  fi
  if diff -q "$SRC" "$dst" >/dev/null 2>&1; then
    echo "up to date: $dst"
  else
    cp "$SRC" "$dst"
    echo "updated:    $dst"
  fi
done
