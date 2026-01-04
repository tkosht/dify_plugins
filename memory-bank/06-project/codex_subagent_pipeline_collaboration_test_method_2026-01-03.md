# codex-subagent pipeline 協調テスト方法

date: 2026-01-03
status: active
scope: pipeline 設計の TDD 実行手順

## 目的
- pipeline 協調の仕様（StageResult/patch/capsule/優先順位）をテストで固定する
- 実装前に失敗条件・境界条件を明確化する

## 実行コマンド（推奨）
### 単体（pipeline 仕様ユニットテスト）
```bash
uv run pytest \
  tests/codex_subagent/test_pipeline_spec.py \
  tests/codex_subagent/test_pipeline_patch.py \
  tests/codex_subagent/test_pipeline_execute.py \
  tests/codex_subagent/test_pipeline_cli.py \
  tests/codex_subagent/test_pipeline_prompt.py \
  tests/codex_subagent/test_pipeline_helpers.py \
  tests/codex_subagent/test_pipeline_schema.py \
  --no-cov
```

### 結合（codex exec を用いたスモーク）
```bash
CODEX_INTEGRATION=1 CODEX_INTEGRATION_MAX_ATTEMPTS=2 uv run pytest \
  tests/codex_subagent/test_pipeline_integration.py \
  --no-cov
```

### 失敗系（任意）
```bash
uv run pytest tests/codex_subagent/test_pipeline_spec.py::test_stage_result_error_rejects_nonempty_patch --no-cov
```

## 注意点
- `pyproject.toml` で `--cov=app` が既定のため、局所テストは `--no-cov` を付ける。
- 結合テストは LLM 出力の逸脱を考慮し、`CODEX_INTEGRATION_MAX_ATTEMPTS` で再実行回数を制御する（既定 2 回）。
- pipeline 実装が進んだらスモーク/失敗系/境界系を追加してテストを拡張する。

## 最低限のカバレッジ対象
- StageResult 制約（status/partial/capsule_patch）
- JSON Patch の許可パス/prefix
- capsule_hash の正規化（pipeline_run_id を除外）
- capsule_store の auto 切替と capsule_path 制約

## 次の拡張
- pipeline モードの実行スモーク（Draft→Critique→Revise）
- Schema 検証（StageSpec/StageResult/Capsule）
- 境界条件（max_stages/capsule_size_bytes）
