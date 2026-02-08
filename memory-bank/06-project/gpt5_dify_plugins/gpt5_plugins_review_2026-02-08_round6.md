# GPT-5 Plugins Review Findings (2026-02-08, round6)

date: 2026-02-08
scope:
  - app/openai_gpt5_responses
  - tests/openai_gpt5_responses
  - app/gpt5_agent_strategies
  - tests/gpt5_agent_strategies
context:
  - 反映後リレビュー（round6）
  - prior_reports:
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round2.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round3.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round4.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round5.md
review_focus: security/bug/regression first
tags: review, gpt5, dify-plugin, openai-responses, agent-strategy, round6

## Problem
- Plugin A/B 反映後の再レビューを実施し、残存する実害リスクを特定する。

## Research
- 重点確認コード:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - `app/gpt5_agent_strategies/internal/tooling.py`
  - `app/openai_gpt5_responses/models/llm/llm.py`
  - `app/openai_gpt5_responses/internal/messages.py`
  - `app/openai_gpt5_responses/internal/payloads.py`
- 重点確認テスト:
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py`
  - `tests/gpt5_agent_strategies/test_strategy_safety.py`
  - `tests/openai_gpt5_responses/test_llm_stream_flag.py`
  - `tests/openai_gpt5_responses/test_messages.py`
- 実行コマンド:
  - `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies tests/test_plugin_small_modules.py`

## Findings

### [P1] `/files/` prefix 判定のみでローカルファイルを開くため、パストラバーサルを防げていない
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:541`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:545`
- Evidence:
  - 分岐条件が `file_info.startswith("/files/")` のみ。
  - 該当分岐で `open(file_info, "rb")` を直接実行。
  - `os.path.normpath("/files/../etc/passwd") == "/etc/passwd"` となるため、`..` を含むパスは `/files` 外へ正規化可能。
- Impact:
  - 実行環境に `/files` が存在する場合、意図しない任意ファイル読取につながる可能性。
  - 併せてサイズ上限なしの全量読込 (`f.read()`) により、大容量ファイルでメモリ圧迫リスクがある。

### [P2] 画像変換失敗時の内部例外文字列をそのままユーザーへ返す
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:558`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:560`
- Evidence:
  - `except Exception as e:` で捕捉後、`f"Failed to create blob message: {e}"` をそのまま `text_message` で出力。
- Impact:
  - 例外内容に内部パスや実行環境情報が含まれる場合、情報露出につながる可能性。

### [Info] round5 の残余リスクは今回再現せず
- Coverage gate:
  - `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies` で Required coverage 85% を満たし pass（87.72%）。
- TODO残存:
  - 対象ディレクトリに `TODO/FIXME` は検出されず。

## Verification
- `uv run ruff check ...`
  - All checks passed
- `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 93 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 93 passed / coverage 87.72%（gate達成）
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies tests/test_plugin_small_modules.py`
  - 96 passed / coverage 87.72%

## Suggested Follow-up
1. 画像ファイル読込前に `realpath` 正規化し、許可ルート (`/files` 配下) 逸脱を拒否する。
2. ファイル読込にサイズ上限を設け、上限超過時は安全なエラーメッセージへ置換する。
3. 例外文言は内部詳細を伏せた固定メッセージにし、詳細はログ側へ送る。
4. `tests/gpt5_agent_strategies` に以下を追加する。
   - `/files/../...` を拒否するテスト
   - 過大ファイル読込を拒否/打ち切るテスト
   - blob変換失敗時に内部例外を露出しないテスト

## Resolution (2026-02-08)
- [Resolved][P1] `/files/` prefix 判定のみのローカル読込
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
    - `_resolve_safe_local_file_path()` を追加し、`realpath` + `commonpath` で `/files` 配下のみ許可。
    - `_read_local_file_for_blob()` を追加し、上記安全パスのみ読込対象に制限。
    - `IMAGE/IMAGE_LINK` 経路は `_read_local_file_for_blob()` 経由に変更。

- [Resolved][P1/P2] 大容量読込・例外露出
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
    - ローカル読込サイズ上限を 5MB に設定（`_MAX_BLOB_FILE_BYTES`）。
    - 画像変換失敗時のユーザー向けメッセージを
      `"Failed to process generated image file."` に固定。
    - 内部詳細は `logger.exception(...)` へ送る方式へ変更。

- [Resolved][P2] image/blob 分岐の追加回帰テスト
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py`
    - `test_resolve_safe_local_file_path_rejects_path_traversal`
    - `test_read_local_file_for_blob_rejects_oversized_file`
    - `test_invoke_image_blob_conversion_error_masks_internal_details`

## Post-fix Verification (2026-02-08)
- `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: pass
- `uv run pytest --no-cov -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: 96 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 結果: 96 passed
  - coverage: `87.96%`（`--cov-fail-under=85` 達成）
