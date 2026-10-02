---
id: 2026-08-23-pointer-not-inline-host-rules
created: 2026-08-23
source_platform: cursor
source_project: /home/itec/emanuele/pointstream
axis: platform
status: applied
summary: Stop inlining host AGENTS.md into projects; point at the host file instead
suggested_action: change sync_agent_rules.py to stop writing the host-rules block; replace generated cursor-harness.mdc with a pointer; drop ~/CLAUDE.md from the farm; migrate remaining projects
verify_platforms: [cursor, claude]
---

# Pointers, not copies, for host rules

**TODO for coding-agent-config.** Pointstream is already on this layout
(2026-08-23). The shared machinery still does the old thing.

## What was rejected

`sync_agent_rules.py` copies `~/.agent-rules/AGENTS.md` into every project's
`AGENTS.md` as a `host-rules` block, and copies `harness/cursor.md` into
`.cursor/rules/cursor-harness.mdc`. An edit to the host file is stale in
every project until someone re-runs the script. That is a second source of
truth pretending not to be one.

## What to do instead

Host rules live in **one** file: `~/.agent-rules/AGENTS.md`.

| Surface | How it reaches the host file |
|---|---|
| Claude Code | `~/.claude/CLAUDE.md` `@`-imports it (already). **No `~/CLAUDE.md`.** |
| Cursor on this host's home dir | `~/AGENTS.md` symlink (already) |
| Cursor (or Claude) opened on a **project** | project `AGENTS.md` points at the host file (`@` import + Read instruction); Cursor also gets an `alwaysApply` `.mdc` that points at `AGENTS.md` and `harness/cursor.md` |
| Cloud agents | they cannot see this home directory — **accepted** for local GPU-server work; do not bring inlining back for them unless that requirement returns |

Pointstream's concrete files: `AGENTS.md` (pointer + `@` import),
`CLAUDE.md` (`@AGENTS.md` only), `.cursor/rules/host.mdc` (alwaysApply
pointer). No `tools/sync_agent_rules.py`, no generated `project-core.md`,
no copied harness.

## Remaining work in this repo

- [ ] `scripts/sync_agent_rules.py`: stop generating the `host-rules` block
      and `cursor-harness.mdc`. Either delete those targets or emit a
      pointer file instead of a copy.
- [ ] `scripts/install.py` / farm: do not create `~/CLAUDE.md`.
      `~/.claude/CLAUDE.md` is the only Claude user-level file.
- [ ] README "How host rules reach each agent": describe pointers as the
      mechanism; mark inlining as retired.
- [ ] Migrate presley, TIGAS, 4DGStudy, moq3dgs off the inlined block.
- [ ] `vendor-sync-agent-rules.sh`: stop requiring a host-block layout.

Do not re-introduce a copy "just for cloud" without an explicit decision.

---

## Status — 2026-08-31: still open, deliberately

Reviewed in the queue sweep and **kept in `open/`**. It is a migration ticket,
not a piece of knowledge: the design is already agreed and recorded, and what
remains is mechanical work across four repositories that does not belong inside
a queue-evaluation session.

State checked today:

- `~/CLAUDE.md` is absent — that box is effectively done.
- `scripts/sync_agent_rules.py` still generates the `host-rules` block and
  `cursor-harness.mdc`; both TODOs are still in its docstring.
- `moq3dgs` is already on the pointer layout. **`presley`, `TIGAS` and
  `4DGStudy` still inline the block.**
- The script is per-repository, so refreshing those three means running each
  project's own copy — there is no one command for it from here.

**New urgency, created today:** `AGENTS.md` was substantially rewritten in this
session (NFS section replaced, four rules added). The three inlined copies are
stale *as of now*, and stale in the exact way this candidate exists to prevent.
Whoever picks this up should treat refreshing or converting those three as the
first step, not the last.

One thing to settle before migrating rather than after: `sync_agent_rules.py`'s
docstring gives a real reason for the inlining — Copilot's and Cursor's cloud
agents run on machines that never see this home directory. `AGENTS.md` accepts
that gap for local GPU-server work, so the migration is consistent with the host
rules; it should just be an explicit decision in the commit, not a silent one.

---

## Resolution — 2026-08-31

**Applied.** Every box is closed.

- `scripts/sync_agent_rules.py` now emits a **pointer** in place of both copies:
  the `host-rules` block names and `@`-imports `~/.agent-rules/AGENTS.md`, and
  `cursor-harness.mdc` names the host rules plus `harness/cursor.md`. The block
  went from 154 lines of duplicated prose to 20 lines of pointer.
- `~/CLAUDE.md` does not exist and `install.py` does not create one.
- README: the inlining section is rewritten as retired, with the reason and the
  accepted cost stated where someone tempted to undo it will read them.
- presley, TIGAS and 4DGStudy migrated and merged. moq3dgs has no `AGENTS.md`,
  so there was nothing to migrate; pointstream was already on this layout.
- `vendor-sync-agent-rules.sh` needed no change: its guard checks that a
  project's `CLAUDE.md` imports `AGENTS.md` — the direction of the layout, not
  the presence of a host block — and that remains correct.

**What finally forced it.** The candidate argued from cleanliness: a copy is a
second source of truth pretending not to be one. That was right but easy to
defer for five weeks. What settled it was the copy failing in the way the
argument predicted — on 2026-08-31 a host `AGENTS.md` rewrite left presley,
TIGAS and 4DGStudy telling their agents *"never destroy work you have not
read"* while the host had replaced that with a policy giving agents autonomy
over anything revertible. Three projects were instructing their agents to
contradict the host, and the stale block read perfectly plausibly.

**The tradeoff was decided, not drifted into.** The copy existed for readers
that cannot see this home directory — Copilot's and Cursor's cloud agents, and
CI runners. They now get a path they cannot follow, which is a real loss.
`AGENTS.md` already accepts it ("Cloud agents on other machines will not see
it; accepted"), because these rules describe a shared GPU server that cloud
agents are not working on. Both the generator's docstring and the README now
say: do not bring a copy back "just for cloud" without changing that decision
in the host file first. That is the door this whole failure came through.
