# Contract Output: Plugin A/B Install-Launch Error Analysis

- Date: 2026-02-09
- Method: `ai-agent-collaboration-exec` (Team A: Plugin A, Team B: Plugin B)
- Constraint: no `codex mcp` usage

## Scope

- Plugin A: `openai_gpt5_responses.difypkg` install decode error
- Plugin B: `gpt5_agent_strategies.difypkg` launch-time subclass conflict

## Team Deliverables

1. Team A (Plugin A)
- Output file: `docs/ai-agent-reviews/gpt5_openai_install_error_review_2026-02-09_round1.md`
- Conclusion:
  - Install failure phase is confirmed at daemon response decode boundary.
  - Most plausible causes: install-time runtime exception and/or pycache artifact contamination.
  - Daemon traceback is required for root-cause closure.

2. Team B (Plugin B)
- Output file: `docs/ai-agent-reviews/gpt5_strategy_launch_error_review_2026-02-09_round1.md`
- Conclusion:
  - Root cause is high-confidence: two `AgentStrategy` subclasses visible in `gpt5_react.py` namespace.
  - Recommended primary fix is plugin-local import style change to keep one strategy class visible.

## Shared Observations

- Both `.difypkg` archives currently contain `__pycache__/*.pyc` entries.
- This is not sufficient to explain Plugin B launch failure, but should still be removed for deterministic packaging.

## Required Follow-up (decision-ready)

1. Apply Plugin B low-risk import fix and repackage/retest.
2. For Plugin A, remove pycache entries, repackage, retry install, and collect daemon traceback if decode error persists.
3. If Plugin B issue appears in other plugins, consider daemon loader hardening (`cls.__module__` filter).

## Evidence Pointers

- Team A run: `docs/ai-agent-reviews/gpt5_openai_install_error_pipeline_run_2026-02-09_retry1.json`
- Team B run: `docs/ai-agent-reviews/gpt5_strategy_launch_error_pipeline_run_2026-02-09.json`
- Team A prompt/spec: `docs/ai-agent-reviews/gpt5_openai_install_error_prompt_2026-02-09.txt`, `docs/ai-agent-reviews/gpt5_openai_install_error_pipeline_spec_2026-02-09.json`
- Team B prompt/spec: `docs/ai-agent-reviews/gpt5_strategy_launch_error_prompt_2026-02-09.txt`, `docs/ai-agent-reviews/gpt5_strategy_launch_error_pipeline_spec_2026-02-09.json`
