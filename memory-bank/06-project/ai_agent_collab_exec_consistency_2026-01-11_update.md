# ai_agent_collab_exec_consistency 2026-01-11 (Update)

Problem:
- Check consistency between ai-agent-collaboration-exec docs, codex-subagent code/schemas, and tests; record pipeline run outcome.

Research:
- Docs: .claude/skills/ai-agent-collaboration-exec/SKILL.md L69-109, L92-96; execution_framework.md L63-86; pipeline_spec_template.json L1-10.
- Code: .claude/skills/codex-subagent/scripts/codex_exec.py L116-131 (patch paths + default stages), L908-961 (allowed_stage_ids applied only to next_stages).
- Schemas: .claude/skills/codex-subagent/schemas/pipeline_spec.schema.json L1-47; capsule.schema.json L4-73.
- Tests: tests/codex_subagent/test_pipeline_spec.py L165-189; tests/codex_subagent/test_tool_use_integration.py L30-134.
- Pipeline logs: .codex/sessions/codex_exec/auto/2026/01/11/run-20260111T103141-b5d100bf.jsonl and run-20260111T104835-1a841a67.jsonl.

Solution/Findings:
- pipeline_spec_template.json fields align with pipeline_spec.schema.json (stages array with id/instructions, allow_dynamic_stages, allowed_stage_ids).
- Capsule paths and patch rules are consistent across docs and code: /draft /critique /revise /facts /open_questions /assumptions.
- Default pipeline stages are draft/critique/revise in codex_exec/tests; ai-agent-collaboration-exec docs explicitly require --pipeline-spec when using execute/review/verify stages, so documented usage is consistent.
- Doc requirement to align allowed_stage_ids with used stages is not enforced for initial pipeline_spec stages in codex_exec (only enforced for dynamic next_stages). Consider adding validation or a test if strict enforcement is needed.

Verification:
- Ran: uv run pytest tests/codex_subagent/test_pipeline_spec.py --no-cov (pass).
- codex-subagent pipeline attempts timed out in draft stage (pipeline_run_id f706ff35-1006-41c4-a63f-09ab57e2fcdf @600s, 3fced875-3aa4-4f8c-91db-817ce3836dcb @900s).
