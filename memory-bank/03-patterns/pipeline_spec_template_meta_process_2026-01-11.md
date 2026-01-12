# pipeline_spec_template メタプロセス精緻化 (2026-01-11)

## Problem
- pipeline_spec_template.json の stage 定義が粗く、タスクに最適なプロセス設計(メタプロセス)が明示できない。
- pipeline_spec.schema.json の追加キー禁止により、構造追加ではなく instructions 内での精緻化が必要。
- 統合テストで pipeline_spec_template.json の stage id 配列が固定値で検証されるため、ID/順序は維持する必要がある。

## Research
- codex-subagent を pipeline モード(draft/critique/revise)で実行し、instructions 内のメタプロセス化を設計。
- 制約: top-level keys は allow_dynamic_stages/allowed_stage_ids/stages/max_total_prompt_chars のみ、stage object は id/instructions/prompt のみ。

## Solution
- stage id と allowed_stage_ids を維持したまま、各 instructions を「目的 + 手順(階層的な手順) + 記録先 + 推測禁止」に拡張。
- draft にメタプロセス定義(成功条件、分解、検証計画、記録形式)を集約し、他ステージは /draft.proposal の記録形式に従う設計に統一。
- execute/verify の「未実施」記録ルールを追加し、運用上の抜け漏れを防止。

## Verification
- 更新対象: .claude/skills/ai-agent-collaboration-exec/references/pipeline_spec_template.json
- 追加キーなし、ID/順序固定、schema 制約と整合。

## Tags
- pipeline_spec_template
- meta_process
- ai-agent-collaboration-exec
- codex-subagent
- schema_constraints

## Examples
```json
{
  "id": "draft",
  "instructions": "目的: ... 手順: 1) ... 2) ... 3) ... 推測禁止..."
}
```
