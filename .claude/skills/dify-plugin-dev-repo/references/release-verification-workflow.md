# Repo Release Verification Workflow

## Objective
- Remote Debug と `.difypkg` リリース経路を事実ベースで検証する。

## Step 1: Prepare runtime config
1. 対象pluginの `.env` を準備する。
2. Remote Debugで取得した `Host Address` と `API Key` を反映する。
3. 方式差異に注意する。
   - `REMOTE_INSTALL_URL` 形式
   - `REMOTE_INSTALL_HOST` + `REMOTE_INSTALL_PORT` 形式
4. 新規pluginでは配布補助ファイルの有無を先に確認する。
   - `_assets/icon.svg`, `README.md`, `PRIVACY.md`, `.env.example`, `requirements.txt`

## Step 2: Run local plugin process
```bash
cd app/<plugin>
python -m main
```

## Step 3: Package and install
```bash
dify plugin package ./app/<plugin>
```

生成された `.difypkg` を Dify Plugin Management からローカルファイルとして導入する。
packageが失敗した場合はこの時点で release readiness を不合格とする。

## Step 4: Troubleshoot known failures
1. `plugin_unique_identifier is not valid`
   - `manifest.yaml` と `provider/*.yaml` の `author` を GitHub ID で一致させる。
   - 再パッケージして再インストールする。
2. `bad signature`
   - self-hostでは `/docker/.env` に `FORCE_VERIFYING_SIGNATURE=false` を追加し再起動する。
   - テスト環境限定で扱い、本番では有効化を維持する。
3. `dify plugin package` 失敗
   - `manifest.yaml` の `plugins.*` が実在YAMLを指しているか確認する。
   - `_assets` ディレクトリと `icon.svg` が存在するか確認する。
4. Remote Debug接続失敗
   - Dify UIで表示される接続情報を `.env` へ再転記する。

## Step 5: Final release checklist
1. package結果とインストール結果を記録する。
2. バージョン、互換性、既知制約を明記する。
3. セキュリティ上の暫定設定を残していないことを確認する。
4. `references/release-readiness-checklist.md` を全項目確認する。
5. 新規pluginは `references/baseline-parity-evaluation.md` で比較評価する。
