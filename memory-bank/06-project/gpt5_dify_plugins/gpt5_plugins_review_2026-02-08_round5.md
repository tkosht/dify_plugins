# GPT-5 Plugins Review Findings (2026-02-08, round5)

date: 2026-02-08
scope:
  - app/openai_gpt5_responses
  - tests/openai_gpt5_responses
  - app/gpt5_agent_strategies
  - tests/gpt5_agent_strategies
context:
  - 反映後リレビュー（round5）
  - prior_reports:
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round2.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round3.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round4.md
review_focus: bug/regression first
tags: review, gpt5, dify-plugin, openai-responses, agent-strategy, round5

## Problem
- Plugin A/B を反映後状態で再レビューし、残存不具合と回帰リスクを再判定する。

## Research
- 重点確認コード:
  - `app/openai_gpt5_responses/models/llm/llm.py`
  - `app/openai_gpt5_responses/internal/messages.py`
  - `app/openai_gpt5_responses/internal/payloads.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - `app/gpt5_agent_strategies/internal/flow.py`
  - `app/gpt5_agent_strategies/internal/tooling.py`
- 重点確認テスト:
  - `tests/openai_gpt5_responses/test_provider_runtime.py`
  - `tests/openai_gpt5_responses/test_llm_stream_flag.py`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py`
  - `tests/test_plugin_small_modules.py`
- 実行コマンド:
  - `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies tests/test_plugin_small_modules.py`
  - `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`

## Findings

### [P1/P2] 新規の機能不具合は検出なし
- Result:
  - 前回指摘の主要不具合（blocking `message=None`、`enable_stream` 判定不一致、non-string arguments、empty tool output）は解消状態を維持。
  - 今回の範囲では追加の P1/P2 機能不具合は確認できなかった。

### [P2] coverage gate は実行対象セット依存
- Location:
  - `pyproject.toml:154`
  - `tests/test_plugin_small_modules.py`
- Evidence:
  - `tests/openai_gpt5_responses tests/gpt5_agent_strategies` のみ: coverage 83.09% で fail。
  - `tests/test_plugin_small_modules.py` を含める: coverage 85.01% で pass。
- Impact:
  - プラグイン配下テストのみを実行する運用では gate 不達が再発しうる。

### [P2] image/blob tool response 変換経路の未完了実装が残存
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:566`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:585`
- Evidence:
  - `TODO: convert to agent invoke message` が残る。
  - tool invoke 内の画像/Blob 分岐は相対的にテスト薄い領域。
- Impact:
  - 画像/ファイル返却系 tool を本格運用する際に UI 表示/変換差異が残る可能性。

## Verification
- `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 87 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - テスト本体 pass
  - coverage fail (83.09% < 85%)
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies tests/test_plugin_small_modules.py`
  - 90 passed
  - coverage pass (85.01%)
- `uv run ruff check ...`
  - All checks passed

## Suggested Follow-up
1. CI/開発手順に `tests/test_plugin_small_modules.py` を常に含めることを明示する。
2. `gpt5_function_calling.py` の image/blob 分岐を TODO 解消までテスト拡充する。

