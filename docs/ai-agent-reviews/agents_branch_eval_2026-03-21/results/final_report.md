# AGENTS Branch Evaluation Report

- date: 2026-03-21
- parent_runs: 60
- subagent_runs: 4

## Parent Evaluation
- arm_alpha: mean=4.725, median=5.0, runs=30
- arm_beta: mean=4.846, median=5.0, runs=30

## Hard Fail Counts

## Review Recall
- arm_alpha: 0.133
- arm_beta: 0.667

## Package Pass Rate
- arm_alpha: 1.0
- arm_beta: 1.0

## One-Pass Pass Rate
- arm_alpha: 1.0
- arm_beta: 1.0

## Active Gate Pass Counts
- arm_alpha: 15
- arm_beta: 15

## Subagent Confirmation
- BUG-01__arm_alpha__subagent: subagent_rc=0, ruff=0, pytest_no_cov=0, package=passed, changed_files=0
- OPS-01__arm_alpha__subagent: subagent_rc=0, ruff=None, pytest_no_cov=None, package=not_required, changed_files=0
- BUG-01__arm_beta__subagent: subagent_rc=0, ruff=0, pytest_no_cov=0, package=passed, changed_files=0
- OPS-01__arm_beta__subagent: subagent_rc=0, ruff=None, pytest_no_cov=None, package=not_required, changed_files=0

## Verdict
- non_inferior: True
- strictly_better: True
- better_or_equal: True
- strict_wins: mean_overall, review_recall
- strict_losses: none
- baseline_alias: arm_alpha
- candidate_alias: arm_beta
- tiebreaker_triggered: False
- alias mapping: arm_alpha=main, arm_beta=docs/agent-instructions-simplify

## Notes
- package gate requires `DIFY_BIN` or a PATH-resolved `dify` binary and now runs package/sign/verify for edit tasks.
- repo-wide fixed instruction reduction is tracked separately in `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md`.
