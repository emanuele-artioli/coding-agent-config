# Validation and rollout record

Recorded 2026-10-02. This distinguishes verified behavior from documentation,
file presence, and capabilities still gated.

## Implementation acceptance

45 standard-library tests pass on the Mac and gpu1 Linux (two platform/native
CLI-dependent tests skip on Linux), including real Seatbelt write denial,
installer preservation/conflicts/exact rollback, malformed native hook payloads,
recursive external symlink protection, dirty/untracked snapshots, evidence reuse
and invalidation, misleading production configurations, failed smoke and scale
confirmation, budget exhaustion, cancellation/checkpoint retention, native-session
recovery, project external-tool overrides, PointStream aliases and idempotent
publication. Native Codex `skills/list` verifies repository roots, nested paths,
worktrees and external skill aliases without inference.

The three skills pass the skill-creator package validator. Runtime dependencies
are Python 3.11+ and its standard library; PyYAML was used only in a disposable
validator environment. CI runs the same suite on Linux and Mac. A native catalog
integration test explicitly skips where the native CLI is unavailable.

The first Linux suite exposed inherited `CODEX_HOME` in installer test fixtures.
They now remove ambient harness-location overrides and explicitly test selected
locations. The test-generated server hook command was restored from managed
ownership after verifying it was the sole difference; a recovery copy was kept.
The original tracked server changes remain unchanged.

## Live infrastructure

| Surface | Observed result | Admission |
|---|---|---|
| Mac | Personal policy and three skills installed with rollback transactions; native catalog returns all three enabled | Attended local jobs; unattended jobs refused |
| gpu1 | Python 3.12.13, Codex 0.152.0, userspace bubblewrap; scoped reads/writes, symlink writes and double-fork daemon cleanup pass | Eligible Linux worker, with a fresh probe before each task |
| gpu2 / gpu3 / gpu5 | Existing compatible Python and native paths enrolled; initial file-isolation probes passed; gpu5 Codex was 0.156.1 | Wider activation remains conditional on current full admission checks |
| gpu4 | Administrative measurements lock still closes SSH | Not enrolled; no jobs started |
| gpu6 | Briefly reachable with compatible Python; connection closed during enrollment | Not activated; no automatic replay |

Mac Seatbelt file isolation does not establish process lifetime containment.
The kernel rejects `kqueue NOTE_TRACK` with errno 45. The runner therefore refuses
unattended Mac jobs rather than promising cancellation of daemonized descendants.
Linux admission checks actual double-fork/new-session cleanup inside its PID
namespace. Unknown or failed isolation prevents execution.

The original server home-directory checkout and its intentional uncommitted
retirement changes were preserved. Old tracked configuration is archived in the
normal local checkout, outside native discovery paths. Effective remote Codex
configuration is `/var/tmp/emanuele-codex`, not an assumed `~/.codex` path.
Install transactions preserve models/plugins and unrelated user settings.

A detached gpu1 command task survived the submission SSH connection and passed
status/collection checks. A native Codex task initially claimed success after
its Node tool host crashed; the independent file check caught the missing file.
The runner had incorrectly treated virtual address reservations as physical RAM.
After correcting that limit, resuming the same native session passed its file
check. Linux task memory is sampled aggregate descendant RSS; an optional virtual
address limit is a separate setting. This is not a hard cgroup memory guarantee.

The final scoped Linux probe also caught a mount-order error for readonly inputs
under `/tmp`. Readonly inputs now mount after fresh temporary filesystems, and
the namespace root is remounted readonly. Protected paths never implicitly grant
read access to unrelated host state. Outputs reside in durable storage separate
from host-local runtime; stopped tasks preserve recovery snapshots and session
JSONL while copied OAuth files are removed.

## Guidance comparison

`tests/benchmark.py` runs isolated fixtures sequentially on an enrolled host.
The initial cohort used nine explicit 60-second CPU-only budgets, one native
model default, independent checks and the existing subscription. It compared
native guidance, archived root plus Codex guidance (799 words), and slim guidance
(233 words). It did not activate unsafe legacy hooks. This is a guidance ablation,
not a complete comparison of every old harness feature.

| Fixture | Native | Legacy guidance | Slim guidance |
|---|---:|---:|---:|
| Median bug fix | Accepted, 50.59 s | Accepted, 34.82 s | Accepted, 35.95 s |
| Multi-file parsing | 60 s budget exhausted | 60 s budget exhausted | 60 s budget exhausted |
| Research CSV processing | 60 s budget exhausted | 60 s budget exhausted | 60 s budget exhausted |

The three bug-fix diffs were independently reviewed and passed edge-case checks.
The larger initial cases remain attention states. Their partial work was retained;
timeouts are not successes. A missing `python` alias caused avoidable retries,
so subsequent task context should state the actual interpreter rather than add
a global packaging rule. The multi-file prompt's whitespace requirement was
clarified in the benchmark driver for future cohorts; the initial comparison
cannot support quality conclusions about that ambiguity.

This sample establishes a 71% reduction in shared guidance words and working
recovery/admission behavior. It does not establish a speed or quality advantage.
Native usage totals for completed runs are in `benchmark-results.json`; timed-out
runs do not expose complete usage. Zero human code edits were made during the
cohort. Do not infer zero future interventions or a representative research
performance distribution from these fixtures.

A separate continuation of the slim multi-file task used the same native session
and an explicitly renewed 90-second budget. With the whitespace requirement and
host interpreter clarified, it passed the independent checks in another 36.86 s.
This validates recovery; it is not part of the initial timing comparison.

## Remaining verification gates

- Claude CLI is installed locally but subscription authentication reports absent;
  its actual memory/skill loading has not been inferred from file presence.
- Cursor editor is present, but the native Agent CLI is unavailable. The global
  user-rule artifact requires the documented UI setting or per-project rule.
- Antigravity CLI interface is verified; isolated auth/external-tool loading is
  not verified. Claude, Cursor and Antigravity worker sessions remain attended.
- Unattended GPU device passthrough is not verified and is refused. PointStream's
  project dispatcher and codec admission remain in place; no GPU production job
  or paid compute was used for this migration.
- Publication idempotence and failed checks are tested with controlled adapters;
  fixture repositories deliberately disable publication. The implementation PR
  validates real branch push and draft PR permissions separately.

After meaningful upgrades, run doctor and native loading probes, then calibrated
bug-fix, multi-file, project research and remote cohorts. Record accepted diffs,
interventions, total elapsed time, instruction volume and available usage. Review
new global rules with the human; do not automatically promote repeated incidents.
