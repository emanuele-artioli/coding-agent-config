# coding-agent-config

Shared infrastructure for running a **fleet of AI coding agents** across
multiple projects without reinventing the same tools, rules, and safety
guards on every platform.

This repo is the single source of truth (SoT) for host-wide agent
configuration used with:

| Platform | Status on this host |
|---|---|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | live (rules, skills, agents, hooks) |
| [Cursor](https://cursor.com) | live (rules via project harness, skills via Claude path, agents, hooks) |
| [Google Antigravity](https://antigravity.google) | live (rules, skills, workflows); hooks pending verification |
| GitHub Copilot CLI | skills/agents farmed; hooks unverified |
| OpenAI Codex | documented paths only — not installed here yet |

Deep layout, hook dialects, verification claims, and living architecture
diagrams live in **[`.agent-rules/README.md`](.agent-rules/README.md)**. This
root file is the public overview.

## The problem

Run more than one coding agent (or the same agent across more than one
research repo) and the same failures show up quickly:

- Each agent forgets your codebase between sessions.
- Sibling projects solve the same problems independently — test-design
  workflows, results summarizers, paper editors — because no agent knows the
  others exist, and platform-native tools do not travel across vendors.
- Agents know average software-engineering practice, not *yours*.
- Prose rules alone are not enforcement: agents forget constraints that are
  already in context, burn tokens reinventing wait-loops, and happily spawn
  the wrong model family for a subagent.

You *can* get work done without shared infrastructure the same way you can
write software without classes or version control — if you waste enough
man-hours and context tokens. This repo exists to keep that waste down.

## What this repo provides

Everything below is authored once under [`.agent-rules/`](.agent-rules/) and
distributed by symlink, `@`-import, or a generated project file — never by
hand-copied drift.

### 1. Host-wide rules (`AGENTS.md` + per-agent harness)

- **[`AGENTS.md`](.agent-rules/AGENTS.md)** — tool-agnostic prose every agent
  should obey (host constraints, git safety, research-test philosophy, long-job
  checkpointing, knowledge-loop habits). Also the register of mistakes that
  happened more than once.
- **[`harness/<agent>.md`](.agent-rules/harness/)** — platform mechanics only
  (tool names, backgrounding, where that agent keeps config). Keeps Claude's
  `Monitor` / `run_in_background` advice from being handed to Cursor, where
  those tools do not exist.

Delivery uses three mechanisms because no single one reaches every consumer:

1. **Import** — `~/.claude/CLAUDE.md` and `~/.gemini/GEMINI.md` `@`-import the
   SoT.
2. **Symlink** — `~/AGENTS.md`, `~/.gemini/AGENTS.md`, … point at the same
   bytes.
3. **Inlining** — `scripts/sync_agent_rules.py` maintains a `host-rules` block
   inside each *project's* `AGENTS.md`, so Copilot's cloud agent and Cursor
   cloud agents (machines that have never seen this home directory) still get
   the rules.

### 2. Global skills and subagents (skeleton + thin project wrappers)

Canonical tools under [`.agent-rules/skills/`](.agent-rules/skills/) and
[`.agent-rules/agents/`](.agent-rules/agents/), symlinked into each platform's
global folder:

| Kind | Name | Role |
|---|---|---|
| Skill | `test-design` | Propose behaviour / misuse / deliberately-untested cases before writing tests |
| Skill | `results-report` | Summarize or compare experiment runs under a project's results dir |
| Skill | `update-paper` | Fold findings into the manuscript + research log |
| Skill | `reviewer-response` | Close a reviewer checklist item end-to-end |
| Skill | `handoff` | Self-contained handoff doc for another agent/platform with zero shared memory |
| Skill | `end-of-session` | Close-out: surface knowledge, optional handoff, commit on invoke, ask before push |
| Skill | `evaluate-candidates` | Apply / discard / defer the central knowledge queue |
| Agent | `paper-editor` | Edit manuscripts via project marker conventions |
| Agent | `gpu-job-runner` | Run long GPU jobs and return a distilled summary |

Projects that need local metrics or paper paths keep a **thin wrapper**
(project-specific `description` + pointer at the global body). Edit the
generic procedure once; it updates everywhere the symlink farm reaches.

### 3. Shared hook policy (`guardlib`) + per-platform adapters

Hook *policy* is shared; hook *plumbing* cannot be — platforms disagree on
event names, payload shape, and denial contracts. Policy lives once in
[`scripts/guardlib/`](.agent-rules/scripts/guardlib/); thin adapters speak each
dialect:

| Guard | What it stops / advises |
|---|---|
| `wait_loop` | Hand-rolled `pgrep`/`sleep` poll loops that match themselves and hang forever |
| `destructive_rm` | Broad `rm -rf` of unrecoverable paths (per-project `.agent-guards.json`) |
| `long_run` | Advisory when a command looks like a multi-hour training entry point |
| `model_family` | Prefer omit/inherit so subagents stay on the platform's in-house models; soft effort-tier nudge via [`effort-models.json`](.agent-rules/effort-models.json) |

Cursor, Claude, and (adapters shipped) Antigravity each get their own wrapper.
Fail-open vs fail-closed is deliberate: advisory scripts are direct-executable;
denying guards run via `python3 <path>` so a missing file fails closed.

### 4. Crossed-axis knowledge loop

Platforms × projects are a **grid**, not a stack. Knowledge can surface on
either axis into [`.agent-rules/candidates/`](.agent-rules/candidates/):

- `open/project/` — other projects may want this
- `open/platform/` — other platforms may need this
- `pending-verification/` — live config / “works on X” claims owned by platform X
- `done/` — audit trail

`end-of-session` considers both axes; `evaluate-candidates` applies or discards
asynchronously from a session on this repo. Progressive context nudges
(Cursor / Claude hooks) suggest handoff before auto-compact — they never force
mid-task handoff.

### 5. Tiered rule delivery for large project `AGENTS.md` files

`AGENTS.md` stays the complete hand-edited source. Platforms that can defer
load do:

| Platform | Always-on | Deferred |
|---|---|---|
| Claude Code | `CLAUDE.md` → `@.claude/project-core.md` | `.claude/rules/*.md` via `paths:` |
| Copilot Chat | `.github/copilot-instructions.md` | `.github/instructions/*.instructions.md` via `applyTo:` |
| Cursor / Codex / Antigravity / Copilot cloud | full `AGENTS.md` | — (eager by design) |

Mark a section with `<!-- scope: src/**, tests/** -->` above its heading.
Eager platforms are byte-for-byte unaffected (HTML comments are inert).
Measured Claude startup shrinks on the order of hundreds of lines per project
(see the table in [`.agent-rules/README.md`](.agent-rules/README.md)).

### 6. Installer, sync, and living docs

```bash
python3 .agent-rules/scripts/install.py          # create/verify symlink farm + MCP upsert
python3 .agent-rules/scripts/install.py --check  # report only
python3 .agent-rules/scripts/sync_agent_rules.py # (vendored into each project) regenerate project rule files
python3 .agent-rules/scripts/render_architecture.py --check  # living mermaid diagrams stay fresh
```

`install.py` only links into agent directories that already exist, reports
conflicts instead of clobbering real files, and upserts shared MCP servers by
name without removing unrelated marketplace entries.

## Unusual shape of this repository

On the author's machine this git repo **is the home directory**, with an
allowlist [`.gitignore`](.gitignore): ignore everything, then un-ignore only
`.agent-rules/`, a few wrapper config files, and this README. That keeps
credentials and project checkouts out of git while still versioning the SoT
in place.

If you adapt the idea elsewhere, you do not need that layout — clone
`.agent-rules/` (or the whole repo) anywhere convenient, point `install.py`'s
`HOST`/`HOME` at your paths, and keep the same “edit once, symlink everywhere”
discipline.

## Who this is for

- People running **more than one** AI coding agent, or one agent across
  **more than one** project, who are tired of duplicated skills and drifting
  rules.
- Anyone who wants host rules to reach **cloud** agents (Copilot / Cursor
  cloud) that never see `~`.
- Research / multi-repo setups where the same paper, test, and results
  workflows should stay generic at the host and thin at the project.

## Learn more / contribute feedback

- Full design notes, tables, and verification status:
  [`.agent-rules/README.md`](.agent-rules/README.md)
- Knowledge-queue schema: [`.agent-rules/candidates/README.md`](.agent-rules/candidates/README.md)
- Enforceable-rules register: [`.agent-rules/enforceable-rules.md`](.agent-rules/enforceable-rules.md)

Issues and alternate designs welcome — this is still early infrastructure for
what a fleet of coding agents actually needs.
