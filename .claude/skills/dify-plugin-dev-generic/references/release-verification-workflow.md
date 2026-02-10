# Generic Release Verification Workflow

## Objective
- Difyプラグインのdebug/package/install経路を一般化して検証する。

## Step 1: Prepare Remote Debug settings
1. Dify UI の Debug Plugin 画面で接続情報を取得する。
2. plugin側 `.env` に設定する。
3. URL一括形式とHOST/PORT分割形式のどちらかをプロジェクト規約に合わせる。
4. 新規pluginでは補助ファイルの存在を先に確認する。
   - `_assets/icon.svg`, `README.md`, `PRIVACY.md`, `.env.example`, `requirements.txt`

## Step 2: Run plugin process
```bash
cd <plugin-root>
python -m main
```

## Step 3: Package plugin
```bash
dify plugin package <plugin-root>
```

package失敗時は release readiness 不合格とする。

## Step 4: Install `.difypkg`
1. Dify Plugin Management からローカルファイルとして導入する。
2. インストールログを記録する。

## Step 5: Troubleshoot common issues
1. `plugin_unique_identifier is not valid`
   - `manifest.yaml` と provider YAML の `author` を GitHub ID で一致させる。
2. `bad signature`
   - self-host検証環境では `FORCE_VERIFYING_SIGNATURE=false` を使って再起動する。
   - 本番環境では署名検証を有効化する。
3. package失敗
   - `manifest.yaml` の `plugins.*` と実在YAMLの不一致を解消する。
   - `_assets` や icon の欠落を解消する。
4. debug接続失敗
   - UI表示の Host/Key を再反映する。

## Step 6: Finalize release verification
1. package/install/debug結果を記録する。
2. バージョン互換性と制約を残す。
3. セキュリティ上の暫定設定を戻す。
4. `references/release-readiness-checklist.md` を全項目確認する。
5. 新規pluginは `references/baseline-parity-evaluation.md` で比較評価する。
