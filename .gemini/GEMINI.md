# Antigravity IDE - Global Agent Constraints

@/home/itec/emanuele/.agent-rules/shared.md

## 1. Environment Guardrails & Permissions
* **Headless Screen Buffering:** If an operation or testing library fundamentally requires an active screen session to process visual content, prioritize configuring library backends to headless mode (e.g., `matplotlib.use('Agg')`). If a display is unavoidable, utilize `pyvirtualdisplay` or prepend the execution command with `xvfb-run -a`.

## 2. Dependency Management
* **Source of Truth:** Standard Python packages must be managed exclusively through `pyproject.toml`. Do not run raw `pip install` commands in the terminal.
* **GPU Environment:** The `environment.yaml` file is strictly reserved as a bootstrap configuration for heavy CUDA drivers, PyTorch binaries, and compiled wheels. Never generate or use a `requirements.txt` fallback file.

## 3. Agent Execution & Review Paradigm
* **Test-Driven Generation:** You must write a unit test or validation script *prior to* or *simultaneously with* implementing new core system algorithms.
* **Post-Task Analysis:** When a mission is completed, provide a clear structural critique regarding performance bottlenecks, structural issues, and code safety. 
* **The Review Boundary:** During the strict Review Phase, you are prohibited from making direct code changes or outputting code snippets. Frame your feedback purely as conceptual and structural architectural guidance.
* **Persistence Principle:** If a previous code modification is missing from the active workspace context, assume it was intentionally modified by the user. Do not attempt to automatically revert or overwrite it.

## 4. MCP Tool Orchestration & Constraints

### GitHub MCP Integration
* **Version Control Awareness:** You have active read/write permissions via the GitHub MCP server. Before generating massive structural refactors, query the active repository state, issues, or recent PR histories to ensure alignment with existing branches.
* **Commit Boundaries:** Do not push code directly to production or `main` branches via automation. Prepare modifications locally within the workspace structure or outline explicit branch/PR steps for manual execution.

### Sequential Thinking Loop Optimization
* **Gated Activation:** The `sequential_thinking` tool is active. Do not invoke this multi-step reasoning tool for simple code syntax fixes, basic docstring updates, or trivial linear scripting tasks.
* **Mandatory Use Cases:** You MUST invoke sequential thinking loops for:
  1. Designing cross-process shared memory abstractions (avoiding PCIe bottlenecks).
  2. Resolving intricate Level-of-Detail (LoD) state synchronization anomalies.
  3. Formulating mathematical definitions or geometric abstractions (like view frustum culling matrix operations).
* **Execution Boundary:** When running a sequential thinking chain, explicitly declare your core hypothesis, map a maximum of 5–7 analytical steps, and actively cross-examine edge cases (e.g., memory overhead, latency penalties) before drafting code blocks.