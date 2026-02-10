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

## Verification gates
1. `uv run ruff check ...` が成功する。
2. `uv run pytest -q --no-cov ...` が成功する。
3. `dify plugin package ./app/<plugin>` が成功する。
4. installまで確認できる場合は `.difypkg` 導入を確認する。

## Completion rule
1. package失敗が1件でもあれば未完成。
2. 必須補助ファイルが1つでも欠ければ未完成。
3. coverage閾値失敗は、機能回帰失敗と分離して評価する。
