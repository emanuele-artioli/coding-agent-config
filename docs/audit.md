# Migration ledger

Audit: 2026-09-30; implementation verification: 2026-10-01.

| Existing component | Decision | Replacement / reason |
|---|---|---|
| Global preservation, honest checks, risk-sensitive review | Simplify | Compact personal policy |
| Senior/junior prompts, fixed model/effort map, mandatory delegation | Retire | Native harness behavior; optional explicit model selection |
| Stub-first implementation and repeated parent checks | Retire | Relevant project checks and implementation review |
| Suppression of diff review | Retire | Risk-sensitive change review |
| Global Python packaging and mandatory worktree rules | Relocate / retire | Project toolchain; independent remote checkouts |
| Paper markers, scientific null controls and evidence protocols | Relocate | Existing research projects retain authority |
| Host GPU/NFS/import-order facts | Relocate | Machine profiles and project environment documentation |
| Shell-only deletion and Git guards | Replace | Canonical path guard plus OS isolation and recoverable snapshots |
| Long-run checkpoint/detachment reminders | Simplify | Supervisor ownership and compute preflight skill |
| 1,744-line installer | Replace | Managed rendering, backups, conflict detection and rollback |
| Closeout receipts and automatic “twice means global rule” | Retire | Factual handoff; human review of proposed guidance |
| Candidate history and old tests/configuration | Archive | Inactive `archive/server-config-2026-09` |
| PointStream codec pilot/confirmation and fleet dispatcher | Retain | Project adapter; no replacement scientific protocol |

## Concrete findings

The original Git checkout is rooted at `/home/itec/emanuele` and has intentional
uncommitted deactivation changes. It must not be migrated by moving, resetting,
cleaning or checking out the new branch in that home directory. The replacement
is developed in a normal Mac checkout; Git history and archived sources preserve
the original implementation.

gpu1's effective Codex home is `/var/tmp/emanuele-codex`, not `~/.codex`. The old
configuration set `approval_policy = "never"` and `sandbox_mode = "danger-full-access"`.
The new installer backs up this file and changes only the root safety keys.
Model choices, plugins and project settings are preserved.

Home storage is shared over NFS. Locks, workspaces and process supervision are
host-local; durable JSON records are written atomically on shared storage.
Installer ownership is host-specific. No runtime SQLite database lives on NFS.

The old removal guard allowed absolute paths and deletion inside saved-run
directories; the Git guard missed `reset --hard`. The replacement tests cover
those cases, symlinks, native file operations, interpreter writes and malformed
hook payloads. Hooks remain fallible; OS isolation is the admission boundary.

PointStream's instruction already requires smoke tests; its codec runner enforces
pilot/confirmation stages. Its generic dispatcher does not establish the same
cross-project gate. Preserve the project dispatcher and prohibit remote agent
sessions for repositories named PointStream, case-insensitively.

## Documented versus verified

The compatibility document links official mechanisms. `doctor` verifies installed
CLI flags and paths, not instruction loading or backend model availability.
File presence is never reported as proof that a harness loaded a rule or skill.
Native smoke sessions and infrastructure probes are recorded separately in
`validation.md`.

Review after substantial harness/model upgrades and recurring incidents. Do not
turn every failure into a new global prompt rule. The active package is separate
from the historical archive; archive line count is not active context volume.
