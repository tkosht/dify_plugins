# GPT-5 Plugin Timeout Configuration (2026-03-07)

date: 2026-03-07
scope:
  - app/openai_gpt5_responses
  - app/gpt5_agent_strategies
tags: dify-plugin, timeout, max-invocation-timeout, max-request-timeout, gpt5

## Problem
- `dify-plugin==0.7.1` の SDK default `MAX_INVOCATION_TIMEOUT=250` により、
  `invocation exited without response after 250 seconds` が発生しうる。
- 既存 plugin は `main.py` で `MAX_REQUEST_TIMEOUT=240` のみ明示しており、
  inner / outer timeout の調整余地が不足していた。

## Research
- SDK layer:
  - `dify_plugin.config.config.DifyPluginEnv`
  - `dify_plugin.plugin.Plugin`
  - `dify_plugin.core.runtime.Session.max_invocation_timeout`
- Repo layer:
  - `app/openai_gpt5_responses/main.py`
  - `app/openai_gpt5_responses/provider/openai_gpt5.py`
  - `app/openai_gpt5_responses/models/llm/llm.py`
  - `app/gpt5_agent_strategies/main.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`

## Solution
- `openai_gpt5_responses`
  - startup default:
    - `MAX_REQUEST_TIMEOUT=1200`
    - `MAX_INVOCATION_TIMEOUT=1200`
  - provider UI:
    - `request_timeout_seconds` default `600`
    - clamp `30..1200`
- `gpt5_agent_strategies`
  - startup default:
    - `MAX_REQUEST_TIMEOUT=1800`
    - `MAX_INVOCATION_TIMEOUT=1200`
  - Agent node UI:
    - `invocation_timeout_seconds` default `1200`
    - clamp `60..1800`
  - runtime:
    - `self.session.max_invocation_timeout` を per-invocation で上書き
- outer process timeout の per-run UI 化は未実施。
  - SDK serverless reader の connection lifetime であり、現状は startup env 管理が妥当。

## Verification
- `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - pass
- `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 166 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 166 passed
  - coverage 87.04%

## Notes
- `dify` CLI は実行環境に入っておらず、`dify plugin package` は未実施。
- `MAX_REQUEST_TIMEOUT` / `MAX_INVOCATION_TIMEOUT` は OS 環境変数で上書きできる。
