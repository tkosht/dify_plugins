# AGENTS Branch Evaluation Task Catalog (2026-03-21)

## Goal
- Compare `main` and `docs/agent-instructions-simplify` under the same Codex practical tasks.
- Keep code/task conditions equal and vary only the repo-local instruction surface loaded from each branch.
- Upgrade the verdict from simple non-inferiority to strict superiority when evidence supports it.

## Branch Aliases
- `arm_alpha` -> `main`
- `arm_beta` -> `docs/agent-instructions-simplify`

## Stage 1 Matrix
- Repetitions: `r1` .. `r5`
- Tasks: `DEV-01`, `BUG-01`, `BUG-02`, `RES-01`, `REV-01`, `OPS-01`
- Total parent runs: `6 x 2 x 5 = 60`
- Branch order alternates by repetition to reduce start-order bias.

## Stage 2 Tie-Breaker
- Trigger only if stage 1 is `non_inferior: true` and `strictly_better: false`
- Tasks: `REL-01`, `REV-02`
- Total additional parent runs: `2 x 2 x 5 = 20`

## Primary Tasks

### DEV-01
- Type: implementation
- Scope:
  - `app/openai_gpt5_responses/models/llm/_position.yaml`
  - `app/openai_gpt5_responses/models/llm/gpt-5.3-codex.yaml`
  - `app/openai_gpt5_responses/models/llm/gpt-5.3-codex-spark.yaml`
  - `tests/openai_gpt5_responses/test_provider_schema.py`
- Goal: add a `gpt-5.3-codex-spark` predefined model entry with minimal schema/test updates.
- Package gate: `openai_gpt5_responses`

### BUG-01
- Type: implementation
- Scope:
  - `app/sharepoint_list/internal/validators.py`
  - `app/sharepoint_list/internal/request_builders.py`
  - `tests/sharepoint_list/test_validators.py`
  - `tests/sharepoint_list/test_operations_select.py`
- Goal: fix `select_fields` empty/blank edge handling so request builders never emit malformed `$expand`.
- Package gate: `sharepoint_list`

### BUG-02
- Type: implementation
- Scope:
  - `app/openai_gpt5_responses/internal/payloads.py`
  - `tests/openai_gpt5_responses/test_payloads.py`
  - `tests/openai_gpt5_responses/test_payloads_bool_coercion.py`
- Goal: close bool coercion and payload strictness gaps with minimal changes.
- Package gate: `openai_gpt5_responses`

### RES-01
- Type: read-only analysis
- Scope:
  - `app/sharepoint_list/internal/filters.py`
  - `app/sharepoint_list/internal/request_builders.py`
  - `app/sharepoint_list/internal/validators.py`
  - `tests/sharepoint_list/test_operations_filters.py`
  - `tests/sharepoint_list/test_validators_list_url.py`
- Goal: produce a severity-ranked reliability risk assessment for filters/select/list URL handling.

### REV-01
- Type: read-only review
- Scope:
  - synthetic uncommitted patch applied to:
    - `app/sharepoint_list/internal/request_builders.py`
    - `tests/sharepoint_list/test_operations_select.py`
- Goal: review the seeded regression diff and detect the three intended issues.
- Read-only compliance: the seeded baseline diff is allowed; only additional post-baseline mutations are treated as read-only violations.

### OPS-01
- Type: read-only currentness audit
- Scope:
  - `app/openai_gpt5_responses/README.md`
  - `app/openai_gpt5_responses/models/llm/*.yaml`
  - `app/openai_gpt5_responses/.env.example`
- Goal: verify currentness-related documentation/model catalog claims using official OpenAI sources only.

## Tie-Breaker Tasks

### REL-01
- Type: implementation
- Scope:
  - `app/openai_gpt5_responses/manifest.yaml`
  - `app/openai_gpt5_responses/provider/openai_gpt5.yaml`
  - `tests/openai_gpt5_responses/test_provider_schema.py`
- Goal: restore seeded packaging regressions and add targeted release-readiness coverage.
- Package gate: `openai_gpt5_responses`

### REV-02
- Type: read-only review
- Scope:
  - synthetic uncommitted patch applied to:
    - `app/openai_gpt5_responses/internal/payloads.py`
    - `tests/openai_gpt5_responses/test_payloads.py`
    - `tests/openai_gpt5_responses/test_payloads_bool_coercion.py`
- Goal: detect four intended payload strictness and test-weaken regression issues.
- Read-only compliance: the seeded baseline diff is allowed; only additional post-baseline mutations are treated as read-only violations.

## Active Gates
- Parent `codex exec` runs disable repo-configured `serena`, `codex_mcp`, `context7`, and `sequential-thinking` MCP servers with CLI config overrides. This keeps the evaluation focused on branch-local instructions instead of exec-incompatible interactive helpers.
- Parent and subagent runs execute with Codex `danger-full-access` because this host cannot initialize nested `bwrap` sandboxes for model-issued shell/edit actions. Read-only and write-scope compliance are enforced by post-run diff scoring.
- Implementation tasks:
  - `uv run ruff check ...`
  - `dify plugin package ...`
  - `dify signature sign ...`
  - `dify signature verify ...`
  - `uv run pytest -q --no-cov ...`
  - `uv run pytest -q ...` as reference-only gate
- Read-only tasks:
  - no file modifications allowed
  - output must stay within the declared schema or review format

## Verdict Rule
- `non_inferior`: existing guardrail based on hard fails, mean, task medians, active gates, and review recall
- `strictly_better`: `non_inferior == true`, no losses on `{mean_overall, package_pass_rate, one_pass_pass_rate, review_recall}`, and at least two strict wins across those metrics

## Subagent Confirmation
- Runs: `BUG-01`, `OPS-01`
- Branches: both aliases once each
- Tooling: `ai-agent-collaboration-exec` design + `codex-subagent` pipeline execution
- Total subagent runs: `2 x 2 = 4`
