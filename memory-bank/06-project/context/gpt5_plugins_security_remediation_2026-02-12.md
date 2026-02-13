# GPT-5 Plugins Security Remediation Record (2026-02-12)

## Problem
- 以下の正本レビューで `FAIL` 判定となった High/Medium 指摘へ、実装と回帰テストで厳格対応する。
  - `memory-bank/06-project/context/openai_gpt5_responses_security_review_2026-02-12.md`
  - `memory-bank/06-project/context/gpt5_agent_strategies_security_review_2026-02-12.md`

## Research
- 主要修正対象:
  - `app/openai_gpt5_responses/internal/credentials.py`
  - `app/openai_gpt5_responses/provider/openai_gpt5.py`
  - `app/openai_gpt5_responses/models/llm/llm.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.yaml`
  - `app/gpt5_agent_strategies/strategies/gpt5_react.yaml`
- 主要テスト対象:
  - `tests/openai_gpt5_responses/*`
  - `tests/gpt5_agent_strategies/*`

## Solution
### OpenAI GPT-5 Responses
1. `openai_api_base` を fail-close 検証へ変更。
   - `https` のみ許可
   - loopback/private/link-local/metadata/localhost 拒否
   - allowlist 方式（既定 `api.openai.com`、追加は `OPENAI_GPT5_ALLOWED_BASE_URL_HOSTS`）
   - パスは空または `/v1` のみ許可（正規化は `/v1` 固定）
2. provider / model の credential validation で `str(exc)` 返却を廃止。
   - 例外種別ごとに安全な固定文言へマッピング

### GPT-5 Agent Strategies
1. ログを metadata-only デフォルトへ変更。
   - model/round/tool-call log で raw payload の直接記録を廃止
   - `output_summary` 形式へ統一
2. verbose ログを opt-in 化。
   - `GPT5_AGENT_VERBOSE_LOGGING=true` 時のみ `debug_output` を追加
   - sensitive key は `***REDACTED***`
3. `emit_intermediate_thoughts` 既定値を `false` 化。
   - `gpt5_function_calling.yaml`, `gpt5_react.yaml`, runtime params を整合
4. tool args 検証を strict 化。
   - schema 定義がある場合 unknown key を拒否
   - 基本型（integer/number/boolean/object/array）の fail-close 検証
   - option 値検証を継続

## Verification
- `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - All checks passed
- `uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 155 passed
- `uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - 155 passed
  - coverage 86.55% (required 85% 達成)

## Notes
- `bandit` / `pip-audit` は環境未導入のため、静的/依存監査は別途CI導入が必要。
- セキュリティ判定更新（FAIL→再判定）は、上記修正後の再レビュー記録を新規作成して実施する。
