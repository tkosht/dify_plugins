# GPT-5 系 Dify Plugins 詳細設計（実装準拠）

## 1. 目的
本書は、以下 2 プラグインの現行実装を正として、公開契約・挙動・テスト観点を定義する。

- Plugin A: `openai_gpt5_responses`（Model Provider）
- Plugin B: `gpt5_agent_strategies`（Agent Strategy Provider）

優先事項:

- GPT-5 系モデルを Dify から安定呼び出しできること
- `gpt-5.2-pro` を含む predefined model を提供すること
- Codex 系モデル（`gpt-5-codex`, `gpt-5.1-codex`, `gpt-5.3-codex`）を選択可能にすること
- Agent Strategy を tool-call 前提で安全に実行できること

## 2. 構成

### 2.1 配置

- `app/openai_gpt5_responses/`
- `app/gpt5_agent_strategies/`

### 2.2 分離方針

- モデル API 追随（model/parameter 変更）と Agent 実行制御を分離する。
- 片側変更時の影響範囲を局所化する。

## 3. Plugin A: openai_gpt5_responses

### 3.1 ディレクトリ構成

```text
app/openai_gpt5_responses/
  manifest.yaml
  main.py
  README.md
  PRIVACY.md
  .env.example
  requirements.txt
  icon.svg
  provider/
    openai_gpt5.yaml
    openai_gpt5.py
  models/
    llm/
      _position.yaml
      llm.py
      gpt-5.2.yaml
      gpt-5.2-pro.yaml
      gpt-5.yaml
      gpt-5-mini.yaml
      gpt-5-nano.yaml
      gpt-5-codex.yaml
      gpt-5.1-codex.yaml
      gpt-5.3-codex.yaml
  internal/
    __init__.py
    credentials.py
    payloads.py
    messages.py
    errors.py
```

### 3.2 Manifest / Provider 契約

- `manifest.yaml`
  - `type: plugin`
  - `plugins.models: ["provider/openai_gpt5.yaml"]`
  - `meta.runner.language: python`
  - `meta.runner.version: "3.12"`
  - `meta.runner.entrypoint: main`
  - `meta.minimum_dify_version: 1.10.0`
- `provider/openai_gpt5.yaml`
  - `supported_model_types: [llm]`
  - `configurate_methods: [predefined-model, customizable-model]`
  - `provider_credential_schema` と `model_credential_schema` を両方提供

### 3.3 認証情報パラメータ

| variable | type | required | default | 実装上の扱い |
|---|---|---:|---|---|
| `openai_api_key` | `secret-input` | yes | - | 必須。欠落時は credential validate 失敗 |
| `openai_organization` | `text-input` | no | - | 前後空白除去して利用 |
| `openai_api_base` | `text-input` | no | `""` | 正規化で末尾 `/v1` を補完 |
| `request_timeout_seconds` | `text-input` | no | `"300"` | int 化して 30〜900 に clamp |
| `max_retries` | `text-input` | no | `"1"` | int 化して 0〜5 に clamp |

### 3.4 Predefined model

- `gpt-5.2`, `gpt-5.2-pro`
- `gpt-5`, `gpt-5-mini`, `gpt-5-nano`
- `gpt-5-codex`, `gpt-5.1-codex`, `gpt-5.3-codex`

補足:

- モデル可用性を事前遮断しない。利用不可は実行時 API エラーで検知する。
- model yaml の `features` には `tool-call`, `multi-tool-call`, `agent-thought`, `stream-tool-call` を含む（`vision` は含まない）。

### 3.5 LLM パラメータ契約（`models/llm/*.yaml`）

| name | type | default | 備考 |
|---|---|---|---|
| `max_output_tokens` | int | `8192` | `1..128000` |
| `reasoning_effort` | string | `medium` | `none/minimal/low/medium/high/xhigh` |
| `reasoning_summary` | string | `auto` | `auto/concise/detailed` |
| `verbosity` | string | `medium` | `low/medium/high` |
| `response_format` | string | `text` | `text/json_schema` |
| `json_schema` | text | - | `response_format=json_schema` 時に必須 |
| `tool_choice` | string | `auto` | `auto/none/required` + 文字列 |
| `parallel_tool_calls` | boolean | `true` | bool-like を厳格変換 |
| `enable_stream` | boolean | `true` | bool-like を厳格変換 |

### 3.6 OpenAI Responses API マッピング

| Dify 側 | Responses API 側 |
|---|---|
| `max_output_tokens` | `max_output_tokens` |
| `reasoning_effort` | `reasoning.effort` |
| `reasoning_summary` | `reasoning.summary` |
| `verbosity` | `text.verbosity` |
| `response_format=json_schema` + `json_schema` | `text.format` (`type=json_schema`) |
| `tool_choice` | `tool_choice` |
| `parallel_tool_calls` | `parallel_tool_calls` |
| `enable_stream` | `stream` |

実装ルール:

- `enable_stream` と `_invoke(..., stream=...)` の AND を `stream` に設定する。
- `stop` が指定された場合は `truncation="disabled"` を付与する。
- `tools` は Responses API の function tool 形式へ変換する。
- `tool name` 欠落時は `ValueError`。

### 3.7 メッセージ変換契約

入力変換（`prompt_messages_to_responses_input`）:

- `assistant`:
  - `content` は文字列化して `{"role":"assistant","content":...}`
  - `tool_calls` は `function_call` 項目として追加
- `tool`:
  - `tool_call_id` を `call_id` とする `function_call_output` に変換
  - `content=""` でも call 事実を保持
- `user/system/developer`:
  - `input_text` 配列形式へ変換

出力変換（`_to_llm_result`）:

- `output_text` 優先でテキスト抽出
- `output` 内 `type=function_call` を tool call として復元
- usage は `input_tokens` / `output_tokens` から集計

### 3.8 検証・エラー方針

- provider credential validate:
  - `OpenAI(...).models.list()` で接続性を確認
- model credential validate:
  - `responses.create` へ軽量 payload（`ping`）を送って確認
- `json_schema` 検証:
  - JSON object 必須
  - `schema` field 必須
- bool-like 検証対象:
  - `enable_stream`
  - `parallel_tool_calls`
  - `json_schema.strict`
- 許容 bool-like:
  - `true/false`
  - `"true"/"false"`
  - `1/0`
  - `"1"/"0"`
- API 例外:
  - `APIStatusError` / `APIConnectionError` / `openai.APIError` を invoke error へ変換

### 3.9 監査ログ

`OPENAI_GPT5_AUDIT_LOG=true` 時のみ出力。event:

- `responses_api_request`
- `responses_api_success`
- `responses_api_error`

出力例項目:

- `model`, `response_model`, `request_id`
- `response_format`, `stream`, `tool_count`, `input_message_count`
- `status_code`, `code`, `param`, `error_type`
- `base_url_host`, `use_custom_base_url`

秘匿対象（出力しない）:

- API key
- Authorization header
- prompt 本文
- schema body / tool argument payload 本文

## 4. Plugin B: gpt5_agent_strategies

### 4.1 ディレクトリ構成

```text
app/gpt5_agent_strategies/
  manifest.yaml
  main.py
  README.md
  PRIVACY.md
  .env.example
  requirements.txt
  icon.svg
  provider/
    gpt5_agent.yaml
    gpt5_agent.py
  strategies/
    gpt5_function_calling.yaml
    gpt5_function_calling.py
    gpt5_react.yaml
    gpt5_react.py
  internal/
    __init__.py
    flow.py
    loop.py
    policy.py
    tooling.py
  prompt/
    template.py
```

### 4.2 Manifest / Provider 契約

- `manifest.yaml`
  - `plugins.agent_strategies: ["provider/gpt5_agent.yaml"]`
  - `meta.minimum_dify_version: 1.10.0`
- `provider/gpt5_agent.yaml`
  - `strategies: [gpt5_function_calling, gpt5_react]`

### 4.3 Strategy パラメータ契約（両 strategy 共通）

| name | type | required | default | 備考 |
|---|---|---:|---|---|
| `model` | model-selector | yes | - | `scope: tool-call&llm` |
| `tools` | array[tools] | yes | - | 呼び出し可能ツール |
| `instruction` | string | yes | - | `prompt_instruction` 由来 |
| `prompt_policy_overrides` | string | no | - | プレーンテキスト/JSON |
| `context` | any | no | - | 実行時コンテキスト |
| `query` | string | yes | - | ユーザー入力 |
| `maximum_iterations` | number | yes | `6` | `1..30` |
| `emit_intermediate_thoughts` | boolean | no | `true` | `<think>` 表示制御 |

### 4.4 Prompt Policy 契約

既定ポリシーは `prompt/template.py` で定義:

- `PERSISTENCE_POLICY`
- `CONTEXT_GATHERING_POLICY`
- `UNCERTAINTY_POLICY`
- `TOOL_PREAMBLE_POLICY`

`build_system_instruction(base_instruction, prompt_policy_overrides)` の挙動:

- `prompt_policy_overrides` が空:
  - 既定 4 ブロック + `instruction` を結合
- プレーンテキスト:
  - `extra_policy` として末尾追記
- JSON object:
  - 対象キーのみ上書き:
    - `persistence_policy`
    - `context_gathering_policy`
    - `uncertainty_policy`
    - `tool_preamble_policy`
    - `extra_policy`
  - 未知キーは無視
  - 上 4 キーはタグ省略時に自動ラップ

### 4.5 実行フロー（`GPT5FunctionCallingStrategy._invoke`）

1. `GPT5FunctionCallingParams` に入力を束ねる
2. round 単位で LLM 呼び出し
3. tool call 抽出
4. tool 実行 or fail-closed 応答作成
5. `ToolPromptMessage` を current thoughts に追加
6. `tool_calls` が無くなるか `maximum_iterations` で停止
7. 終了時に `execution_metadata`（JSON message）を返す

`gpt5_react` は `gpt5_function_calling` を継承し、同じ実行基盤を利用する。

### 4.6 表示制御（stream / intermediate thought）

- `emit_intermediate_thoughts=true`:
  - 中間 `<think>` を表示
  - tool call がある round でも thought を表示可能
- `emit_intermediate_thoughts=false`:
  - `<think>` ブロックをユーザー表示から除去
  - tool call あり round の中間表示を抑制し、最終側のみ表示

補助挙動:

- `<think>` が欠落した場合は fallback thought 文を生成
- `delta.message is None` など欠落 chunk は安全にスキップ

### 4.7 tool invoke 安全方針

- tool arguments:
  - JSON object 文字列のみ許容
  - 空文字は `{}` として扱う
  - 非文字列/不正 JSON/非 object は parse error（fail-closed）
- tool が存在しない:
  - `there is not a tool named ...` を返す
- option 制約:
  - parameter options 不一致時は validation error
- 例外発生:
  - `tool invoke error: failed to execute tool` で固定化
- 重複失敗抑止:
  - 同一 signature の再失敗呼び出しはスキップし、重複失敗メッセージを返す

### 4.8 ファイル/画像出力の扱い

- `/files` 配下のみ local file 読み込み許可（`realpath` + `commonpath` 検証）
- 5MB 上限 (`_MAX_BLOB_FILE_BYTES`) を超えるファイルは拒否
- IMAGE / IMAGE_LINK / BLOB は `AgentInvokeMessage` へ正規化して返却

## 5. テスト・品質ゲート

対象:

- `tests/openai_gpt5_responses`
- `tests/gpt5_agent_strategies`

標準実行:

```bash
cd /home/devuser/workspace
uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies
uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies
```

確認観点:

- provider/schema 定義
- payload/message 変換
- bool coercion / json_schema 検証
- stream 経路・tool call 経路
- prompt policy override 契約
- fail-closed 挙動

## 6. 既定値

- Plugin A:
  - `max_output_tokens=8192`
  - `reasoning_effort=medium`
  - `reasoning_summary=auto`
  - `verbosity=medium`
  - `response_format=text`
  - `parallel_tool_calls=true`
  - `enable_stream=true`
- Plugin B:
  - `maximum_iterations=6`
  - `emit_intermediate_thoughts=true`

## 7. 既知制約

- OpenAI 側のモデル可用性は環境依存で変動する。predefined model は UI で選択可能でも、実行時に unavailable となりうる。
- Plugin A はテキスト中心設計で、vision feature を model yaml に公開していない。
- Plugin B は tool 引数を JSON object 文字列前提で処理するため、非準拠出力は fail-closed となる。
