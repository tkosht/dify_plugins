# GPT5 Agent Strategies アーキテクチャ詳細（実装準拠）

## 1. 全体構成

`gpt5_agent_strategies` は Dify の Agent Strategy Provider プラグインで、以下で構成される。

- エントリポイント: `main.py`
- Manifest: `manifest.yaml`
- Provider:
  - `provider/gpt5_agent.yaml`
  - `provider/gpt5_agent.py`
- Strategy:
  - `strategies/gpt5_function_calling.py`
  - `strategies/gpt5_react.py`（function-calling 実装を継承）
- 内部モジュール:
  - `internal/flow.py`（ラウンド構築・text 出力判定・tool call 抽出）
  - `internal/tooling.py`（tool arguments parse / tool 解決）
  - `internal/policy.py`（system instruction 合成）
  - `internal/loop.py`（反復条件ヘルパー）
- Prompt テンプレート:
  - `prompt/template.py`

## 2. 入出力契約

### 2.1 Dify -> Strategy 入力

主要入力:

- `query`
- `instruction`
- `prompt_policy_overrides`
- `model` (`AgentModelConfig`)
- `tools` (`ToolEntity[]`)
- `maximum_iterations`
- `emit_intermediate_thoughts`
- `context`

### 2.2 Strategy -> Dify 出力

`AgentStrategy` の message API で逐次返却する。

- `create_text_message`
- `create_log_message` / `finish_log_message`
- `create_retriever_resource_message`
- `create_json_message`（`execution_metadata`）

## 3. 実行フロー

`GPT5FunctionCallingStrategy._invoke()` の実装フロー:

1. `GPT5FunctionCallingParams` を構築
2. system/history/user を連結して round prompt を作成
3. `session.model.llm.invoke(...)` を実行
4. stream/blocking の両経路で tool call を抽出
5. tool 実行結果を `ToolPromptMessage` として次 round へ反映
6. `tool_calls` が無くなるか `maximum_iterations` 到達で停止
7. `execution_metadata` を JSON で返却

補足:

- `gpt5_react` は function-calling 基盤をそのまま使う（別実装分岐なし）。

## 4. Prompt Policy 合成

`build_system_instruction()` は次を順に結合する。

1. `instruction`
2. `persistence_policy`
3. `context_gathering_policy`
4. `uncertainty_policy`
5. `tool_preamble_policy`
6. `extra_policy`

`prompt_policy_overrides` の仕様:

- 空文字: 上書きなし
- プレーンテキスト: `extra_policy` として末尾追記
- JSON object:
  - 有効キー:
    - `persistence_policy`
    - `context_gathering_policy`
    - `uncertainty_policy`
    - `tool_preamble_policy`
    - `extra_policy`
  - 未知キーは無視
  - 上 4 キーはタグ省略時に自動ラップ

## 5. stream 表示制御

`emit_intermediate_thoughts` により表示方針を切り替える。

- `true`:
  - 中間 `<think>` を表示
  - tool call がある round でも thought block を表示可能
- `false`:
  - `<think>...</think>` をユーザー表示から除去
  - tool call がある round では中間表示を抑制
  - 最終表示時はユーザー向け可視テキストのみ返す

`should_emit_response_text(...)` は以下を判定する:

- tool call なし: 常に表示
- tool call あり + `emit_intermediate_thoughts=true`: 表示
- tool call あり + `emit_intermediate_thoughts=false`: 最終 iteration のみ表示

## 6. tool invoke 安全設計

### 6.1 引数パース

`parse_tool_arguments` の契約:

- `""` -> `{}`
- JSON object 文字列 -> parse 成功
- 非文字列 / 不正 JSON / 非 object -> parse error

parse error 時は fail-closed:

- tool 呼び出しせず error message を `tool_response` に格納

### 6.2 tool 実行時ガード

- tool 不在:
  - `there is not a tool named ...`
- option 不一致:
  - parameter option validation error
- 実行例外:
  - `tool invoke error: failed to execute tool`
- 同一 signature 再失敗:
  - 再実行をスキップし重複失敗メッセージを返す

## 7. ファイル/画像メッセージ処理

画像/ファイル応答の local file 読み込み制約:

- `/files` 配下のみ許可（`realpath` 検証）
- `..` など root 逸脱パスは拒否
- 5MB 超過ファイルは拒否

IMAGE / IMAGE_LINK / BLOB 応答は `AgentInvokeMessage` として返却し、UI 側表示互換を維持する。

## 8. 運用上の要点

- `instruction` はタスク依存指示に利用する。
- 組織ポリシー切替は `prompt_policy_overrides` を利用する。
- `context_gathering_policy`（system prompt 方針）と `context`（実行時データ）は別概念として扱う。
