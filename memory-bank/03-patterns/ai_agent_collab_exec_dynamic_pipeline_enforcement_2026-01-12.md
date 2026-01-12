# ai-agent-collaboration-exec 動的パイプライン強制 (2026-01-12)

## Problem
- 既定パイプラインの踏襲が前提化すると、タスク最適化と動的設計（途中再設計）が機能せず、協調実行の価値が失われる。

## Decision
- 既定パイプラインの踏襲を禁止し、タスクに合わせた初期/動的ステージ設計を必須化する。
- 動的追加は `next_stages` を前提とし、設計理由・最適化観点を /draft.proposal に記録する。
- 動的設計が必要な場合は `--pipeline-spec` を使用し、`--pipeline-stages` の固定テンプレートに依存しない。
- 成果物契約に「パイプライン設計根拠」「動的追加の実績」を追加し、未実施時の報告を必須化する。

## Changes
- SKILL.md: 手順に「既定パイプライン踏襲禁止」「動的追加条件明記」を追加。
- execution_framework.md: 既定踏襲禁止と動的追加前提を明記、例は初期ステージのみ。
- pipeline_spec_template.json: draft instructions に「既定踏襲禁止」「初期/動的ステージ設計」を明記。
- subagent_prompt_templates.md: パイプライン設計を必須化、Reviewer が不適合を NG 指摘。
- contract_output.md: パイプライン設計根拠と動的追加実績を必須出力に追加。

## Files
- .claude/skills/ai-agent-collaboration-exec/SKILL.md
- .claude/skills/ai-agent-collaboration-exec/references/execution_framework.md
- .claude/skills/ai-agent-collaboration-exec/references/pipeline_spec_template.json
- .claude/skills/ai-agent-collaboration-exec/references/subagent_prompt_templates.md
- .claude/skills/ai-agent-collaboration-exec/references/contract_output.md

## Tags
- ai-agent-collaboration-exec
- dynamic-pipeline
- next_stages
- pipeline-spec
- governance
