# Repo Release Readiness Checklist

## Objective
- 「動く」だけでなく「配布可能」な完成状態を定義する。

## Mandatory files for new plugins
1. `_assets/icon.svg`
2. `README.md`
3. `PRIVACY.md`
4. `.env.example`
5. `requirements.txt`

## Manifest and schema integrity
1. `manifest.yaml` の `plugins.*` が実在YAMLのみを参照している。
2. `manifest.yaml` と provider YAML の `author` が整合している。
3. `manifest.yaml` に `privacy: PRIVACY.md` を設定している。
4. provider/tool/model/strategy YAML と Python実装の責務が一致している。
5. packager required fields（`Resource.Memory`, `Meta.Version`, `Meta.Arch`, `Meta.Runner.Language`, `Meta.Runner.Version`, `Meta.Runner.Entrypoint`, `CreatedAt`）が欠落していない。

## Verification gates
1. `uv run ruff check ...` が成功する。
2. `uv run pytest -q --no-cov ...` が成功する。
3. `dify plugin package ./app/<plugin>` が成功する。
4. installまで確認できる場合は `.difypkg` 導入を確認する。
5. サブエージェント評価時は `parent_gate_results.txt` を正本ログとして保存する。
6. サブエージェント評価時は `sha256sum -c SHA256SUMS.txt` が成功する。
7. `handoff_SHA256SUMS.txt` が存在する場合は `sha256sum -c handoff_SHA256SUMS.txt` も成功する。
8. サブエージェント評価時は required artifacts（`subagent_result_final.json`, `parent_gate_results.txt`, `repro_evidence.txt`, `SHA256SUMS.txt`, `hash_check_results.txt`）を保存する。
9. サブエージェント評価時は events/stderr ログ（`subagent_events*.jsonl`, `subagent_stderr*.log`）を保存する。
10. サブエージェント評価時は再現性推奨セット（`run_metadata.env`, `subagent_prompt_codex.txt`, `TASK_SPEC.md`, source snapshot, `.difypkg`, `handoff_file_set.txt`）を保存する。

## One-pass execution order
1. fail-fast preflight: `uv run ruff check ...` と `dify plugin package ...` を先行実行する。
2. preflight成功後に `uv run pytest -q --no-cov ...` と `uv run pytest -q ...` を実行する。
3. サブエージェント評価時は最後に hash検証（`SHA256SUMS`, optional `handoff_SHA256SUMS`）を実行する。
4. diff判定では `__pycache__`, `.pytest_cache`, `.venv`, 一時ラッパ生成物を除外する。
5. baseline 比 `test-depth ratio >= 0.40` を確認する。
6. 上記シーケンスで hard-fail が1件でも出たら未完成と判定する。

## Runtime contract gates (LLM providers)
1. abstract methods が未解消でない（`__abstractmethods__` が空）。
2. `LLMResultChunkDelta` の必須項目を満たす chunk を生成できる。
3. chunk再現は signature-adaptive で実行する。
4. payload strictness（bool coercion / json_schema要件 / verbosity配置）が期待契約と一致する。
5. Dify runtime integration（`ModelProvider` / `Plugin(DifyPluginEnv)`）が対象リポジトリ契約と整合する。
6. chunk再現証跡で `NO_CHUNK_METHOD` が出ない。
7. payload strictness 再現証跡で `BOOL_STRICT_FAIL` が出ない。

## Completion rule
1. package失敗が1件でもあれば未完成。
2. 必須補助ファイルが1つでも欠ければ未完成。
3. coverage閾値失敗は、機能回帰失敗と分離して評価する。
4. Runtime contract gates の失敗が1件でもあれば未完成。
5. `ruff check` が失敗していれば未完成。
6. required artifacts 欠落または hash 検証失敗なら未完成。
7. subagent自己報告のみで合格判定しない。parent gate結果を正本とする。
8. payload strictness（`bool` / `response_format.strict` / `json_schema`）再現証跡に fail が1件でもあれば未完成。
9. packager required fields 欠落が1件でもあれば未完成。
10. `NO_CHUNK_METHOD` または `BOOL_STRICT_FAIL` が1件でも出たら未完成。
11. `test-depth ratio < 0.40` なら未完成。
12. baseline主要責務のテストが欠落する場合は未完成。
