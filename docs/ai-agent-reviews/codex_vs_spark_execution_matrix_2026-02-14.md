# Codex vs Spark Execution Matrix (2026-02-14)

## Dimensions
- Tasks: `DEV-01`, `DEV-02`, `BUG-01`, `BUG-02`, `RES-01`, `RES-02`
- Models: `gpt-5.3-codex`, `gpt-5.3-codex-spark`
- Repetitions: `r1`, `r2`, `r3`

## Run IDs
- Pattern: `{task_id}__{model_alias}__{rep}`
- `model_alias`:
  - `codex` -> `gpt-5.3-codex`
  - `spark` -> `gpt-5.3-codex-spark`

Total run IDs: 36

```
DEV-01__codex__r1
DEV-01__codex__r2
DEV-01__codex__r3
DEV-01__spark__r1
DEV-01__spark__r2
DEV-01__spark__r3
DEV-02__codex__r1
DEV-02__codex__r2
DEV-02__codex__r3
DEV-02__spark__r1
DEV-02__spark__r2
DEV-02__spark__r3
BUG-01__codex__r1
BUG-01__codex__r2
BUG-01__codex__r3
BUG-01__spark__r1
BUG-01__spark__r2
BUG-01__spark__r3
BUG-02__codex__r1
BUG-02__codex__r2
BUG-02__codex__r3
BUG-02__spark__r1
BUG-02__spark__r2
BUG-02__spark__r3
RES-01__codex__r1
RES-01__codex__r2
RES-01__codex__r3
RES-01__spark__r1
RES-01__spark__r2
RES-01__spark__r3
RES-02__codex__r1
RES-02__codex__r2
RES-02__codex__r3
RES-02__spark__r1
RES-02__spark__r2
RES-02__spark__r3
```

## Command Template
```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode single \
  --task-type "$TASK_TYPE" \
  --sandbox read-only \
  --timeout 240 \
  --model "$MODEL" \
  --json \
  --prompt "$(cat $PROMPT_FILE)"
```

## Actual Run Profile (2026-02-14)
- For the completed 36-run benchmark, the command used:
  - `--timeout 90`
  - `--profile fast`
  - `--no-log`
- Artifact root:
  - `memory-bank/06-project/context/codex_vs_spark_eval_fast_20260214_014027_artifacts`

## Actual Run Profile (xhigh Re-run, 2026-02-14)
- For the practical/default benchmark, the command used:
  - `--timeout 300`
  - no `--profile` override (default reasoning effort: `xhigh`)
  - `--no-log`
- Artifact root:
  - `memory-bank/06-project/context/codex_vs_spark_eval_xhigh_20260214_025806_artifacts`
- This xhigh run is the authoritative result for substitutability judgement.
