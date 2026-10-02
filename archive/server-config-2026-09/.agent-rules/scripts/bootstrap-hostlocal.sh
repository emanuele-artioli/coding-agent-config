#!/usr/bin/env bash
# Create this host's local scratch directories, and point Python's bytecode
# cache at them.
#
# WHY THIS EXISTS
#
# Home is one NFS export shared by every machine here (gpu5, gpu6, …), but
# `/var/tmp` is local disk on each. So a symlink written into the shared home
# resolves to a *different* directory on every host — and to a **missing** one
# on any host where nobody created it.
#
# That is not hypothetical. On 2026-08-31 `~/.cursor-server` was symlinked to
# `/var/tmp/emanuele-editor-servers/cursor-server` to get the editor server off
# NFS. It fixed gpu5 and silently broke gpu6, where the target did not exist and
# the editor could not install its server at all: the connection was refused
# with nothing in any log to explain it.
#
# The rule this encodes: **anything placed on local disk must be created on
# every host, because the symlink pointing at it is shared and the target is
# not.**
#
# Idempotent, silent, and safe to run any number of times from any host.
# Sourced from ~/.bashrc so it runs before an editor tries to install its
# server. Also runnable directly.

# Deliberately no `set -u`/`set -e`: this file is *sourced* from ~/.bashrc, so
# any shell option it sets leaks into the caller's interactive shell and turns
# every later unset-variable reference into a fatal error. A bootstrap must
# not change the shell it is bootstrapping.

HOSTLOCAL_SERVERS="/var/tmp/emanuele-editor-servers"
HOSTLOCAL_PYCACHE="/var/tmp/emanuele-pycache"
HOSTLOCAL_CODEX="/var/tmp/emanuele-codex"
HOSTLOCAL_CODEX_BIN="/var/tmp/emanuele-codex-bin"

# Codex app-server state must be host-local. All GPU machines share the same
# NFS home, but Unix sockets, startup locks, SQLite WAL files and temporary
# arg0 directories are machine-local resources. Sharing ~/.codex made every
# reconnect race on the same control socket and databases, leaving many stale
# app-server processes and eventually blocking in NFS I/O.
mkdir -p "$HOSTLOCAL_CODEX" "$HOSTLOCAL_CODEX_BIN" 2>/dev/null || true
chmod 700 "$HOSTLOCAL_CODEX" "$HOSTLOCAL_CODEX_BIN" 2>/dev/null || true

# Synchronize durable settings from the shared configuration when it changes. Runtime state stays local;
# Authentication is seeded once; configuration follows the shared source.
if [ -f "$HOME/.codex/config.toml" ] && { [ ! -e "$HOSTLOCAL_CODEX/config.toml" ] || [ "$HOME/.codex/config.toml" -nt "$HOSTLOCAL_CODEX/config.toml" ]; }; then
    install -m 600 "$HOME/.codex/config.toml" "$HOSTLOCAL_CODEX/config.toml" 2>/dev/null || true
fi
if [ ! -e "$HOSTLOCAL_CODEX/auth.json" ] && [ -f "$HOME/.codex/auth.json" ]; then
    install -m 600 "$HOME/.codex/auth.json" "$HOSTLOCAL_CODEX/auth.json" 2>/dev/null || true
fi

# Keep future standalone updates host-local too. Until the first local update,
# a local symlink reuses the already installed binary without duplicating it.
if [ ! -e "$HOSTLOCAL_CODEX_BIN/codex" ] && [ -x "$HOME/.local/bin/codex" ]; then
    ln -s "$(readlink -f "$HOME/.local/bin/codex")" "$HOSTLOCAL_CODEX_BIN/codex" 2>/dev/null || true
fi

export CODEX_HOME="$HOSTLOCAL_CODEX"
export CODEX_SQLITE_HOME="$HOSTLOCAL_CODEX"
export CODEX_INSTALL_DIR="$HOSTLOCAL_CODEX_BIN"
case ":$PATH:" in
    *":$HOSTLOCAL_CODEX_BIN:"*) ;;
    *) export PATH="$HOSTLOCAL_CODEX_BIN:$PATH" ;;
esac

# Editor servers. Empty directories are enough: Cursor and VS Code install into
# them on connect, which is a network download plus a local extract — fast.
# Copying an existing install across from NFS would cost hours at this mount's
# serial open rate, so a fresh install per host is the cheaper answer as well as
# the correct one (server binaries are host-specific anyway).
mkdir -p "$HOSTLOCAL_SERVERS/cursor-server" \
         "$HOSTLOCAL_SERVERS/vscode-server" \
         "$HOSTLOCAL_PYCACHE" 2>/dev/null || true
chmod 700 "$HOSTLOCAL_SERVERS" "$HOSTLOCAL_PYCACHE" 2>/dev/null || true

# Keep Python bytecode off NFS. The agent shell guards are Python and run on
# every shell call an agent makes; importing `guardlib` from NFS measured
# 4.43 s, which Cursor hit as a ~5 s delay before *every* command and which can
# exhaust a hook's failClosed budget. With the cache on local disk the same
# import is 0.83 s. This writes no source anywhere — the scripts stay the single
# copy in `.agent-rules/`, only their compiled form is local.
export PYTHONPYCACHEPREFIX="$HOSTLOCAL_PYCACHE"

# Python scans ~/.local/lib/python3.*/site-packages at every start -- 5,068
# files on NFS, measured 1.08 s against 0.01 s without it. Nothing on this host
# installs into user site; conda envs and system packages are unaffected.
export PYTHONNOUSERSITE=1

# Warm it, so the first guarded command of a session is not the one that pays.
# Backgrounded and silenced: this must never delay or fail a login.
if [ -d "$HOME/.agent-rules/scripts" ]; then
    ( /usr/bin/python3 -c "
import sys
sys.path.insert(0, '$HOME/.agent-rules/scripts')
from guardlib import destructive_git, destructive_rm, wait_loop, long_run  # noqa
" >/dev/null 2>&1 & ) 2>/dev/null
fi
