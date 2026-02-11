# Generic Release Readiness Checklist

## Objective
- 任意リポジトリでも配布可能な完成条件を固定する。

## Mandatory files for new plugins
1. `_assets/icon.svg`
2. `README.md`
3. `PRIVACY.md`
4. `.env.example`
5. `requirements.txt`

## Manifest and schema integrity
1. `manifest.yaml` の `plugins.*` が実在YAMLのみを参照する。
2. `manifest.yaml` と provider YAML の `author` が整合する。
3. `privacy` 設定が実ファイルと整合する。
4. provider/tool/model/strategy YAML と Python実装が一致する。
5. packager required fields（`Resource.Memory`, `Meta.Version`, `Meta.Arch`, `Meta.Runner.Language`, `Meta.Runner.Version`, `Meta.Runner.Entrypoint`, `CreatedAt`）が欠落していない。

## Verification gates
1. `uv run ruff check ...` が成功する。
2. `uv run pytest -q --no-cov ...` が成功する。
3. `dify plugin package <plugin-root>` が成功する。
4. install確認可能な環境では `.difypkg` 導入結果を確認する。
5. サブエージェント評価時は `parent_gate_results.txt` を正本ログとして保存する。
6. サブエージェント評価時は `sha256sum -c SHA256SUMS.txt` が成功する。
7. `handoff_SHA256SUMS.txt` が存在する場合は `sha256sum -c handoff_SHA256SUMS.txt` も成功する。
8. サブエージェント評価時は required artifacts（`subagent_result_final.json`, `parent_gate_results.txt`, `repro_evidence.txt`, `SHA256SUMS.txt`, `hash_check_results.txt`）を保存する。
9. サブエージェント評価時は events/stderr ログ（`subagent_events*.jsonl`, `subagent_stderr*.log`）を保存する。
10. サブエージェント評価時は再現性推奨セット（`run_metadata.env`, `subagent_prompt_codex.txt`, `TASK_SPEC.md`, source snapshot, `.difypkg`, `handoff_file_set.txt`）を保存する。

## One-pass excellence gate
1. fail-fast preflight として `ruff` / `package` を先行実行する。
2. preflight成功後に `pytest --no-cov` / `pytest` を同一環境で連続実行する。
3. サブエージェント評価時は最後に hash検証（`SHA256SUMS`, optional `handoff_SHA256SUMS`）を実行する。
4. diff判定では `__pycache__`, `.pytest_cache`, `.venv`, 一時ラッパ生成物を除外する。
5. baseline 比 `test-depth ratio >= 0.40` を確認する。
6. one-pass運用では上記シーケンスが全成功であること。
7. hard-fail 条件（lint/package/runtime integration/evidence integrity/test-depth）を0件にする。
8. 採点は最低80点を合格目安、運用目標は90点以上とする。
9. subagent自己報告は参考のみとし、parent gate結果のみで合否を判定する。

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
3. coverage閾値失敗は機能回帰失敗と切り分けて扱う。
4. Runtime contract gates の失敗が1件でもあれば未完成。
5. `ruff check` が失敗していれば未完成。
6. required artifacts 欠落または hash 検証失敗なら未完成。
7. subagent自己報告のみで合格判定しない。parent gate結果を正本とする。
8. one-pass運用で hard-fail が1件でもある場合は未完成。
9. payload strictness（`bool` / `response_format.strict` / `json_schema`）再現証跡に fail が1件でも未完成。
10. packager required fields 欠落が1件でもあれば未完成。
11. `NO_CHUNK_METHOD` または `BOOL_STRICT_FAIL` が1件でも出たら未完成。
12. `test-depth ratio < 0.40` なら未完成。
13. baseline主要責務のテストが欠落する場合は未完成。
