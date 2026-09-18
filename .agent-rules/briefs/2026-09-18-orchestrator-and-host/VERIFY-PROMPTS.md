# Copy-paste verification prompts (2026-09-18)

Use a **fresh** session on each harness, opened on
`/home/itec/emanuele` (coding-agent-config). Do not implement new policy.
Report pass/fail per check.

Host branch: `2026-09-18-orchestrator-and-host`.
PointStream edits are in `/home/itec/emanuele/pointstream` (that repo’s
own git).

---

## Antigravity (Gemini 3.8 Flash medium)

```
Verify host coding-agent-config + PointStream subagent routing from inside Antigravity. Do not change policy. Do not run cleanup_merged_worktrees.sh.

1. Read ~/.gemini/GEMINI.md (should import host AGENTS + harness/antigravity.md). Confirm the harness says children are Flash, there is no 3.8 Pro, and there is no “review every cheap diff” / review-fix instruction.

2. Read /home/itec/emanuele/.agent-rules/effort-models.json. antigravity low/medium/high must all be model flash (high may set effort high). No session_defaults key.

3. Confirm skill ~/.gemini/config/skills/model-routing/SKILL.md exists (symlink) and tells the parent to dispatch bounded children and escalate only on STUCK: out of ideas.

4. Confirm ~/.cursor is irrelevant here. Check ~/.gemini/config/agents or farmed stuck-escalation if present.

5. Read /home/itec/emanuele/pointstream/.agents/agents/budget-default.md and expert-retry.md. Expect Flash medium then Flash high, stuck phrase, not Flash low or pro.

6. Spawn a tiny invoke_subagent (read-only): Model flash, Workspace inherit, prompt: “Reply with the model/effort you believe you are, then STUCK: out of ideas. if you cannot read effort-models.json.” Confirm it runs as Flash, not Pro. Do not write files.

7. Confirm hooks: ~/.gemini/config/hooks.json still points at the host guard-model-family adapter if that file exists. Optional: a spawn with Model something off-family should deny or no-op; do not fight the product if the schema omits Model.

Report: GEMINI import ok Y/N; JSON map ok Y/N; PointStream profiles ok Y/N; live Flash child ok Y/N; anything that still says Pro / review-fix / Composer.
```

---

## Codex (Sol medium parent)

```
Verify host coding-agent-config + PointStream Codex profiles from inside Codex. Do not change policy. Do not force-delete worktrees.

1. Confirm $CODEX_HOME is /var/tmp/emanuele-codex (or print the actual value). Confirm $CODEX_HOME/AGENTS.md is a symlink to host AGENTS.md.

2. Read /home/itec/emanuele/.agent-rules/harness/codex.md Models section and .agent-rules/effort-models.json platforms.codex. Expect Luna extra-high for ordinary children, Astra low for high/stuck. Interactive Sol is UI, not a README table.

3. Confirm user skill ~/.agents/skills/model-routing/SKILL.md exists and uses STUCK: out of ideas. / stuck-escalation, not review-fix.

4. Read /home/itec/emanuele/pointstream/.codex/config.toml. Production: budget_default = gpt-5.6-luna with xhigh; expert_retry = gpt-5.6-astra with low. trial_a_* must still exist and stay unused for this check. balanced_retry / Terra must not be the production path.

5. If spawn_agent / multi_agent_v2 works: spawn budget_default with a one-line prompt “Name your model and reasoning effort, then stop.” Confirm Luna extra-high (or report the actual metadata). Do not spawn Astra unless the first child returns STUCK.

6. Optional: grep AGENTS.md for “one live session → one worktree → one branch”. Do not git checkout other branches if this tree is dirty.

Report: CODEX_HOME ok Y/N; JSON/harness ok Y/N; PointStream toml ok Y/N; live Luna child metadata; whether xhigh was accepted by the product (if the spawn failed on effort enum, quote the error — do not invent a new enum in this session).
```
