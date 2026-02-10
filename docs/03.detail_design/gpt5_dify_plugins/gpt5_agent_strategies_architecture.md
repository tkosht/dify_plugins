# GPT5 Agent Strategies アーキテクチャ詳細

## 1. 全体構成

`gpt5_agent_strategies` は Dify の Agent Strategy Provider プラグインで、主に次の層で構成される。

- エントリポイント: `main.py`
- Plugin マニフェスト: `manifest.yaml`
- Provider 定義: `provider/gpt5_agent.yaml`, `provider/gpt5_agent.py`
- Strategy 実装:
  - `strategies/gpt5_function_calling.py`
  - `strategies/gpt5_react.py`（function_calling 実装を継承）
- Prompt ポリシー:
  - `internal/policy.py`
  - `prompt/template.py`

## 2. Dify 本体とのやり取り

### 2.1 Dify -> Strategy 入力

Strategy 実行時に Dify から主に以下が渡る。

- `query`: ユーザー入力
- `instruction`: Dify 側で作成される指示文（`prompt_instruction`）
- `prompt_policy_overrides`: 任意のポリシー上書き文字列（本プラグイン拡張）
- `model`: `AgentModelConfig`
- `tools`: `ToolEntity[]`
- `maximum_iterations`
- `emit_intermediate_thoughts`
- `context`

### 2.2 Strategy -> Dify 出力

Strategy は `AgentStrategy` の message API を使って Dify へ逐次返却する。

- `create_text_message`: ユーザー向けテキスト / `<think>` 表示
- `create_log_message` + `finish_log_message`: ラウンド/モデル/ツール実行ログ
- `create_retriever_resource_message`: context 由来の参照情報
- `create_json_message`: 実行メタデータ（usage など）

## 3. Agent 制御フロー

`GPT5FunctionCallingStrategy._invoke()` はラウンド反復で制御される。

1. prompt 構築（system/history/user）
2. `self.session.model.llm.invoke(...)`
3. LLM出力から tool call を抽出
4. 必要時 `self.session.tool.invoke(...)`
5. tool 結果を `ToolPromptMessage` として次ラウンドへ連結
6. `maximum_iterations` に達するか tool call がなくなるまで継続

ストリーミング時は以下を保証する。

- tool call なし: chunk を逐次 `text` 送信
- tool call あり: `<think>` 形式で中間思考を送信
- 遅延 tool call でも `<think>` 重複送信を抑止

## 4. プロンプトの実体（現行）

System prompt は `build_system_instruction()` で合成される。

1. `instruction`（Dify からの可変入力）
2. `PERSISTENCE_POLICY`
3. `CONTEXT_GATHERING_POLICY`
4. `UNCERTAINTY_POLICY`
5. `TOOL_PREAMBLE_POLICY`
6. `extra_policy`（override 指定時のみ）

ポリシー原文は `prompt/template.py` に集約される。

## 5. プロンプト可変化の仕様

`prompt_policy_overrides` は 2 形式を受け付ける。

### 5.0 Dify UI での編集導線

- `gpt5_function_calling` / `gpt5_react` の strategy パラメータに `help` と `placeholder` を設定済み。
- Dify UI がツールチップやプレースホルダを表示しない場合は、`app/gpt5_agent_strategies/README.md` の入力例を参照して貼り付け編集する。
- `context_gathering_policy` は system prompt 内の方針ブロックであり、strategy パラメータ `context`（実行時コンテキスト）とは別概念。

### 5.1 生テキスト形式（追記）

JSON でない文字列は `extra_policy` として末尾へ追記する。

例:

```text
<runtime_policy>
- Use bullet points for final answers.
</runtime_policy>
```

### 5.2 JSON 形式（ブロック置換 + 追記）

以下キーを部分指定で上書きできる。

- `persistence_policy`
- `context_gathering_policy`
- `uncertainty_policy`
- `tool_preamble_policy`
- `extra_policy`

上記以外のキーは無視される。

`persistence_policy` / `context_gathering_policy` / `uncertainty_policy` / `tool_preamble_policy`
は、タグ（`<...>`）を省略しても内部で自動付与される。

例:

```json
{
  "persistence_policy": "- Continue until task completion.",
  "context_gathering_policy": "- Search broadly, then narrow quickly.",
  "uncertainty_policy": "- State assumptions explicitly.",
  "tool_preamble_policy": "- Before tools, emit <think> in Japanese.",
  "extra_policy": "- Prefer official sources first."
}
```

## 6. 互換性ポリシー

- `prompt_policy_overrides` 未指定時は完全に従来互換。
- 既存パラメータ（`instruction`, `maximum_iterations`, `emit_intermediate_thoughts`）は非破壊。
- `gpt5_react` は `gpt5_function_calling` を継承するため、同一仕様で利用可能。

## 7. 既知の運用指針

- `instruction` はタスク文脈の可変領域として使う。
- 組織共通ポリシーを動的に切替える場合は `prompt_policy_overrides` を使う。
- 既存 UI 互換を維持したい場合は override を空のままにする。
