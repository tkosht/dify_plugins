# GPT-5 Plugins Review Findings (2026-02-08, round4)

date: 2026-02-08
scope:
  - app/openai_gpt5_responses
  - tests/openai_gpt5_responses
  - app/gpt5_agent_strategies
  - tests/gpt5_agent_strategies
context:
  - 前回指摘反映後の再レビュー（round4）
  - prior_reports:
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round2.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round3.md
review_focus: bug/regression first
tags: review, gpt5, dify-plugin, openai-responses, agent-strategy, round4

## Problem
- Plugin A/B に対する反映後レビューを再実施し、重大不具合の残存有無と残余リスクを確認する。

## Research
- 読み取り対象（主要）:
  - `app/openai_gpt5_responses/internal/payloads.py`
  - `app/openai_gpt5_responses/internal/messages.py`
  - `app/openai_gpt5_responses/models/llm/llm.py`
  - `app/gpt5_agent_strategies/internal/tooling.py`
  - `app/gpt5_agent_strategies/internal/flow.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
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

### [P1/P2] 新規の重大不具合は検出なし
- Result:
  - 前回までの主要指摘（blocking `message=None`、`enable_stream` 判定不一致、non-string tool arguments、empty tool output欠落）は解消を確認。
  - 今回の再レビュー範囲では、追加の P1/P2 機能不具合は検出されなかった。

## Residual Risks / Gaps

### [P2] 実行コマンドの範囲次第で coverage gate を通過しない
- Location:
  - `pyproject.toml:154`
  - `tests/test_plugin_small_modules.py`
- Evidence:
  - `tests/openai_gpt5_responses` と `tests/gpt5_agent_strategies` だけで実行すると total 83.09% で fail。
  - `tests/test_plugin_small_modules.py` を含めると total 85.01% で gate 通過。
- Impact:
  - プラグイン単体ディレクトリのみ実行する運用では CI 失敗の再発余地がある。

### [P2] 画像/Blob 応答の変換分岐は未テスト領域が残る
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:566`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:585`
- Evidence:
  - `TODO: convert to agent invoke message` が残存。
  - coverage missing でも該当分岐（tool invoke 内の image/blob 経路）が未充足。
- Impact:
  - 画像/ファイル応答を返す tool の統合時に表示・変換の挙動差異が潜在する。

## Verification
- `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 87 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - テスト本体は通過
  - coverage fail（83.09% < 85%）
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies tests/test_plugin_small_modules.py`
  - 90 passed
  - coverage pass（85.01%）
- `uv run ruff check ...`
  - All checks passed

## Suggested Follow-up
1. CI/開発手順に `tests/test_plugin_small_modules.py` を含めることを明示する。
2. `gpt5_function_calling.py` の image/blob 分岐に対する回帰テストを追加し、TODOを解消する。

## Resolution (2026-02-08)
- [Resolved][P2] 実行コマンド範囲に依存する coverage gate 未達
  - `tests/openai_gpt5_responses/test_entrypoints_and_errors.py` を追加。
    - `app/openai_gpt5_responses/main.py`
    - `app/openai_gpt5_responses/internal/errors.py`
    の回帰を plugin 配下テストに統合。
  - `tests/gpt5_agent_strategies/test_entrypoints_and_react.py` を追加。
    - `app/gpt5_agent_strategies/main.py`
    - `app/gpt5_agent_strategies/provider/gpt5_agent.py`
    - `app/gpt5_agent_strategies/strategies/gpt5_react.py`
    の回帰を plugin 配下テストに統合。
  - 結果:
    - `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
      だけで coverage gate (`>=85`) を達成。

- [Resolved][P2] image/blob 分岐の未テスト領域 + TODO 残存
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
    - image/blob 分岐の `yield tool_invoke_response` を
      `_to_agent_invoke_message()` 経由に統一し、TODO を解消。
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py`
    - `test_invoke_tool_image_message_path`
    - `test_invoke_tool_blob_message_path`
    を追加し、tool invoke の image/blob 経路を本体で回帰検証。

## Post-fix Verification (2026-02-08)
- `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies tests/test_plugin_small_modules.py`
  - 結果: pass
- `uv run pytest --no-cov -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: 93 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: 93 passed
  - coverage: `87.72%`（`--cov-fail-under=85` 達成）
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies tests/test_plugin_small_modules.py`
  - 結果: 96 passed
  - coverage: `87.72%`
