# Dify プラグイン開発ガイド（最短で動かす）

このドキュメントは、Difyプラグインを **「remote debug → `.difypkg` 作成 → Difyに導入」** まで最短で到達するための手順書です。

より詳細な仕様・根拠・制約・落とし穴は、以下を参照してください。
- `memory-bank/07-external-research/dify_plugin_development_hub.md`

---

## 1. 前提
- Difyインスタンスにアクセスでき、Workspaceの **Plugin Management** を操作できる。
- 「Debug Plugin」機能から **Host Address / Debug Key（API Key）** を取得できる。

---

## 2. 開発フロー（最短）
### 2.1 Dify CLI を導入する
macOS（Homebrew）:

```bash
brew tap langgenius/dify
brew install dify

dify version
```

出典: [Initializing Development Tools](https://docs.dify.ai/plugins/quick-start/develop-plugins/initialize-development-tools)

---

### 2.2 雛形生成（init）
```bash
dify plugin init
```

出典: [Initializing Development Tools](https://docs.dify.ai/plugins/quick-start/develop-plugins/initialize-development-tools)

---

### 2.3 `manifest.yaml` を整備する（最低限）
- `manifest.yaml` には **メタデータ** と **plugins.*（拡張YAMLの一覧）** を書きます。
- `plugins.*` に列挙したYAMLが存在しないと packaging が失敗します。

出典: [Plugin Info by Manifest](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/plugin-info-by-manifest)

---

### 2.4 Remote Debug で動作確認する
1) Difyの plugin management 画面で Debug Plugin を開き、Host Address と Debug Key を取得

2) プラグインプロジェクトで `.env.example` を `.env` にコピーして設定

```bash
cp .env.example .env
```

`.env` の例（ページ間で表記差があるため注意）:

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

3) プラグインを起動

```bash
python -m main
```

出典: [Develop Flomo Plugin](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/develop-flomo-plugin)

---

### 2.5 `.difypkg` を作成して Dify に導入する
#### packaging
```bash
dify plugin package ./your_plugin_project
```

出典: [Release by File](https://docs.dify.ai/en/develop-plugin/publishing/marketplace-listing/release-by-file)

#### install
- Difyの plugin management ページで「Install Plugin → Via Local File」から `.difypkg` をアップロード（またはドラッグ&ドロップ）

出典: [Release by File](https://docs.dify.ai/en/develop-plugin/publishing/marketplace-listing/release-by-file)

---

## 3. Toolプラグイン最小構成（概念）
- Tool定義YAML（例: `flomo.yaml`）で `identity` / `credential_schema` / `tool_schema` を宣言
- Python実装は `dify_plugin` SDK を利用し、
  - `ToolProvider`（資格情報の検証）
  - `Tool`（ツール呼び出し処理）
  を実装

具体例: [Develop Flomo Plugin](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/develop-flomo-plugin)

---

## 4. OAuthが必要な場合（Tool）
- provider YAML に `oauth_schema` を追加
- Provider実装で `_oauth_get_authorization_url` / `_oauth_get_credentials` / `_oauth_refresh_credentials` を実装
- `manifest.yaml` に `meta.minimum_dify_version` を追加（例が提示されている）
- **client_secret を credentials に返さない**（公式明記）

出典: [Tool OAuth](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/tool-oauth)

---

## 5. よくあるエラー
### 5.1 `plugin_unique_identifier is not valid`
- `manifest.yaml` と `/provider` 配下の `.yaml` の **author を GitHub ID に揃える** → 再パッケージ → 再インストール

出典: [Publishing FAQ](https://docs.dify.ai/en/develop-plugin/publishing/faq/faq)

### 5.2 `bad signature`（署名検証エラー）
- self-host の場合、`/docker/.env` 末尾に `FORCE_VERIFYING_SIGNATURE=false` を追加し、Difyを再起動する案内がある
- **Marketplace未掲載プラグインも通る可能性がありセキュリティリスク**があるため、テスト環境での検証が推奨される

出典: [Publishing FAQ](https://docs.dify.ai/en/develop-plugin/publishing/faq/faq)

---

## 参考（深掘り）
- 詳細ナレッジ（仕様・根拠・制約）:
  - `memory-bank/07-external-research/dify_plugin_development_research_2025-12-12.md`
- トラブルシュート集:
  - `memory-bank/07-external-research/dify_plugin_development_troubleshooting_2025-12-12.md`
- 公式SDK:
  - https://github.com/langgenius/dify-plugin-sdks

