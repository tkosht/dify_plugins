# sharepoint_list consistency check subagent prompts (2026-01-13)

## Executor
- 役割: Executor（評価作業の実行）
- 目的: app/sharepoint_list のドキュメント・コード・テストの整合性を事実ベースで評価する
- 対象: app/sharepoint_list/**, docs/03.detail_design/sharepoint_list_list_items_filters.md, tests/sharepoint_list/**
- 書き込み範囲: docs/ai-agent-reviews/ のみ（コード変更は禁止）
- 制約: ツール実行禁止、FACTS INPUT のみ使用、推測禁止、不明は不明
- 記録先: /facts と /revise
- 成果物契約出力: references/contract_output.md に従う

## Reviewer
- 役割: Reviewer（独立レビュー）
- 実行: 読み取りのみ
- 書き込み範囲: docs/ai-agent-reviews/ のみ
- 記録先: /critique
- 要求: 不整合・リスク・未解決事項を根拠付きで列挙（パイプライン設計適合性も確認）

## Verifier
- 役割: Verifier（検証）
- 実行: 追加テストは実施しない（本タスクは整合性レビューのみ）
- 書き込み範囲: 原則なし（必要時のみ /facts 追記）
- 記録先: /facts
- 要求: 追加検証の要否を明記。必要時は理由と次の一手を示す

## Timeout Policy
- タスク難易度や要求水準を下げない
- timeout が発生したら同一スコープで再実行（最大2回まで）
- 再実行でも進められない場合はタスクを停止し設計の見直しに移行
