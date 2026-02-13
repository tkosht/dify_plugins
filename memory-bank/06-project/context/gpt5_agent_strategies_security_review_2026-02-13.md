# GPT-5 Agent Strategies Security Review Record (2026-02-13)

## Metadata
- recorded_at: 2026-02-13T23:02:55+09:00
- reviewer: Codex (GPT-5)
- target: `app/gpt5_agent_strategies`
- review_profile: standard
- gate_result: PASS
- gate_reason: Critical/High は未検出（Low 1件）
- tags: security-review, app-security-review, gpt5-agent-strategies, owasp-api, cwe, pass-with-recommendations

## Problem
- `app/gpt5_agent_strategies` の再監査結果を、開発元AIエージェントへ再解釈不要な形で連携する。
- 2026-02-12版（FAIL）および同日 earlier 版（PASS/Medium含む）との差分を反映し、現時点の最新判定を固定する。

## Research
- Scope inventory:
  - `app/gpt5_agent_strategies/manifest.yaml`
  - `app/gpt5_agent_strategies/provider/gpt5_agent.yaml`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.yaml`
  - `app/gpt5_agent_strategies/strategies/gpt5_react.yaml`
  - `app/gpt5_agent_strategies/internal/tooling.py`
  - `app/gpt5_agent_strategies/requirements.txt`
  - `tests/gpt5_agent_strategies/*.py`
- Executed baseline checks:
  - `uvx --with bandit bandit -q -r app/openai_gpt5_responses app/gpt5_agent_strategies -x tests` -> `exit code 0`
  - `uvx --with pip-audit pip-audit -r app/gpt5_agent_strategies/requirements.txt` -> `No known vulnerabilities found`
- Executed test checks:
  - `uv run pytest -q --no-cov tests/gpt5_agent_strategies` -> `73 passed`
- Manual matrix focus:
  - INPUT-001 (Input validation)
  - SECR-002 (Secrets in logs)
  - CONF-002 (Safe defaults)
  - DEP-001 / DEP-002 (Dependency risk)

## Solution
### 1) Summary
- Target: `app/gpt5_agent_strategies`
- Review date: 2026-02-13
- Gate result: **PASS**
- Gate reason: Critical/High がないため `PASS with recommendations`

### 2) Findings
#### [F-001] 互換モード有効化時の設定統制リスク（限定的）
- Severity: Low
- Confidence: Medium
- Standard refs:
  - OWASP API Security Top 10 2023: API8
  - OWASP Top 10 2021: A05
  - OWASP ASVS v4: V5 (Input Validation)
- CWE: CWE-16
- Evidence:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.yaml:172` `allow_schemaless_tool_args` 設定が公開されている
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.yaml:184` 互換モードは `GPT5_AGENT_ALLOW_SCHEMELESS_OVERRIDE=true` の場合のみ有効
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:138` `GPT5_AGENT_ALLOW_SCHEMELESS_OVERRIDE` を導入
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:226` override 無効時は `compat_mode_blocked` イベントを記録
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:1314` スキーマ未定義は既定 fail-closed
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:1643` override 有効時のみ opt-in 許可を検証
- Impact:
  - 管理者が override 環境変数を有効化した場合のみ、スキーマ未定義ツール引数が許可される。
  - 運用統制が弱い環境では入力検証水準が下流実装依存になる。
- Remediation (minimum viable fix):
  1. `allow_schemaless_tool_args` は既定 `false` を維持し、override 環境変数を管理者限定運用にする
  2. CI で `allow_schemaless_tool_args: true` を禁止するゲートを維持する
  3. 互換要件が消えた時点でオプション廃止を検討する
- Verification steps:
  - 設定監査で `allow_schemaless_tool_args` が既定 `false` であることを確認
  - `allow_schemaless_tool_args=true` かつ override 無効時に `compat_mode_blocked` が記録されることを確認
  - CI の `allow_schemaless_tool_args:true` 禁止ゲートが有効であることを確認

### 3) Positive Controls Observed
- `emit_intermediate_thoughts` の既定値が `false`:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.yaml:159`
  - `app/gpt5_agent_strategies/strategies/gpt5_react.yaml:159`
  - `tests/gpt5_agent_strategies/test_strategy_schema.py:133`
- 既定ログは metadata-only:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:1221`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:2014`
- verboseログでも機密キーは伏字化:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:1158`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:2028`
- 文字列 preview は明示フラグ時のみ有効:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:1144`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:2060`
- スキーマ未定義ツールは既定 fail-closed:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:1314`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:1517`
- 互換モードは管理者 override 環境変数がある場合のみ有効:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:138`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:226`
- CI で `allow_schemaless_tool_args:true` を禁止:
  - `.github/workflows/ci.yml:58`
  - `.github/workflows/test-all-subsystems.yml:171`
- 依存監査ゲート（pip-audit/bandit）を CI へ導入:
  - `.github/workflows/ci.yml:63`
  - `.github/workflows/test-all-subsystems.yml:176`

### 4) Residual Risks
- `allow_schemaless_tool_args=true` と override 環境変数を同時に有効化した場合の安全性は運用統制に依存

### 5) Recommended Next Actions
1. `GPT5_AGENT_ALLOW_SCHEMELESS_OVERRIDE` の利用を管理者限定で監査する
2. 互換要件の整理後に `allow_schemaless_tool_args` 廃止を検討する
3. 現行 CI security gates（pip-audit / bandit / policy check）を release gate として維持する

## Verification
- Executed checks:
  - `uvx --with bandit bandit -q -r app/openai_gpt5_responses app/gpt5_agent_strategies -x tests` -> `exit code 0`
  - `uvx --with pip-audit pip-audit -r app/gpt5_agent_strategies/requirements.txt` -> `No known vulnerabilities found`
  - `uv run pytest -q --no-cov tests/gpt5_agent_strategies` -> `73 passed`
- Gate rule: Critical または High が1件以上で FAIL
- Determination:
  - `F-001`: Low
  - => **PASS with recommendations**
