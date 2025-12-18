# Difyプラグイン開発 トラブルシューティング（2025-12-12）

## KEYWORDS: dify, plugin, troubleshooting, plugin_unique_identifier, bad signature, FORCE_VERIFYING_SIGNATURE, manifest.yaml, provider yaml, difypkg, remote debug
## DOMAIN: external-research|dify|plugin-development|troubleshooting
## PRIORITY: HIGH
## WHEN: プラグインのパッケージ/インストール/デバッグで詰まったとき
## VERIFIED_AT: 2025-12-12
## RELATED:
- `memory-bank/07-external-research/dify_plugin_development_hub.md`
- `memory-bank/07-external-research/dify_plugin_development_research_2025-12-12.md`

## 0. まず見る（切り分けの順）
1. **どのフェーズで失敗したか**を固定する
   - packaging（`dify plugin package`）か
   - install（Dify UIに `.difypkg` を入れる）か
   - remote debug（Debug pluginで一覧に出る/動かない）か
2. エラーメッセージがある場合は、その文言で本ファイル内検索する

---

## 1. インストール時: `plugin_unique_identifier is not valid`
### 症状
- インストール時に以下のエラーが出る:
  - `PluginDaemonBadRequestError: plugin_unique_identifier is not valid`

### 原因（公式FAQの指示）
- `author` が要件に合っていない（GitHub IDとの整合が必要）。

### 対処（公式FAQの手順）
1. プラグインプロジェクト配下の `manifest.yaml` の `author` を **GitHub ID** に修正
2. `/provider` 配下の `.yaml` の `author` も **GitHub ID** に修正
3. 再度パッケージングし、生成された `.difypkg` を入れ直す

### 再発防止
- `author` は **manifest と provider YAML で一致**させる。
- Marketplace公開を考える場合、命名や識別子の整合は早い段階で固定する。

出典: [Publishing FAQ](https://docs.dify.ai/en/develop-plugin/publishing/faq/faq)

---

## 2. インストール時: `bad signature`（署名検証エラー）
### 症状
- インストール時に以下の趣旨の例外が出る:
  - `plugin verification has been enabled, and the plugin you want to install has a bad signature`

### 原因（公式FAQの前提）
- Dify側でプラグイン検証が有効になっており、未レビュー等のプラグインが弾かれる。

### 対処（公式FAQの手順）
1. `/docker/.env` の末尾に以下を追加
   - `FORCE_VERIFYING_SIGNATURE=false`
2. Difyサービスを再起動

```bash
cd docker
docker compose down
docker compose up -d
```

### 重要な注意（公式FAQに明記）
- 上記設定により **Marketplace未掲載（未レビュー）のプラグインもインストール可能**になり、**セキュリティリスク**がある。
- **テスト/サンドボックス環境での導入が推奨**される。

出典: [Publishing FAQ](https://docs.dify.ai/en/develop-plugin/publishing/faq/faq)

---

## 3. Remote Debug: プラグインがデバッグ一覧に出ない/接続できない
### 症状
- `python -m main` 等で起動しているのに、Dify側でデバッグプラグインとして見えない/使えない。

### 典型原因
- `.env` の `INSTALL_METHOD=remote` や remote install のホスト/キー設定が誤っている。
- Dify UI 側で表示される Host Address / API Key（debug key）を転記できていない。

### 対処
- DifyのPlugin Managementで Debug Plugin を開き、表示される情報を `.env` に反映する。
- `.env` 変数名がページにより異なるため、以下どちらの形式を前提にしているか確認する:

**A) URL一括**
```dotenv
INSTALL_METHOD=remote
REMOTE_INSTALL_URL=debug.dify.ai:5003
REMOTE_INSTALL_KEY=<YOUR_DEBUG_KEY>
```
出典: [Plugin Debugging](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/remote-debug-a-plugin)

**B) HOST/PORT分割**
```dotenv
INSTALL_METHOD=remote
REMOTE_INSTALL_HOST=debug-plugin.dify.dev
REMOTE_INSTALL_PORT=5003
REMOTE_INSTALL_KEY=your_debug_key
```
出典: [Develop Flomo Plugin](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/develop-flomo-plugin)

---

## 4. Packaging: `dify plugin package` が失敗する
### 症状
- `dify plugin package ...` がエラーで終了し、`.difypkg` が生成されない。

### 典型原因（manifest仕様に明記）
- `manifest.yaml` の `plugins.*` に列挙した YAML ファイルが **実在しない**（指定パスのファイルがパッケージ内にない）。

### 対処
- `manifest.yaml` の `plugins.*` に列挙したパスに、実際に該当YAMLが存在することを確認する。

出典: [Plugin Info by Manifest](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/plugin-info-by-manifest)

---

## Sources（参照一覧・参照日: 2025-12-12）
- [Publishing FAQ](https://docs.dify.ai/en/develop-plugin/publishing/faq/faq)
- [Plugin Debugging](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/remote-debug-a-plugin)
- [Develop Flomo Plugin](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/develop-flomo-plugin)
- [Plugin Info by Manifest](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/plugin-info-by-manifest)

