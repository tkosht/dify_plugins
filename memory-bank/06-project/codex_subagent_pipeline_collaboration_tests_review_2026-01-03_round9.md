# codex-subagent パイプライン協調 総合レビュー（round9）

date: 2026-01-03
scope: 単体/結合テスト + 実装 + 設計ドキュメントの整合性レビュー（round7反映後）
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

### Low
1) **動的 StageSpec の prompt 反映を結合テストで直接検証していない**
   - 実装は `dynamic_stage_specs` を通じて StageSpec を反映するが、結合テストではその反映結果をアサートしていない。
   - 保証レベルを上げるなら、動的ステージに専用指示を埋め込み、それが prompt に反映された痕跡を検証するテストが必要。
   - 参照: `tests/codex_subagent/test_pipeline_integration.py:45` `.claude/skills/codex-subagent/scripts/codex_exec.py:676` `.claude/skills/codex-subagent/scripts/codex_exec.py:952`

## 解消済み（round7 指摘の反映）
- **動的ステージ指示の競合**: `allow_dynamic=True` の場合にテンプレートへ `next_stages` を含めるよう修正され、矛盾が解消。
  - 参照: `tests/codex_subagent/test_pipeline_prompt.py:56` `.claude/skills/codex-subagent/scripts/codex_exec.py:485`
- **動的 StageSpec の反映**: `next_stages` の spec が `dynamic_stage_specs` に保存され、`find_stage_spec` 経由で prompt に反映される。
  - 参照: `.claude/skills/codex-subagent/scripts/codex_exec.py:676` `.claude/skills/codex-subagent/scripts/codex_exec.py:952` `.claude/skills/codex-subagent/scripts/codex_exec.py:2252`
- **schema_version 不一致**: 設計ドキュメントの例が `1.1` に更新され、実装/テストと一致。
  - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:75` `.claude/skills/codex-subagent/scripts/codex_exec.py:109` `tests/codex_subagent/test_pipeline_spec.py:12`

## 全体整合性の評価
- 単体テストは Schema 検証 / StageResult 制約 / Patch 適用 / 動的 stage / 境界 / ログ / exit code を実装と一致させて網羅。
- 結合テストは `payload` フィールドと `capsule_hash` 整合まで検証し、`build_pipeline_output_payload` と一致。
- 設計ドキュメントの主要仕様（capsule_store 境界/patch ルール/exit code）も実装・テストと整合。

## 総評
- 適切性・相互整合性は高い水準。
- 残る課題は、動的 StageSpec の prompt 反映を結合テストで直接検証するかどうかのみ。
