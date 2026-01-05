# codex-subagent パイプライン協調 総合レビュー（round10）

date: 2026-01-03
scope: 単体/結合テスト + 実装 + 設計ドキュメントの整合性レビュー（非決定性対策方針反映）
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

## 追加方針（議論反映）
- 結合テストの非決定性は「ゼロではない」前提で扱う。
- 具体的には、結合テストケースとして **リトライ（再実行）または出力逸脱時の再生成**などの対処を組み込むことを方針とする。
- 目的は CI 安定性の担保であり、LLM 出力の厳格性を緩めることではない。

## 現状の評価
- 主要な単体/結合テストと実装・設計は高い整合性を維持している。
- 動的 StageSpec 反映の痕跡は結合テストで検証済み。
- 残る課題は、LLM 出力逸脱による flake の実務的な対策を「結合テストの責務」として組み込むこと。

## 総評
- 現時点の設計・実装・テストは整合しているが、結合テストの安定性を実務的に高めるためのリトライ/再実行戦略を追加する方針を明記する。
