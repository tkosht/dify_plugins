# codex-subagent パイプライン協調 総合レビュー（round8）

date: 2026-01-03
scope: 単体/結合テスト + 実装 + 設計ドキュメントの整合性レビュー
sources:
  - memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md
  - .claude/skills/codex-subagent/scripts/codex_exec.py
  - .claude/skills/codex-subagent/schemas/*.json
  - tests/codex_subagent/test_pipeline_schema.py
  - tests/codex_subagent/test_pipeline_spec.py
  - tests/codex_subagent/test_pipeline_cli.py
  - tests/codex_subagent/test_pipeline_helpers.py
  - tests/codex_subagent/test_pipeline_prompt.py
  - tests/codex_subagent/test_pipeline_patch.py
  - tests/codex_subagent/test_pipeline_execute.py
  - tests/codex_subagent/test_pipeline_integration.py

## 指摘（重要度順）

### Medium
1) **動的ステージ指示と固定テンプレートの競合（フレーク要因）**
   - `build_stage_prompt` は next_stages を含まない形を固定で提示。
   - 結合テストは `next_stages` を返すよう指示しており、命令が競合して不安定化する。
   - 参照: `tests/codex_subagent/test_pipeline_integration.py:45` `.claude/skills/codex-subagent/scripts/codex_exec.py:451`

2) **動的 StageSpec の instructions が実行に反映されない**
   - `next_stages` の `instructions/prompt` を与えても、実装は `id` のみ挿入し次ステージで使わない。
   - 動的 StageSpec を活かす前提なら、実装/テストの整合が不足。
   - 参照: `tests/codex_subagent/test_pipeline_integration.py:45` `.claude/skills/codex-subagent/scripts/codex_exec.py:657` `.claude/skills/codex-subagent/scripts/codex_exec.py:914`

3) **設計ドキュメントの schema_version が実装と不一致**
   - 設計例は `1.0` だが実装/テストは `SCHEMA_VERSION=1.1` を強制。
   - ドキュメント更新が未反映で仕様整合が崩れている。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:73` `.claude/skills/codex-subagent/scripts/codex_exec.py:109` `tests/codex_subagent/test_pipeline_spec.py:12`

## 適切な点（全体整合）
- 単体テストは Schema 検証/StageResult 制約/JSON Patch/動的 stage/境界/ログ/exit code を実装と一致させて網羅している。
- 結合テストは JSON 出力の主要フィールドと `capsule_hash` の一致まで検証し、`build_pipeline_output_payload` と整合している。

## 総評
- 主要機能の相互整合性は概ね良好。
- ただし、動的ステージの指示競合（フレーク）と StageSpec の扱い、設計ドキュメントの schema_version だけは不整合が残るため、修正が必要。
