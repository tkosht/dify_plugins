# codex-subagent パイプライン協調 テストレビュー（round6: 結合テスト）

date: 2026-01-03
scope: tests/codex_subagent/test_pipeline_integration.py のレビュー
sources:
  - tests/codex_subagent/test_pipeline_integration.py
  - .claude/skills/codex-subagent/scripts/codex_exec.py
  - .claude/skills/codex-subagent/schemas/stage_result.schema.json
  - memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md

## 総評
- 正常系（3段パイプライン成功）と動的ステージ追加の検証は満たしており、要件は概ね達成できている。
- ただし LLM 出力依存のためフレーク性があり、JSON 出力の内容検証が弱い。

## テストケース別レビュー（適切性と対応コード）

### _run_pipeline
- CLI で実際に `--mode pipeline` を実行し `returncode==0` を要求する構成は結合テストとして適切。
- 対応コード: `main()` の pipeline 分岐、`run_pipeline_with_runner`、`build_pipeline_output_payload`。

### test_pipeline_cli_smoke_success
- 3段（draft/critique/revise）を通して `success=True` と stage_id の順序を確認しており、正常系スモークとして適切。
- 対応コード: `execute_pipeline`（順次実行）、`build_pipeline_output_payload`（JSON 出力）。

### test_pipeline_cli_dynamic_stage
- `draft` が `next_stages` を返し `extra` が挿入されることを検証しており、動的エージェント構築の正当性確認として適切。
- 対応コード: `execute_pipeline` の `next_stages` 挿入ロジック、`find_stage_spec` と `build_stage_prompt`。

## 指摘事項
- **Medium: フレーク耐性**
  - `stage_result.schema.json` は `additionalProperties=false` のため、LLM が余計なキーを返すと失敗する。プロンプト制御は強いが完全ではなく、CI では不安定化の可能性がある。
- **Low: JSON 出力の中身検証が弱い**
  - `payload` の `pipeline_run_id` / `capsule_hash` / `capsule_store` などの存在検証を追加すると、設計の「実装時点の JSON 出力（暫定）」の保証が強くなる。

## 要件適合性
- 正常系テスト: 充足。
- 動的エージェント構築テスト: 充足。
