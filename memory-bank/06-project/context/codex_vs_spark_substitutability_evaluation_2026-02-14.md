# gpt-5.3-codex vs gpt-5.3-codex-spark Substitutability Evaluation (2026-02-14)

> Note: This document summarizes the fast-profile benchmark.  
> For practical/default usage (`reasoning_effort=xhigh`), refer to `memory-bank/06-project/context/codex_vs_spark_substitutability_evaluation_2026-02-14_xhigh.md`.

## 0. Purpose
- Evaluate whether `gpt-5.3-codex-spark` can substitute `gpt-5.3-codex` in routine development/bugfix/research tasks using codex-cli subagents.
- Execution date (JST): 2026-02-14

## 1. Protocol
- Runs: 36 (`6 tasks x 2 models x 3 repetitions`)
- Wrapper: `.claude/skills/codex-subagent/scripts/codex_exec.py`
- Runtime flags: `--mode single --sandbox read-only --timeout 90 --profile fast --json --no-log`
- Models: `gpt-5.3-codex`, `gpt-5.3-codex-spark`
- Artifacts: `memory-bank/06-project/context/codex_vs_spark_eval_fast_20260214_014027_artifacts`

## 2. Decision
- Final decision: **SUBSTITUTABLE**
- Quality ratio (`spark/codex`): `1.0031`
- Time ratio (`spark/codex`): `0.4459`

## 3. Model Metrics
- Codex quality: `86.090`
- Spark quality: `86.360`
- Codex mean time: `31.340s`
- Spark mean time: `13.975s`
- Codex hard-fail rate: `0.000`
- Spark hard-fail rate: `0.056`

## 4. Task-Level Summary
| Task | Codex median Q | Codex mean time(s) | Spark median Q | Spark mean time(s) |
|---|---:|---:|---:|---:|
| DEV-01 | 85.96 | 25.99 | 85.96 | 10.20 |
| DEV-02 | 88.36 | 24.14 | 85.96 | 12.77 |
| BUG-01 | 85.42 | 32.52 | 85.96 | 15.95 |
| BUG-02 | 85.42 | 33.66 | 88.36 | 11.31 |
| RES-01 | 85.96 | 25.20 | 85.96 | 10.63 |
| RES-02 | 85.42 | 46.52 | 85.96 | 22.98 |

## 5. Hard-Fail Details
- `BUG-01__spark__r3`: reasons=['task_output_json_parse_error']

## 6. Slowest Runs (Top 5)
- `RES-02__codex__r3`: `63.742s`, quality=`84.34`
- `RES-02__codex__r1`: `41.825s`, quality=`85.42`
- `BUG-01__codex__r2`: `37.877s`, quality=`85.42`
- `BUG-02__codex__r1`: `35.959s`, quality=`85.42`
- `BUG-02__codex__r2`: `34.568s`, quality=`85.42`

## 7. Notes / Limits
- This benchmark intentionally used `--profile fast` for both models to complete 36 runs under practical time constraints.
- Quality scoring combines wrapper heuristic + schema validity + evidence coverage; it is suitable for relative comparison in this controlled runbook, not absolute product quality certification.
