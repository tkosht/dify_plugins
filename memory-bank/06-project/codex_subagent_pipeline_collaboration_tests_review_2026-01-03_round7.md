# codex-subagent パイプライン協調 テストレビュー（round7: 結合テスト再レビュー）

date: 2026-01-03
scope: tests/codex_subagent/test_pipeline_integration.py の精緻レビュー（更新反映後）
sources:
  - tests/codex_subagent/test_pipeline_integration.py
  - .claude/skills/codex-subagent/scripts/codex_exec.py
  - memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md

## 指摘事項（重要度順）

### Medium
1) **動的ステージ指示とプロンプト雛形の競合によるフレーク要因**
   - `build_stage_prompt` は「Return JSON ONLY with this shape」(next_stages を含まない形) を常に提示する。
   - 動的テストでは `next_stages` を返すよう指示しているため、LLM に相反する命令が入る。
   - その結果、`next_stages` が返らず失敗する経路があり、CI で不安定化する可能性がある。
   - 参照: `tests/codex_subagent/test_pipeline_integration.py:45` `.claude/skills/codex-subagent/scripts/codex_exec.py:451`

2) **動的 StageSpec の instructions/prompt が実行で使われない**
   - `next_stages` 内で `{id, instructions}` を指定しているが、実装は `id` のみ挿入し `instructions` は無視される。
   - 動的ステージの仕様として instructions を反映する想定がある場合、実装とテスト双方で未検証。
   - 参照: `tests/codex_subagent/test_pipeline_integration.py:45` `.claude/skills/codex-subagent/scripts/codex_exec.py:914`

## 適切な点（テストと実装の整合）
- 正常系スモークで `returncode==0`・`success=True`・`stage_results` の順序を検証しており妥当。
  - 参照: `tests/codex_subagent/test_pipeline_integration.py:121`
- 動的ステージ構築で `draft → extra → revise` の順序を検証しており、挿入ロジックと整合。
  - 参照: `tests/codex_subagent/test_pipeline_integration.py:139` `.claude/skills/codex-subagent/scripts/codex_exec.py:914`
- `payload` の `capsule_hash` を `compute_capsule_hash` と照合し、CLI JSON 出力整合を担保。
  - 参照: `tests/codex_subagent/test_pipeline_integration.py:57` `.claude/skills/codex-subagent/scripts/codex_exec.py:587`
- `schema_version` を `SCHEMA_VERSION` に一致させ、`validate_stage_result` の厳格チェックと整合。
  - 参照: `tests/codex_subagent/test_pipeline_integration.py:76` `.claude/skills/codex-subagent/scripts/codex_exec.py:695`

## 総評
- 正常系と動的エージェント構築の要件は満たしている。
- ただし、動的ステージに関する仕様（StageSpec の instructions を使うか否か）が曖昧で、現行実装は未反映。そこを前提とするなら実装/テスト双方に不足がある。
- LLM 指示の競合によりフレークしやすい点は残るため、安定性を重視する場合は改善が必要。
