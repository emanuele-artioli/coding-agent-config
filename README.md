# coding-agent-config

Small cross-project guidance, native harness adapters and bounded local/SSH
orchestration. Python 3.11+, no third-party runtime dependencies. Historical
server configuration is preserved under `archive/` and is inactive.

## Use

Run from a normal checkout with `python3 -m agentctl`, or install the package
with `python3 -m pip install .` in your chosen environment. Do not check this
branch out in the historical server home-directory repository.

```sh
agentctl doctor --probe
agentctl install --dry-run
agentctl install
agentctl install --project /absolute/project --harness claude --harness cursor
agentctl rollback TRANSACTION
agentctl enroll --host gpu1 --python /absolute/python3.11 --codex-home /actual/CODEX_HOME
agentctl doctor --host gpu1 --probe
agentctl run task.json --host gpu1
agentctl status TASK
agentctl logs TASK --lines 40
agentctl cancel TASK
agentctl collect TASK --destination /new/artifact/directory
agentctl handoff TASK
agentctl continue TASK --prompt "Continue the assigned work" --seconds 300
```

`run --attended` stays in the foreground on the executing host. It never
silently falls back from failed unattended containment. Mac jobs currently require
`--attended`: Seatbelt file isolation passes, but daemonized-process lifetime
containment is unverified. Linux unattended admission also tests daemon cleanup. Attended SSH work
requires a terminal on that host. Enrolling installs a new immutable package
release and updates local routing; it does not change the server Git checkout
or install native CLIs. `install --host HOST` defaults to Codex only; specify
other installed harnesses explicitly. `--retire-legacy` removes only known old
hook commands and symlink aliases, with recoverable backups.

The installer preserves unrelated settings and native model choices. It owns
only generated files/blocks and safety-key changes, records backups before
mutation, refuses subsequent user-edit conflicts, and supports exact rollback.
A Cursor global rule must be pasted into its User Rules UI or installed as a
managed per-project rule. Hooks require native loading/trust verification.

## Task contract

Copy an example from `examples/` and replace project-specific paths and checks.
A task has `kind` (`agent`, `command`, `compute`), a Git `repo`, named `revision`,
explicitly selected `changes`, `seconds`, and `resources` (`cpu_threads`,
`memory_mb`). GPU requests add `gpu_uuid` and `gpu_memory_mb`. Thread environment
limits apply everywhere; Linux workers also use CPU affinity. Memory limits
monitor aggregate process-tree RSS. An optional `address_space_mb` separately
limits virtual memory on Linux; it must accommodate runtime reservations.

Agent tasks name a native `harness`, `prompt`, and verification `checks` as
argv lists. An optional `model` is an explicit override; no automatic model or
provider fallback occurs. Remote coding tasks default to commit, branch push
and draft PR; `publish: false` is reserved for narrower project authority or
disposable acceptance fixtures. Merges and deployments are never automatic.

`read_only` adds protected data/evidence paths, relative to the isolated
checkout or absolute on the executing host. `read_paths` grants extra read
access for installed environments/tools. Machine policy is outside writable
worker directories; existing `.agent-guards.json` declarations add protection
and cannot weaken it. PointStream remote agent tasks are refused; command
adapters retain its fleet entrypoint.

Each task gets a fresh checkout and output directory. The source checkout,
including unselected changes and untracked files, stays untouched. Only explicit
individual files enter a dirty snapshot. A detached supervisor records checks,
logs, native session IDs, budgets and artifacts. Disconnection means inspect the
existing task; never replay it. Cancellation touches a supervisor request and
kills only its owned process group. Collection refuses existing destinations
and output symlinks, and preserves committed, dirty and untracked code.

Unattended commands require a successful scoped OS probe. Unattended Codex
requires saved subscription OAuth and a fresh isolated HOME with external apps,
plugins and MCP disabled. Other harnesses stay attended until an isolated
subscription/tool profile is verified. GPU device passthrough stays attended
until its isolation is verified. These are enforced admission restrictions,
not claims that every installed harness supports identical capabilities.

## Expensive compute

GPU production and multi-hour jobs use `kind: compute`. The task predeclares
metrics/targets, representative input, environment/hardware identity, a bounded
candidate set and smoke/pilot/confirmation/full stages. Each stage uses the
same declared production entrypoint and writes a metrics JSON file:

```json
{"valid": true, "metrics": {"quality": 0.95, "peak_memory_mb": 2200}, "cost": 12.4}
```

`cost` is a positive measured project-defined cost. Smoke checks output validity
and finite metrics; pilot candidates missing the target are excluded, and the
cheapest eligible configuration advances. Missing/nonfinite metrics, failed
commands, exhausted budgets or failed confirmation prevent the full run.
Full output must meet the declared targets too. A justified confirmation waiver
must be explicit. Project adapters determine scientific validity; the generic
runner cannot infer whether a sample is representative from its filename.

Record relevant input/environment manifests in `fingerprint_files`. The runner
hashes these and actual code, records executable/environment/hardware identity,
and rejects changes between stages. `reuse_evidence: TASK` reuses supervisor-owned
preflight only when that fingerprint matches. All stages keep the same production
arguments and selected parameters. `scale_arguments` can declare justified
input/size/duration differences, with a stated basis for extrapolation. Completed output is preserved.
PointStream retains its own richer scientific protocol and dispatcher.

## Maintenance and validation

```sh
python3 -m unittest discover -s tests -v
```

OS isolation tests need an environment allowed to create namespaces or apply
Seatbelt; a nested parent sandbox may prevent this. Failed probes deny dispatch.
Outputs live in durable storage beside the state directory; host-local scratch,
sockets and native databases stay in `/var/tmp`. Each stopped task retains a
separate recovery snapshot with Git state, logs and native session JSONL files.
Copied OAuth credentials are removed rather than archived.

See `docs/audit.md`, `docs/compatibility.md` and `docs/validation.md` for the
migration ledger, primary documentation, measured checks and remaining gaps.
Keep guidance only when evidence shows it helps. Review after substantial
harness/model upgrades; propose new global rules for human review.

For a native skill-discovery check without inference, use
`agentctl doctor --catalog --project /absolute/project/path` (or `--host gpu1`).
This queries Codex `skills/list`, including enabled state and discovery scope;
it does not infer instruction loading from file presence.
