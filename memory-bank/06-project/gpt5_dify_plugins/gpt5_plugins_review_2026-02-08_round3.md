# GPT-5 Plugins Review Findings (2026-02-08, round3)

date: 2026-02-08
scope:
  - app/openai_gpt5_responses
  - tests/openai_gpt5_responses
  - app/gpt5_agent_strategies
  - tests/gpt5_agent_strategies
context:
  - 前回反映後の再レビュー
  - prior_reports:
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round2.md
review_focus: bug/regression first
tags: review, gpt5, dify-plugin, openai-responses, agent-strategy, round3

## Problem
- 反映済みコードに対して Plugin A/B を再レビューし、残存不具合とテストギャップを記録する。

## Research
- 読み取り対象:
  - `app/openai_gpt5_responses/internal/payloads.py`
  - `app/openai_gpt5_responses/internal/messages.py`
  - `app/openai_gpt5_responses/models/llm/llm.py`
  - `app/gpt5_agent_strategies/internal/flow.py`
  - `app/gpt5_agent_strategies/internal/tooling.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - `tests/openai_gpt5_responses/test_llm_stream_flag.py`
  - `tests/openai_gpt5_responses/test_messages.py`
  - `tests/gpt5_agent_strategies/test_flow.py`
  - `tests/gpt5_agent_strategies/test_strategy_safety.py`
- 実行コマンド:
  - `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`

## Findings

### [P1] blocking 経路で `result.message is None` を未防御
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:358`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:376`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:383`
- Evidence:
  - `check_blocking_tool_calls()` は `message is None` を安全に扱う実装だが、その後に `result.message.content` を直接参照している。
- Impact:
  - providerから `LLMResult.message=None` が返る経路で `AttributeError` によりエージェント実行が停止する可能性。
- Required tests:
  - `LLMResult(message=None)` を用いた blocking 経路の異常系テスト。

### [P2] コア実行経路の回帰検知不足（coverage gate 未達）
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - `app/openai_gpt5_responses/models/llm/llm.py`
  - `pyproject.toml:154`
- Evidence:
  - `--no-cov` 実行では 61 passed。
  - 通常実行では `--cov-fail-under=85` に対し total 33.14% で失敗。
  - `gpt5_function_calling.py` の coverage は 0% のまま。
- Impact:
  - 主要な実行分岐（stream/blocking/tool invoke/error path）の回帰が検知されにくい。
- Required tests:
  - strategy本体と llm本体に対する実行経路テスト（正常・異常・境界）。

## Improvements Confirmed in this round
- `coerce_bool_strict` の `llm.py` 側利用により、`enable_stream` 判定不一致は解消。
- `messages.py` は空文字の tool output を `function_call_output` として保持。
- `flow.py` 追加により stream/blocking の `tool_calls` 抽出は `message=None` で安全化。
- `tooling.py` は non-string tool arguments を安全にエラー化。

## Verification
- `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`:
  - 結果: 61 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`:
  - 結果: テスト本体は通過
  - 失敗理由: coverage gate (`--cov-fail-under=85`) 未達、total 33.14%
- `uv run ruff check ...`:
  - 結果: All checks passed

## Suggested Follow-up
1. `gpt5_function_calling.py` の blocking 経路で `result.message` null-guard を追加。
2. strategy本体と llm本体を直接検証する回帰テストを追加して coverage を引き上げる。

## Resolution (2026-02-08)
- [Resolved][P1] blocking 経路の `result.message is None` 未防御
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
    - blocking 分岐で `result_message = result.message` を導入。
    - `result_message is not None` 条件下でのみ `content` 参照・text emit を実行する null-guard を追加。
  - テスト:
    - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py`
      - `test_invoke_blocking_result_message_none_is_safe`

- [Resolved][P2] コア実行経路の回帰検知不足（coverage gate 未達）
  - strategy 本体実行経路テストを追加:
    - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py`
      - blocking tool-not-found
      - parse_error fail-closed
      - max-iteration 到達分岐
      - streaming 応答分岐
      - prompt helper（system/image）
  - llm 本体実行経路テストを拡張:
    - `tests/openai_gpt5_responses/test_llm_stream_flag.py`
      - `_to_credential_kwargs`, `_safe_int`, `get_num_tokens`, `_normalize_parameters`
      - `_to_llm_result` の usage/tool_call 変換
      - `validate_credentials` 正常/異常
      - `_invoke` の `user`/`stop` 反映
  - メッセージ変換・provider runtime・small modules の回帰テストを追加:
    - `tests/openai_gpt5_responses/test_messages.py`
    - `tests/openai_gpt5_responses/test_provider_runtime.py`
    - `tests/test_plugin_small_modules.py`

## Post-fix Verification (2026-02-08)
- `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies tests/test_plugin_small_modules.py`
  - 結果: pass
- `uv run pytest --no-cov -q tests/openai_gpt5_responses tests/gpt5_agent_strategies tests/test_plugin_small_modules.py`
  - 結果: 90 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies tests/test_plugin_small_modules.py`
  - 結果: 90 passed
  - coverage: `85.01%`（`--cov-fail-under=85` 達成）
