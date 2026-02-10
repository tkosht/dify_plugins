# Plugin B Review (Round 1)

- Date: 2026-02-09
- Target: `gpt5_agent_strategies.difypkg`
- Scope: `app/gpt5_agent_strategies`, `tests/gpt5_agent_strategies`
- Symptom: install dialog appears, but launch fails with `Multiple subclasses of AgentStrategy in strategies/gpt5_react.py`

## Findings (severity order)

1. Critical: `gpt5_react.py` module namespace exposes two `AgentStrategy` subclasses, matching daemon error exactly.
- Evidence:
  - `app/gpt5_agent_strategies/strategies/gpt5_react.py:2` imports `GPT5FunctionCallingStrategy` into module namespace.
  - `app/gpt5_agent_strategies/strategies/gpt5_react.py:17` defines `GPT5ReActStrategy(GPT5FunctionCallingStrategy)`.
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:125` defines `GPT5FunctionCallingStrategy(AgentStrategy)`.
  - Local reproduction (stubbed dependency import) showed exactly 2 subclasses in `gpt5_react` namespace:
    - `GPT5FunctionCallingStrategy`
    - `GPT5ReActStrategy`
- Impact:
  - plugin launch fails deterministically in loader expecting a single subclass per strategy script.
- Confidence:
  - High.

2. Medium: package and module metadata are not the failing layer.
- Evidence:
  - User-provided flow: install dialog opens, failure occurs at launch step.
  - Subagent Team B concluded failure is class-loader stage, not packaging decode stage.
- Impact:
  - Fix should focus on strategy script symbol exposure, not packaging format first.
- Confidence:
  - High.

3. Low: daemon-side loader lacks module-origin filter (`cls.__module__`) may be a systemic risk across plugins.
- Evidence:
  - Error is consistent with loaders scanning imported classes in target module namespace.
- Impact:
  - Other plugins with imported base strategy classes can hit same issue.
- Confidence:
  - Medium without daemon source/log confirmation.

## Recommended Fix (low-risk first)

1. Low-risk (plugin-local): avoid importing strategy class symbol directly in `gpt5_react.py`.
- Change idea:
  - Replace `from ...gpt5_function_calling import GPT5FunctionCallingStrategy, ...` style with module import.
  - Use module-qualified inheritance: `class GPT5ReActStrategy(gpt5_function_calling.GPT5FunctionCallingStrategy): ...`
- Expected effect:
  - Only `GPT5ReActStrategy` remains as top-level class in `gpt5_react` module namespace.

2. Medium-risk (platform): tighten daemon loader selection.
- Require `cls.__module__ == target_module` when resolving strategy class candidates.
- Apply only if plugin-local fix is insufficient or if platform-wide hardening is desired.

## Verification Steps

1. `pytest tests/gpt5_agent_strategies -q`
2. `dify plugin package app/gpt5_agent_strategies`
3. `dify plugin module list plugins/gpt5_agent_strategies.difypkg`
4. Install and launch in Dify UI; confirm `Multiple subclasses` no longer appears.

## Subagent Execution Records

- Spec: `docs/ai-agent-reviews/gpt5_strategy_launch_error_pipeline_spec_2026-02-09.json`
- Prompt: `docs/ai-agent-reviews/gpt5_strategy_launch_error_prompt_2026-02-09.txt`
- Run: `docs/ai-agent-reviews/gpt5_strategy_launch_error_pipeline_run_2026-02-09.json`
