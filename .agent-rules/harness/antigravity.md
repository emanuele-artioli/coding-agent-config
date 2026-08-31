# Antigravity / Gemini harness rules

Antigravity-specific mechanics. Imported by `~/.gemini/GEMINI.md` alongside
the tool-agnostic host rules in `../AGENTS.md`. Antigravity reads both
`AGENTS.md` and `GEMINI.md` and lets `GEMINI.md` win on conflicts, so this
file is also the place for any deliberate override of a host-wide rule.

## Agent execution & review paradigm

- **Post-task analysis:** when a mission completes, give a structural critique
  covering performance bottlenecks, structural issues, and code safety.
- **The review boundary:** during a strict Review Phase, do not make direct
  code changes or output code snippets. Frame feedback as conceptual and
  structural architectural guidance.

## MCP tool orchestration

### GitHub MCP

Active read/write permissions via the GitHub MCP server. Before generating a
large structural refactor, query the repository state, issues, or recent PR
history so the work aligns with branches that already exist.

### Sequential thinking loop

- **Gated activation:** do not invoke `sequential_thinking` for simple syntax
  fixes, docstring updates, or trivial linear scripting.
- **Mandatory use cases:**
  1. Designing cross-process shared-memory abstractions (avoiding PCIe
     bottlenecks).
  2. Resolving intricate Level-of-Detail state-synchronization anomalies.
  3. Formulating mathematical definitions or geometric abstractions (view
     frustum culling matrix operations and the like).
- **Execution boundary:** when running a chain, state the core hypothesis,
  map at most 5–7 analytical steps, and cross-examine edge cases (memory
  overhead, latency penalties) before drafting code.

## Model family and effort tier (subagent spawns only)

Before spawning subagent work, assess the effort its task needs
(low/medium/high) and check `../effort-models.json` for the mapped model —
today all three Antigravity tiers map to the same Gemini Flash 3.6 model, so
in practice this collapses to "prefer omitting an explicit model" so it
inherits the parent session (Gemini in-house). Do not pin versioned slugs —
they go stale. If you must pass a model, use only the Gemini family. This
never applies to your own top-level session model, which the user picks
freely.

Do not follow multi-family skill defaults from other platforms. If Gemini is
clearly struggling, ask the user; prefer switching platform/session over
silently crossing family. Live deny wiring (hard, family mismatch only):
`../scripts/antigravity/guard-model-family.py` (absolute path). The same
script logs (never blocks) an effort-tier nudge to stderr when a model is
in-family but off the tier table — no confirmed "ask"-style prompt exists on
this platform yet. See `../candidates/pending-verification/antigravity.md`.

## Where Antigravity's own config lives

- Prose: `~/.gemini/GEMINI.md` (this file's importer) and `~/.gemini/AGENTS.md`
  (a symlink to `../AGENTS.md`, read natively since v1.20.3). Per project, the
  root `AGENTS.md` is read directly — no generated per-project copy is needed
  any more.
- Skills: `~/.gemini/config/skills/<name>/` globally, `.agents/skills/<name>/`
  per project. The per-project path is the same directory Cursor, Codex and
  Copilot read, so one real directory serves all of them.
- Workflows (slash prompts): `~/.gemini/config/global_workflows/<name>.md`
  globally (linked from `../workflows/` by `install.py`), `.agents/workflows/`
  per project. Cursor's `.cursor/commands` is a symlink onto the project
  workflows directory so both agents share one tree.
- MCP: `~/.gemini/config/mcp_config.json` globally, `.agents/mcp_config.json`
  per project. Shared servers come from `../mcp/catalog.json` via `install.py`
  (remote entries use `serverUrl`). Unrelated entries are left alone.
- Hooks: `~/.gemini/config/hooks.json` globally, `.agents/hooks.json` per
  project. Structure is a map of named hook objects (e.g. `{"shell-guard": {"PreToolUse": [{"matcher": "run_command", "hooks": [{"command": "..."}]}]}}`).
  Events are `PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`, `Stop`.
  Handlers receive JSON on stdin and return JSON verdicts on stdout (e.g. `{"decision": "deny"|"allow", "reason": "..."}`
  for `PreToolUse`, `{"injectSteps": [...]}` for `PreInvocation`, `{"decision": "stop"|"continue"}` for `Stop`).
  **Commands must be absolute paths** (`python3 <abs-path>`).
- Server execution: The VS Code extension runs inside `~/.vscode-server`
  (relocated to local ext4 at `/var/tmp/emanuele-editor-servers/vscode-server`)
  and launches `/home/itec/emanuele/.gemini/bin/agy`. Legacy standalone trees
  `~/.antigravity-ide-server` and `~/.antigravity-server` are unused.

## Knowledge loop (Antigravity)

- Shared queue and skills: `../candidates/`, `../skills/` (`end-of-session`,
  `evaluate-candidates`, `handoff`), linked under `~/.gemini/config/skills/`.
- `end-of-session`: commit on invoke, ask before push; optional handoff step.
