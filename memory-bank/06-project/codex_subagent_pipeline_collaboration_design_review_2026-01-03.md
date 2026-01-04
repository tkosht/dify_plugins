# codex-subagent pipeline collaboration design review (2026-01-03)

date: 2026-01-03
status: recorded
source: memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md
scope: design review
tags: review, pipeline, codex-subagent, capsule, StageResult

## 対象
- codex-subagent パイプライン協調設計（Draft→Critique→Revise）

## 指摘事項（重要度順）
- [重大] StageResult が例のみで、必須/任意/型/失敗時挙動の定義が本文にない (ref: L74-L78)
- [高] capsule_patch が差分とだけ記載され、差分形式と適用手順が本文にない (ref: L78)
- [高] output_is_partial の扱いが本文にあるが StageResult 定義に含まれていない (ref: L82)
- [高] ステージ定義の経路と CLI 指定の同時指定時の優先順位・衝突解決が本文にない (ref: L22-L30, L91-L98)
- [中] capsule_hash の算出方式（正規化規則/ハッシュアルゴリズム）が本文にない (ref: L85-L89)
- [中] --capsule-path と保存方式の関係、および capsule_size の定義が本文にない (ref: L38-L42, L96-L98, L107)

## 確認事項
- PipelineSpec / StageSpec / StageResult の JSON Schema をどこで定義・管理するか (ref: L29)
- capsule_patch の差分形式は何を採用するか (ref: L78)
- --pipeline-stages / --pipeline-spec / planner の同時指定時の優先順位はどうするか (ref: L22-L30)
- capsule_hash の正規化規則とハッシュアルゴリズムは何を使うか (ref: L87)

## 提案
- JSON Schema（必須/任意/型/失敗時）の明文化と capsule_patch 形式の決定
- ステージ定義の優先順位・衝突解決・バリデーション失敗時の挙動の明記
- capsule_hash の正規化・アルゴリズム、capsule_size と保存方式の仕様追記

## 次アクション
- 仕様（Schema/patch/partial/exit-code/優先順位）を確定し設計書へ反映
- capsule 保存・サイズ上限・auto 判定条件を明文化
- テスト方針に schema 検証と境界条件を追記
