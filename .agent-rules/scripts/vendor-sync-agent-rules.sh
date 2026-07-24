#!/usr/bin/env bash
# Vendors the canonical sync_agent_rules.py into each project's tools/
# directory. sync_agent_rules.py can't be referenced centrally by absolute
# path like the hooks in this directory are -- it's invoked by CI in both
# projects (and pre-commit in pointstream), and CI runners have no access to
# ~/.agent-rules/ at all. So each project keeps a real, physical copy, and
# this script is the propagation step: edit
# ~/.agent-rules/scripts/sync_agent_rules.py, then run this, and both
# projects' copies are updated in one step instead of two hand-edits.
#
# Not runnable in CI and not meant to be -- same trust model each project's
# own tools/host_rules_snapshot.md already operates under: refreshed locally
# when the source is reachable, never enforced on CI.
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
  if diff -q "$SRC" "$dst" >/dev/null 2>&1; then
    echo "up to date: $dst"
  else
    cp "$SRC" "$dst"
    echo "updated:    $dst"
  fi
done
