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
