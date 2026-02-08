# GPT-5 Plugins Review Findings (2026-02-08, round7)

date: 2026-02-08
scope:
  - app/openai_gpt5_responses
  - tests/openai_gpt5_responses
  - app/gpt5_agent_strategies
  - tests/gpt5_agent_strategies
context:
  - 反映後リレビュー（round7）
  - prior_reports:
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round2.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round3.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round4.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round5.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round6.md
review_focus: security/bug/regression first
tags: review, gpt5, dify-plugin, openai-responses, agent-strategy, round7

## Problem
- Plugin A/B に対して、前回指摘反映後の再レビューを実施し、残存リスクを再判定する。

## Research
- 重点確認コード:
  - `app/openai_gpt5_responses/models/llm/llm.py`
  - `app/openai_gpt5_responses/internal/messages.py`
  - `app/openai_gpt5_responses/internal/payloads.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
- 重点確認テスト:
  - `tests/openai_gpt5_responses/*`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py`
  - `tests/gpt5_agent_strategies/test_strategy_safety.py`
- 実行コマンド:
  - `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 再現確認スクリプト（tool invoke 例外文字列のユーザー出力確認）

## Findings

### [P2] tool invoke 例外の内部詳細がユーザー文面へ露出しうる
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:601`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:602`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:669`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:671`
- Evidence:
  - tool 呼び出し例外時、`tool_result = f"tool invoke error: {e!s}"` で例外文字列を保持。
  - `maximum_iterations == 1` の経路では `create_text_message(str(resp["tool_response"]))` でそのままユーザーへ返却。
  - 再現確認で `RuntimeError("internal error path=/srv/secret")` を発生させると、ユーザー向けテキストに `tool invoke error: internal error path=/srv/secret` が出力されることを確認。
- Impact:
  - ツール実装由来の内部パス・内部エラー情報が対話出力に漏れる可能性。

### [Info] round6 指摘のP1/P2は修正維持
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:547`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:555`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:851`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:858`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:676`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:683`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:699`
- Evidence:
  - `/files` 配下判定に `realpath/commonpath` が導入され、traversal拒否テストが追加。
  - ファイルサイズ上限チェックが導入され、oversize拒否テストが追加。
  - blob変換失敗時は固定文言（内部詳細マスク）テストが追加。

### [Info] Plugin A 側で新規の重大不具合は未検出
- Result:
  - bool coercion / stream判定 / tool argument整形 / schema検証の主要経路は既存テストと実装の整合を確認。
  - 今回範囲で追加の P1/P2 は確認できなかった。

## Verification
- `uv run ruff check ...`
  - All checks passed
- `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 96 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 96 passed / coverage 87.96%（gate達成）
- 再現確認スクリプト
  - 例外発生時に `tool invoke error: internal error path=/srv/secret` が対話テキストに現れることを確認。

## Suggested Follow-up
1. tool invoke 例外のユーザー向け文言を固定化し、詳細は `logger.exception` 側へ退避する。
2. `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py` に、`tool invoke error` のマスキングを担保する回帰テストを追加する。

## Resolution (2026-02-08)
- [Resolved][P2] tool invoke 例外詳細のユーザー露出
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
    - tool invoke 例外時の `tool_result` を固定文言
      `"tool invoke error: failed to execute tool"` へ変更。
    - 例外詳細は `logger.exception("Tool invoke failed: tool=%s", tool_call_name)`
      でログへ退避し、ユーザー文面には含めない。

- [Resolved][P2] 回帰テスト追加
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py`
    - `test_invoke_tool_exception_masks_internal_details` を追加。
    - `RuntimeError("internal error path=/srv/secret")` を発生させても
      ユーザー向け text に内部文字列が出ないことを検証。

## Post-fix Verification (2026-02-08)
- `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: pass
- `uv run pytest --no-cov -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: 96 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: 96 passed
  - coverage: `87.96%`（`--cov-fail-under=85` 達成）
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies tests/test_plugin_small_modules.py`
  - 結果: 99 passed
  - coverage: `87.96%`
