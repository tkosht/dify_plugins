# ai-agent-collaboration-exec Test Plan (2026-01-05)

## Purpose
- Evaluate the practical usability of the collaboration skill by running the full pipeline (draft/execute/review/revise/verify).
- Verify that required artifacts, capsule structure, and role boundaries are produced as specified.

## Scope
- Target repo: /home/devuser/workspace
- Skill spec: .claude/skills/ai-agent-collaboration-exec/SKILL.md
- References:
  - .claude/skills/ai-agent-collaboration-exec/references/execution_framework.md
  - .claude/skills/ai-agent-collaboration-exec/references/pipeline_spec_template.json
  - .claude/skills/ai-agent-collaboration-exec/references/subagent_prompt_templates.md
  - .claude/skills/ai-agent-collaboration-exec/references/contract_output.md

## Constraints
- No MCP tools.
- No external web access.
- No secrets or credentials.
- Avoid destructive commands.
- Allowed writes: docs/ai-agent-reviews/ and .codex/sessions/ only.

## Test Approach
- Validate generated artifacts and capsule content against the skill spec and references.
- Confirm role responsibilities, write scopes, and output paths are respected.
- Treat unspecified or environment-dependent items as Unknown and record them explicitly.

## Test Cases

### TC-01 Input Capture Completeness
- Intent: Ensure the skill captures all required inputs (objective, target paths, constraints, write scope, review_output_dir, required stages, test/CI requirements).
- Evidence: /draft contains a concise list of required inputs or artifacts that reflect them.
- Rationale: SKILL.md lists mandatory inputs; missing inputs reduce usability.

### TC-02 Role Responsibilities and Write Scopes
- Intent: Verify Executor/Reviewer/Verifier roles and allowed write scopes are defined and consistent with references.
- Evidence: Subagent prompts or pipeline docs include role definitions and write bounds.
- Rationale: execution_framework.md defines strict role separation and guardrails.

### TC-03 Pipeline Spec Coherence
- Intent: Confirm stages and allowed_stage_ids align and only required stages are included.
- Evidence: Generated pipeline spec (if used) shows matching stages and allowed_stage_ids; release stage only if required.
- Rationale: SKILL.md requires alignment and conditional release handling.

### TC-04 Capsule Structure and Patch Rules
- Intent: Validate capsule sections and patch constraints.
- Evidence: /draft, /critique, /revise are objects; /facts is an array of objects; /open_questions and /assumptions present.
- Rationale: Capsule rules are mandatory for pipeline integrity.

### TC-05 Subagent Prompt Conformance
- Intent: Ensure prompts follow the templates and include constraints (no secrets, no destructive commands, facts only).
- Evidence: Subagent prompts file reflects template fields and constraints.
- Rationale: subagent_prompt_templates.md defines required prompt structure.

### TC-06 Contract Output Completeness
- Intent: Confirm contract output includes change list, command list, test results, and failure next steps.
- Evidence: Contract output file contains all required sections.
- Rationale: contract_output.md mandates these fields for accountability.

### TC-07 Independent Review Artifact
- Intent: Verify review is independent, evidence-based, and written to the review output directory.
- Evidence: Review file exists under docs/ai-agent-reviews and includes findings and evidence.
- Rationale: execution_framework.md requires independent review with evidence.

### TC-08 Verify Stage Re-run Evidence
- Intent: Confirm verification re-runs tests and records results or failure analysis.
- Evidence: Pipeline spec verify instructions reference `docs/ai-agent-reviews/ai-agent-collaboration-exec_test_plan_2026-01-05.md`; /facts includes verify-stage test results and, if failed, a clear next step.
- Rationale: execution_framework.md and subagent prompts require re-run verification.

### TC-09 Logging and Artifact Locations
- Intent: Ensure logs and capsule paths match documented locations.
- Evidence: .codex/sessions/codex_exec/... contains run logs and capsule path; review artifacts in docs/ai-agent-reviews.
- Rationale: SKILL.md specifies log and capsule locations.

### TC-10 Timeout Handling and Re-run Policy
- Intent: Check timeout handling and retry limits are declared and followed.
- Evidence: Prompts or outputs mention retry limit and same-scope re-run policy.
- Rationale: execution_framework.md and subagent prompts specify timeout policy.

### TC-11 Constraint Adherence
- Intent: Confirm no MCP tools or external web access used; writes limited to allowed directories.
- Evidence: /facts or logs show only permitted paths; no external access recorded.
- Rationale: Task constraints are mandatory for evaluation integrity.

### TC-12 Optional Release Stage Gating
- Intent: Ensure release stage is included only if needed and aligned with allowed_stage_ids.
- Evidence: Pipeline spec either includes release explicitly or omits it with consistent allowed_stage_ids.
- Rationale: SKILL.md requires release stage alignment.

## Coverage Rationale
- Inputs and roles: SKILL.md (Inputs, Roles) and execution_framework.md (role guardrails).
- Pipeline and capsule: SKILL.md (Steps, Capsule rules) and pipeline_spec_template.json.
- Prompts and contract outputs: subagent_prompt_templates.md and contract_output.md.
- Policies: execution_framework.md (loop/exit, timeout, CI gating) and SKILL.md (quality policy).

## Unknowns / Notes
- Resolved: `codex` is available on PATH (`/home/devuser/workspace/node_modules/.bin/codex`).
- Resolved: `jsonschema` is available via `uv run python`.
- Timeout used in evaluation runs: 600s (per command). SKILL guidance still lists 360–420s.
- Repo test command example: `poetry run pytest -v .` (project_overview/auto_debug). No standard test command documented in README/Makefile/package.json.
- Release stage: not required for this evaluation (intentionally omitted from pipeline spec).
