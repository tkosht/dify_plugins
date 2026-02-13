# GPT-5 Plugins Review Findings (2026-02-08, round8)

date: 2026-02-08
scope:
  - app/openai_gpt5_responses
  - tests/openai_gpt5_responses
  - app/gpt5_agent_strategies
  - tests/gpt5_agent_strategies
context:
  - 反映後リレビュー（round8）
  - note:
      - 外部サブエージェント実行は `https://api.openai.com/v1/responses` の stream disconnected により実施不可
      - ローカル lint/test + コード精査で検証
  - prior_reports:
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round2.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round3.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round4.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round5.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round6.md
      - memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08_round7.md
review_focus: security/bug/regression first
tags: review, gpt5, dify-plugin, openai-responses, agent-strategy, round8

## Problem
- Plugin A/B に対して、前回指摘反映後の再レビューを実施し、新規不具合と回帰の有無を再判定する。

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
  - `rg -n "TODO|FIXME|HACK|XXX" app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`

## Findings

### [P1/P2] 新規の重大不具合・回帰は検出なし
- Result:
  - Plugin A/B とテスト範囲で新しい P1/P2 は確認できなかった。
  - ローカル lint/test はすべて成功。

### [Info] round7 指摘の tool invoke 例外露出は修正維持
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:116`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:602`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:606`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:758`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:807`
- Evidence:
  - 例外時のユーザー向け文言は固定文字列 `_TOOL_INVOKE_ERROR_MESSAGE` へ統一。
  - 回帰テストで内部エラー文字列（例: `/srv/secret`）がユーザー出力へ露出しないことを確認。

### [Info] round6 指摘（path traversal / oversized file / imageエラー文言）も修正維持
- Location:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:855`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:862`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:878`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:676`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:683`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:699`
- Evidence:
  - `/files` 配下の `realpath/commonpath` 境界チェックとサイズ上限チェックが有効。
  - 失敗時固定文言 (`Failed to process generated image file.`) のテストが維持。

## Verification
- `uv run ruff check ...`
  - All checks passed
- `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 97 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 97 passed
  - coverage 88.28%（required 85% を達成）
- `rg -n "TODO|FIXME|HACK|XXX" ...`
  - 対象範囲で該当なし

## Residual Risks / Gaps
1. 外部サブエージェント実行（OpenAI Responses API 接続）による独立再現は未実施。
2. 実 API 接続時のネットワーク変動・stream切断ハンドリングは今回のローカルレビュー範囲外。

## Linked Security Records
- 2026-02-12 の `gpt5_agent_strategies` セキュリティ正本:
  - `memory-bank/06-project/context/gpt5_agent_strategies_security_review_2026-02-12.md`
  - `memory-bank/06-project/context/gpt5_agent_strategies_security_review_2026-02-12.json`
  - `memory-bank/06-project/context/gpt5_agent_strategies_security_review_2026-02-12_handoff.md`
- 2026-02-13 の `gpt5_agent_strategies` 再レビュー正本（最新）:
  - `memory-bank/06-project/context/gpt5_agent_strategies_security_review_2026-02-13.md`
  - `memory-bank/06-project/context/gpt5_agent_strategies_security_review_2026-02-13.json`
  - `memory-bank/06-project/context/gpt5_agent_strategies_security_review_2026-02-13_handoff.md`

## Security Remediation Follow-up (2026-02-12)
- 実装修正と回帰検証の記録:
  - `memory-bank/06-project/context/gpt5_plugins_security_remediation_2026-02-12.md`
- 要点:
  - `openai_api_base` の fail-close 検証（https + allowlist + private/meta拒否）を実装。
  - `gpt5_agent_strategies` のログを metadata-only デフォルトへ変更し、verbose は opt-in 化。
  - `emit_intermediate_thoughts` の既定を `false` へ変更。
  - strict tool args 検証（unknown key reject / 基本型検証）を追加。

## Security Remediation Follow-up (2026-02-13)
- 実装修正と回帰検証の記録:
  - `memory-bank/06-project/context/gpt5_plugins_security_remediation_2026-02-13.md`
- 要点:
  - スキーマ未定義ツール引数を既定拒否（fail-closed）へ変更し、互換用途の opt-in (`allow_schemaless_tool_args`) を追加。
  - verbose ログの文字列 preview を既定停止し、明示フラグ有効時のみ出力するよう変更。
  - plugin requirements を pin 化（`dify-plugin==0.7.1` など）し、CI へ `pip-audit` / `bandit` の blocking gate を追加。
