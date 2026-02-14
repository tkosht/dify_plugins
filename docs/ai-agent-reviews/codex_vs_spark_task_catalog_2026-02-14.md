# Codex vs Spark Task Catalog (2026-02-14)

## Purpose
- Evaluate whether `gpt-5.3-codex-spark` can substitute `gpt-5.3-codex` for day-to-day engineering and investigation tasks.
- Keep all conditions equal except `--model`.

## Global Constraints
- Workspace: `/home/devuser/workspace`
- Subagent wrapper: `.claude/skills/codex-subagent/scripts/codex_exec.py`
- Output format: JSON only (each task has a fixed schema)
- Evidence policy: every claim must include file paths from the allowed scope
- Timeout: 240 seconds per run
- Sandbox: `read-only`

## Task Set (6 tasks)

### DEV-01 (Development)
- Project: `app/openai_gpt5_responses`
- Goal: propose minimal code changes to add `gpt-5.3-codex-spark` model entry with schema/test updates.
- Allowed scope:
  - `app/openai_gpt5_responses/models/llm/_position.yaml`
  - `app/openai_gpt5_responses/models/llm/gpt-5.3-codex.yaml`
  - `tests/openai_gpt5_responses/test_provider_schema.py`

### DEV-02 (Development)
- Project: `app/gpt5_agent_strategies`
- Goal: propose consistency updates between strategy YAML metadata and schema tests.
- Allowed scope:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.yaml`
  - `app/gpt5_agent_strategies/strategies/gpt5_react.yaml`
  - `tests/gpt5_agent_strategies/test_strategy_schema.py`

### BUG-01 (Bugfix)
- Project: `app/sharepoint_list`
- Goal: identify likely mismatch around select/validation behavior and propose minimal fix steps.
- Allowed scope:
  - `app/sharepoint_list/internal/validators.py`
  - `app/sharepoint_list/internal/request_builders.py`
  - `tests/sharepoint_list/test_validators.py`
  - `tests/sharepoint_list/test_operations_select.py`

### BUG-02 (Bugfix)
- Project: `app/openai_gpt5_responses`
- Goal: identify bool coercion / payload strictness gaps and propose minimal patch plan.
- Allowed scope:
  - `app/openai_gpt5_responses/internal/payloads.py`
  - `tests/openai_gpt5_responses/test_payloads.py`
  - `tests/openai_gpt5_responses/test_payloads_bool_coercion.py`

### RES-01 (Research)
- Project: `app/sharepoint_list`
- Goal: produce reliability risk assessment for filters/select/list URL handling.
- Allowed scope:
  - `app/sharepoint_list/internal/filters.py`
  - `app/sharepoint_list/internal/request_builders.py`
  - `app/sharepoint_list/internal/validators.py`
  - `tests/sharepoint_list/test_operations_filters.py`
  - `tests/sharepoint_list/test_validators_list_url.py`

### RES-02 (Research)
- Project: `app/gpt5_agent_strategies`
- Goal: produce safety-oriented strategy comparison and operational recommendations.
- Allowed scope:
  - `app/gpt5_agent_strategies/internal/policy.py`
  - `app/gpt5_agent_strategies/internal/flow.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - `tests/gpt5_agent_strategies/test_strategy_safety.py`

## Execution Matrix Summary
- Models: `gpt-5.3-codex`, `gpt-5.3-codex-spark`
- Repetitions: 3 per task/model
- Total runs: `6 tasks x 2 models x 3 repetitions = 36`
