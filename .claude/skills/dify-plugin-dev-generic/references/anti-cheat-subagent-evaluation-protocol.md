# Anti-Cheat Subagent Evaluation Protocol

## Objective
- サブエージェントが baseline 実装や履歴を流用せず、与えられた仕様だけで実装・評価していることを検証する。
- 採点は parent gate 実行結果を正本とし、再現証跡の整合（ハッシュ）まで担保する。

## When to apply
- 新規pluginをサブエージェントに実装させ、baselineとの parity 評価を行うタスクで適用する。

## Step 1: Prepare isolated workspace
1. 作業用ディレクトリを新規作成する。
2. 最小構成のみ配置する。
   - target plugin scaffold
   - target tests scaffold
   - 実行に必要なSkillファイル
   - task spec
3. baseline plugin/tests/difypkg を workspace に配置しない。

## Step 2: Enforce prompt-level constraints
1. サブエージェントへ以下を明示する。
   - `git log/show` など履歴参照禁止
   - 外部URL/外部ネットワーク参照禁止（明示許可がある場合のみ例外）
   - 作業ディレクトリ外アクセス禁止
   - baseline 名称とファイル群の直接参照禁止
2. 不明項目は推測せず `不明` と記載させる。

## Step 3: Run subagent
1. `codex-subagent` などの実行器を isolated workspace で実行する。
2. 実行ログとJSON結果を保存する。

## Step 3.5: Persist artifacts and verify integrity
1. required authoritative artifacts を保存する。
   - `subagent_result_final.json`
   - `parent_gate_results.txt`
   - `repro_evidence.txt`
   - `SHA256SUMS.txt`
   - `hash_check_results.txt`
   - `subagent_events.jsonl` または `subagent_events_rerun.jsonl`
   - `subagent_stderr.log` または `subagent_stderr_rerun.log`
2. reproducibility 推奨追加セットを保存する。
   - `run_metadata.env`
   - `subagent_prompt_codex.txt`
   - `TASK_SPEC.md`
   - `subagent_report.json`
   - `subagent_last_message.txt`
   - `subagent_exit_code.txt`
   - `subagent_status.txt`
   - `openai_responses_provider_source_snapshot.tar.gz`
   - `openai_responses_provider.difypkg`
   - `handoff_file_set.txt`
   - `handoff_SHA256SUMS.txt`（存在する場合）
   - `handoff_hash_check_results.txt`（存在する場合）
3. ハッシュを検証する。
```bash
sha256sum -c <artifact_dir>/SHA256SUMS.txt
test -f <artifact_dir>/handoff_SHA256SUMS.txt && sha256sum -c <artifact_dir>/handoff_SHA256SUMS.txt
```
4. ハッシュ検証が失敗した場合は評価を中断し、証跡不整合として不合格にする。
5. `hash_check_results.txt` に検証コマンドと結果を保存する。

## Step 4: Verify anti-cheat evidence
1. baseline artifact absent
```bash
test ! -e <isolated>/app/<baseline_plugin>
test ! -e <isolated>/tests/<baseline_plugin>
ls -1 <isolated> | rg '<baseline_plugin>.*\\.difypkg' && exit 1 || true
```

2. history/remote absence
```bash
cd <isolated>
git rev-list --all --count
git remote -v
```

3. leakage scan
```bash
rg -n '<baseline_plugin>|git[[:space:]]+log|git[[:space:]]+show' <target_plugin_path> <target_test_path>
```
`rg` の `EXIT_CODE=1`（no match）は pass として扱う。

## Step 5: Run quality and parity gates
最終評価の前に fail-fast preflight を実施する。
```bash
uv run ruff --version
uv run pytest --version
dify --version
uv run ruff check <target_plugin_path> <target_test_path>
dify plugin package <target_plugin_path>
```

preflight成功後に full gate を実行する。
```bash
uv run pytest -q --no-cov <target_test_path>
uv run pytest -q <target_test_path>
sha256sum -c <artifact_dir>/SHA256SUMS.txt
test -f <artifact_dir>/handoff_SHA256SUMS.txt && sha256sum -c <artifact_dir>/handoff_SHA256SUMS.txt
diff -rq --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.venv' <baseline_plugin_path> <target_plugin_path>
diff -rq --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.venv' <baseline_test_path> <target_test_path>
wc -l <baseline_test_path>/*.py <target_test_path>/*.py
```

gate結果の正本は parent が実行した出力ログ（`parent_gate_results.txt`）とする。
subagentの自己報告値は参考情報として扱う。

## Step 6: Report template
1. isolation setup facts
2. anti-cheat evidence results
3. gate results (ruff/no-cov/coverage/package) from parent authoritative logs
4. parity score breakdown
5. fail reasons and required follow-up actions
6. artifact paths and hash verification result
7. required artifacts completeness check
8. events/stderr artifacts completeness check
9. reproducibility recommended set completeness check
10. parent authoritative verdict
