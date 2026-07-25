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
  project. Events are `PreToolUse`, `PostToolUse`, `PreInvocation`,
  `PostInvocation`, `Stop`; the shell-command matcher is `run_command`.
  **Commands must be absolute paths** — a relative path resolves against the
  directory the session was launched from and fails with exit 127, silently
  bypassing the guard it was supposed to enforce.
