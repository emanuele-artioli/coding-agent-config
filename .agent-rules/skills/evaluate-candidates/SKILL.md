---
name: evaluate-candidates
description: Process open knowledge candidates under .agent-rules/candidates/ — apply, discard, or defer; respect platform write-ownership and pending-verification. Use from a coding-agent-config session when SessionStart reports open candidates, or when the user asks to evaluate the queue.
---

# Evaluate candidates

Async apply/discard for the central queue. One skill walks both axes.

## Procedure

1. List `/home/itec/emanuele/.agent-rules/candidates/open/project/` and
   `.../open/platform/`.
2. For each candidate, read frontmatter + body. Decide: apply, discard, or defer.
3. **Apply — branch on `axis`:**
   - `project` → lift into foundation skills/agents/AGENTS notes and/or copy
     into targets from `projects.json`.
   - `platform` → harness / shared scripts / adapters. If the product is
     another platform’s **live** config or an unverified claim about that
     platform, do **not** mark done: set `status: needs_verification`, append
     a checklist item under
     `candidates/pending-verification/<platform>.md`, and only close what
     *this* platform can verify.
4. Move resolved files to `candidates/done/` with final `status` in
   frontmatter (`applied` / `discarded` / keep `needs_verification` if still
   waiting on another platform — or leave a stub in `open/` linked from
   pending-verification; prefer `done/` with `needs_verification` plus a
   pending-verification row that links the id).

## Write-ownership

- Shared SoT (`.agent-rules/` prose, skills, guardlib) — apply from any
  platform, but still file verification tickets when live hook wiring for
  other platforms is required.
- Never claim Claude/Antigravity/Codex behavior verified from a Cursor
  session.

## Afterward

Summarize applied / discarded / deferred / needs_verification. Suggest
`install.py` if symlink farm or MCP catalog should refresh.
