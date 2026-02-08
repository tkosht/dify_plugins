# SharePoint List 整合性チェックの改善ループ・パイプライン設計 (2026-01-16)

## 目的
- verify で追加検証が必要と判断された場合に、改善→再検証まで自動で回せるパイプラインを定義する。
- ドキュメント/コード/テストの三者整合を「証拠ベース」で判定し、再現性のある修正ループを確立する。

## 設計方針
- 既定パイプラインは使わず、整合性レビューに最適化したステージ構成を採用。
- ループは verify が判定し、`next_stages` で再実行させる。
- ループ上限を設け、無限再実行を防止する（max_loops=2）。
- 事実ベース: /facts 以外の推測は不許可。不明は不明で記録する。

## ステージ構成（初期実行順）
1) draft
- 目的: チェック観点、成功条件、ループ条件、証拠要件を確定。
- 出力: /draft に {checks, success, loop_policy, evidence_requirements} を記録。

2) execute
- 目的: 証拠収集と必要テストの実行。
- 出力: /facts（item/evidence/source/status の配列）。

3) review
- 目的: /facts と /draft を照合し不整合を抽出。
- 出力: /critique に {summary, issues[], needs_fix, needs_more_evidence}。

4) revise
- 目的: need_fix が true または blocker/major がある場合に修正を適用。
- 出力: /revise に {changes, files, commands, noop}。

5) verify
- 目的: 成功条件の再確認とループ判定。
- 出力: /facts に loop_count を更新。必要なら next_stages で再実行。

## ループ条件
- /critique に blocker または major が残る
- /critique.needs_more_evidence が true
- /open_questions が残る
- テスト失敗が /facts に記録されている

## ループ動作
- verify がループ条件に該当し、loop_count < max_loops の場合:
  - next_stages に execute → review → revise → verify を追加
- loop_count >= max_loops の場合:
  - /open_questions に「手動介入が必要」を記録し終了

## 成功条件
- blocker/major 指摘ゼロ
- /open_questions が空
- 追加検証要否なし
- テストが通過（必要な場合のみ）

## ガードレール
- stage_result は単一行 JSON のみ
- capsule_patch は 1 件のみ（replace）
- /facts は配列（文字列禁止）
- next_stages は {id} 形式のオブジェクト配列のみ

## 成果物
- パイプライン spec: docs/ai-agent-reviews/sharepoint_list_pipeline_spec_2026-01-16_loop.json
- パイプライン prompt: docs/ai-agent-reviews/sharepoint_list_pipeline_prompt_2026-01-16_loop.txt
- サブエージェント依頼文: docs/ai-agent-reviews/sharepoint_list_subagent_prompts_2026-01-16_loop.md
