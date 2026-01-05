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
- `memory-bank/06-project/ai_agent_collaboration_execution_framework_2026-01-05.md`
- `references/pipeline_spec_template.json`
- `references/subagent_prompt_templates.md`
- `references/contract_output.md`

## 入力
- 目的/期待成果
- 対象リポ/対象パス
- 制約（権限、期限、禁止事項）
- 書き込み許可範囲
- 必須ステージ/任意ステージ
- テスト/CI 要件

## 役割分担（実行責任）
- 親エージェント: 要件/品質合意、協調ループ起動、ゲート判定、最終報告のみを担当。
- Executor: 実ファイル変更、テスト実行、ログ収集。
- Reviewer: 独立レビュー、根拠付き指摘、未解消事項の提示。
- Verifier: テスト/CI 再実行、失敗時の切り分け・再試行。

## 手順
1. 参照ドキュメントを読み、役割分担と例外条件を確定すること。
2. Executor/Reviewer/Verifier の責務と書き込み範囲を明示すること。
3. パイプラインを `references/pipeline_spec_template.json` で組成し、必要なステージのみ残すこと。
4. Capsule 構造を `/draft /critique /revise /facts /open_questions /assumptions` に合わせること。
5. サブエージェントの依頼文を `references/subagent_prompt_templates.md` から作成すること。
6. ループ条件/終了条件、テスト/CI ゲートを明記すること。
7. 成果物契約出力を `references/contract_output.md` に従って固定化すること。
8. 事実ベースで記述し、不明は "不明" と明記すること。

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

## 出力
- パイプライン spec（JSON）
- 役割分担と書き込み範囲
- Capsule 構造
- サブエージェント依頼文
- 成果物契約出力
- 未解決事項（ある場合のみ）
