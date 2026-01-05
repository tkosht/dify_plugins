# codex-subagent パイプライン協調 テストレビュー（再レビュー・round3）

date: 2026-01-03
scope: tests/codex_subagent/* の設計整合レビュー（更新後）
sources:
  - memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md
  - tests/codex_subagent/test_pipeline_schema.py
  - tests/codex_subagent/test_pipeline_spec.py
  - tests/codex_subagent/test_pipeline_cli.py
  - tests/codex_subagent/test_pipeline_helpers.py
  - tests/codex_subagent/test_pipeline_prompt.py
  - tests/codex_subagent/test_pipeline_patch.py
  - tests/codex_subagent/test_pipeline_execute.py

## 対象
- 設計: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md`
- テスト: `tests/codex_subagent/` 配下7ファイル

## 現状カバー（要約）
- Schema 検証（PipelineSpec/StageSpec/StageResult/Capsule）
- StageResult 制約（`status`/`output_is_partial`/空パッチ許容/`capsule_patch` 必須）
- JSON Patch の許可 prefix/禁止 op と基本操作（add/replace/remove）
- 3段 pipeline の成功/停止、動的 stage の許可/拒否、`max_stages`/`allowed_stage_ids`
- パッチ適用失敗時の停止
- pipeline spec の読み込み/存在/不正JSON
- capsule path の既定/カスタム/`embed` 禁止、`auto`+境界値 20,000 と path 利用条件
- prompt 構築（embed/file）と StageResult パース失敗
- ログに `pipeline_run_id`/`capsule_hash`/`capsule_path` を含むこと
- `run_pipeline_with_runner` の exit code（サブエージェント失敗/ラッパーエラー）

## 指摘事項（設計との未整合・不足）

### 重大
1) **スモーク要件の `exit_code=0` 検証不足**
   - 設計はスモークで `exit_code=0` を要求。
   - 現行テストは `execute_pipeline` の成功のみで、`run_pipeline_with_runner`/CLI で成功時の `exit_code=0` を検証していない。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:171`

2) **timeout 失敗 → `exit_code=2` の実行経路検証不足**
   - timeout の StageResult 変換はあるが、`run_pipeline_with_runner`/CLI で `exit_code=2` となる経路が未検証。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:134` `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:171`

### 中
3) **動的 stage の「追加のみ（削除/置換禁止）」制約のテスト欠如**
   - `next_stages` が既存 stage を削除/置換するケースの拒否を検証していない。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:54`

4) **`max_total_prompt_chars` の実行経路検証不足**
   - 単体の拒否は確認済みだが、pipeline 実行経路（Spec/動的 stage 組み合わせ）での強制が未検証。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:50`

5) **暫定 JSON 出力のフィールド検証不足**
   - `pipeline_run_id`/`stage_results`/`capsule_hash` などの最終 JSON 出力確認が未検証。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:159`

## 改善済みの点（前回からの反映）
- Schema 検証の追加。
- `run_pipeline_with_runner` の exit code（失敗/ラッパーエラー）検証追加。
- パッチ適用失敗時の停止挙動追加。
- `allowed_stage_ids` の拒否追加。
- ログに `pipeline_run_id` を含む検証追加。

## 追加推奨テスト
- 成功時 `exit_code=0` を `run_pipeline_with_runner`/CLI で検証。
- timeout を意図的に発生させ `exit_code=2` を実行経路で検証。
- `next_stages` による削除/置換を拒否するテスト。
- `max_total_prompt_chars` を pipeline 実行経路で超過させるテスト。
- 暫定 JSON 出力フィールドの存在検証。

## 確認事項
- exit code の責務範囲（CLI まで含めるか、`run_pipeline_with_runner` までで十分か）
- 暫定 JSON 出力をテスト対象に含めるか
