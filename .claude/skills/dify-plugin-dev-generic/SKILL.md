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
3. `references/source-map.md` の探索パターンを使い、ローカル情報源を集める。
4. 新規plugin作成時は同種baselineとの比較評価を必須化する。
5. 実装後は対象pluginのlint/test/package評価を実行し、結果を記録する。

## Required Checks

1. 開発回帰ゲートを実行する。

```bash
uv run ruff check <plugin-path> <test-path>
uv run pytest -q --no-cov <test-path>
uv run pytest -q <test-path>
```

2. リリース準備ゲートを実行する。

```bash
dify plugin package <plugin-path>
diff -rq <baseline-plugin-path> <plugin-path>
diff -rq <baseline-test-path> <test-path>
```

3. 判定ルールを固定する。
   - `pytest --no-cov` の成功を機能回帰合格とする。
   - coverage付きテスト失敗が全体閾値由来か対象機能由来かを切り分けて報告する。
   - package失敗時は release readiness 不合格とする。

## Guardrails

- 秘密情報をログや成果物へ出力しない。
- `manifest.yaml` と参照YAML群の不整合を残さない。
- `author` と識別子ルールを `manifest` / `provider` 間で一致させる。
- 新規pluginでは配布補助ファイル群（README/PRIVACY/.env.example/requirements/icon）を満たすまで完成扱いにしない。
- 推測で操作せず、ローカルに存在する仕様・コード・テストを根拠にする。
- リリース検証の危険設定（例: 署名検証無効化）は検証環境限定で扱う。

## References

- `references/design-workflow.md`
- `references/implementation-workflow.md`
- `references/release-verification-workflow.md`
- `references/release-readiness-checklist.md`
- `references/baseline-parity-evaluation.md`
- `references/source-map.md`
