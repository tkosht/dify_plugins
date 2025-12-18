# Difyプラグイン開発 調査ナレッジ（2025-12-12）

## KEYWORDS: dify, plugin, manifest.yaml, difypkg, remote debug, oauth_schema, minimum_dify_version, tool plugin, marketplace
## DOMAIN: external-research|dify|plugin-development
## PRIORITY: HIGH
## WHEN: Difyプラグインの設計・実装・デバッグ・配布手順を一次情報に基づいて再現したいとき
## VERIFIED_AT: 2025-12-12
## RELATED:
- `memory-bank/07-external-research/dify_plugin_development_hub.md`
- `memory-bank/07-external-research/dify_plugin_development_troubleshooting_2025-12-12.md`
- `docs/03.detail_design/dify_plugin_development_guide.md`

## 0. このナレッジの位置づけ
- 本ファイルは **Dify公式Docs + 公式SDK** の一次情報を根拠に、Difyプラグイン開発の要点を「再現可能な形」で記録する。
- ドキュメント内で **環境変数名やホスト表記がページ間で異なる**箇所があるため、観測できた差分は明示する（後で再確認できるように出典URLを併記）。

## 1. エンドツーエンドの開発フロー（再現用）
1. Dify CLI を導入する（後述）
2. `dify plugin init` で雛形を生成する
3. `manifest.yaml` を整備する（メタ/権限/拡張YAML一覧）
4. 拡張タイプに応じて YAML（例: tool定義）と Python 実装（SDK）を作る
5. Remote Debug（Dify側のDebug機能 + `.env` 設定）で動作確認する
6. `dify plugin package ...` で `.difypkg` を作る
7. Difyのプラグイン管理画面から `.difypkg` をインストールする
8. 配布（ファイル共有 / GitHub / Marketplace）

根拠（代表）:
- CLI導入: [Initializing Development Tools](https://docs.dify.ai/plugins/quick-start/develop-plugins/initialize-development-tools)
- Remote Debug: [Plugin Debugging](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/remote-debug-a-plugin)
- Packaging/Install: [Release by File](https://docs.dify.ai/en/develop-plugin/publishing/marketplace-listing/release-by-file)

## 2. Dify CLI の導入（公式記載ベース）
### 2.1 macOS（Homebrew）
```bash
brew tap langgenius/dify
brew install dify

dify version
```
出典: [Initializing Development Tools](https://docs.dify.ai/plugins/quick-start/develop-plugins/initialize-development-tools)

### 2.2 GitHub Releases から取得する流れ（ページ内に言及）
- 上記ページには、Homebrew以外に「Dify GitHub releases から最新CLIを取得する」旨が記載されている。
出典: [Initializing Development Tools](https://docs.dify.ai/plugins/quick-start/develop-plugins/initialize-development-tools)

### 2.3 Linux例（チュートリアル記載）
```bash
chmod +x dify-plugin-linux-amd64
mv dify-plugin-linux-amd64 dify
sudo mv dify /usr/local/bin/

dify version
```
出典: [Develop Flomo Plugin](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/develop-flomo-plugin)

## 3. プロジェクト初期化（雛形生成）
```bash
dify plugin init
```
- 対話プロンプトに従い、プラグイン名・author等を入力して雛形を作成する。
出典: [Initializing Development Tools](https://docs.dify.ai/plugins/quick-start/develop-plugins/initialize-development-tools)

## 4. `manifest.yaml`（仕様・制約）
### 4.1 役割
`manifest.yaml` は、プラグインのメタデータ・権限（resource/permission）・拡張する機能（plugins.* のYAML一覧）を定義する。
出典: [Plugin Info by Manifest](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/plugin-info-by-manifest)

### 4.2 公式のコード例（抜粋）
（全文は仕様ページ参照）
```yaml
version: 0.0.1
type: "plugin"
author: "Yeuoly"
name: "neko"
label:
  en_US: "Neko"
created_at: "2024-07-12T08:03:44.658609186Z"
icon: "icon.svg"
resource:
  memory: 1048576
  permission:
    tool:
      enabled: true
    model:
      enabled: true
      llm: true
    endpoint:
      enabled: true
    app:
      enabled: true
    storage:
      enabled: true
      size: 1048576
plugins:
  endpoints:
    - "provider/neko.yaml"
meta:
  version: 0.0.1
  arch:
    - "amd64"
    - "arm64"
  runner:
    language: "python"
    version: "3.10"
    entrypoint: "main"
privacy: "./privacy.md"
```
出典: [Plugin Info by Manifest](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/plugin-info-by-manifest)

### 4.3 `plugins.*` の拡張キー（manifest仕様に明記）
- `plugins.tools`: Tool providers
- `plugins.models`: Model providers
- `plugins.endpoints`: Endpoints
- `plugins.agent_strategies`: Agent Strategy providers
出典: [Plugin Info by Manifest](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/plugin-info-by-manifest)

### 4.4 重要な制約（manifest仕様に明記）
- `plugins` に列挙した YAML ファイルが実在しないと **packaging が失敗**する（指定パスはプラグインパッケージ内の絶対パス扱い）。
- **Tools と Models の同時拡張は不可**。
- **Models と Endpoints の同時拡張は不可**。
- **拡張なしは不可**（何も拡張しないプラグインは不可）。
- 現状、各拡張タイプごとに provider は1つのみサポート。
出典: [Plugin Info by Manifest](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/plugin-info-by-manifest)

### 4.5 Marketplaceを見据えた `privacy`
- `privacy` は相対パスまたはURLでプライバシーポリシーを指定でき、Marketplaceに掲載する場合は要件になる旨が仕様に明記されている。
出典: [Plugin Info by Manifest](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/plugin-info-by-manifest)

## 5. Remote Debug（デバッグ）
### 5.1 基本
- Difyの「Plugin Management」側で Debug Plugin を実行し、remote server address と debugging key を取得してプラグイン側 `.env` に設定する。
出典: [Plugin Debugging](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/remote-debug-a-plugin)

### 5.2 `.env` の設定（ページ差異の記録）
**A) Remote Debug専用ページの例**
```dotenv
INSTALL_METHOD=remote
REMOTE_INSTALL_URL=debug.dify.ai:5003
REMOTE_INSTALL_KEY=<YOUR_DEBUG_KEY>
```
出典: [Plugin Debugging](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/remote-debug-a-plugin)

**B) Flomoチュートリアルの例（HOST/PORT分割）**
```dotenv
INSTALL_METHOD=remote
REMOTE_INSTALL_HOST=debug-plugin.dify.dev
REMOTE_INSTALL_PORT=5003
REMOTE_INSTALL_KEY=your_debug_key
```
出典: [Develop Flomo Plugin](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/develop-flomo-plugin)

注意:
- `.env` 変数名がページによって異なるため、まずは **利用しているガイドに合わせる**。
- 最終的には Dify UI で表示される Host Address / API Key（debug key）を優先する。

## 6. Packaging / Install（`.difypkg`）
### 6.1 パッケージ作成
```bash
dify plugin package ./your_plugin_project
```
- 実行するとカレントパスに `.difypkg` が生成される。
出典: [Release by File](https://docs.dify.ai/en/develop-plugin/publishing/marketplace-listing/release-by-file)

### 6.2 インストール
- Difyの plugin management ページで「Install Plugin → Via Local File」から `.difypkg` をアップロード、またはページの空白へドラッグ&ドロップ。
出典: [Release by File](https://docs.dify.ai/en/develop-plugin/publishing/marketplace-listing/release-by-file)

### 6.3 配布
- `.difypkg` を共有するか、GitHubやDify Marketplaceへ公開する流れが案内されている。
出典: [Release by File](https://docs.dify.ai/en/develop-plugin/publishing/marketplace-listing/release-by-file)

## 7. Toolプラグイン実装の具体例（公式チュートリアル: Flomo）
- tool定義YAML（例: `flomo.yaml`）で、`identity`/`description`/`credential_schema`/`tool_schema` を定義する。
- 実装は `dify_plugin` SDK を利用し、Provider（資格情報検証）と Tool（呼び出し処理）を実装する。
出典: [Develop Flomo Plugin](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/develop-flomo-plugin)

（実装断片の例）
- Provider: `from dify_plugin import ToolProvider`
- Tool: `from dify_plugin import Tool`
- Tool invoke message: `from dify_plugin.entities.tool import ToolInvokeMessage`
出典: [Develop Flomo Plugin](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/develop-flomo-plugin)

## 8. OAuth（Toolプラグイン）
### 8.1 provider YAML で `oauth_schema` を定義
- `client_schema`（OAuth client setup）と `credentials_schema`（認可後のトークン等）を宣言する。
出典: [Tool OAuth](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/tool-oauth)

### 8.2 Provider 側で必要なOAuthメソッド
- `_oauth_get_authorization_url`
- `_oauth_get_credentials`
- `_oauth_refresh_credentials`
出典: [Tool OAuth](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/tool-oauth)

### 8.3 セキュリティ注意（公式明記）
- `ToolOAuthCredentials` の credentials に **client_secret を返してはいけない**（セキュリティリスク）。
出典: [Tool OAuth](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/tool-oauth)

### 8.4 `meta.minimum_dify_version`
- OAuth利用のため、`manifest.yaml` に最低Difyバージョンを追加する例がある。
出典: [Tool OAuth](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/tool-oauth)

## 9. 互換性（SDK/最低Difyバージョン）
- 公式SDK `langgenius/dify-plugin-sdks` の README に、機能ごとの Minimum Dify Version が表で整理されている。
- 例として、Datasource/Triggerサポート等が SDK バージョンと紐づけられている。
出典:
- `https://github.com/langgenius/dify-plugin-sdks`
- `https://raw.githubusercontent.com/langgenius/dify-plugin-sdks/main/README.md`

## 10. 公式FAQ（落とし穴）
- `PluginDaemonBadRequestError: plugin_unique_identifier is not valid` が出る場合:
  - `manifest.yaml` の `author` と、`/provider` 配下の `.yaml` の author を **GitHub ID** に修正し、再パッケージして再インストール。
出典: [Publishing FAQ](https://docs.dify.ai/en/develop-plugin/publishing/faq/faq)

- 署名検証の例外（bad signature）:
  - `FORCE_VERIFYING_SIGNATURE=false` を環境変数に追加する案内がある。
出典: [Publishing FAQ](https://docs.dify.ai/en/develop-plugin/publishing/faq/faq)

---

## Sources（参照一覧・参照日: 2025-12-12）
- [Initializing Development Tools](https://docs.dify.ai/plugins/quick-start/develop-plugins/initialize-development-tools)
- [Plugin Info by Manifest](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/plugin-info-by-manifest)
- [Plugin Debugging](https://docs.dify.ai/en/develop-plugin/features-and-specs/plugin-types/remote-debug-a-plugin)
- [Release by File](https://docs.dify.ai/en/develop-plugin/publishing/marketplace-listing/release-by-file)
- [Develop Flomo Plugin](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/develop-flomo-plugin)
- [Tool OAuth](https://docs.dify.ai/en/develop-plugin/dev-guides-and-walkthroughs/tool-oauth)
- [Publishing FAQ](https://docs.dify.ai/en/develop-plugin/publishing/faq/faq)
- https://github.com/langgenius/dify-plugin-sdks
- https://raw.githubusercontent.com/langgenius/dify-plugin-sdks/main/README.md

