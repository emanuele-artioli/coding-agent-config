# Prompt — verify the host changes from the Antigravity VS Code extension on gpu5

Paste below the line, from an **Antigravity extension session in VS Code
connected to gpu5**, with one worktree open as the folder — never the parent.

---

On 2026-08-31 a Claude Code session changed things that affect every agent on
this host, and wrote an Antigravity adapter it could not run. **Nothing in
Part 2 has ever executed on this platform.** Treat every claim below as a
hypothesis you are testing.

There is a further complication the author did not know about: this host's
Antigravity config was written for the **desktop app**, and you are the
**VS Code extension**. Whether any of it still applies is the first thing to
find out, and it may invalidate the rest.

Read first: `/home/itec/emanuele/.agent-rules/AGENTS.md`,
`/home/itec/emanuele/.agent-rules/harness/` (whichever file matches this
platform), and `/home/itec/emanuele/.agent-rules/FINDINGS-nfs-editor-slowness.md`.

## Part 0 — which Antigravity is this, and does it read the old config? (do this first)

Everything else depends on the answer.

1. **Does the extension read `~/.gemini/config/hooks.json`?** That file exists
   and currently wires three hooks (`PreInvocation`, `Stop`, and a `PreToolUse`
   matcher on `run_command`). It was written for the desktop app. Determine
   whether the extension reads it, reads a different path, or has no hook
   mechanism at all. **If it has no hooks, say so plainly and stop Part 2** —
   that is the single most valuable finding this prompt can produce, because
   the host's whole safety story assumes every harness can be hooked.

2. **Which server backs the extension?** There are three candidate trees, all
   on the slow NFS mount:

   | path | inodes | last touched |
   |---|---:|---|
   | `~/.antigravity-ide-server` | 6,562 | 2026-08-27 |
   | `~/.antigravity-server` | 6,332 | 2026-05-11 |
   | `~/.vscode-server` | — | **already moved to local disk** |

   Report which one the extension actually uses. If it is one of the first two,
   it is still paying full NFS cost and should be relocated the same way (Part 1
   has the recipe). If the extension runs entirely inside the VS Code server,
   the work is already done and both `.antigravity-*` trees are dead weight
   worth deleting.

3. **Where does this platform's config live now** — hooks, rules, skills,
   subagents? `.agent-rules/harness/` and `.agent-rules/README.md` describe the
   desktop-app layout. If the extension differs, the routing table is wrong and
   correcting it is worth more than anything else here.

## Part 1 — the host's NFS behaviour

The diagnosis: one NFS server backs every home here and serves `open()` at
2.4–4.3 calls/second, while `stat()` on the same files runs at ~13,000/s and
local ext4 at 15,774/s. It is per-request round-trip latency, not throughput —
and **parallelism beats it**, measured at 1.7 opens/s serial against 23.3 at
`xargs -P 24`.

Report numbers, not impressions.

1. **Re-measure both rates**, since the originals were taken while a co-tenant's
   `grep` sat in `D` state for 13 hours:

       python3 -c "
       import time,subprocess
       fs=subprocess.run(['find','TIGAS','-type','f'],capture_output=True,text=True).stdout.split()[:100]
       t=time.time()
       for f in fs:
           try: open(f,'rb').read(1)
           except OSError: pass
       print(f'{len(fs)} serial opens in {time.time()-t:.1f}s')"

       find TIGAS -type f | head -100 | xargs -P 24 -I{} head -c1 {} > /dev/null

2. **Time your own startup**, from connect to a usable editor, and say what the
   project was and how many files it holds. Cursor reached usable in ~20 s after
   its server was moved to local disk; before the move it did not connect at
   all. If Antigravity is slow, the first suspect is its server tree from
   Part 0.2, not the project.

3. **If the extension's server is on NFS, relocate it.** The recipe that worked
   for Cursor, and its two traps:

   - Rename the tree aside rather than copying it — a same-filesystem rename is
     one metadata operation and instant, while copying 58,495 files off this
     mount would have taken about seven hours.
   - Symlink `~/.<name>-server` to a directory under `/var/tmp`, which is local
     ext4 here and whose age-based cleanup is commented out in
     `/usr/lib/tmpfiles.d/tmp.conf`, so it survives reboots.
   - Copy back only `data/` (settings, history, workspace storage) **and**
     `extensions/`. Forgetting `extensions/` is what made Cursor come up
     connected but with no language server, which reads exactly like a failure.
     Use `xargs -P 32` for the copy, not `cp -r`.
   - Watch for `cp -n` refusing to overwrite a manifest the editor just wrote
     empty. That happened, and left the extensions present on disk but invisible
     to the editor.

   Ask before deleting anything. `/local/users/<user>` is this host's per-user
   local scratch convention and would be better than `/var/tmp`, but only an
   admin can create it.

## Part 2 — the shell guard that has never run here

`.agent-rules/scripts/antigravity/before-shell.py` was written on 2026-08-31
from a Claude Code session. Its payload keys and its exit-status contract were
**inferred** from `antigravity/guard-model-family.py`, not observed. It is not
wired to anything. Until it is, it denies nothing.

It applies four shared policies from `guardlib/`, the same modules Claude and
Cursor use: irreversible git, `rm` against protected trees, hand-rolled wait
loops, and long-run advice.

Only attempt this if Part 0.1 found a hook mechanism. Then:

1. **Wire it** with an absolute path, invoked as `python3 <absolute-path>`.
   Relative paths exit 127 and silently bypass, which is worse than no guard.

2. **Confirm the contract.** The script assumes non-zero exit blocks and stderr
   carries the message. Verify that is true for this platform's shell hook, and
   correct the script if not.

3. **Check both directions.** A guard with false positives is worse than none —
   it teaches people to route around it.

   Must be **denied**: a force push; a force push with `--force-with-lease`;
   `git push --delete origin <branch>`; `git clean -fd`.

   Must be **allowed**, with no prompt: `git commit -m "a test commit"`;
   `git push -u origin <branch>`; `git merge --ff-only <branch>`;
   `git reset --hard HEAD~1`; `git branch -D <local-branch>`.

   And three cases that have already bitten, each reported separately:
   a commit whose **message** names a forbidden operation; a **heredoc** whose
   body quotes one as prose (this was a live false positive on 2026-08-31 —
   writing these prompts tripped the guard — now fixed in `guardlib/shell.py`);
   and that same heredoc followed by a **real** forbidden command on a later
   line, which must still be denied.

4. **Check the UI path too.** If the extension can run git through its own
   interface rather than a shell, find out whether that routes through the hook.
   A guard the built-in git UI bypasses is not a boundary, and `AGENTS.md`
   currently claims more than that.

5. The branch-discipline note is **advisory**: committing on `main` should print
   a line to stderr and still succeed. If this platform cannot surface hook
   stderr, say so — the same limitation already applies to the effort-tier nudge.

## Part 3 — rules delivery

`AGENTS.md` was rewritten and shortened, and two sections now carry
`<!-- scope: … -->` comments. Those are inert HTML comments. Antigravity reads
`AGENTS.md` natively and in full, so it should be **unaffected** and every rule
should still be present.

Confirm the file loads cleanly with no missing sections, and that the scope
comments change nothing. Also confirm this platform does not *additionally* load
`.claude/rules/*.md` or `~/.claude/rules/*.md`, which would deliver those two
sections twice.

## When you are done

Update `/home/itec/emanuele/.agent-rules/candidates/pending-verification/antigravity.md`
— tick only what you exercised, with a dated note on how, and leave the rest
unticked with a reason.

If Part 0 shows the extension has a different config layout from the desktop
app, that supersedes the checklist: **write down the real layout** in
`.agent-rules/harness/` and `README.md`. Stale routing information is worse than
none, because the next session will act on it.

Work on a branch and commit and push without asking. Anything that cannot be
undone — deleting commits already on origin, deleting server trees — leave for a
human and say what you would have done.
