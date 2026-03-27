ROLE: Parent agent orchestration for AGENTS branch comparison / __TASK_ID__
DATE: 2026-03-19

OBJECTIVE
- In the worktree at `__WORKTREE__`, perform an independent read-only confirmation run for `OPS-01`.
- Check currentness-sensitive local claims conservatively and mark unverifiable points as `不明`.

SCOPE
- Target repo: `__WORKTREE__`
- Target paths:
  - `app/openai_gpt5_responses/README.md`
  - `app/openai_gpt5_responses/models/llm/_position.yaml`
  - `app/openai_gpt5_responses/models/llm/*.yaml`
  - `app/openai_gpt5_responses/.env.example`

CONSTRAINTS
- Branch alias: `__BRANCH_ALIAS__`
- Read-only. Do not edit files.
- Official OpenAI sources only if external verification is possible in your runtime.
- Do not inspect or print any real `.env` file.
- Parent will run authoritative checks after the pipeline.

REQUIRED OUTPUTS
1. `/draft` local claims to verify
2. `/critique` current/stale/unknown conclusions with evidence
3. `/facts` URLs, local file evidence, and blocked points
4. `/revise` concise final recommendation

REVIEW OUTPUT DIR
- `__OUTPUT_DIR__`
