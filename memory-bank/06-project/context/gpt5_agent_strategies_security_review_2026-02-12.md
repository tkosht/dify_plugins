# GPT-5 Agent Strategies Security Review Record (2026-02-12)

## Metadata
- recorded_at: 2026-02-12T16:16:29+09:00
- reviewer: Codex (GPT-5)
- target: `app/gpt5_agent_strategies`
- review_profile: standard
- gate_result: FAIL
- gate_reason: ログへの生データ記録が High (`F-001`, `CWE-532`) で残存
- tags: security-review, app-security-review, gpt5-agent-strategies, owasp-api, cwe

## Problem
- `app/gpt5_agent_strategies` のセキュリティレビュー結果を、開発元AIエージェントへ再解釈不要な形で連携する。
- 目的は、修正タスクへそのまま接続できる証跡付きレビュー正本を `memory-bank/06-project/context` に残すこと。

## Research
- Scope inventory:
  - `app/gpt5_agent_strategies/manifest.yaml`
  - `app/gpt5_agent_strategies/provider/gpt5_agent.yaml`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.yaml`
  - `app/gpt5_agent_strategies/strategies/gpt5_react.yaml`
  - `app/gpt5_agent_strategies/internal/tooling.py`
  - `app/gpt5_agent_strategies/requirements.txt`
  - `tests/gpt5_agent_strategies/test_strategy_safety.py`
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py`
- Executed baseline checks:
  - `bandit -r app/gpt5_agent_strategies` -> `command not found`
  - `pip-audit -r app/gpt5_agent_strategies/requirements.txt` -> `command not found`
- Executed test checks:
  - `uv run pytest -q --no-cov tests/gpt5_agent_strategies/test_strategy_safety.py tests/gpt5_agent_strategies/test_strategy_invoke_paths.py` -> `36 passed`
- Manual matrix focus:
  - SECR-002 (Secrets in logs)
  - INPUT-001 (Input validation)
  - CONF-002 (Safe defaults)
  - DEP-001 / DEP-002 (Dependency risk)

## Solution
### 1) Summary
- Target: `app/gpt5_agent_strategies`
- Review date: 2026-02-12
- Gate result: **FAIL**
- Gate reason: High finding (`F-001`) が存在

### 2) Findings
#### [F-001] ツール入出力とLLM応答が生ログに記録される
- Severity: High
- Confidence: High
- Standard refs:
  - OWASP Top 10 2021: A09 (Security Logging and Monitoring Failures)
  - OWASP API Security Top 10 2023: API3 (Broken Object Property Level Authorization; exposed data surface)
  - OWASP ASVS v4: V9 (Logging and Monitoring)
  - NIST SP 800-218 SSDF: PW.4
- CWE: CWE-532
- Evidence:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:494` `tool_input` に引数をそのまま記録
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:877` ツール応答を `output` として記録
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:910` `llm_response` と `tool_responses` を丸ごと記録
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:657` 非表示設定時でも `<think>` がログ保持されることを検証
- Impact:
  - ツール引数/応答に機密値が含まれる場合、ログ経由で漏えい面が増える
  - 内部思考や文脈断片が運用ログに残り、不要な情報露出が起きる
- Remediation (minimum viable fix):
  1. ログ記録前にキー/値サニタイズ（`token`, `secret`, `authorization`, `password` など）を共通化
  2. 既定は本文記録を禁止し、メタデータ（件数・長さ・ステータス）中心へ変更
  3. 詳細ログは明示的なデバッグモード時のみ許可し、保持期限を短期化
  4. ログ赤線化の回帰テストを追加
- Verification steps:
  - ログ出力を収集し、機密キー値が伏字化されること
  - `llm_response`/`tool_responses` が既定設定で生記録されないこと

#### [F-002] `<think>` 中間思考の既定公開
- Severity: Medium
- Confidence: High
- Standard refs:
  - OWASP API Security Top 10 2023: API3 (Excessive Data Exposure)
  - OWASP Top 10 2021: A04 (Insecure Design)
  - OWASP ASVS v4: V1/V9 (Architecture, Logging)
- CWE: CWE-200
- Evidence:
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.yaml:159` `emit_intermediate_thoughts` 既定値が `true`
  - `app/gpt5_agent_strategies/strategies/gpt5_react.yaml:159` 同様に `true`
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:333` `<think>` 整形してユーザーへ出力
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:1565` `<think>` が表示される回帰テストが存在
- Impact:
  - 内部推論・方針断片の露出により、情報露出面とプロンプト悪用面が増える
- Remediation (minimum viable fix):
  1. `emit_intermediate_thoughts` の既定を `false` に変更
  2. 管理者限定のデバッグ設定へ分離
  3. 表示時にも機微パターン除去フィルタを適用
- Verification steps:
  - 既定設定で `<think>` がユーザー表示に出ないこと
  - デバッグ有効時のみ `<think>` が表示されること

#### [F-003] ツール引数バリデーションが限定的で未知キーを広く許容
- Severity: Medium
- Confidence: Medium
- Standard refs:
  - OWASP API Security Top 10 2023: API8 (Security Misconfiguration / input handling)
  - OWASP Top 10 2021: A03 (Injection)
  - OWASP ASVS v4: V5 (Input Validation)
- CWE: CWE-20
- Evidence:
  - `app/gpt5_agent_strategies/internal/tooling.py:36` JSON object 判定までで、許可キー制御なし
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:704` runtime params と tool args を単純マージ
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:1100` option定義のある項目のみ検証
  - `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:746` 検証後パラメータをそのまま実行
  - `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:1440` option外値の拒否は確認されるが、未知キー拒否は未確認
- Impact:
  - 下流ツール側の検証が弱い場合、想定外パラメータによる誤動作・悪用余地が残る
- Remediation (minimum viable fix):
  1. ツールごとに許可キー・型・必須を定義した strict schema 検証を導入
  2. 未知キーは既定拒否（allowlistのみ通過）
  3. 文字列化変換前後で型安全テーブルテストを追加
- Verification steps:
  - 未知キー混入時に tool invoke が実行されないこと
  - 型不一致（配列/オブジェクト混入）を fail-closed で拒否すること

#### [F-004] 依存関係がレンジ指定のみで供給網ドリフト耐性が低い
- Severity: Low
- Confidence: High
- Standard refs:
  - OWASP Top 10 2021: A06 (Vulnerable and Outdated Components)
  - NIST SP 800-218 SSDF: PS.3, RV.1
- CWE: CWE-1104
- Evidence:
  - `app/gpt5_agent_strategies/requirements.txt:1` `dify-plugin>=0.6.0,<0.7.0`
  - `app/gpt5_agent_strategies/requirements.txt:2` `pydantic>=2.0.0,<3`
- Impact:
  - 将来更新で予期しない挙動差分や脆弱性流入を検知しにくい
- Remediation (minimum viable fix):
  1. lock file または tighter pin を導入
  2. `pip-audit` をCIへ統合し、CVE triage を定常化
- Verification steps:
  - 依存バージョンが再現可能に固定されること
  - 定期監査で High/Critical CVE の未対応が残らないこと

### 3) Positive Controls Observed
- `app/gpt5_agent_strategies/internal/tooling.py:20` 非文字列引数を拒否する fail-closed 実装
- `tests/gpt5_agent_strategies/test_strategy_safety.py:39` 非文字列引数拒否の回帰テストが存在
- `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:1300` `/files` 配下境界チェックで path traversal を防御
- `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:1170` traversal 拒否テストが存在
- `app/gpt5_agent_strategies/strategies/gpt5_function_calling.py:1325` ローカルファイルサイズ上限（5MB）
- `tests/gpt5_agent_strategies/test_strategy_invoke_paths.py:1250` 画像失敗時に内部パス露出しないことを確認

### 4) Residual Risks
- `bandit` / `pip-audit` が環境未導入で static/dependency scan 証跡が未取得
- 運用環境のログ保持期間・アクセス制御（RBAC）未確認のため、F-001の実運用リスクは環境設定依存

### 5) Recommended Next Actions
1. F-001対応: ログサニタイズ + 本文非記録（既定）を最優先で実装
2. F-002対応: `emit_intermediate_thoughts` 既定を `false` に変更
3. F-003対応: strict schema + unknown key reject を導入
4. F-004対応: 依存固定戦略と `pip-audit` CI導入

## Verification
- Executed checks:
  - `bandit -r app/gpt5_agent_strategies` -> `command not found`
  - `pip-audit -r app/gpt5_agent_strategies/requirements.txt` -> `command not found`
  - `uv run pytest -q --no-cov tests/gpt5_agent_strategies/test_strategy_safety.py tests/gpt5_agent_strategies/test_strategy_invoke_paths.py` -> `36 passed`
- Gate rule: Critical または High が1件以上で FAIL
- Determination:
  - `F-001`: High
  - `F-002`: Medium
  - `F-003`: Medium
  - `F-004`: Low
  - => **FAIL**
