# OpenAI GPT-5 Responses プラグイン

このプラグインは、OpenAI Responses API を利用して Dify に GPT-5 ファミリーモデルを提供します。

## 主な特徴
- API パラメータ名を UI にほぼそのまま表示します。
- `gpt-5.2` と `gpt-5.2-pro` を同梱しています。
- `gpt-5.3-codex` を含む Codex 系モデル ID を選択できます。
- 不明または利用不可のモデルは、API エラーとして実行時に検知します。

## プロバイダー認証情報
- `openai_api_key`（必須）
- `openai_organization`（任意）
- `openai_api_base`（任意）
- `request_timeout_seconds`（任意）
- `max_retries`（任意）

## 安全な監査ログ
- `OPENAI_GPT5_AUDIT_LOG=true` を設定すると、監査ログを標準出力へ出力します。
- 監査ログは、シークレットを露出せずにリクエスト実行状況を確認できる情報のみを出力します。

### 出力される項目
- event: `responses_api_request` / `responses_api_success` / `responses_api_error`
- model / response_model
- request_id（利用可能な場合）
- status_code / code / param（API エラー時）
- response_format / stream / tool_count / input_message_count
- base_url_host

### 出力しない項目
- API key（`openai_api_key`）
- Authorization header
- Prompt content/body
- JSON schema body と tool argument payloads
