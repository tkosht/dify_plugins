# gpt-5.3-codex vs gpt-5.3-codex-spark Substitutability Evaluation (xhigh, 2026-02-14)

## 0. Purpose
- Re-evaluate substitutability under practical default usage: reasoning effort `xhigh` (no `--profile fast`).

## 1. Protocol
- Runs: `36` (`6 tasks x 2 models x 3 repetitions`)
- Runtime flags: `--mode single --sandbox read-only --timeout 300 --json --no-log`
- Model switch only: `--model gpt-5.3-codex` / `--model gpt-5.3-codex-spark`
- Artifact root: `/home/devuser/workspace/memory-bank/06-project/context/codex_vs_spark_eval_xhigh_20260214_025806_artifacts`

## 2. Decision
- Final decision: **SUBSTITUTABLE**
- Quality ratio (`spark/codex`): `1.0246`
- Time ratio (`spark/codex`): `0.1795`

## 3. Model Metrics
- Codex quality: `84.200`
- Spark quality: `86.270`
- Codex mean time: `113.842s`
- Spark mean time: `20.440s`
- Codex hard-fail rate: `0.111`
- Spark hard-fail rate: `0.056`

## 4. Task-Level Summary
| Task | Codex median Q | Codex mean time(s) | Codex fail rate | Spark median Q | Spark mean time(s) | Spark fail rate |
|---|---:|---:|---:|---:|---:|---:|
| DEV-01 | 84.34 | 73.58 | 0.000 | 85.96 | 15.76 | 0.000 |
| DEV-02 | 85.66 | 121.37 | 0.000 | 85.96 | 17.23 | 0.000 |
| BUG-01 | 83.26 | 129.12 | 0.333 | 85.42 | 28.29 | 0.333 |
| BUG-02 | 84.34 | 104.99 | 0.000 | 88.36 | 17.11 | 0.000 |
| RES-01 | 84.34 | 105.89 | 0.000 | 85.96 | 21.48 | 0.000 |
| RES-02 | 83.26 | 148.10 | 0.333 | 85.96 | 22.76 | 0.000 |

## 5. Hard-Fail Details
- `BUG-01__codex__r1`: reasons=['out_of_scope_paths']
- `BUG-01__spark__r2`: reasons=['task_output_json_parse_error']
- `RES-02__codex__r3`: reasons=['out_of_scope_paths']

## 6. Slowest Runs (Top 5)
- `RES-02__codex__r1`: `176.300s`, quality=`83.26`
- `BUG-01__codex__r3`: `152.322s`, quality=`83.26`
- `RES-02__codex__r2`: `135.748s`, quality=`85.66`
- `RES-02__codex__r3`: `132.266s`, quality=`0.00`
- `DEV-02__codex__r2`: `131.889s`, quality=`85.66`

## 7. Notes
- This report supersedes the fast-profile benchmark for practical day-to-day judgment.
- Out-of-scope hard-fails were evaluated using strict path matching; evidence path strings with `:line` suffix were treated as out-of-scope by this rubric.
