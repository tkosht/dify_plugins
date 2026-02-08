# GPT-5 系 Dify Plugins 詳細設計

## 1. 目的
本設計は、Dify で GPT-5 系モデルを安定利用するための 2 プラグイン構成を定義する。

- Plugin A: `openai_gpt5_responses`（Model Provider）
- Plugin B: `gpt5_agent_strategies`（Agent Strategies）

要件上の最優先事項:
- GPT-5 系を LLM から利用可能にする
- `gpt-5.2-pro` を必須対応
- Codex 系（`gpt-5-codex`, `gpt-5.1-codex`, `gpt-5.3-codex`）を選択可能にする
- Agent Strategy を GPT-5 系向けに最適化する
- UI で指定するパラメータ名は OpenAI API 名を維持する

## 2. 構成方針
### 2.1 分離方針（2プラグイン）
- モデル API 追随（価格/パラメータ/モデル ID 変更）と Agent 行動最適化を分離する。
- 片側の変更が他方を巻き込まないようにする。

### 2.2 配置
- `app/openai_gpt5_responses/`
- `app/gpt5_agent_strategies/`

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
    payloads.py
    messages.py
    errors.py
```

### 3.2 Manifest 要件
- `type: plugin`
- `plugins.models: ["provider/openai_gpt5.yaml"]`
- `meta.runner.language: python`, `version: "3.12"`, `entrypoint: main`
- `meta.minimum_dify_version: 1.10.0`

### 3.3 Provider 設定 UI（provider_credential_schema）
| variable | type | required | default | 備考 |
|---|---|---:|---|---|
| `openai_api_key` | `secret-input` | yes | - | API Key |
| `openai_organization` | `text-input` | no | - | Organization ID |
| `openai_api_base` | `text-input` | no | `""` | 空なら OpenAI 既定 endpoint、指定時は末尾 `/v1` を内部正規化 |
| `request_timeout_seconds` | `text-input` | no | `300` | 30-900 推奨 |
| `max_retries` | `text-input` | no | `1` | 0-5 推奨 |

### 3.4 LLM UI パラメータ（API 名そのまま）
以下は `models/llm/*.yaml` の `parameter_rules` として露出する。

| name | type | default | min | max | 備考 |
|---|---|---:|---:|---:|---|
| `max_output_tokens` | number | 8192 | 1 | 128000 | OpenAI Responses API へそのまま渡す |
| `reasoning_effort` | string | medium | - | - | `none/minimal/low/medium/high/xhigh` |
| `verbosity` | string | medium | - | - | `low/medium/high` |
| `response_format` | string | text | - | - | `text/json_schema` |
| `json_schema` | text | - | - | - | `response_format=json_schema` のとき必須 |
| `tool_choice` | string | auto | - | - | `auto/none/required` + 文字列許容 |
| `parallel_tool_calls` | boolean | true | - | - | 並列ツール呼び出し |
| `enable_stream` | boolean | true | - | - | ストリーミング実行 |

### 3.5 モデルポリシー
- predefined モデルに下記を含める。
  - `gpt-5.2`, `gpt-5.2-pro`（必須）
  - `gpt-5`, `gpt-5-mini`, `gpt-5-nano`
  - `gpt-5-codex`, `gpt-5.1-codex`, `gpt-5.3-codex`
- `vision` feature は本実装では未対応のため公開しない（入力は text ベース）。
- `customizable-model` 有効化。
- モデル可用性は事前遮断しない。実行時 API エラーで検知する。

### 3.6 実装方針
- 呼び出し基盤: `OpenAI().responses.create(...)`
- 変換方針:
  - UI パラメータ名を OpenAI API 名に揃えるため、余計なエイリアスを持たない。
  - `response_format=json_schema` の場合は `text.format` を構築。
  - tool definitions は Responses API の関数ツール形式に変換。
- エラー方針:
  - model not found / auth / bad request をユーザー可読メッセージへ整形。

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
  prompt/
    template.py
  internal/
    __init__.py
    policy.py
    loop.py
```

### 4.2 Manifest 要件
- `plugins.agent_strategies: ["provider/gpt5_agent.yaml"]`
- `minimum_dify_version: 1.10.0`

### 4.3 Strategy パラメータ
| name | type | required | default | 備考 |
|---|---|---:|---:|---|
| `model` | model-selector | yes | - | scope: `tool-call&llm` |
| `tools` | array[tools] | yes | - | 呼び出し可能ツール |
| `instruction` | string | yes | - | prompt_instruction 対応 |
| `query` | string | yes | - | ユーザ入力 |
| `maximum_iterations` | number | yes | 6 | 1-30 |
| `context` | any | no | - | 任意コンテキスト |

### 4.4 Prompt Policy
- GPT-5 ガイドに基づく以下の方針をテンプレート化:
  - persistence
  - context_gathering
  - uncertainty handling
  - concise tool preamble
- 反復停止条件:
  - FinalAnswer 生成
  - tool call 不要
  - `maximum_iterations` 到達

## 5. API マッピング（Plugin A）

| Dify UI | OpenAI Responses API |
|---|---|
| `max_output_tokens` | `max_output_tokens` |
| `reasoning_effort` | `reasoning.effort` |
| `verbosity` | `text.verbosity` |
| `response_format` + `json_schema` | `text.format` |
| `tool_choice` | `tool_choice` |
| `parallel_tool_calls` | `parallel_tool_calls` |
| `enable_stream` | `stream` |

補足（メッセージ変換）:
- `assistant` の `tool_calls` は `function_call` 入力として保持する。
- `tool` ロールは `function_call_output` と `tool_call_id` を保持して入力へ渡す。
- `tool` の `content` が空文字でも `function_call_output` を保持し、呼び出し事実を文脈に残す。
- `assistant` テキストは `output_text` として保持する。

## 6. エラー仕様

### 6.1 入力検証エラー
- `json_schema` が JSON として不正
- `response_format=json_schema` だが `json_schema` 未指定
- bool パラメータが boolean-like でない
  - 対象: `enable_stream`, `parallel_tool_calls`, `json_schema.strict`
  - 許容: `true/false`, `1/0`, `True/False`, `1/0`(int)

### 6.2 実行時エラー（外部 API）
- model not found
- permission denied
- rate limit
- timeout

### 6.3 Agent 実行エラー方針
- tool arguments が不正 JSON の場合は fail-closed とし、tool invoke を行わない。
- tool arguments が非str（`dict/bytes/None` など）の場合も fail-closed とし、tool invoke を行わない。
- 解析エラーを `tool_response` に明示して次の推論へ返す。
- stream 時は tool call が存在するラウンドで中間テキストを先出ししない。
- stream chunk で `delta.message is None` の場合は tool call 抽出をスキップして継続する。
- blocking 応答で `result.message is None` の場合は content 参照を行わず継続する。
- image/blob の tool invoke 応答は `_to_agent_invoke_message()` 経由で Agent メッセージへ正規化する。
- 画像ファイル読込は `realpath` で `/files` 配下のみ許可し、逸脱パス（`..` 含む）を拒否する。
- ローカル画像読込はサイズ上限（5MB）を適用し、超過時は読み込みを中断する。
- 画像変換失敗時のユーザー向け文言は固定化し、内部例外詳細はログへ記録する。
- tool invoke 失敗時もユーザー向け文言は固定化し、内部例外詳細はログへ記録する。

返却原則:
- 原因カテゴリを維持して、簡潔な日本語メッセージを返す。

## 7. TDD 実施計画

### 7.1 Red（先にテスト）
- Plugin A
  - provider schema が必要項目を公開
  - API 名パラメータ露出
  - payload 変換が仕様どおり
- Plugin B
  - strategy schema が必要項目を公開
  - ループ停止条件
  - prompt policy 適用

### 7.2 Green（最小実装）
- テストを満たす最小コードのみ実装

### 7.3 Refactor
- 重複排除、命名・責務整形

## 8. テスト観点

### 8.1 単体
- payload 変換
- schema 検証
- iteration ガード

### 8.2 結合
- `gpt-5.2-pro` 呼び出し
- Codex 系モデル呼び出し（可用時）
- 未提供モデルで実行時エラー整形

### 8.3 パッケージ
- `.difypkg` 生成

## 9. 運用
- remote debug の `.env` を整備
- README に導入手順と既知制約を明記

## 10. 既定値
- `reasoning_effort=medium`
- `verbosity=medium`
- `max_output_tokens=8192`
- `parallel_tool_calls=true`
- `enable_stream=true`

## 11. 既知制約
- `gpt-5.3-codex` は環境により利用不可の可能性がある。
- その場合は UI 選択可能のまま、実行時エラーで検知する。
