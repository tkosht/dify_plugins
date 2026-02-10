# Repo Source Map

## Core implementation sources
- `app/sharepoint_list/**`: OAuth付きTool plugin実装、tool YAML/実装、filter・validatorの実装例。
- `app/openai_gpt5_responses/**`: provider + llm model catalog + payload/message整形の実装例。
- `app/gpt5_agent_strategies/**`: strategy plugin設計、安全ガード、tool invoke保護の実装例。
- `app/nanobana/**`: tool pluginの最小構成とガイド付き実装例。
- baseline比較時は同種pluginを1つ決め、差分確認の基準とする。
  - 例: OpenAI Responses provider の新規作成時は `app/openai_gpt5_responses/**` をbaselineにする。

## Test sources
- `tests/sharepoint_list/**`: SharePoint pluginのバリデーション、リクエスト、操作系の回帰例。
- `tests/openai_gpt5_responses/**`: provider/runtime/payload/messages の回帰例。
- `tests/gpt5_agent_strategies/**`: flow/policy/strategy invoke/safety の回帰例。

## Historical decision sources
- `memory-bank/07-external-research/dify_plugin_development_research_2025-12-12.md`
  - CLI、manifest、remote debug、package/install、OAuth、互換性の一次情報サマリ。
- `memory-bank/07-external-research/dify_plugin_development_troubleshooting_2025-12-12.md`
  - `plugin_unique_identifier`, `bad signature`, remote debug不達、package失敗の切り分け手順。
- `memory-bank/06-project/gpt5_dify_plugins/gpt5_plugins_review_2026-02-08*.md`
  - GPT5系プラグインの複数ラウンド再レビュー結果、検証コマンド、残リスク。
- `memory-bank/06-project/sharepoint_list_dify_doc_review_2025-12-26.md`
  - ドキュメントと実装差分の整合化履歴。
- `memory-bank/06-project/openai_responses_provider_subagent_evaluation_2026-02-10.md`
  - サブエージェント生成結果の完成度評価と不足点（package失敗、配布補助ファイル欠落、テスト深度不足）。
- `docs/03.detail_design/dify_plugin_development_guide.md`
  - ローカル最短フローの運用手順。

## Usage rule
1. 実装判断は `app/*` と `tests/*` を主根拠とする。
2. 手順・落とし穴は `memory-bank` を補助根拠として使う。
3. 根拠のない推測は採用しない。
