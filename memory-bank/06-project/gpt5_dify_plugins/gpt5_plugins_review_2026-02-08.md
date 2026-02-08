# GPT-5 Plugins Review Findings (2026-02-08)

date: 2026-02-08
scope:
  - app/openai_gpt5_responses
  - tests/openai_gpt5_responses
  - app/gpt5_agent_strategies
  - tests/gpt5_agent_strategies
review_focus: bug/regression first
tags: review, gpt5, dify-plugin, openai-responses, agent-strategy, findings

## Problem
- Plugin A/B の実装とテストを不具合・回帰優先で精緻レビューし、重大度付きの指摘を記録する。

## Research
- 読み取り対象:
  - `app/openai_gpt5_responses/internal/payloads.py`
  - `app/openai_gpt5_responses/internal/messages.py`
  - `app/openai_gpt5_responses/models/llm/llm.py`
  - `app/openai_gpt5_responses/provider/openai_gpt5.py`
  - `app/openai_gpt5_responses/models/llm/*.yaml`
  - `app/openai_gpt5_responses/provider/openai_gpt5.yaml`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - `app/gpt5_agent_strategies/internal/tooling.py`
  - `app/gpt5_agent_strategies/internal/loop.py`
  - `app/gpt5_agent_strategies/internal/policy.py`
  - `app/gpt5_agent_strategies/strategies/*.yaml`
  - `tests/openai_gpt5_responses/*.py`
  - `tests/gpt5_agent_strategies/*.py`
- 実行コマンド:
  - `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `python3` で `build_responses_request(...)` と `prompt_messages_to_responses_input(...)` の最小再現

## Findings

### [P1] Responses API 向け tool 文脈が入力変換時に欠落
- Location:
  - `app/openai_gpt5_responses/internal/messages.py:27`
  - `app/openai_gpt5_responses/internal/messages.py:39`
  - `app/openai_gpt5_responses/internal/messages.py:75`
- Evidence:
  - `prompt_messages_to_responses_input()` がメッセージを `role + input_text` に平坦化し、`tool_call_id` と function-call output の構造を保持しない。
  - `tool` ロールの再現入力を与えても `tool_call_id` が落ちることをローカルで確認。
- Impact:
  - 複数ターンでの tool 呼び出し連携時に、モデルへ返す履歴文脈が欠落し、呼び出し整合性が崩れる。
- Required tests:
  - assistant tool_call -> tool response の往復で `tool_call_id` が維持されることの検証。

### [P1] ブール値文字列の誤解釈で挙動が逆転
- Location:
  - `app/openai_gpt5_responses/internal/payloads.py:81`
  - `app/openai_gpt5_responses/internal/payloads.py:121`
  - `app/openai_gpt5_responses/internal/payloads.py:33`
- Evidence:
  - `bool("false") is True` のため、`enable_stream="false"`/`parallel_tool_calls="false"`/`strict="false"` が True に変換される。
  - 最小再現で `payload["stream"] == True`、`payload["parallel_tool_calls"] == True`、`format["strict"] == True` を確認。
- Impact:
  - UI 入力と実際の API リクエストが不一致になり、制御不能な回帰要因となる。
- Required tests:
  - `True/False/"true"/"false"/"0"/"1"` のテーブルテスト。

### [P1] tool 引数 JSON 失敗時に fail-open 実行
- Location:
  - `app/gpt5_agent_strategies/internal/tooling.py:8`
  - `app/gpt5_agent_strategies/internal/tooling.py:14`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:460`
- Evidence:
  - `parse_tool_arguments()` は不正 JSON を `{}` として返す。
  - 呼び出し側は `{**runtime_parameters, **tool_call_args}` でそのまま invoke する。
- Impact:
  - 本来失敗すべき不正引数が、既定値で実行される fail-open 動作になる。
- Required tests:
  - 不正 JSON で invoke せず、明示的エラー応答へ分岐することの検証。

### [P1] ストリームで tool call 判明前テキストが先出しされる経路
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:223`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:233`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:241`
- Evidence:
  - `function_call_state` が False の時点で content を即時 yield。
  - 後続 chunk で tool call が見つかっても先出し済み text は回収できない。
- Impact:
  - ユーザーに中間文言が漏れ、最終応答との一貫性が崩れる。
- Required tests:
  - `text chunk -> tool_call chunk` 順序で先出し抑止を検証。

### [P2] 履歴メッセージの破壊的更新
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:131`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:132`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:133`
- Evidence:
  - `history_prompt_messages.insert(...)` と `append(...)` を直接実行。
- Impact:
  - 呼び出し側が同一オブジェクトを再利用する場合に system/user が蓄積し、再実行で重複履歴となる。
- Required tests:
  - 同一 `history_prompt_messages` 再利用時に長さが増殖しないこと。

### [P2] テストがコア経路の回帰を検知できない
- Location:
  - `tests/openai_gpt5_responses/test_payloads.py`
  - `tests/openai_gpt5_responses/test_provider_schema.py`
  - `tests/gpt5_agent_strategies/test_policy.py`
  - `tests/gpt5_agent_strategies/test_strategy_safety.py`
  - `tests/gpt5_agent_strategies/test_strategy_schema.py`
- Evidence:
  - 実装中心の `gpt5_function_calling.py` と `models/llm/llm.py` の挙動テストがない。
  - `--no-cov` では 19 passed だが、通常実行は全体カバレッジ閾値で失敗（total 15.17%）。
- Impact:
  - 重要経路の regressions が事前検知されない。
- Required tests:
  - stream/non-stream、tool call、max iteration、error path の統合ユニット。

## Verification
- `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`:
  - 結果: 19 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`:
  - 結果: テスト本体は 19 passed
  - 失敗理由: `pyproject.toml` の `--cov-fail-under=85` に対して total 15.17%
- 追加確認:
  - `build_responses_request()` の bool 文字列入力誤解釈を再現。
  - `prompt_messages_to_responses_input()` で tool 文脈が落ちることを再現。

## Resolution (2026-02-08)
- [P1] Responses API 向け tool 文脈欠落: **Resolved**
  - `app/openai_gpt5_responses/internal/messages.py`
  - assistant `tool_calls` -> `function_call`、tool role -> `function_call_output` + `tool_call_id` を保持。
  - tests: `tests/openai_gpt5_responses/test_messages.py`
- [P1] ブール値文字列誤解釈: **Resolved**
  - `app/openai_gpt5_responses/internal/payloads.py`
  - strict bool coercion を導入（`enable_stream`, `parallel_tool_calls`, `json_schema.strict`）。
  - tests: `tests/openai_gpt5_responses/test_payloads_bool_coercion.py`
- [P1] tool 引数 JSON fail-open: **Resolved**
  - `app/gpt5_agent_strategies/internal/tooling.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - parse 失敗時は fail-closed（tool invoke せずエラー応答）。
  - tests: `tests/gpt5_agent_strategies/test_strategy_safety.py`
- [P1] stream 先出しリーク: **Resolved**
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - tool call があるラウンドでは中間 text を先出ししない判定へ変更。
  - tests: `tests/gpt5_agent_strategies/test_flow.py`
- [P2] 履歴メッセージ破壊更新: **Resolved**
  - `app/gpt5_agent_strategies/internal/flow.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - round prompt 構築を非破壊化。
  - tests: `tests/gpt5_agent_strategies/test_flow.py`
- [P2] コア回帰テスト不足: **Resolved (scope内)**
  - 追加テスト: `test_messages.py`, `test_payloads_bool_coercion.py`, `test_flow.py`
  - 重点経路（tool文脈、bool coercion、stream判定、履歴非破壊）を補強。

## Post-fix Verification (2026-02-08)
- `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: pass
- `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: 52 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: テスト本体は 52 passed
  - 注意: リポジトリ全体の `--cov-fail-under=85` のため Coverage gate は未達（総計 25.84%）

## Suggested Follow-up
1. `payloads.py` に厳密な bool coercion 関数を導入。
2. `messages.py` に Responses API 互換の tool input 変換を実装。
3. `gpt5_function_calling.py` で invalid tool arguments を fail-closed 化。
4. コア経路を対象に回帰テストを追加し、カバレッジ対象の最小範囲を見直す。
