# GPT-5 Plugins Review Findings (2026-02-08, round2)

date: 2026-02-08
scope:
  - app/openai_gpt5_responses
  - tests/openai_gpt5_responses
  - app/gpt5_agent_strategies
  - tests/gpt5_agent_strategies
context:
  - 前回レビュー指摘の反映後リレビュー
  - prior_report: memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08.md
review_focus: bug/regression first
tags: review, gpt5, dify-plugin, openai-responses, agent-strategy, round2

## Problem
- 先行レビュー指摘が反映された状態で、Plugin A/B を再度精査し、残存リスクを重大度付きで記録する。

## Research
- 読み取り対象:
  - `app/openai_gpt5_responses/internal/payloads.py`
  - `app/openai_gpt5_responses/internal/messages.py`
  - `app/openai_gpt5_responses/models/llm/llm.py`
  - `app/gpt5_agent_strategies/internal/tooling.py`
  - `app/gpt5_agent_strategies/internal/flow.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - `tests/openai_gpt5_responses/test_messages.py`
  - `tests/openai_gpt5_responses/test_payloads_bool_coercion.py`
  - `tests/gpt5_agent_strategies/test_flow.py`
  - `tests/gpt5_agent_strategies/test_strategy_safety.py`
- 実行コマンド:
  - `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `python3` で最小再現（bool判定、tool出力空文字、parse_tool_arguments型）

## Findings

### [P1] streaming chunk で `delta.message is None` の経路を未防御
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:696`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:715`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:236`
- Evidence:
  - `check_tool_calls()` / `extract_tool_calls()` が `llm_result_chunk.delta.message.tool_calls` を無条件参照。
  - 同ファイル内で `chunk.delta.message` が `None` になり得る前提の分岐が存在。
- Impact:
  - usage-only chunk 等で `AttributeError` によりループが異常終了するリスク。
- Required tests:
  - `delta.message=None` chunk を含むストリーム入力でクラッシュしないことの検証。

### [P1] tool arguments が string 以外だと `TypeError` で停止
- Location:
  - `app/gpt5_agent_strategies/internal/tooling.py:21`
  - `app/gpt5_agent_strategies/internal/tooling.py:22`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:716`
- Evidence:
  - `json.loads(arguments)` は `dict` 入力で `TypeError` を投げるが、except は `JSONDecodeError` のみ。
  - 最小再現: `parse_tool_arguments({'q':'x'})` で `TypeError` を確認。
- Impact:
  - provider実装差異で arguments が dict 返却される場合、実行が fail-closed ではなくクラッシュする。
- Required tests:
  - dict / bytes / None などの非str入力時に `ok=False` で安全に返すテスト。

### [P2] `enable_stream` 文字列 `"false"` の判定不一致が LLM 層に残存
- Location:
  - `app/openai_gpt5_responses/models/llm/llm.py:162`
  - `app/openai_gpt5_responses/internal/payloads.py:103`
- Evidence:
  - LLM層で `bool(model_parameters.get("enable_stream", True))` を使用しており `"false"` が True 扱い。
  - payload生成側は strict coercion 実装に更新済みで、層間の判定規則が不一致。
- Impact:
  - 疑似ストリーミング制御が入力意図と逆転する可能性。
- Required tests:
  - `enable_stream` の bool-like 入力に対して `_invoke` の戻り型（stream/non-stream）が期待通りであること。

### [P2] 空文字の tool output が履歴に残らず文脈が脱落
- Location:
  - `app/openai_gpt5_responses/internal/messages.py:226`
  - `app/openai_gpt5_responses/internal/messages.py:227`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:615`
- Evidence:
  - `tool_call_id` があっても `content==""` だと `_to_tool_content()` は `[]` を返し履歴に載らない。
  - 最小再現: `tool empty output -> []`。
- Impact:
  - 「toolを呼んだ事実」が次ラウンドのコンテキストから消える可能性。
- Required tests:
  - 空文字 output でも `function_call_output` を保持するか、保持しない設計なら明示仕様化を検証。

### [P2] テストは増えたが実行本体経路の回帰検知は依然薄い
- Location:
  - `tests/gpt5_agent_strategies/test_flow.py`
  - `tests/gpt5_agent_strategies/test_strategy_safety.py`
  - `tests/openai_gpt5_responses/test_messages.py`
  - `tests/openai_gpt5_responses/test_payloads_bool_coercion.py`
- Evidence:
  - 追加テストは helper中心で、`gpt5_function_calling.py` / `models/llm/llm.py` 本体の実行分岐テストが未整備。
  - `uv run pytest -q tests/...` は 52 passed だが coverage gate 85% に届かず total 25.84%。
- Impact:
  - 主要統合経路の回帰が将来再流入する余地がある。
- Required tests:
  - stream/non-stream、tool_callsありなし、parse_error分岐、max_iterations分岐を本体経路で検証するテスト。

## Improvements Confirmed in this round
- `payloads.py` の bool strict coercion 実装追加。
- `messages.py` の assistant/tool 文脈保持変換実装追加。
- `flow.py` 導入による履歴リストの非破壊構築。
- `parse_error` 分岐追加による不正JSON時の tool fail-open 抑制。

## Verification
- `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`:
  - 結果: 52 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`:
  - 結果: テスト本体は 52 passed
  - 失敗理由: `--cov-fail-under=85` に対して total 25.84%
- `uv run ruff check ...`:
  - 結果: All checks passed

## Suggested Follow-up
1. `check_tool_calls()` / `extract_tool_calls()` に `delta.message` null-guard を追加。
2. `parse_tool_arguments()` が非str入力でも `ToolArgumentsParseResult(ok=False, ...)` を返すように修正。
3. `_invoke` の `enable_stream` 判定を payload と同一の strict coercion に統一。
4. `gpt5_function_calling.py` / `llm.py` の実行本体を直接叩く回帰テストを追加。

## Resolution (2026-02-08)
- [Resolved][P1] `delta.message is None` の stream 経路クラッシュ
  - `app/gpt5_agent_strategies/internal/flow.py`
    - `extract_stream_tool_calls()` / `extract_blocking_tool_calls()` を追加し、`delta.message` / `message` が `None` の場合に `[]` を返す null-safe 抽出へ統一。
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
    - `check_tool_calls()` / `extract_tool_calls()` / `check_blocking_tool_calls()` / `extract_blocking_tool_calls()` を上記 helper 経由に変更。
  - テスト:
    - `tests/gpt5_agent_strategies/test_flow.py`
      - `test_extract_stream_tool_calls_handles_none_message`
      - `test_extract_stream_tool_calls_reads_existing_calls`
      - `test_extract_blocking_tool_calls_handles_none_message`

- [Resolved][P1] tool arguments 非str入力時の `TypeError` 停止
  - `app/gpt5_agent_strategies/internal/tooling.py`
    - `parse_tool_arguments(arguments: Any)` へ変更。
    - 空文字 `""` のみ `ok=True,args={}` とし、`dict/bytes/None` を含む非strは `ok=False` で fail-closed。
    - JSON decode 失敗時の例外捕捉を `TypeError/ValueError/JSONDecodeError` に拡張。
  - テスト:
    - `tests/gpt5_agent_strategies/test_strategy_safety.py`
      - `test_parse_tool_arguments_rejects_non_string_payload`

- [Resolved][P2] `enable_stream="false"` 判定不一致
  - `app/openai_gpt5_responses/internal/payloads.py`
    - `coerce_bool_strict()` を共通化（公開関数化）。
  - `app/openai_gpt5_responses/models/llm/llm.py`
    - `_invoke` の `effective_stream` を `coerce_bool_strict(..., field_name="enable_stream")` 基準へ変更。
  - テスト:
    - `tests/openai_gpt5_responses/test_llm_stream_flag.py`
      - `test_invoke_disable_stream_string_returns_blocking_result`
      - `test_invoke_enable_stream_string_returns_generator`

- [Resolved][P2] 空文字 tool output の文脈脱落
  - `app/openai_gpt5_responses/internal/messages.py`
    - `_to_tool_content()` を `tool_call_id` のみ必須化し、`content==""` でも `function_call_output` を保持。
  - テスト:
    - `tests/openai_gpt5_responses/test_messages.py`
      - `test_prompt_messages_keep_empty_tool_output_with_call_id`

## Post-fix Verification (2026-02-08)
- `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: pass
- `uv run pytest --no-cov -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: 61 passed
