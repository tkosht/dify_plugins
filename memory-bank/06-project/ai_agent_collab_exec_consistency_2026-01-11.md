# ai_agent_collab_exec_consistency 2026-01-11

Problem:
- Check consistency between ai-agent-collaboration-exec docs and codex-subagent code/tests.

Research:
- Evidence from SKILL.md L89-106, pipeline_spec_template.json L1-10, execution_framework.md L70-85.
- Code: codex_exec.py L117-130, L632-645, L755-782.
- Schemas: pipeline_spec.schema.json L1-47, capsule.schema.json L47-73.
- Tests: test_pipeline_spec.py L62-88, L165-170, L187-189; test_pipeline_schema.py L16-35.

Solution/Findings:
- Pipeline spec template fields (allow_dynamic_stages, allowed_stage_ids, stages with id/instructions) match pipeline_spec schema and loader tests.
- Capsule patch rules largely align with capsule schema and patch allowed prefixes, but SKILL.md does not mention open_questions/assumptions paths that are allowed by code/tests.
- Stage names in execution_framework and SKILL examples use review/execute/verify, while default pipeline stages and pipeline-stages validation are draft/critique/revise; using pipeline_spec avoids the default restriction but docs should clarify this to prevent confusion.

Verification:
- codex-subagent pipeline run (pipeline_run_id 01312020-06aa-4f80-baf8-6707785e04dd) completed with draft/critique/revise stage results and captured findings.
