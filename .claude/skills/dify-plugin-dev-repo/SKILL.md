---
name: dify-plugin-dev-repo
description: "このリポジトリのDifyプラグイン（app/sharepoint_list, app/openai_gpt5_responses, app/gpt5_agent_strategies, app/nanobana）を設計・実装・検証・パッケージングする。Use when requests involve manifest/provider/tools/models/strategies changes, app/* Python実装、tests/* 更新、Remote Debugや.difypkgインストール障害の切り分け、baselineとの完成度比較、またはmemory-bank履歴を根拠にしたDifyプラグイン開発。"
---

# Dify Plugin Dev Repo

## Purpose

- このリポジトリに存在するDifyプラグインの変更を、設計から実装・検証・リリース確認まで一貫して進める。
- `app/*` の実装事実と `memory-bank/*` の過去検証履歴を統合し、再発防止を前提に開発する。

## Workflow Selector

1. 対象プラグインと変更範囲を確定する。
2. 次のサブワークフローから必要なものだけ読む。
   - `references/design-workflow.md`: 仕様設計、YAML契約設計、変更計画を固める。
   - `references/implementation-workflow.md`: Python/YAML実装とテスト追加・実行を進める。
   - `references/release-verification-workflow.md`: Remote Debug、package/install、既知障害の切り分けを行う。
   - `references/release-readiness-checklist.md`: リリース成立条件を満たしているかを機械的に確認する。
   - `references/baseline-parity-evaluation.md`: 既存baselineとの比較評価と合格判定を行う。
   - `.claude/skills/dify-plugin-dev-generic/references/anti-cheat-subagent-evaluation-protocol.md`: subagent parity 評価時の反チート手順を適用する。
   - `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_011017.md`: canonical evaluation evidence を確認する。
   - `memory-bank/06-project/context/openai_responses_provider_subagent_handoff_2026-02-12_011017.md`: canonical handoff file set を確認する。
3. `references/source-map.md` を参照し、根拠となるローカルファイルを特定する。
4. 新規plugin作成時は baseline parity 評価を必須化する。
5. 変更後は対応するlint/test/package評価を実行し、結果と残課題を報告する。
6. LLM provider 実装では、abstract/chunk/payload の再現証跡を必ず残す。
7. サブエージェント評価では parent gate 結果を唯一の採点根拠とし、subagent自己報告は参考情報扱いにする。
8. 一発合格を狙うタスクでは one-pass quality gate（hard-fail 0件）を必須化する。
9. 品質優先案件では `ai-agent-collaboration-exec` の Executor/Reviewer/Verifier 協調パイプラインを使う。

## Plugin Map

| Plugin | Root | Typical Editable Files | Test Scope |
| --- | --- | --- | --- |
| sharepoint_list | `app/sharepoint_list` | `manifest.yaml`, `provider/sharepoint_list.*`, `tools/*`, `internal/*` | `tests/sharepoint_list` |
| openai_gpt5_responses | `app/openai_gpt5_responses` | `manifest.yaml`, `provider/openai_gpt5.*`, `models/llm/*`, `internal/*` | `tests/openai_gpt5_responses` |
| gpt5_agent_strategies | `app/gpt5_agent_strategies` | `manifest.yaml`, `provider/gpt5_agent.*`, `strategies/*`, `internal/*` | `tests/gpt5_agent_strategies` |
| nanobana | `app/nanobana` | `manifest.yaml`, `provider/nanobana.*`, `tools/nanobana.*` | 必要に応じて `tests/nanobana` を新設 |

## Required Checks

1. 実行環境 preflight を実行する。

```bash
uv run ruff --version
uv run pytest --version
dify --version
```

2. 開発回帰ゲートを実行する。

```bash
uv run ruff check app/<plugin> tests/<plugin>
uv run pytest -q --no-cov tests/<plugin>
uv run pytest -q tests/<plugin>
```

3. 証跡整合ゲート（サブエージェント評価時のみ）を実行する。

```bash
sha256sum -c <artifact_dir>/SHA256SUMS.txt
test -f <artifact_dir>/handoff_SHA256SUMS.txt && sha256sum -c <artifact_dir>/handoff_SHA256SUMS.txt
```

サブエージェント評価時の required artifacts は次を必須化する。
- `subagent_result_final.json`
- `parent_gate_results.txt`
- `repro_evidence.txt`
- `SHA256SUMS.txt`
- `hash_check_results.txt`
- `subagent_events.jsonl` または `subagent_events_rerun.jsonl`
- `subagent_stderr.log` または `subagent_stderr_rerun.log`

再現性向上の推奨追加セット（生成物スナップショット含む）は次を保存する。
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
- `handoff_SHA256SUMS.txt`
- `handoff_hash_check_results.txt`

4. リリース準備ゲートを実行する。

```bash
dify plugin package ./app/<plugin>
diff -rq --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.venv' app/<baseline_plugin> app/<plugin>
diff -rq --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.venv' tests/<baseline_plugin> tests/<plugin>
```

5. 判定ルールを固定する。
   - 親エージェントの gate 実行結果（`ruff` / `pytest` / `package` / `diff` / `wc -l`）を authoritative verdict とする。
   - subagent の自己申告結果は矛盾時に採点根拠として採用しない。
   - `sha256sum -c` 失敗時は証跡改ざんまたは欠落として不合格とする。
   - `handoff_SHA256SUMS.txt` が存在する場合、`handoff_SHA256SUMS` の検証失敗を証跡不整合として不合格とする。
   - `ruff check` 失敗時は release readiness 不合格とする。
   - `pytest --no-cov` が通り、対象機能のテストが通ることを回帰合格とする。
   - coverage 付き `pytest` がリポジトリ全体閾値で失敗した場合、機能回帰失敗とは分離して報告する。
   - `dify plugin package` が失敗した時点で release readiness は不合格とする。
   - packager required fields（`Resource.Memory`, `Meta.Version`, `Meta.Arch`, `Meta.Runner.Language`, `Meta.Runner.Version`, `Meta.Runner.Entrypoint`, `CreatedAt`）に欠落がある場合は不合格とする。
   - LLM providerで abstract method 未解消、chunk schema 不整合、payload strictness 不整合が1件でもあれば不合格とする。
   - `__abstractmethods__` が空でない場合は runtime parity 不合格とする。
   - chunk再現証跡は signature-adaptive で実施し、最終的に `NO_CHUNK_METHOD` が出た場合は runtime parity 不合格とする。
   - Dify runtime integration 不整合（`ModelProvider` / `Plugin(DifyPluginEnv)` 契約差異）があれば runtime parity 不合格とする。
   - payload strictness（`bool` / `response_format.strict` / `json_schema`）の再現証跡で fail が1件でもあれば不合格とする。
   - payload strictness 再現で `BOOL_STRICT_FAIL` が出た場合は不合格とする。
   - `test-depth ratio < 0.40` の場合は hard-fail とする。
   - baseline主要責務（entrypoint/error, llm stream flag, messages, payloads, bool coercion, provider runtime/schema）を欠く場合は test depth 不足として不合格とする。

6. One-Pass Quality Gate（初回で合格水準超えを狙う運用）を固定する。
   - fail-fast preflight として `ruff` と `dify plugin package` を先行実行する。
   - preflight成功後に `pytest --no-cov` / `pytest` /（subagent評価時）`sha256sum -c` を同一環境で連続実行する。
   - diff判定では `__pycache__`, `.pytest_cache`, 一時ラッパ/venv生成物を除外してノイズ差分を採点根拠にしない。
   - hard-fail 条件が1件でも発火した場合は「未完成」として実装フェーズに戻す。
   - スコアは最低80点を合格目安、運用目標は90点以上を推奨する。
   - parent gate結果とsubagent自己報告が矛盾した場合、parent gate結果のみで再判定する。
   - `ai-agent-collaboration-exec` 運用時は pipeline spec / subagent prompts / contract output を成果物として保存する。

`openai_gpt5_responses` と `gpt5_agent_strategies` をまたぐ変更では、次を優先する。

```bash
uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies
uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies
uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies
```

## Guardrails

- 秘密情報（APIキー、トークン、`.env` の実値）を出力しない。
- `manifest.yaml` の `plugins.*` に列挙したYAMLを実ファイルと同期させる。
- `author` の整合性を `manifest.yaml` と provider YAML で維持する。
- 変更範囲と同じ責務のテストを必ず更新または追加する。
- 新規pluginでは `_assets/icon.svg`, `README.md`, `PRIVACY.md`, `.env.example`, `requirements.txt` を原則必須とする。
- package成功前の成果物を「完成」と判定しない。
- baseline比でテスト深度が大幅不足（line-count sanity check不合格）の場合、合格判定しない。
- サブエージェント評価時は anti-cheat 証跡（隔離・履歴・リーク検証）を必ず提出する。
- サブエージェント評価時は required artifacts（`subagent_result_final.json`, `parent_gate_results.txt`, `repro_evidence.txt`, `SHA256SUMS.txt`, `hash_check_results.txt`）を保存し、ハッシュ整合を必ず検証する。
- サブエージェント評価時は events/stderr ログ（`subagent_events*.jsonl`, `subagent_stderr*.log`）を保存する。
- サブエージェント評価時は推奨追加セット（`handoff_SHA256SUMS.txt`, `handoff_hash_check_results.txt`, `handoff_file_set.txt`, source snapshot, `.difypkg`）を保存し、再現性を担保する。
- one-pass運用では「self-reportのみで成功扱い」を禁止し、parent authoritative gate でのみ完了判定する。
- one-pass運用では hard-fail 0件 + release readiness満点（lint/package成功）を満たすまで最終化しない。
- 推測で仕様を埋めず、参照元ファイルを明記して判断する。

## References

- `references/design-workflow.md`
- `references/implementation-workflow.md`
- `references/release-verification-workflow.md`
- `references/release-readiness-checklist.md`
- `references/baseline-parity-evaluation.md`
- `.claude/skills/dify-plugin-dev-generic/references/anti-cheat-subagent-evaluation-protocol.md` (for subagent parity evaluations)
- `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_011017.md`
- `memory-bank/06-project/context/openai_responses_provider_subagent_handoff_2026-02-12_011017.md`
- `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_0006.md`
- `.claude/skills/dify-plugin-dev-generic/references/openai_responses_provider_subagent_handoff_2026-02-12_0006.md`
- `references/source-map.md`
- `docs/ai-agent-reviews/openai_responses_provider_collab_pipeline_spec_2026-02-12.json`
- `docs/ai-agent-reviews/openai_responses_provider_subagent_prompts_2026-02-12.md`
- `docs/ai-agent-reviews/openai_responses_provider_contract_output_2026-02-12.md`
