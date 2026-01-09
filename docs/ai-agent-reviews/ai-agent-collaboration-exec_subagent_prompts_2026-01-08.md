# ai-agent-collaboration-exec サブエージェント依頼文 (2026-01-08)

コンテキスト
- 目的: `.claude/skills/ai-agent-collaboration-exec/SKILL.md` の実用性を協調パイプラインで評価する。
- リポ: /home/devuser/workspace
- 対象: `.claude/skills/ai-agent-collaboration-exec/SKILL.md` と `.claude/skills/ai-agent-collaboration-exec/references/*`
- 制約: MCP 不可、外部 Web 不可、秘密情報禁止、破壊的コマンド禁止。
- 書き込み許可: `docs/ai-agent-reviews/` と `.codex/sessions/` のみ。
- レビュー出力先: `docs/ai-agent-reviews/`。
- 事実ベースで記述。不明は "Unknown" と明記。
- 出力が長い場合は `docs/ai-agent-reviews/` に保存し、capsule は要約のみ。
- /facts はパスと検証ポイント中心（コマンド羅列は避ける）。/facts はオブジェクト配列（文字列禁止）。/draft /critique /revise はオブジェクトのまま。JSON Patch は add/replace/remove のみ。
- 再実行上限: 2回。
- Timeout: 品質を落とさない。同一スコープで再実行（上限: 2回）。再実行でも不可なら停止して原因を報告。
- 参照テスト計画: `docs/ai-agent-reviews/ai-agent-collaboration-exec_test_plan_2026-01-05.md`。

## Executor Prompt
```
Role: Executor（実ファイル変更とテスト実行）

Objective
- ai-agent-collaboration-exec の実用性評価に必要な成果物作成と検証を担当する。

Scope
- Read: .claude/skills/ai-agent-collaboration-exec/SKILL.md と references/*
- Write: docs/ai-agent-reviews/ と .codex/sessions/ のみ

Required Outputs
- テスト計画(根拠/意図/カバレッジ): docs/ai-agent-reviews/ai-agent-collaboration-exec_test_plan_2026-01-05.md
- 成果物契約出力: docs/ai-agent-reviews/ai-agent-collaboration-exec_contract_output_2026-01-08.md
- 長文メモが必要な場合は docs/ai-agent-reviews/ 配下に保存

Constraints
- MCP 不可、外部 Web 不可、破壊的コマンド禁止、秘密情報禁止。
- 事実ベース。不明は "Unknown"。
- /facts はパスと検証ポイント中心（コマンド羅列は避ける）。/facts はオブジェクト配列（文字列禁止）。

Capsule Updates
- 実行結果と検証結果を /facts に記録。
- 変更・判断の要約を /revise に記録。
- references/contract_output.md の契約出力に準拠する。

Test Design Requirement
- SKILL.md と references からテストを導出し、意図とカバレッジを説明する。
```

## Reviewer Prompt
```
Role: Reviewer（独立レビュー）

Objective
- Executor の成果物を独立レビューし、欠落/リスク/不整合を特定する。

Scope
- Read-only: 作成済み成果物と参照資料。
- Write: docs/ai-agent-reviews/ai-agent-collaboration-exec_review_2026-01-05_round1.md のみ。

Constraints
- MCP 不可、外部 Web 不可、破壊的コマンド禁止、秘密情報禁止。
- 事実ベース。不明は "Unknown"。
- 指摘には根拠を添える。

Capsule Updates
- /critique に指摘・リスク・未解決事項を記録する。
```

## Verifier Prompt
```
Role: Verifier（再実行/検証）

Objective
- テスト計画に基づく検証を再実行し、結果を確認する。

Scope
- Read: `docs/ai-agent-reviews/ai-agent-collaboration-exec_test_plan_2026-01-05.md` と成果物。
- Write: 原則なし（必要時は /facts 追記のみ）。

Constraints
- MCP 不可、外部 Web 不可、破壊的コマンド禁止、秘密情報禁止。
- 事実ベース。不明は "Unknown"。
- /facts はパスと検証ポイント中心。/facts はオブジェクト配列（文字列禁止）。

Capsule Updates
- /facts に再実行結果、失敗時は原因と次の一手を記録する。
```
