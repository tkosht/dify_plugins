# ai-agent-collaboration-exec Pipeline Practicality Notes (2026-01-05)
Tags: ai-agent-collaboration-exec, codex-subagent, pipeline, capsule-schema, jsonschema, PATH

## Problem
Pipeline runs for ai-agent-collaboration-exec failed to complete due to schema validation and timeout issues.

## Research
- Reviewed skill spec and references.
- Checked codex-subagent capsule schema requirements.
- Attempted pipeline runs and inspected run logs.

## Solution
- Enforced capsule patch rules: /facts must be array of objects; /draft,/critique,/revise must remain objects with nested keys.
- Ensure codex binary is on PATH (e.g., node_modules/.bin).
- Run codex_exec via uv-managed python with jsonschema installed.
- Use per-stage timeouts that allow file reading and output formatting.

## Verification
- Log evidence:
  - Capsule schema error: .codex/sessions/codex_exec/auto/2026/01/05/run-20260105T094235-d05a323f.jsonl
  - Stage timeout: .codex/sessions/codex_exec/auto/2026/01/05/run-20260105T095901-30c7f0a8.jsonl
  - Missing codex binary: .codex/sessions/codex_exec/auto/2026/01/05/run-20260105T085758-e1bac9db.jsonl

## Update (2026-01-05)
- Pipeline draft stage succeeded with 420s but execute stage timed out.
  - Log: .codex/sessions/codex_exec/auto/2026/01/05/run-20260105T150815-376bef30.jsonl
- Capsule store file + light pipeline still timed out at draft stage (300s).
  - Log: .codex/sessions/codex_exec/auto/2026/01/05/run-20260105T152156-4bee043f.jsonl
- `--profile fast` triggers regex error ("unbalanced parenthesis") due to a bug in codex_exec.
  - Repro: uv run python .claude/skills/codex-subagent/scripts/codex_exec.py --mode single --profile fast --prompt "test"

## Log Analysis (2026-01-08)
- Timeout is not caused by shell commands: commands finish within 30ms, while stage execution_time reaches 300-420s.
  - Evidence: run-20260105T150815-376bef30.jsonl (draft exec_time 416.7s, max command 19ms)
  - Evidence: run-20260105T095901-30c7f0a8.jsonl (draft exec_time 180s, max command 29ms)
- Execute stage timed out without any shell command execution, indicating LLM response wait as the bottleneck.
  - Evidence: run-20260105T150815-376bef30.jsonl (execute timed_out true, 0 parsed commands)

## Fix Applied (2026-01-08)
- codex_exec fast-profile regex bug fixed (unbalanced parenthesis resolved).
  - File: .claude/skills/codex-subagent/scripts/codex_exec.py
  - Verification: --profile fast no longer errors; timeout occurs only when timeout_seconds is too small.

## Pipeline Recomposition (2026-01-08)
- Full-quality pipeline completed by splitting into draft/execute/review specs to reduce per-run latency while preserving overall phases.
  - Draft run log: .codex/sessions/codex_exec/auto/2026/01/07/run-20260107T155020-c2ca4448.jsonl
  - Execute run log: .codex/sessions/codex_exec/auto/2026/01/07/run-20260107T160317-b7a56ec0.jsonl
  - Review run log: .codex/sessions/codex_exec/auto/2026/01/07/run-20260107T161732-ef4ff0da.jsonl

## Pipeline Re-run After Open Question Resolution (2026-01-08)
- Draft/Execute/Review specs re-run successfully to incorporate resolved inputs.
  - Draft run log: .codex/sessions/codex_exec/auto/2026/01/07/run-20260107T165204-57441a11.jsonl
  - Execute run log: .codex/sessions/codex_exec/auto/2026/01/07/run-20260107T165843-057abe2a.jsonl
  - Review run log: .codex/sessions/codex_exec/auto/2026/01/07/run-20260107T171423-48235d3e.jsonl

## Verification (2026-01-08)
- Pipeline spec validation test executed and passed.
  - Command: uv run pytest tests/codex_subagent/test_pipeline_spec.py --no-cov

## Update (2026-01-08)
- System python lacks jsonschema; run codex_exec via `uv run`.
  - Error log: .codex/sessions/codex_exec/auto/2026/01/08/run-20260108T000254-91b81f34.jsonl (profile normal not found)
- `--profile normal` is not a valid config; omit `--profile` for default (normal) behavior.
- Review pipeline completed after rerun without profile.
  - Log: .codex/sessions/codex_exec/auto/2026/01/08/run-20260108T001928-58af7f92.jsonl
