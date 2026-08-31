# Prompt — verify the host changes from a Cursor session on gpu5

Paste below the line, from a **Cursor session connected to gpu5** with one
worktree open as the folder (`pointstream` or `TIGAS`) — never the parent.

---

On 2026-08-31 a Claude Code session changed things that affect every agent on
this host. Some was verified from Claude; some was written *for* Cursor and has
never been run here. **You are the only session that can close the Cursor half.**

Do not mark anything verified that you did not observe. A "this works on Cursor"
claim written from another platform is precisely the failure mode
`.agent-rules/AGENTS.md` warns about, and two rows in the queue exist because of
it.

Read first: `/home/itec/emanuele/.agent-rules/AGENTS.md` and
`/home/itec/emanuele/.agent-rules/FINDINGS-nfs-editor-slowness.md`.

## Part 1 — is the host actually fast for you now?

The diagnosis: this host's NFS server serves `open()` at 2.4–4.3 calls/second
while `stat()` on the same files runs at ~13,000/s and local ext4 at 15,774/s.
It is per-request round-trip latency, not throughput. The fix was to move the
editor servers to local disk — `~/.cursor-server` is now a symlink into
`/var/tmp/emanuele-editor-servers/`.

Report numbers, not impressions.

1. **Connect time.** In the newest directory under
   `/var/tmp/emanuele-editor-servers/cursor-server/data/logs/`, read
   `remoteagent.log` and report the gap between "Extension host agent started"
   and the last extension activation. It was ~20 s on 2026-08-31. If it is
   minutes now, say so and attach the log.

2. **Are the extensions really installed?** Six should be:
   `ms-python.python`, `anysphere.cursorpyright`, `ms-python.debugpy`,
   `anthropic.claude-code`, `github.vscode-github-actions`,
   `iamhyc.overleaf-workshop`. Check the files on disk **and** what Cursor's UI
   shows. Those disagreed once already: an empty `extensions.json` manifest
   survived beside a fully populated directory, so the editor believed nothing
   was installed.

3. **Does indexing finish, and when?** PointStream is ~1,500 files outside
   `.git` since its `.mypy_cache` was moved out; at the serial open rate that is
   roughly 7 minutes. Report what you actually see.

4. **Re-measure the mount.** The original figures were taken while a co-tenant's
   `grep` had been in `D` state for 13 hours, which is not a measurement of the
   server at rest. Run the serial and parallel versions and report both:

       python3 -c "
       import time,subprocess
       fs=subprocess.run(['find','TIGAS','-type','f'],capture_output=True,text=True).stdout.split()[:100]
       t=time.time()
       for f in fs:
           try: open(f,'rb').read(1)
           except OSError: pass
       print(f'{len(fs)} serial opens in {time.time()-t:.1f}s')"

       find TIGAS -type f | head -100 | xargs -P 24 -I{} head -c1 {} > /dev/null

   Serial was 1.7–4.3/s, parallel 23.3/s — a 14× gap that is the basis of a rule
   in `AGENTS.md`. If parallel is no longer faster, that rule needs revisiting
   and you should say so.

Also note whether anyone else is loading the mount
(`ps -eo user,pid,etime,stat,comm | awk '$4 ~ /D/'`). **Do not kill another
user's process.**

## Part 2 — the new git guard, already wired for you

`~/.cursor/hooks.json` already routes `beforeShellExecution` to
`cursor/before-shell.py`, and that script gained `guardlib/destructive_git.py`
on 2026-08-31. Cursor may need to reload `hooks.json` first.

The rule is **recoverability, not danger**: everything you can undo runs with no
prompt, and only the unrecoverable set is denied. Check both directions — a
guard with false positives is worse than no guard, because it teaches people to
route around it.

Must be **denied**, each with a readable reason: a force push; a force push with
`--force-with-lease`; `git push --delete origin <branch>`; `git clean -fd`.

Must be **allowed**, with no prompt: `git commit -m "a test commit"`;
`git push -u origin <branch>`; `git merge --ff-only <branch>`;
`git reset --hard HEAD~1`; `git branch -D <local-branch>`.

Then three cases that have already caused trouble, each worth reporting
separately:

- A commit whose **message text** names a forbidden operation — e.g. committing
  with a message that mentions forcing a push. The words must not trigger the
  guard.
- A **heredoc** whose body contains such a command as prose (writing a document
  that quotes it). This was a real false positive on 2026-08-31 — writing these
  very prompts tripped the guard — and is now fixed by
  `guardlib/shell.py`. Confirm the fix holds on Cursor.
- The same heredoc followed by a **real** forbidden command on a later line.
  That must still be denied; if it is not, the fix went too far.

**The open question this prompt mainly exists for:** does Cursor's built-in
**source-control panel** route through `beforeShellExecution` at all? Try a
force push from the UI rather than the terminal. If the panel bypasses the hook,
the guard is a boundary for agent shell commands only, and `AGENTS.md` currently
overstates it. Say so plainly — that is a useful finding, not a failure.

Finally, confirm the advisory: on a `main`/`master` checkout, a `git commit`
should print a branch-discipline line to stderr (visible in Cursor's Hooks
output channel) and still **succeed**. It is a note, never a block.

## Part 3 — rules delivery

`AGENTS.md` was rewritten and shortened, and two sections now carry
`<!-- scope: … -->` comments. Those are inert HTML comments; Cursor reads the
root `AGENTS.md` whole and should be **unaffected**.

Confirm: (a) the scope comments change no rule and render as nothing;
(b) Cursor does **not** additionally load `.claude/rules/*.md`, which would
deliver those two sections twice. Ask yourself to quote a rule from the
research-code-tests section and see whether you cite one source or two. That is
the real regression risk here and is already an open row in
`candidates/pending-verification/cursor.md`.

## When you are done

Tick only the rows you actually exercised in
`/home/itec/emanuele/.agent-rules/candidates/pending-verification/cursor.md`,
each with a dated one-line note on *how*. Leave the rest unticked with a reason.
If a claim in `AGENTS.md` turns out wrong on this platform, correct it — a wrong
rule that every session loads costs more than a missing one.

Work on a branch and commit and push without asking; the git rule above says
what is off-limits.
