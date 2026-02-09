# OpenAI GPT-5 Responses Plugin

This plugin provides GPT-5 family models for Dify by using OpenAI Responses API.

## Highlights
- API parameter names are exposed as-is in UI.
- `gpt-5.2` and `gpt-5.2-pro` are included.
- Codex family model IDs can be selected, including `gpt-5.3-codex`.
- Unknown/unavailable models are detected at runtime by API errors.

## Provider Credentials
- `openai_api_key` (required)
- `openai_organization` (optional)
- `openai_api_base` (optional)
- `request_timeout_seconds` (optional)
- `max_retries` (optional)

## Safe Audit Logging
- Set `OPENAI_GPT5_AUDIT_LOG=true` to print audit logs to stdout.
- Audit logs confirm request execution without exposing secrets.

### Logged Fields
- event: `responses_api_request` / `responses_api_success` / `responses_api_error`
- model / response_model
- request_id (if available)
- status_code / code / param (on API errors)
- response_format / stream / tool_count / input_message_count
- base_url_host

### Not Logged
- API key (`openai_api_key`)
- Authorization header
- Prompt content/body
- JSON schema body and tool argument payloads
