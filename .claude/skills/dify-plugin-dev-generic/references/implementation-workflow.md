# Generic Implementation Workflow

## Objective
- 任意リポジトリでDifyプラグイン変更を安全に実装し、検証可能な状態にする。

## Step 0: Confirm scaffold completeness for new plugins
1. 新規plugin作成時は次を先に揃える。
   - `_assets/icon.svg`
   - `README.md`
   - `PRIVACY.md`
   - `.env.example`
   - `requirements.txt`
2. `manifest.yaml` から参照する補助ファイルを先に確定する。

## Step 1: Update metadata and schemas
1. `manifest.yaml` を更新する。
2. provider/tool/model/strategy YAML を更新する。
3. `manifest.yaml` の参照パスと実ファイル存在を確認する。

## Step 2: Update runtime code
1. 対応するPythonエントリポイントを更新する。
2. 例外処理を明確化する。
3. 機密情報を出力しない。

## Step 3: Update tests
1. 対応する test ディレクトリを特定する。
2. 正常系と失敗系を追加する。
3. 既知不具合の回帰ケースを追加する。
4. baselineと同等責務のテスト深度を確認する。

## Step 4: Run checks
```bash
uv run ruff check <plugin-path> <test-path>
uv run pytest -q --no-cov <test-path>
uv run pytest -q <test-path>
dify plugin package <plugin-path>
diff -rq <baseline-plugin-path> <plugin-path>
diff -rq <baseline-test-path> <test-path>
```

プロジェクト標準コマンドがある場合はそちらを優先する。

## Step 5: Confirm implementation readiness
1. 設計時に定義した受け入れ条件を満たす。
2. packageが成功している。
3. lint/test/package結果を添えて報告できる。
4. coverage失敗時は閾値問題と機能回帰問題を分離して説明できる。
5. 既知制約と残リスクを説明できる。
