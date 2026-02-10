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

## Verification gates
1. `uv run ruff check ...` が成功する。
2. `uv run pytest -q --no-cov ...` が成功する。
3. `dify plugin package <plugin-root>` が成功する。
4. install確認可能な環境では `.difypkg` 導入結果を確認する。

## Completion rule
1. package失敗が1件でもあれば未完成。
2. 必須補助ファイルが1つでも欠ければ未完成。
3. coverage閾値失敗は機能回帰失敗と切り分けて扱う。
