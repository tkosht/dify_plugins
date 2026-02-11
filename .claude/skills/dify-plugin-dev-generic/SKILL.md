---
name: dify-plugin-dev-generic
description: "任意リポジトリ向けにDifyプラグインを設計・実装・検証・パッケージングする。Use when requests involve creating/updating plugin manifest/provider/tools/models, implementing Python runtime, adding tests, handling Remote Debug/.difypkg release flow, troubleshooting install/package errors, or evaluating completion parity against an existing baseline plugin."
---

# Dify Plugin Dev Generic

## Purpose

- Difyプラグイン開発の共通ワークフローを、リポジトリ非依存で適用する。
- 設計、実装、リリース検証を分離し、必要な手順だけをロードして実行する。

## Workflow Selector

1. まず対象リポジトリの plugin root を特定する（`manifest.yaml` があるディレクトリ）。
2. タスクに応じて次の参照を選ぶ。
   - `references/design-workflow.md`
   - `references/implementation-workflow.md`
   - `references/release-verification-workflow.md`
   - `references/release-readiness-checklist.md`
   - `references/baseline-parity-evaluation.md`
   - `references/anti-cheat-subagent-evaluation-protocol.md`
   - `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_011017.md` (canonical evidence)
   - `memory-bank/06-project/context/openai_responses_provider_subagent_handoff_2026-02-12_011017.md` (canonical handoff file set)
   - `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_0006.md` (historical strict-failure evidence)
   - `references/openai_responses_provider_subagent_parity_evaluation_2026-02-11.md` (fallback evidence)
   - `references/openai_responses_provider_subagent_handoff_2026-02-11_182702.md` (skill source handoff)
   - `references/openai_responses_provider_subagent_handoff_2026-02-12_0006.md` (latest strict-failure handoff)
   - `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_file_set.txt` (reproducibility file set index)
3. `references/source-map.md` の探索パターンを使い、ローカル情報源を集める。
4. 新規plugin作成時は同種baselineとの比較評価を必須化する。
5. 実装後は対象pluginのlint/test/package評価を実行し、結果を記録する。
6. LLM provider 実装では、abstract/chunk/payload の再現証跡を提出する。
7. サブエージェント評価では parent gate 結果を唯一の採点根拠とし、subagent自己報告は参考情報扱いにする。
8. 一発合格を狙うタスクでは one-pass quality gate（hard-fail 0件）を必須化する。
9. 品質優先案件では `ai-agent-collaboration-exec` を使い、Executor/Reviewer/Verifier の協調パイプラインで実行する。

## Required Checks

1. 実行環境 preflight を実行する。

```bash
uv run ruff --version
uv run pytest --version
dify --version
```

2. 開発回帰ゲートを実行する。

```bash
uv run ruff check <plugin-path> <test-path>
uv run pytest -q --no-cov <test-path>
uv run pytest -q <test-path>
```

3. 反チート評価ゲート（サブエージェント評価時のみ）を実行する。

- `references/anti-cheat-subagent-evaluation-protocol.md` に従い、隔離環境・baseline除外・禁止制約・リーク検証を実施する。

4. 証跡整合ゲート（サブエージェント評価時のみ）を実行する。

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
- `handoff_SHA256SUMS.txt`
- `handoff_hash_check_results.txt`
- `handoff_file_set.txt`
- `openai_responses_provider_source_snapshot.tar.gz`
- `openai_responses_provider.difypkg`
- `run_metadata.env`
- `subagent_prompt_codex.txt`
- `TASK_SPEC.md`

5. リリース準備ゲートを実行する。

```bash
dify plugin package <plugin-path>
diff -rq <baseline-plugin-path> <plugin-path>
diff -rq <baseline-test-path> <test-path>
```

6. 判定ルールを固定する。
   - 親エージェントの gate 実行結果（`ruff` / `pytest` / `package` / `diff` / `wc -l`）を authoritative verdict とする。
   - subagent の自己申告結果は矛盾時に採点根拠として採用しない。
   - `sha256sum -c` 失敗時は証跡改ざんまたは欠落として不合格とする。
   - `handoff_SHA256SUMS.txt` が存在する場合、`handoff_SHA256SUMS` の検証失敗を証跡不整合として不合格とする。
   - `ruff check` 失敗時は release readiness 不合格とする。
   - `pytest --no-cov` の成功を機能回帰合格とする。
   - coverage付きテスト失敗が全体閾値由来か対象機能由来かを切り分けて報告する。
   - package失敗時は release readiness 不合格とする。
   - packager required fields（`Resource.Memory`, `Meta.Version`, `Meta.Arch`, `Meta.Runner.Language`, `Meta.Runner.Version`, `Meta.Runner.Entrypoint`, `CreatedAt`）に欠落がある場合は不合格とする。
   - LLM providerで abstract method 未解消、chunk schema 不整合、payload strictness 不整合が1件でもあれば不合格とする。
   - `__abstractmethods__` が空でない場合は runtime parity 不合格とする。
   - chunk再現証跡で `NO_CHUNK_METHOD` が出た場合は runtime parity 不合格とする。
   - chunk再現証跡は signature-adaptive で実施し、引数不一致の `TypeError` は手順不備として再試行する。最終再試行で `NO_CHUNK_METHOD` または chunk生成不能なら不合格とする。
   - Dify runtime integration 不整合（`ModelProvider` / `Plugin(DifyPluginEnv)` 契約差異）があれば runtime parity 不合格とする。
   - payload strictness（`bool` / `response_format.strict` / `json_schema`）の再現証跡で fail が1件でもあれば不合格とする。
   - payload strictness 再現で `BOOL_STRICT_FAIL` が出た場合は不合格とする。
   - `test-depth ratio < 0.40` の場合は hard-fail とする。
   - baseline主要責務（entrypoint/error, llm stream flag, messages, payloads, bool coercion, provider runtime/schema）を欠く場合は test depth 不足として不合格とする。

7. One-Pass Quality Gate（初回で合格水準超えを狙う運用）を固定する。
   - fail-fast preflight として `ruff` と `dify plugin package` を先行実行する。
   - preflight成功後に `pytest --no-cov` / `pytest` /（subagent評価時）`sha256sum -c` を同一環境で連続実行する。
   - diff判定では `__pycache__`, `.pytest_cache`, 一時ラッパ/venv生成物を除外してノイズ差分を採点根拠にしない。
   - hard-fail 条件が1件でも発火した場合は「未完成」として実装フェーズに戻す。
   - スコアは最低80点を合格目安、運用目標は90点以上を推奨する。
   - parent gate結果とsubagent自己報告が矛盾した場合、parent gate結果のみで再判定する。
   - `ai-agent-collaboration-exec` 運用時は pipeline spec / subagent prompts / contract output を成果物として保存する。

## Guardrails

- 秘密情報をログや成果物へ出力しない。
- `manifest.yaml` と参照YAML群の不整合を残さない。
- `author` と識別子ルールを `manifest` / `provider` 間で一致させる。
- 新規pluginでは配布補助ファイル群（README/PRIVACY/.env.example/requirements/icon）を満たすまで完成扱いにしない。
- 推測で操作せず、ローカルに存在する仕様・コード・テストを根拠にする。
- リリース検証の危険設定（例: 署名検証無効化）は検証環境限定で扱う。
- baseline比でテスト深度が大幅不足（line-count sanity check不合格）の場合、合格判定しない。
- サブエージェント評価では anti-cheat 証跡（隔離・履歴・リーク検証）を必ず提出する。
- サブエージェント評価では required artifacts（`subagent_result_final.json`, `parent_gate_results.txt`, `repro_evidence.txt`, `SHA256SUMS.txt`, `hash_check_results.txt`）を保存し、ハッシュ整合を必ず検証する。
- サブエージェント評価では events/stderr ログ（`subagent_events*.jsonl`, `subagent_stderr*.log`）を保存する。
- サブエージェント評価では推奨追加セット（`handoff_SHA256SUMS.txt`, `handoff_hash_check_results.txt`, `handoff_file_set.txt`, source snapshot, `.difypkg`）を保存し、再現性を担保する。
- one-pass運用では「self-reportのみで成功扱い」を禁止し、parent authoritative gate でのみ完了判定する。
- one-pass運用では hard-fail 0件 + release readiness満点（lint/package成功）を満たすまで最終化しない。

## References

- `references/design-workflow.md`
- `references/implementation-workflow.md`
- `references/release-verification-workflow.md`
- `references/release-readiness-checklist.md`
- `references/baseline-parity-evaluation.md`
- `references/anti-cheat-subagent-evaluation-protocol.md`
- `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_011017.md`
- `memory-bank/06-project/context/openai_responses_provider_subagent_handoff_2026-02-12_011017.md`
- `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_0006.md`
- `references/openai_responses_provider_subagent_parity_evaluation_2026-02-11.md`
- `references/openai_responses_provider_subagent_parity_evaluation_2026-02-10.md`
- `references/openai_responses_provider_subagent_handoff_2026-02-11_182702.md`
- `references/openai_responses_provider_subagent_handoff_2026-02-12_0006.md`
- `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_file_set.txt`
- `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_SHA256SUMS.txt`
- `references/source-map.md`
- `docs/ai-agent-reviews/openai_responses_provider_collab_pipeline_spec_2026-02-12.json`
- `docs/ai-agent-reviews/openai_responses_provider_subagent_prompts_2026-02-12.md`
- `docs/ai-agent-reviews/openai_responses_provider_contract_output_2026-02-12.md`
