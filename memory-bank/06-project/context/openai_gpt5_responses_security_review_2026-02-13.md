# OpenAI GPT-5 Responses Security Review Record (2026-02-13, standard)

## Metadata
- recorded_at: 2026-02-13T22:39:57+09:00
- reviewer: Codex (GPT-5)
- target: `app/openai_gpt5_responses`
- review_profile: standard
- gate_result: PASS
- gate_reason: Critical/High findings not identified
- supersedes: `memory-bank/06-project/context/openai_gpt5_responses_security_review_2026-02-12.md`
- tags: security-review, app-security-review, openai-gpt5-responses, owasp-api, cwe, handoff

## Problem
- `app/openai_gpt5_responses` の最新実装を `app-security-review` プロトコルで再監査し、開発元AIエージェントへ連携可能な決裁資料を作成する。

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
- Trust-boundary map (manual):
  - Credentials path: `provider/openai_gpt5.py`, `models/llm/llm.py`
  - Outbound destination controls: `internal/credentials.py`
  - Outbound API calls: `OpenAI(...)`, `models.list()`, `responses.create()`
  - Logging path: `models/llm/llm.py` (`OPENAI_GPT5_AUDIT_LOG`)
- Executed checks:
  - `bandit`: `uvx --from bandit bandit -r app/openai_gpt5_responses` -> `No issues identified.`
  - `pip-audit`: `uvx --from pip-audit pip-audit -r app/openai_gpt5_responses/requirements.txt` -> `No known vulnerabilities found`
  - `security_tests`: `uv run pytest -q --no-cov tests/openai_gpt5_responses` -> `87 passed`

## Solution
## 1. Summary
- Target: `app/openai_gpt5_responses`
- Review profile: `standard`
- Review date: `2026-02-13`
- Reviewer: `Codex (GPT-5)`
- Gate result: `PASS`
- Gate reason: `Critical/High finding なし`

## 2. Scope and Method
- In-scope files:
  - `app/openai_gpt5_responses/internal/credentials.py`
  - `app/openai_gpt5_responses/provider/openai_gpt5.py`
  - `app/openai_gpt5_responses/models/llm/llm.py`
  - `app/openai_gpt5_responses/requirements.txt`
  - `tests/openai_gpt5_responses/test_provider_schema.py`
  - `tests/openai_gpt5_responses/test_provider_runtime.py`
  - `tests/openai_gpt5_responses/test_llm_stream_flag.py`
- Out-of-scope or unavailable artifacts:
  - 本番IAM/RBAC設定（credential編集権限の環境実態）
- Executed checks:
  - `manual_matrix`: `done`
  - `bandit`: `done`
  - `pip-audit`: `done`

## 3. Findings
- No findings.

## 4. Positive Controls Observed
- `openai_api_base` に `https` 強制・資格情報禁止・allowlist 制御・`/v1` パス制約:
  - `app/openai_gpt5_responses/internal/credentials.py:58`
  - `app/openai_gpt5_responses/internal/credentials.py:62`
  - `app/openai_gpt5_responses/internal/credentials.py:67`
  - `app/openai_gpt5_responses/internal/credentials.py:77`
- ローカル/プライベート/リンクローカル系宛先の拒否:
  - `app/openai_gpt5_responses/internal/credentials.py:29`
  - `app/openai_gpt5_responses/internal/credentials.py:40`
- 上記制約の回帰テスト:
  - `tests/openai_gpt5_responses/test_provider_schema.py:155`
  - `tests/openai_gpt5_responses/test_provider_schema.py:160`
  - `tests/openai_gpt5_responses/test_provider_schema.py:179`
  - `tests/openai_gpt5_responses/test_provider_runtime.py:161`
  - `tests/openai_gpt5_responses/test_llm_stream_flag.py:625`
- 例外サニタイズ（予期しない詳細を返さない）:
  - `app/openai_gpt5_responses/provider/openai_gpt5.py:16`
  - `app/openai_gpt5_responses/models/llm/llm.py:63`
  - `tests/openai_gpt5_responses/test_llm_stream_flag.py:641`
- 監査ログの秘密情報非露出テスト:
  - `tests/openai_gpt5_responses/test_llm_stream_flag.py:705`
  - `tests/openai_gpt5_responses/test_llm_stream_flag.py:762`
- 依存関係が固定バージョン化済み:
  - `app/openai_gpt5_responses/requirements.txt:1`
  - `app/openai_gpt5_responses/requirements.txt:2`
  - `app/openai_gpt5_responses/requirements.txt:3`

## 5. Residual Risks
- `OPENAI_GPT5_ALLOWED_BASE_URL_HOSTS` の運用値を過剰に広げた場合、外部送信先のリスク境界が広がる。

## 6. Recommended Next Actions
1. CIで `bandit` / `pip-audit` / `tests/openai_gpt5_responses` を定期ゲートとして固定する。
2. `OPENAI_GPT5_ALLOWED_BASE_URL_HOSTS` の変更管理（レビュー・監査ログ）を運用ルール化する。
3. セキュリティレビューをリリース前チェックリストに組み込み、同テンプレートで継続記録する。

## Verification
- Gate rule: Critical または High が1件以上で FAIL。
- This run:
  - findings count = `0`
  - bandit = `No issues identified`
  - pip-audit = `No known vulnerabilities found`
  - pytest = `87 passed`
- Decision: **PASS with recommendations**
