# Codex vs Spark Scoring Rubric (2026-02-14)

## Hard-Fail Conditions
- Non-JSON output
- JSON parse error
- Missing required keys for task schema
- `timed_out=true` or `success=false`
- Output includes file paths outside allowed scope

Any hard-fail run gets quality score `0`.

## Per-Run Quality Score (0-100)
- `heuristic_score` (0-5) from `codex_exec` -> normalized to 0-60
  - formula: `(heuristic_score / 5.0) * 60`
- `schema_score` (0/20)
  - required keys + required list/object types + non-empty summary fields
- `evidence_score` (0-20)
  - 20: >=3 evidence entries and all entries reference allowed files
  - 10: 1-2 valid evidence entries
  - 0: no evidence or invalid evidence

`run_quality = heuristic_component + schema_score + evidence_score`

## Task-Level Aggregation
- For each task/model: median of 3 runs

## Model-Level Aggregation
- `model_quality`: average of 6 task medians
- `model_time`: average execution time across 18 runs
- `hard_fail_rate`: hard-fail runs / 18

## Substitutability Decision
- `quality_ratio = spark_quality / codex_quality`
- `time_ratio = spark_time / codex_time`

Decision:
- `quality_ratio >= 0.95` and `time_ratio <= 0.80` -> `SUBSTITUTABLE`
- `quality_ratio >= 0.92` and `time_ratio <= 0.90` -> `CONDITIONALLY_SUBSTITUTABLE`
- otherwise -> `NOT_SUBSTITUTABLE`

Penalty:
- If `spark_hard_fail_rate - codex_hard_fail_rate > 0.10`, downgrade one level.
