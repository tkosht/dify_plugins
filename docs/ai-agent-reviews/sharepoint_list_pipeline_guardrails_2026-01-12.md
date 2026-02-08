# sharepoint_list pipeline guardrails (2026-01-12)

目的
- codex-subagent pipeline の JSON スキーマ逸脱を再発させないための最小ガードレールを残す。

観測された失敗パターン（ログ根拠）
- stage_result parse failed: "capsule_patch" required property missing
- stage_result parse failed: next_stages 要素が id 必須条件を満たさない
- stage_result の JSON が構文不正（余分な } など）で JSONDecodeError

対策（実施済み/推奨）
- 1ステージあたり capsule_patch は **1件のみ** に制限する。
- stage_result は **単一行 JSON** を強制し、文字列内の改行/\n を禁止する。
- next_stages を使わない（allow_dynamic_stages=false を採用）。
- ステージ出力を小さく保ち、ネストを最小化する（長い配列・大量のオブジェクトを避ける）。
- パイプライン spec 検証: `uv run pytest tests/codex_subagent/test_pipeline_spec.py --no-cov`

使用した安定構成
- pipeline spec: docs/ai-agent-reviews/sharepoint_list_pipeline_spec_2026-01-12_v3.json
- pipeline prompt: docs/ai-agent-reviews/sharepoint_list_pipeline_prompt_2026-01-12_v3.txt

