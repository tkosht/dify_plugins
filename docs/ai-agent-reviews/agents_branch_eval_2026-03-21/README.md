# AGENTS Branch Evaluation 2026-03-21

## Purpose
- Re-run the `main` vs `docs/agent-instructions-simplify` comparison on the latest local Codex environment.
- Preserve the original non-inferiority design, then add package/release-discipline metrics that can support a strict superiority claim.

## Evaluation Shape
- Stage 1: `6` primary tasks x `2` branches x `5` repetitions = `60` parent runs.
- Subagent confirmation: `BUG-01` and `OPS-01` on both branches = `4` runs.
- Stage 2 tie-breaker: if stage 1 is still non-inferior but not strictly better, run `REL-01` and `REV-02` for `20` additional parent runs.

## Entry Points
- Evaluation design: `task_catalog.md`
- Runner: `bin/agents_branch_eval.py`
- Prompts: `prompts/*.md`
- Schemas: `schemas/*.json`
- Seed diffs: `fixtures/*.patch`

## Required Environment
- `codex` must be available on `PATH`
- `uv` must be available on `PATH`
- `DIFY_BIN` must point to an executable `dify` binary for any run that includes edit tasks
- Existing signing keys are expected at `plugins/custom_plugins.private.pem` and `plugins/custom_plugins.public.pem`
- Parent `codex exec` runs intentionally disable repo-configured `serena`, `codex_mcp`, `context7`, and `sequential-thinking` MCP servers via CLI config overrides so non-interactive exec mode is not polluted by interactive-only tool behavior.
- Parent and subagent runs use Codex `danger-full-access` execution because this environment cannot initialize `bwrap` for nested `workspace-write` / `read-only` shell actions. Read-only vs write-scope compliance is enforced by diff-based scoring instead.

## Outputs
- Tracked summaries:
  - `results/preflight.json`
  - `results/parent_score_summary.md`
  - `results/parent_score_summary.json`
  - `results/subagent_summary.json`
  - `results/final_report.md`
- Ignored detailed artifacts:
  - `results/parent_runs/`
  - `results/subagent_runs/`
- Local scratch snapshots such as `results_probe_*` and `results_full*` are intentionally out of scope for the retained repo snapshot.

## Re-run
- Full rerun with auto tie-breaker:
  - `DIFY_BIN=/abs/path/to/dify python3 bin/agents_branch_eval.py all`
- Primary matrix only:
  - `DIFY_BIN=/abs/path/to/dify python3 bin/agents_branch_eval.py parent`
- Manual tie-breaker only:
  - `DIFY_BIN=/abs/path/to/dify python3 bin/agents_branch_eval.py parent --tasks REL-01,REV-02`
- Re-score existing local manifests:
  - `python3 bin/agents_branch_eval.py score`
