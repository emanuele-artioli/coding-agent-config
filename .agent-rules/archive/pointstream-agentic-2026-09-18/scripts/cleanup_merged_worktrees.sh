#!/usr/bin/env bash
# Clean up linked git worktrees whose commits are fully merged into origin/main.
# Never removes worktrees with unstaged, staged, or untracked changes.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$REPO_ROOT" ]; then
    echo "Error: Not inside a git repository." >&2
    exit 1
fi

cd "$REPO_ROOT"

# Fetch latest origin/main ref quietly
git fetch origin main --quiet 2>/dev/null || true

MAIN_WT="$REPO_ROOT"
CURRENT_WT=""
IS_DETACHED=0
CURRENT_BRANCH=""
HEAD_SHA=""

while IFS= read -r line; do
    case "$line" in
        worktree\ *)
            CURRENT_WT="${line#worktree }"
            IS_DETACHED=0
            CURRENT_BRANCH=""
            HEAD_SHA=""
            ;;
        bare)
            CURRENT_WT=""
            ;;
        HEAD\ *)
            HEAD_SHA="${line#HEAD }"
            ;;
        branch\ *)
            CURRENT_BRANCH="${line#branch refs/heads/}"
            ;;
        detached)
            IS_DETACHED=1
            ;;
        "")
            if [ -n "$CURRENT_WT" ] && [ "$CURRENT_WT" != "$MAIN_WT" ]; then
                if [ ! -d "$CURRENT_WT" ]; then
                    echo "[CLEANUP] Pruning missing worktree reference: $CURRENT_WT"
                    git worktree prune
                    CURRENT_WT=""
                    continue
                fi

                # Safety check 1: dirty files, staged changes, or untracked files
                DIRTY_STATUS="$(git -C "$CURRENT_WT" status --porcelain 2>/dev/null || true)"
                if [ -n "$DIRTY_STATUS" ]; then
                    echo "[SKIP] Worktree has uncommitted or untracked changes: $CURRENT_WT"
                    CURRENT_WT=""
                    continue
                fi

                # Safety check 2: verify commit ancestry against origin/main
                if [ "$IS_DETACHED" -eq 1 ]; then
                    if [ -n "$HEAD_SHA" ] && git merge-base --is-ancestor "$HEAD_SHA" origin/main 2>/dev/null; then
                        echo "[CLEANUP] Removing detached merged worktree: $CURRENT_WT"
                        git worktree remove "$CURRENT_WT" 2>/dev/null || rm -rf "$CURRENT_WT"
                    else
                        echo "[SKIP] Detached worktree $CURRENT_WT ($HEAD_SHA) is not in origin/main"
                    fi
                elif [ -n "$CURRENT_BRANCH" ]; then
                    UNMERGED="$(git log origin/main.."$CURRENT_BRANCH" --oneline 2>/dev/null || true)"
                    if [ -z "$UNMERGED" ]; then
                        echo "[CLEANUP] Removing merged worktree: $CURRENT_WT (branch: $CURRENT_BRANCH)"
                        git worktree remove "$CURRENT_WT" 2>/dev/null || rm -rf "$CURRENT_WT"
                        echo "[CLEANUP] Deleting merged local branch: $CURRENT_BRANCH"
                        git branch -d "$CURRENT_BRANCH" 2>/dev/null || true
                    else
                        echo "[SKIP] Worktree $CURRENT_WT (branch: $CURRENT_BRANCH) has unmerged commits:"
                        echo "$UNMERGED"
                    fi
                fi
            fi
            CURRENT_WT=""
            ;;
    esac
done < <(git worktree list --porcelain; echo "")

git worktree prune 2>/dev/null || true
git remote prune origin 2>/dev/null || true
