# OpenAI GPT-5 Responses Security Review Record (2026-02-12)

## Metadata
- recorded_at: 2026-02-12T14:57:34+09:00
- reviewer: Codex (GPT-5)
- target: `app/openai_gpt5_responses`
- review_profile: standard
- gate_result: FAIL
- gate_reason: `openai_api_base` の無制限受け入れにより High (CWE-918) が存在
- tags: security-review, app-security-review, openai-gpt5-responses, owasp-api, cwe

## Problem
- `app/openai_gpt5_responses` のセキュリティレビュー結果を、開発元AIエージェントへ再利用可能な正本として記録する。
- 目的は、再実装不要でそのまま修正計画へ接続できる「証跡付きの意思決定資料」を残すこと。

## Research
- Scope inventory:
  - `app/openai_gpt5_responses/manifest.yaml`
  - `app/openai_gpt5_responses/provider/openai_gpt5.yaml`
  - `app/openai_gpt5_responses/provider/openai_gpt5.py`
  - `app/openai_gpt5_responses/models/llm/llm.py`
  - `app/openai_gpt5_responses/internal/credentials.py`
  - `app/openai_gpt5_responses/internal/payloads.py`
  - `app/openai_gpt5_responses/requirements.txt`
  - `tests/openai_gpt5_responses/*.py`
- Executed baseline checks:
  - `bandit -r app/openai_gpt5_responses` -> `command not found`
  - `pip-audit -r app/openai_gpt5_responses/requirements.txt` -> `command not found`
- Manual matrix focus:
  - HTTP-002 (SSRF対策)
  - ERR-001 (エラー露出)
  - SECR-002 (秘密情報ログ露出)
  - DEP-001 (依存関係監査実施可否)

## Solution
### 1) Summary
- Target: `app/openai_gpt5_responses`
- Review date: 2026-02-12
- Gate result: **FAIL**
- Gate reason: High finding (F-001) が存在

### 2) Findings
#### [F-001] `openai_api_base` 無制限受け入れによる SSRF/送信先改ざん
- Severity: High
- Confidence: High
- Standard refs:
  - OWASP API Security Top 10 2023: API7 (Server Side Request Forgery)
  - OWASP Top 10 2021: A10 (SSRF)
  - NIST SP 800-53 Rev.5: SC-7
- CWE: CWE-918
- Evidence:
  - `app/openai_gpt5_responses/provider/openai_gpt5.yaml:45` `openai_api_base` が `text-input` 自由入力
  - `app/openai_gpt5_responses/provider/openai_gpt5.yaml:80` provider credential でも同様に自由入力
  - `app/openai_gpt5_responses/internal/credentials.py:4` 正規化は `/v1` 付与のみでホスト検証なし
  - `app/openai_gpt5_responses/provider/openai_gpt5.py:25` 入力値を `normalize_api_base()` 経由で受理
  - `app/openai_gpt5_responses/provider/openai_gpt5.py:39` `kwargs["base_url"]` へ直接設定
  - `app/openai_gpt5_responses/models/llm/llm.py:188` LLM実行経路でも同一処理
  - `app/openai_gpt5_responses/models/llm/llm.py:203` 実リクエストクライアントへ `base_url` を適用
- Impact:
  - credential編集主体が攻撃者/侵害状態の場合、内部ネットワークまたは攻撃者管理ホストへの送信が可能
  - 推論入力、ツール情報、メタデータが許可外宛先へ流出し得る
- Remediation (minimum viable fix):
  1. `openai_api_base` は `https` のみ許可
  2. private/link-local/loopback/metadata endpoint を拒否
  3. 許可ドメイン allowlist (`api.openai.com` + 明示許可先) を実装
  4. provider/model credential validation で同一検証を強制
- Verification steps:
  - `openai_api_base=http://127.0.0.1:8000` を設定して拒否されること
  - `openai_api_base=http://169.254.169.254` を設定して拒否されること
  - `openai_api_base=https://api.openai.com` は許可され `/v1` 正規化後に動作すること

#### [F-002] `str(exc)` 返却による内部情報露出リスク
- Severity: Medium
- Confidence: Medium
- Standard refs:
  - OWASP Top 10 2021: A09 (Security Logging and Monitoring Failures)
  - OWASP API Security Top 10 2023: API8 (Security Misconfiguration)
  - NIST SP 800-53 Rev.5: SI-11
- CWE: CWE-209
- Evidence:
  - `app/openai_gpt5_responses/provider/openai_gpt5.py:66` 予期しない例外を `CredentialsValidateFailedError(str(exc))` で返却
  - `app/openai_gpt5_responses/models/llm/llm.py:239` 同様に `str(exc)` を返却
- Impact:
  - ネットワーク情報や内部実装由来メッセージが利用者面に露出し得る
  - 攻撃者の偵察情報として利用される可能性がある
- Remediation (minimum viable fix):
  1. ユーザー向けには固定メッセージ/コードのみ返却
  2. 詳細例外は監査ログ側へ限定し、UIには非公開
  3. 例外種別ごとの安全メッセージマッピングを導入
- Verification steps:
  - 接続失敗時に UI へ内部ホスト名や詳細エラー文字列が出ないこと
  - 監査ログにはトラブルシュートに必要な情報のみ残ること

### 3) Positive Controls Observed
- Timeout/Retry のクランプ実装:
  - `app/openai_gpt5_responses/provider/openai_gpt5.py:26`
  - `app/openai_gpt5_responses/models/llm/llm.py:192`
- 監査ログ出力の安全性テストが存在し、APIキー/プロンプト非露出を検証:
  - `tests/openai_gpt5_responses/test_llm_stream_flag.py:668`
  - `tests/openai_gpt5_responses/test_llm_stream_flag.py:724`
- bool-like パラメータ強制変換と不正値拒否:
  - `app/openai_gpt5_responses/internal/payloads.py:20`
  - `app/openai_gpt5_responses/internal/payloads.py:169`

### 4) Residual Risks
- `bandit` / `pip-audit` が環境未導入で dependency/static scan は未実施。
- 実運用RBAC（誰が credential を編集可能か）未確認のため、F-001 の実攻撃可能性は運用設定依存。

### 5) Recommended Next Actions
1. `openai_api_base` の宛先検証実装（https限定、private/meta拒否、allowlist）
2. `str(exc)` 返却の廃止と安全なエラーマッピング導入
3. CI に `bandit` / `pip-audit` を導入し、定期監査を自動化
4. SSRF拒否ケースの回帰テストを `tests/openai_gpt5_responses` に追加

## Verification
- Gate rule: Critical または High が1件以上で FAIL
- 判定:
  - F-001 = High
  - F-002 = Medium
  - => **FAIL**
- Decision integrity:
  - 全主張に `path:line` 証跡を付与
  - 推測ベース記述なし
  - 開発元AIエージェントへの連携可能状態
