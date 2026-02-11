# OpenAI Responses Provider Collaboration Prompts (2026-02-12)

## Parent Integrated Prompt
```text
ROLE: Parent agent orchestration for openai_responses_provider quality uplift
DATE: 2026-02-12

OBJECTIVE
- Improve dify-plugin-dev-generic and dify-plugin-dev-repo so that subagent-driven development reaches release-ready quality.
- Enforce parent-authoritative verdict and hard-fail zero policy.

SCOPE
- Target repo: /home/devuser/workspace
- Target paths:
  - .claude/skills/dify-plugin-dev-generic/**
  - .claude/skills/dify-plugin-dev-repo/**
  - docs/ai-agent-reviews/**

CONSTRAINTS
- No secrets exposure.
- No speculative claims.
- Keep authoritative evidence from:
  - memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_011017.md
  - memory-bank/06-project/context/openai_responses_provider_subagent_handoff_2026-02-12_011017.md
  - memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/*

REQUIRED OUTPUTS
1) Updated skill/references with hard-fail rules:
   - packager required fields missing
   - unresolved abstract methods
   - NO_CHUNK_METHOD
   - BOOL_STRICT_FAIL
   - test-depth ratio < 0.40
2) Collaboration artifacts:
   - pipeline spec JSON
   - subagent prompts
   - contract output
3) Verification logs from parent gates.

CAPSULE PATCH RULES
- /facts must be an array of objects.
- /draft /critique /revise must stay objects.
- /open_questions and /assumptions are arrays.

PIPELINE DESIGN REQUIREMENT
- Do not copy default pipeline blindly.
- Use initial stages: draft, execute, review.
- Add next_stages only when evidence requires revise/verify.

TEST DESIGN REQUIREMENT
- Run fail-fast preflight: ruff + package.
- Run full gates: pytest --no-cov, pytest, diff, wc, hash checks (SHA256SUMS + optional handoff_SHA256SUMS).
- Parent authoritative gate is the only verdict source.
```

## Executor Prompt
```text
ROLE: Executor
TASK: Apply planned edits to skill files and collaboration artifacts.
WRITE SCOPE:
- .claude/skills/dify-plugin-dev-generic/**
- .claude/skills/dify-plugin-dev-repo/**
- docs/ai-agent-reviews/**
RULES:
- Record commands and evidence in /facts.
- If a hard-fail condition remains, do not mark complete.
- Keep diff-noise exclusions (__pycache__, .pytest_cache, .venv) in parity instructions.
```

## Reviewer Prompt
```text
ROLE: Reviewer
TASK: Independently review edits and detect gaps against authoritative evidence.
READ SCOPE:
- Updated files in .claude/skills/**
- memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_011017.md
- memory-bank/06-project/context/openai_responses_provider_subagent_handoff_2026-02-12_011017.md
- parent_gate_results.txt / repro_evidence.txt in 20260212_011017 artifacts
RULES:
- Record only fact-based findings in /critique.
- If parent/self-report mismatch exists, enforce parent verdict.
- Ensure signature-adaptive chunk repro instructions are present.
```

## Verifier Prompt
```text
ROLE: Verifier
TASK: Re-run required checks and validate final readiness.
CHECKS:
- uv run pytest tests/codex_subagent/test_pipeline_spec.py --no-cov
- Structured grep checks for hard-fail keywords in updated skill files.
- JSON validation for pipeline spec.
RULES:
- Append verification evidence to /facts.
- If any hard-fail condition remains, return status=needs_revision.
```
