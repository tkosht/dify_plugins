# GPT-5 Agent Strategies プラグイン

このプラグインは、Dify で GPT-5 系モデル向けの Agent Strategy を提供します。

## 戦略
- `gpt5_function_calling`
- `gpt5_react`

## 設計
- Agent の継続実行ポリシーやコンテキスト収集ポリシーを、共通の prompt policy モジュールで一元管理します。
- モデル選択・ツール選択の契約は、Dify 公式の strategy プラグインと同等の形式を採用しています。

## プロンプトのカスタマイズ
- `instruction`: Dify で生成・設定されるタスク固有の指示文です。
- `prompt_policy_overrides`: 実行時にポリシーを任意で上書きするための入力です。
  - プレーンテキスト: 追加ポリシーブロックとして末尾に追記されます。
  - JSON オブジェクト: 指定したポリシーブロック（`persistence_policy`, `context_gathering_policy`, `uncertainty_policy`, `tool_preamble_policy`, `extra_policy`）を上書きできます。
  - `persistence_policy` / `context_gathering_policy` / `uncertainty_policy` / `tool_preamble_policy` は、タグ記法（`<...>`）を省略しても内部で自動付与されます。
  - `context_gathering_policy` は system prompt の方針ブロックです。strategy の `context`（実行時コンテキストデータ）とは用途が異なります。

## 主要パラメータ（Dify UI の help）
- `context`: 実行時に strategy へ渡す構造化データです。`context_gathering_policy`（system prompt 方針）とは別概念です。
- `emit_intermediate_thoughts`: `true` で中間 `<think>` を表示、`false` で中間思考を非表示にします。
- `maximum_iterations`: 1 ターン内のツール呼び出しループ上限です。小さすぎると探索不足、大きすぎると遅延が増える可能性があります。

## Dify UI での入力例（`prompt_policy_overrides`）
- Strategy パラメータの `prompt_policy_overrides` には `help` と `placeholder` を設定してあります。
- UI でツールチップ/プレースホルダが表示されない環境でも、以下をそのまま貼り付けて編集できます。

### 指定可能キー（JSON）
- `persistence_policy`
- `context_gathering_policy`
- `uncertainty_policy`
- `tool_preamble_policy`
- `extra_policy`

### 例1: プレーンテキスト（末尾追記）
```text
<runtime_policy>
- 回答は箇条書きを優先してください。
</runtime_policy>
```

### 例2: JSON（ブロック上書き）
```json
{
  "persistence_policy": "- タスク完了まで継続します。",
  "context_gathering_policy": "- まず広く確認し、その後に絞り込みます。",
  "uncertainty_policy": "- 前提は明示して進めます。",
  "tool_preamble_policy": "- ツール呼び出し前に <think> を日本語で出力してください。",
  "extra_policy": "- 最終回答は日本語で簡潔に。"
}
```
