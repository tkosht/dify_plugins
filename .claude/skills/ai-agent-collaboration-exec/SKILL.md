---
name: ai-agent-collaboration-exec
description: "Auto-trigger when the user asks to design or run an AI collaboration process where the parent agent is the sole user interface and execution is delegated to subagents (Executor/Reviewer/Verifier)."
allowed-tools:
  - Bash(codex:*)
  - Bash(uv run python:*)
  - Bash(timeout:*)
  - Read
  - Write
  - Glob
metadata:
  version: 0.1.0
  owner: codex
  maturity: draft
  tags: [skill, collaboration, subagent, executor, pipeline]
---

## 概要
親エージェントが唯一のユーザ窓口となり、実行はサブエージェント（Executor/Reviewer/Verifier）に委譲する協調開発の設計/運用を定義するスキル。

## 参照（必読）
- `references/execution_framework.md`
- `references/pipeline_spec_template.json`
- `references/subagent_prompt_templates.md`
- `references/contract_output.md`

## 入力
- 目的/期待成果
- 対象リポ/対象パス
- 制約（権限、期限、禁止事項）
- 書き込み許可範囲
- レビュー/検証の記録先（review_output_dir）
- 必須ステージ/任意ステージ
- テスト/CI 要件

## 入力受け渡し例
- 親エージェントは 1 つの PROMPT に統合して `codex_exec.py --prompt` に渡す。
- 必須要素: OBJECTIVE / SCOPE / CONSTRAINTS / REQUIRED OUTPUTS / CAPSULE PATCH RULES / TEST DESIGN REQUIREMENT。
- 例（最小構成）:
  ```text
  ROLE: Parent agent orchestration for <topic>
  DATE: YYYY-MM-DD

  OBJECTIVE
  - <goal>

  SCOPE
  - Target repo: <path>
  - Target paths: <paths>

  CONSTRAINTS
  - <constraints>

  REQUIRED OUTPUTS
  1) <artifact list>

  CAPSULE PATCH RULES
  - /facts はオブジェクト配列（文字列禁止）
  - /draft /critique /revise はオブジェクトのまま
  ```

## 役割分担（実行責任）
- 親エージェント: 要件/品質合意、協調ループ起動、ゲート判定、最終報告のみを担当。
- Executor: 実ファイル変更、テスト実行、ログ収集。
- Reviewer: 独立レビュー、根拠付き指摘、未解消事項の提示。
- Verifier: テスト/CI 再実行、失敗時の切り分け・再試行。
- Releaser: commit/PR などの運用作業（任意、必要時のみ）。

## 手順
1. 参照ドキュメントを読み、役割分担と例外条件を確定すること。
2. Executor/Reviewer/Verifier の責務と書き込み範囲を明示すること。
3. パイプラインを `references/pipeline_spec_template.json` で組成し、必要なステージのみ残すこと。
4. `allowed_stage_ids` と使用ステージの整合を確認すること（`release` を使う場合は追加、使わない場合は削除）。
5. Capsule 構造を `/draft /critique /revise /facts /open_questions /assumptions` に合わせること。
6. サブエージェントの依頼文を `references/subagent_prompt_templates.md` から作成すること。
7. ループ条件/終了条件、テスト/CI ゲートを明記すること。
8. 成果物契約出力を `references/contract_output.md` に従って固定化すること。
9. 事実ベースで記述し、不明は "不明" と明記すること。

## 実行前提/依存
- `codex` 実行バイナリが PATH にあること（例: `node_modules/.bin`）。
- `jsonschema` が `uv run python` で利用可能であること。
- pipeline は 360〜420s/ステージの timeout を推奨（読み取り/整形が多い場合）。
- 確認手順（例）:
  - `command -v codex`
  - `command -v uv`
  - `uv run python -c "import jsonschema, sys; print('jsonschema_ok')"`

## 検証手順（必須）
- pipeline spec の妥当性検証: `uv run pytest tests/codex_subagent/test_pipeline_spec.py --no-cov`

## Capsule パッチルール（必須）
- `/facts` は「オブジェクト配列」。文字列は不可。
- `/draft` `/critique` `/revise` はオブジェクトのまま、キー追加で記録する。
- JSON Patch 例:
  `{ "op": "add", "path": "/facts/-", "value": { "type": "commands", "items": ["cmd1"], "evidence": "shell" } }`

## 最小 pipeline spec 例
```json
{
  "allow_dynamic_stages": false,
  "allowed_stage_ids": ["draft", "review", "revise"],
  "stages": [
    { "id": "draft", "instructions": "評価方針を /draft に記録。根拠は /facts。" },
    { "id": "review", "instructions": "独立レビューを /critique に記録。根拠必須。" },
    { "id": "revise", "instructions": "修正と結論を /revise に記録。未解決は /open_questions。" }
  ]
}
```

## 起動/成果物保存先
- 起動は `codex-subagent` を使用する。
- 例（pipeline spec を使う場合）:
  ```bash
  uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
    --mode pipeline --pipeline-spec <spec.json> \
    --capsule-store auto --sandbox read-only --json --prompt "$PROMPT"
  ```
- ログ: `.codex/sessions/codex_exec/{human|auto}/YYYY/MM/DD/run-*.jsonl`
- capsule（`--capsule-store file|auto`）: `.codex/sessions/codex_exec/{human|auto}/artifacts/<pipeline_run_id>/capsule.json`
- レビュー/検証の成果物: `review_output_dir`（既定は `docs/ai-agent-reviews/`）

## 実行ポリシー（品質優先）
- タスク難易度や要求水準を下げての短縮はしない。
- 時間がかかる場合は timeout を延長して対応する。
- timeout が発生したら、同一スコープで再実行する（再実行上限を明示）。
- 再実行しても進められない場合は、タスクを停止しフレームワークのデバッグ/改善に移行する。

## 例外（親が実行）
- 仕様変更/品質基準変更などユーザ合意が必要な判断。
- サブエージェント権限不足で進行不可となった操作。
- 秘密情報や承認が必要な操作。

## オプション
- `review`/`verify`/`release` ステージの有無を選択すること。
- `allow_dynamic_stages` の有効/無効を決めること。
- 再実行上限を明示すること。
- 書き込み許可パスとテスト範囲を最小化すること。

## 既定値（codex_exec）
- `--mode`: `single`
- `--count`: `3`
- `--sandbox`: `read-only`
- `--timeout`: `360`
- `--profile`: 未指定（None）
- `--task-type`: `code_gen`
- `--strategy`: `best_single`
- `--merge`: `concat`
- `--log`: 有効
- `--capsule-store`: `auto`
- `--max-stages`: `10`

## 成果物命名（推奨）
- 基本ディレクトリ: `docs/ai-agent-reviews/`
- パイプライン spec: `<topic>_pipeline_spec_YYYY-MM-DD.json`
- サブエージェント依頼文: `<topic>_subagent_prompts_YYYY-MM-DD.md`
- テスト計画: `<topic>_test_plan_YYYY-MM-DD.md`
- レビュー記録: `<topic>_review_YYYY-MM-DD_roundN.md`
- 成果物契約出力: `<topic>_contract_output_YYYY-MM-DD.md`

## 出力
- パイプライン spec（JSON）
- 役割分担と書き込み範囲
- Capsule 構造
- サブエージェント依頼文
- 成果物契約出力
- 未解決事項（ある場合のみ）
