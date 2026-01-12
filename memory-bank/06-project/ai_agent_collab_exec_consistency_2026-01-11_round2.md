# ai-agent-collaboration-exec 整合チェック (2026-01-11 Round2)

## Problem
- pipeline_spec_template.json の精緻化後、関連ドキュメント/スキーマ/テストとの整合性を確認する必要があった。

## Research
- codex-subagent pipeline で整合チェックを実施。
  - pipeline_run_id: 8fb3dd56-d64a-472e-abb1-59cdc2cc1aa3
  - log: .codex/sessions/codex_exec/auto/2026/01/11/run-20260111T143019-b1aba0f6.jsonl
- 指摘事項（事実）:
  - テンプレ内で allowed_stage_ids / stages の固定を指示しており、SKILL.md / execution_framework.md の「必要ステージのみ残す」方針と矛盾。
  - /open_questions の記録形式に object を示唆していたが、capsule.schema.json は string 配列を要求。

## Solution
- pipeline_spec_template.json の draft instructions を修正:
  - allowed_stage_ids は採用ステージに合わせる/未使用なら削除に変更。
  - /open_questions は文字列配列で 1 件 1 行の記録に変更。

## Verification
- 手動確認: .claude/skills/ai-agent-collaboration-exec/references/pipeline_spec_template.json の draft instructions が上記方針に更新されていることを確認。
- codex-subagent での再実行は未実施。

## Tags
- ai-agent-collaboration-exec
- pipeline_spec_template
- consistency_check
- capsule_schema
- codex-subagent
