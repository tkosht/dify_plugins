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
3. `references/source-map.md` を参照し、根拠となるローカルファイルを特定する。
4. 新規plugin作成時は baseline parity 評価を必須化する。
5. 変更後は対応するlint/test/package評価を実行し、結果と残課題を報告する。

## Plugin Map

| Plugin | Root | Typical Editable Files | Test Scope |
| --- | --- | --- | --- |
| sharepoint_list | `app/sharepoint_list` | `manifest.yaml`, `provider/sharepoint_list.*`, `tools/*`, `internal/*` | `tests/sharepoint_list` |
| openai_gpt5_responses | `app/openai_gpt5_responses` | `manifest.yaml`, `provider/openai_gpt5.*`, `models/llm/*`, `internal/*` | `tests/openai_gpt5_responses` |
| gpt5_agent_strategies | `app/gpt5_agent_strategies` | `manifest.yaml`, `provider/gpt5_agent.*`, `strategies/*`, `internal/*` | `tests/gpt5_agent_strategies` |
| nanobana | `app/nanobana` | `manifest.yaml`, `provider/nanobana.*`, `tools/nanobana.*` | 必要に応じて `tests/nanobana` を新設 |

## Required Checks

1. 開発回帰ゲートを実行する。

```bash
uv run ruff check app/<plugin> tests/<plugin>
uv run pytest -q --no-cov tests/<plugin>
uv run pytest -q tests/<plugin>
```

2. リリース準備ゲートを実行する。

```bash
dify plugin package ./app/<plugin>
diff -rq app/<baseline_plugin> app/<plugin>
diff -rq tests/<baseline_plugin> tests/<plugin>
```

3. 判定ルールを固定する。
   - `pytest --no-cov` が通り、対象機能のテストが通ることを回帰合格とする。
   - coverage 付き `pytest` がリポジトリ全体閾値で失敗した場合、機能回帰失敗とは分離して報告する。
   - `dify plugin package` が失敗した時点で release readiness は不合格とする。

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
- 推測で仕様を埋めず、参照元ファイルを明記して判断する。

## References

- `references/design-workflow.md`
- `references/implementation-workflow.md`
- `references/release-verification-workflow.md`
- `references/release-readiness-checklist.md`
- `references/baseline-parity-evaluation.md`
- `references/source-map.md`
