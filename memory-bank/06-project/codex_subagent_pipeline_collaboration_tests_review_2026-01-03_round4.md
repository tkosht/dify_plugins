# codex-subagent パイプライン協調 テストレビュー（round4: テストと実装の対応精査）

date: 2026-01-03
scope: tests/codex_subagent/* と .claude/skills/codex-subagent/scripts/codex_exec.py の対応レビュー
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
- 設計で要求される主要要件（Schema 検証、StageResult 制約、JSON Patch、動的 stage、境界値、ログ、終了コード）の多くがテストに反映されており、実装との整合性は概ね良好。
- ただし、`schema_version` の扱いがコード内で不一致（`SCHEMA_VERSION=1.1` と初期 Capsule/テストが `1.0`）で、仕様/実装/テストの整合性が弱い。

## テストケース別レビュー

### tests/codex_subagent/test_pipeline_schema.py
- test_pipeline_spec_schema_valid: `load_pipeline_spec` が JSON Schema を読み込んで妥当な PipelineSpec を受理することを確認。`validate_json_schema` の仕様に合致し適切。対応コード: `load_pipeline_spec` `validate_json_schema` `pipeline_spec.schema.json`。
- test_pipeline_spec_schema_rejects_unknown_key: `additionalProperties=false` を検証。Schema どおりに拒否されるため適切。対応コード: `load_pipeline_spec` `pipeline_spec.schema.json`。
- test_stage_spec_schema_rejects_unknown_key: StageSpec の未知キー拒否を直接確認。Schema どおりで適切。対応コード: `validate_json_schema` `stage_spec.schema.json`。
- test_stage_result_schema_rejects_wrong_type: `parse_stage_result_output` が schema 検証で型不一致を拒否することを確認。実装が先に schema 検証を行うため適切。対応コード: `parse_stage_result_output` `validate_json_schema` `stage_result.schema.json`。
- test_capsule_schema_rejects_missing_required: Capsule の必須項目欠落を拒否することを確認。実装が schema 検証のみを実施しているため適切。対応コード: `validate_json_schema` `capsule.schema.json`。

### tests/codex_subagent/test_pipeline_spec.py
- test_stage_result_ok_requires_not_partial: `status=ok` と `output_is_partial=true` を拒否する検証。`validate_stage_result` の条件に一致し適切。対応コード: `validate_stage_result`。
- test_stage_result_requires_capsule_patch: `capsule_patch` 必須を検証。`validate_stage_result` が None を拒否するため適切。対応コード: `validate_stage_result`。
- test_stage_result_error_allows_empty_patch: エラー時の空パッチ許容を確認。実装どおりで適切。対応コード: `validate_stage_result`。
- test_stage_result_error_rejects_nonempty_patch: エラー時の非空パッチ拒否を確認。実装どおりで適切。対応コード: `validate_stage_result`。
- test_patch_path_prefix_allows_children: JSON Patch 許可 prefix を検証。`_is_allowed_patch_path` の prefix 判定と一致し適切。対応コード: `_is_allowed_patch_path` `validate_patch_ops`。
- test_patch_path_prefix_rejects_outside: 許可外 prefix を拒否する検証。実装どおりで適切。対応コード: `_is_allowed_patch_path` `validate_patch_ops`。
- test_patch_path_prefix_allows_all_prefixes: `/open_questions` `/assumptions` `/critique` `/revise` を網羅。実装の `PATCH_ALLOWED_PREFIXES` と一致し適切。対応コード: `PATCH_ALLOWED_PREFIXES` `validate_patch_ops`。
- test_patch_ops_rejects_disallowed_op: `move` を拒否する検証。`PATCH_ALLOWED_OPS` に合致し適切。対応コード: `validate_patch_ops`。
- test_capsule_hash_excludes_pipeline_run_id: `compute_capsule_hash` が `pipeline_run_id` を除外する検証。`CAPSULE_HASH_EXCLUDE_KEYS` に合致し適切。対応コード: `_normalize_capsule` `compute_capsule_hash`。
- test_capsule_store_auto/test_capsule_store_auto_boundary: `CAPSULE_STORE_AUTO_THRESHOLD=20_000` に対する境界検証。`resolve_capsule_store` と一致し適切。対応コード: `resolve_capsule_store` `capsule_size_bytes`。
- test_capsule_path_constraints/test_resolve_capsule_delivery_auto_uses_path_only_for_file: `embed` で path 指定不可、`auto` で file のみ path 使用を検証。`resolve_capsule_delivery` の挙動と一致し適切。対応コード: `resolve_capsule_store` `resolve_capsule_path` `resolve_capsule_delivery`。
- test_resolve_pipeline_stages_default/conflict/from_spec/reject_unknown: `resolve_pipeline_stage_ids` の分岐を網羅。CLI 指定と Spec 指定の排他・未知 ID 拒否に合致し適切。対応コード: `resolve_pipeline_stage_ids`。

### tests/codex_subagent/test_pipeline_cli.py
- load_pipeline_spec 系: Spec 読み込みの正/異常パスを確認。`load_pipeline_spec` の例外設計と一致し適切。対応コード: `load_pipeline_spec`。
- resolve_capsule_path 系: file/embd の path 取り扱いを検証。`resolve_capsule_path` と一致し適切。対応コード: `resolve_capsule_path`。

### tests/codex_subagent/test_pipeline_patch.py
- test_apply_patch_add_append/replace/remove: JSON Patch 基本操作の適用確認。`apply_capsule_patch` の実装と一致し適切。対応コード: `apply_capsule_patch`。
- test_apply_patch_invalid_index: リスト境界エラーを検証。`apply_capsule_patch` の例外仕様と一致し適切。対応コード: `_resolve_parent` `apply_capsule_patch`。

### tests/codex_subagent/test_pipeline_execute.py
- test_execute_pipeline_success: 3段成功でパッチ適用されることを確認。`execute_pipeline` の順次実行/適用ロジックに合致し適切。対応コード: `execute_pipeline` `apply_stage_result`。
- test_execute_pipeline_stops_on_failure: `retryable_error` で停止することを確認。`apply_stage_result` が False を返して中断する挙動と一致し適切。対応コード: `apply_stage_result` `execute_pipeline`。
- test_execute_pipeline_rejects_next_stages_without_allow: `allow_dynamic=False` で next_stages を拒否。`validate_stage_result` と一致し適切。対応コード: `validate_stage_result`。
- test_execute_pipeline_allows_dynamic_stages: 動的 stage 追加と実行順序を検証。`execute_pipeline` の挿入ロジックに合致し適切。対応コード: `execute_pipeline` `validate_json_schema`。
- test_execute_pipeline_enforces_max_stages: `max_stages` 超過を拒否。`execute_pipeline` の長さチェックと一致し適切。対応コード: `execute_pipeline`。
- test_execute_pipeline_stops_on_patch_apply_failure: パッチ適用失敗で中断することを確認。`apply_stage_result` の例外捕捉挙動と一致し適切。対応コード: `apply_stage_result`。
- test_execute_pipeline_rejects_disallowed_dynamic_stage: `allowed_stage_ids` 制約を検証。`execute_pipeline` の allowed 判定と一致し適切。対応コード: `execute_pipeline`。

### tests/codex_subagent/test_pipeline_helpers.py
- test_stage_result_from_exec_failure_timeout/non_timeout: 失敗時 StageResult 生成を検証。`stage_result_from_exec_failure` の仕様と一致し適切。対応コード: `stage_result_from_exec_failure`。
- test_determine_pipeline_exit_code: 終了コードの分岐を検証。`determine_pipeline_exit_code` と一致し適切。対応コード: `determine_pipeline_exit_code`。
- test_build_stage_log_includes_capsule_fields: `pipeline_run_id`/`capsule_hash`/`capsule_path` を含むログ構造を確認。`build_stage_log` と一致し適切。対応コード: `build_stage_log`。
- test_run_pipeline_with_runner_exit_code_on_stage_failure/wrapper_error/success/timeout_failure: `run_pipeline_with_runner` の `exit_code` 結果を検証。`execute_pipeline` の例外/成功/失敗挙動と整合し適切。対応コード: `run_pipeline_with_runner` `execute_pipeline` `determine_pipeline_exit_code`。
- test_build_pipeline_output_payload_fields: JSON 出力の必須フィールドを検証。`build_pipeline_output_payload` と一致し適切。対応コード: `build_pipeline_output_payload`。

### tests/codex_subagent/test_pipeline_prompt.py
- test_build_stage_prompt_embed_includes_capsule_and_stage: embed 時に capsule を埋め込むことを確認。`build_stage_prompt` と一致し適切。対応コード: `build_stage_prompt`。
- test_build_stage_prompt_file_includes_path: file 時に path のみを提示し capsule 内容を含めないことを確認。実装と一致し適切。対応コード: `build_stage_prompt`。
- test_parse_stage_result_output_accepts_json/rejects_invalid: JSON 抽出と schema 検証の成功/失敗を確認。実装と一致し適切。対応コード: `_extract_json_object` `parse_stage_result_output`。
- test_ensure_prompt_limit_rejects_oversize/test_prepare_stage_prompt_enforces_max_total_prompt_chars: `max_total_prompt_chars` の境界検証。`ensure_prompt_limit` と `prepare_stage_prompt` の実装に合致し適切。対応コード: `ensure_prompt_limit` `prepare_stage_prompt`。

## 実装側の適切性に関する指摘
- `SCHEMA_VERSION=1.1` に対し、`build_initial_capsule` が `schema_version="1.0"` を固定しており、StageResult 生成は `SCHEMA_VERSION` を使用しているため、同一 pipeline 内で schema_version が混在する。仕様/実装/テストの整合性が不足。対応コード: `SCHEMA_VERSION` `build_initial_capsule` `stage_result_from_exec_failure`。
- `validate_stage_result`/schema では `schema_version` の値一致を要求しておらず、バージョン整合性が保証されない。テストもここを検証していないため、仕様に固定値要件がある場合は要修正。対応コード: `validate_stage_result` `stage_result.schema.json`。

## 追加推奨（品質向上）
- `schema_version` の整合（固定値か許容範囲か）を仕様で確定し、実装とテストに反映。
- pipeline JSON 出力（`args.json`）の構造確認テストを追加し、`build_pipeline_output_payload` と CLI 出力の一致を担保。
