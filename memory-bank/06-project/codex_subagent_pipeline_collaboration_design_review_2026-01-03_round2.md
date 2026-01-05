# codex-subagent pipeline collaboration design review (round2, 2026-01-03)

date: 2026-01-03
status: recorded
source: memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md
scope: design review (updated spec)
tags: review, pipeline, codex-subagent, capsule, StageResult, json-patch

## 指摘事項（重要度順）
- [高] JSON Patch 許可 path に `/open_questions` `/assumptions` がある一方、Capsule 例ではこれらが `draft` 配下にあるため、現仕様では更新不能 (ref: L85-L88, L121)
- [中] `capsule_patch` が必須だが、失敗/部分出力時の空配列許容 or 必須解除の方針が未定義 (ref: L109, L114)
- [中] `output_is_partial` と `status` の組み合わせ制約が未定義で、`status="ok"` と併用可否が不明 (ref: L107, L115)
- [中] 許可 path が「完全一致」か「配下含む」かの定義がなく、`/facts/-` など JSON Patch の標準パス可否が不明 (ref: L119-L121)

## 確認事項
- `status!="ok"` または `output_is_partial=true` の場合、`capsule_patch` は空配列を許容するか、必須から除外するか (ref: L109, L114)
- `output_is_partial=true` は `status="ok"` と併用可能か、禁止するか (ref: L107, L115)

## 所見
- 前回指摘（優先順位/Schema 管理/capsule_size 定義）は反映済みで、仕様の骨格は明確化した (ref: L32-L46, L62-L70)
