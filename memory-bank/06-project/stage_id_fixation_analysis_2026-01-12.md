# stage_id 固定要否の分析 (2026-01-12)

## Problem
- codex-subagent の pipeline において stage_id を固定にする必要があるかを明確化したい。

## Research
- codex-subagent pipeline で解析。
  - pipeline_run_id: e6bf4f73-fa88-4db6-b678-5d364ea6c7f8
  - log: .codex/sessions/codex_exec/auto/2026/01/11/run-20260111T164816-b7ab5fcf.jsonl
- 事実:
  - pipeline_spec.schema.json は stages[].id を非空文字列として要求するのみ。
  - codex_exec.py の `--pipeline-stages` 経路は `PIPELINE_STAGE_TEMPLATES` 外のIDを拒否（既定は draft/critique/revise）。
  - codex_exec.py の `--pipeline-spec` 経路は stages[].id を受理し、IDの列挙制限はない。
  - allow_dynamic_stages 時の allowed_stage_ids 制約は next_stages のみに適用。
  - テストは default/unknown のみ検証し、非デフォルトIDの許容を直接検証していない。

## Solution
- 結論は「経路依存」。
  - `--pipeline-stages`: 固定が必須（テンプレ外は拒否）。
  - `--pipeline-spec`: 任意の非空文字列が許容される（列挙制約なし）。
- 固定ID以外を使う場合は `--pipeline-spec` を使用し、allowed_stage_ids と stages の整合を運用で確認する。

## Verification
- codex-subagent pipeline 実行ログを確認（上記 run）。

## Tags
- codex-subagent
- pipeline
- stage_id
- pipeline_spec
- analysis
