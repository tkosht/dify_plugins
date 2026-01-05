# codex-subagent パイプライン協調 テストレビュー（round5）

date: 2026-01-03
scope: tests/codex_subagent/* と .claude/skills/codex-subagent/scripts/codex_exec.py の対応レビュー（更新反映後）
sources:
  - memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md
  - .claude/skills/codex-subagent/scripts/codex_exec.py
  - .claude/skills/codex-subagent/schemas/*.json
  - tests/codex_subagent/test_pipeline_schema.py
  - tests/codex_subagent/test_pipeline_spec.py
  - tests/codex_subagent/test_pipeline_cli.py
  - tests/codex_subagent/test_pipeline_patch.py
  - tests/codex_subagent/test_pipeline_execute.py
  - tests/codex_subagent/test_pipeline_helpers.py
  - tests/codex_subagent/test_pipeline_prompt.py

## 総評
- 主要要件（Schema 検証、StageResult 制約、Patch 適用、動的 stage、境界、ログ、終了コード）がテストで網羅され、実装との対応も一貫している。
- `schema_version` の厳密一致チェックが実装に入ったため、テスト側も `SCHEMA_VERSION` 参照で整合している点は適切。

## テストケース別レビュー（適切性と対応コード）

### tests/codex_subagent/test_pipeline_schema.py
- test_pipeline_spec_schema_valid: 適切。`load_pipeline_spec` が schema を通過し正常に読み込むことを確認。対応コード: `load_pipeline_spec`, `validate_json_schema`, `pipeline_spec.schema.json`。
- test_pipeline_spec_schema_rejects_unknown_key: 適切。`additionalProperties=false` を検証。対応コード: `pipeline_spec.schema.json`。
- test_stage_spec_schema_rejects_unknown_key: 適切。StageSpec の未知キー拒否を確認。対応コード: `validate_json_schema`, `stage_spec.schema.json`。
- test_stage_result_schema_rejects_wrong_type: 適切。`parse_stage_result_output` が schema 違反を拒否することを確認。対応コード: `_extract_json_object`, `validate_json_schema`, `stage_result.schema.json`。
- test_capsule_schema_rejects_missing_required: 適切。Capsule 必須キー欠落時の拒否を確認。対応コード: `validate_json_schema`, `capsule.schema.json`。

### tests/codex_subagent/test_pipeline_spec.py
- test_stage_result_ok_requires_not_partial: 適切。`status=ok` と `output_is_partial=true` の禁止を検証。対応コード: `validate_stage_result`。
- test_stage_result_requires_capsule_patch: 適切。`capsule_patch` 必須を検証。対応コード: `validate_stage_result`。
- test_stage_result_error_allows_empty_patch: 適切。エラー時の空パッチ許容を検証。対応コード: `validate_stage_result`。
- test_stage_result_error_rejects_nonempty_patch: 適切。エラー時非空パッチを拒否。対応コード: `validate_stage_result`。
- test_patch_path_prefix_allows_children: 適切。許可 prefix を検証。対応コード: `_is_allowed_patch_path`, `validate_patch_ops`。
- test_patch_path_prefix_rejects_outside: 適切。許可外 prefix を拒否。対応コード: `_is_allowed_patch_path`, `validate_patch_ops`。
- test_patch_path_prefix_allows_all_prefixes: 適切。全 prefix を網羅確認。対応コード: `PATCH_ALLOWED_PREFIXES`。
- test_patch_ops_rejects_disallowed_op: 適切。`move` 禁止を検証。対応コード: `PATCH_ALLOWED_OPS`。
- test_capsule_hash_excludes_pipeline_run_id: 適切。`pipeline_run_id` 除外を検証。対応コード: `_normalize_capsule`, `compute_capsule_hash`。
- test_capsule_store_auto/test_capsule_store_auto_boundary: 適切。`CAPSULE_STORE_AUTO_THRESHOLD=20_000` の境界を確認。対応コード: `resolve_capsule_store`, `capsule_size_bytes`。
- test_capsule_path_constraints: 適切。`embed` で `capsule_path` 指定不可を確認。対応コード: `resolve_capsule_store`。
- test_resolve_capsule_delivery_auto_uses_path_only_for_file: 適切。`auto` で file のみ `capsule_path` を使うことを検証。対応コード: `resolve_capsule_delivery`, `resolve_capsule_path`。
- test_resolve_pipeline_stages_default/conflict/from_spec/reject_unknown: 適切。`resolve_pipeline_stage_ids` の分岐と排他/未知 ID 拒否を確認。対応コード: `resolve_pipeline_stage_ids`。

### tests/codex_subagent/test_pipeline_cli.py
- test_load_pipeline_spec_success/invalid/missing: 適切。Spec 読み込みの正/異常系を検証。対応コード: `load_pipeline_spec`。
- test_resolve_capsule_path_default/custom/embed_rejects_custom: 適切。file/embd の path 取り扱いを確認。対応コード: `resolve_capsule_path`。

### tests/codex_subagent/test_pipeline_patch.py
- test_apply_patch_add_append/replace/remove: 適切。JSON Patch の基本操作を確認。対応コード: `apply_capsule_patch`。
- test_apply_patch_invalid_index: 適切。範囲外インデックスを拒否。対応コード: `_resolve_parent`, `apply_capsule_patch`。

### tests/codex_subagent/test_pipeline_execute.py
- test_execute_pipeline_success: 適切。3段成功時の適用結果を確認。対応コード: `execute_pipeline`, `apply_stage_result`。
- test_execute_pipeline_stops_on_failure: 適切。`retryable_error` で停止することを確認。対応コード: `apply_stage_result`, `execute_pipeline`。
- test_execute_pipeline_rejects_next_stages_without_allow: 適切。`allow_dynamic=False` で `next_stages` を拒否。対応コード: `validate_stage_result`。
- test_execute_pipeline_allows_dynamic_stages: 適切。`next_stages` 追加と実行順序を確認。対応コード: `execute_pipeline`。
- test_execute_pipeline_enforces_max_stages: 適切。`max_stages` 超過拒否を確認。対応コード: `execute_pipeline`。
- test_execute_pipeline_dynamic_add_does_not_replace_queue: 適切。動的追加が既存 queue を置換しないことを確認。対応コード: `execute_pipeline` の `queue.insert`。
- test_execute_pipeline_stops_on_patch_apply_failure: 適切。パッチ適用失敗時の停止を確認。対応コード: `apply_stage_result`。
- test_execute_pipeline_rejects_disallowed_dynamic_stage: 適切。`allowed_stage_ids` 制約を確認。対応コード: `execute_pipeline`。

### tests/codex_subagent/test_pipeline_helpers.py
- test_stage_result_from_exec_failure_timeout/non_timeout: 適切。timeout と非 timeout の `status`/`output_is_partial` を検証。対応コード: `stage_result_from_exec_failure`。
- test_determine_pipeline_exit_code: 適切。`EXIT_SUCCESS/EXIT_SUBAGENT_FAILED/EXIT_WRAPPER_ERROR` 分岐を確認。対応コード: `determine_pipeline_exit_code`。
- test_build_stage_log_includes_capsule_fields: 適切。`pipeline_run_id`/`capsule_hash`/`capsule_path` を含むことを確認。対応コード: `build_stage_log`。
- test_run_pipeline_with_runner_exit_code_on_stage_failure/wrapper_error/success/timeout_failure: 適切。`run_pipeline_with_runner` の exit code を経路別に確認。対応コード: `run_pipeline_with_runner`, `execute_pipeline`, `determine_pipeline_exit_code`。
- test_build_pipeline_output_payload_fields: 適切。JSON 出力の必須フィールド存在を検証。対応コード: `build_pipeline_output_payload`。

### tests/codex_subagent/test_pipeline_prompt.py
- test_build_stage_prompt_embed_includes_capsule_and_stage: 適切。embed で Capsule 内容を含めることを確認。対応コード: `build_stage_prompt`。
- test_build_stage_prompt_file_includes_path: 適切。file で path のみ出力することを確認。対応コード: `build_stage_prompt`。
- test_parse_stage_result_output_accepts_json/rejects_invalid: 適切。JSON 抽出と schema 検証を確認。対応コード: `_extract_json_object`, `parse_stage_result_output`, `validate_json_schema`。
- test_ensure_prompt_limit_rejects_oversize/test_prepare_stage_prompt_enforces_max_total_prompt_chars: 適切。`max_total_prompt_chars` の強制を検証。対応コード: `ensure_prompt_limit`, `prepare_stage_prompt`。

## 実装側の適切性（設計との整合）
- `schema_version` の厳密一致を `validate_stage_result` が強制しており、テスト側も `SCHEMA_VERSION` を使用して整合している。設計に version 一致が必要な場合は適切。
- `build_initial_capsule` で `SCHEMA_VERSION` を使用するよう統一され、StageResult と整合している。

## 補足（追加検証の価値がある点）
- `build_pipeline_output_payload` の値（`capsule_hash` が `compute_capsule_hash` と一致するか）まで検証すると、仕様への結び付きがより明確になる。
- CLI の `--json` 出力が `build_pipeline_output_payload` と一致するかの結合テストがあると、設計の「実装時点の JSON 出力」項目の保証が強化できる。
