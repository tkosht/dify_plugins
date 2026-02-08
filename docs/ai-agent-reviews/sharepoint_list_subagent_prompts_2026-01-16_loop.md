# sharepoint_list consistency loop subagent prompts (2026-01-16)

## Executor
- 役割: Executor（証拠収集・修正・再検証の実行）
- 目的: 整合性評価と改善ループを回して最終整合を達成
- 対象: app/sharepoint_list/**, docs/03.detail_design/sharepoint_list_list_items_filters.md, tests/sharepoint_list/**
- 書き込み範囲: app/sharepoint_list/**, docs/**, tests/sharepoint_list/**（明示スコープ内のみ）
- 制約: 推測禁止。証拠を /facts に記録。破壊的コマンド禁止。
- 記録先: /facts と /revise

## Reviewer
- 役割: Reviewer（独立レビュー）
- 実行: 読み取りのみ
- 書き込み範囲: docs/ai-agent-reviews/ のみ
- 記録先: /critique
- 要求: 不整合/リスク/不足テストを根拠付きで列挙（severity 明記）

## Verifier
- 役割: Verifier（再検証とループ判定）
- 実行: verify ステージで成功条件を再確認
- 書き込み範囲: 原則なし（必要時のみ /facts 追記）
- 記録先: /facts
- 要求: ループ条件に該当する場合 next_stages を追加し再実行を指示

## Timeout / Loop Policy
- 再実行は最大 2 回まで
- ループ上限超過時は手動介入を /open_questions に記録
