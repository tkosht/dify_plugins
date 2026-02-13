# GPT-5 Plugins Security Remediation Record (2026-02-13)

## Problem
- 以下の正本レビューで提示された未解消項目（Medium/Low）を実装で是正し、再発防止を含めて厳格に反映する。
  - `memory-bank/06-project/context/openai_gpt5_responses_security_review_2026-02-13.md`
  - `memory-bank/06-project/context/gpt5_agent_strategies_security_review_2026-02-13.md`

## Research
- `gpt5_agent_strategies`:
  - Medium: スキーマ未定義ツールで引数検証がバイパスされる（CWE-20）
  - Low: verbose ログで文字列 preview が残る（CWE-532）
  - Low: 依存監査証跡不足（CWE-1104）
- `openai_gpt5_responses`:
  - Low: `requirements.txt` の範囲指定により供給網ドリフト余地（CWE-1104）
- 対応対象:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.yaml`
  - `app/gpt5_agent_strategies/strategies/gpt5_react.yaml`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py`
  - `tests/gpt5_agent_strategies/test_strategy_schema.py`
  - `app/openai_gpt5_responses/requirements.txt`
  - `app/gpt5_agent_strategies/requirements.txt`
  - `.github/workflows/ci.yml`
  - `.github/workflows/test-all-subsystems.yml`

## Solution
### 1. Input Validation Fail-Close（F-001, Medium）
1. `allow_schemaless_tool_args`（default: `false`）を strategy parameter として追加。
2. ツールスキーマ未定義かつ tool-call arguments がある場合、既定で拒否する fail-close を実装。
3. 互換モードが必要な場合のみ `allow_schemaless_tool_args=true` で許可できるようにした。
4. 互換モードは `GPT5_AGENT_ALLOW_SCHEMELESS_OVERRIDE=true` の管理者 override がある場合のみ有効化するよう制約した。
5. スキーマ未定義の互換許可経路に上限制約（引数数/キー長/値サイズ）を追加した。
6. structured security event（`compat_mode_blocked`, `compat_mode_enabled`, `tool_schema_missing_*`）を記録するようにした。
7. 回帰テストを追加:
   - スキーマ未定義時の既定拒否
   - opt-in でも override 未設定時は拒否
   - opt-in + override 有効時のみ許可
   - スキーマ未定義互換引数の上限制約

### 2. Verbose Logging Hardening（F-002, Low）
1. verbose 時の文字列サニタイズを `{"chars": <len>}` のみへ変更。
2. `preview` 出力は `GPT5_AGENT_VERBOSE_LOG_PREVIEW=true` の明示時のみ許可。
3. 既存の機密キー redaction は維持。
4. 回帰テストを追加:
   - verbose 既定で preview 不出力
   - 明示フラグ時のみ preview 出力

### 3. Dependency Drift / Audit Gate（F-003, Low）
1. plugin requirements を pin 化:
   - `dify-plugin==0.7.1`
   - `openai==2.17.0`
   - `httpx==0.28.1`
   - `pydantic==2.12.3`
2. CI に security gate を追加（blocking）:
   - `pip-audit`（両 plugin requirements）
   - `bandit`（`app/openai_gpt5_responses`, `app/gpt5_agent_strategies`）
   - `allow_schemaless_tool_args:true` を app デフォルト設定で禁止する policy check
3. `dify-plugin` は `0.6.x` 系が `Werkzeug~=3.0.3` を要求し CVE 残存のため、`0.7.1` へ更新。

## Verification
- `uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies`
  - All checks passed
- `uv run pytest -q --no-cov tests/gpt5_agent_strategies tests/openai_gpt5_responses`
  - 160 passed
- `uv run pytest -q tests/gpt5_agent_strategies tests/openai_gpt5_responses`
  - 160 passed
  - coverage 86.86%（required 85% 達成）
- `if rg -n "allow_schemaless_tool_args:\\s*true" app/gpt5_agent_strategies; then exit 1; fi`
  - policy_ok（該当なし）
- `uvx --with pip-audit pip-audit -r app/openai_gpt5_responses/requirements.txt`
  - No known vulnerabilities found
- `uvx --with pip-audit pip-audit -r app/gpt5_agent_strategies/requirements.txt`
  - No known vulnerabilities found
- `uvx --with bandit bandit -q -r app/openai_gpt5_responses app/gpt5_agent_strategies -x tests`
  - exit code 0

## Notes
- `dify-plugin==0.6.x` は `Werkzeug~=3.0.3` に固定され、`pip-audit` で CVE が検出されることを確認済み。
- そのため、供給網・監査観点で `dify-plugin==0.7.1` へ更新し、CI 監査ゲートを必須化した。
