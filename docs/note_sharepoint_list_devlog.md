## SharePoint × Dify：Cursorで作る業務向けToolプラグイン開発 実録（ハマりどころと解決の型）

### TL;DR
- SharePoint List を **Microsoft Graph + Delegated OAuth** で操作する Dify Tool Plugin を、**Cursor IDE** で実装・デバッグ・配布（`.difypkg`）まで通しました。
- 事故ポイントは「OAuth」「YAML/packaging」「SharePoint固有（内部名/インデックス）」に集中します。**原因→確認→直し方**の型を作ると強いです。
- 最終的にツール入力は **`list_url` 1本化**し、フィルタは **JSON配列（複数条件）**、表示名（日本語）も内部名へ解決して扱える形にしました。

### 注記（公開向け）
- 本記事は公開用のため、**tenant名・サイト名・アプリID・リダイレクトURI等はすべてダミー表記**にしています。
- `client_secret` / token / `.env` の中身など、**秘密情報は一切掲載しません**。

### 対象読者
- 生成AI/Difyに興味があり、業務データ（例：SharePoint List）をつなぐ「小さなプラグイン」を自分で作ってみたいビジネスユーザ
- PythonやAPIは“読める/いじれる”くらいでOK（深い実装は雰囲気でつかめるように書きます）

### この記事で得られるもの
- Dify Tool Plugin の最短開発フロー（remote debug → packaging → install）
- よくあるエラーの「潰し方」テンプレ
- SharePoint List 特有のハマり（表示名/内部名、Choice、インデックス）への対処法

---

## 1. 何を作ったか（完成イメージ）
### 背景（業務あるある）
SharePoint List は「申請」「問い合わせ」「タスク管理」などの業務データが溜まりやすい一方、UIからの操作が中心で、生成AIに“道具”として渡すには一手間かかります。  
そこで **Dify の Tool Plugin** として SharePoint List を扱えるようにし、チャット/ワークフローから CRUD と一覧・フィルタ、選択肢取得までできるようにしました。

【スクショ①】Plugin Management（入口）  
<!-- screenshot:01 Dify Workspace > Plugin Management の一覧。要マスク: Workspace名/組織名 -->

作ったのは **SharePoint List 操作用の Dify Tool Plugin** です。具体的には以下のツールを持ちます（最終仕様）。

- **作成**: `sharepoint_list_create_item`
- **更新**: `sharepoint_list_update_item`
- **取得**: `sharepoint_list_get_item`
- **一覧**: `sharepoint_list_list_items`（ページネーション・フィルタ対応、`createdDateTime desc` 固定）
- **Choice選択肢取得**: `sharepoint_list_get_choices`

入力は「サイト指定」「リスト指定」を分けず、**SharePoint のリストURLを1つ渡すだけ**にしました：

例（ダミー）:
`https://<tenant>.sharepoint.com/sites/<site>/Lists/<list>/AllItems.aspx`

---

## 2. 全体像（Dify Plugin と Graph API）

### 2.1 コンポーネント構成
Dify の Tool Plugin は雑に言うと、以下の“セット”です。

- `manifest.yaml`：プラグインの宣言（バージョン、読み込むprovider/tool YAML一覧など）
- `provider/*.yaml`：OAuthスキーマ等の宣言
- `tools/*.yaml`：各ツールの入力UI/説明（人間向け・LLM向け）
- `provider/*.py`：OAuth（認可URL生成、code→token交換、refresh）
- `tools/*.py`：各ツールの実処理（入力検証→operations呼び出し→結果返却）
- `internal/*.py`：Graph API のリクエスト生成、OData組み立て、表示名→内部名解決など「ロジック本体」

### 2.2 データフロー（超ざっくり）

```text
Dify UI
  ├─(1) OAuth: Provider が認可URLを返す
  ├─(2) Callback: code を Provider が受け取り token 交換
  └─(3) Tool実行: Tool が access_token を使って Graph API を叩く

Graph API（SharePoint List）
  ├─ sites / lists / columns（列定義＝表示名→内部名マップ）
  └─ lists/{listId}/items?$expand=fields(...)（取得/一覧/作成/更新）
```

【スクショ⑨】アプリ編集画面（Toolの選択/呼び出し）  
<!-- screenshot:09 Dify App（Chatflow/Workflow等）で Tool ノード設定。要マスク: アプリ名/組織情報 -->

---

## 3. 開発フロー（Cursor IDE 前提・最短）
ここは「迷わない順番」が大事です。

### 3.1 まず remote debug で“最短で動かす”
1) Dify 側で Debug Plugin の Host/Key を取得  
2) プラグインを起動して、Dify 側から叩ける状態にする  
3) 最小動線（Create→Read→Update→Read）で確認

【スクショ②】Debug Plugin 画面（Host Address / Debug Key）  
<!-- screenshot:02 Plugin Management > Debug Plugin。要マスク: Host Address/Debug Key -->

remote debug の `.env` は、概ねこういう形です（値はダミー）:

```dotenv
INSTALL_METHOD=remote
REMOTE_INSTALL_URL=<debug-host>:5003
REMOTE_INSTALL_KEY=<DEBUG_KEY>
```

起動（このリポジトリでは `uv` 前提）:

```bash
uv run python -m main
```

### 3.2 packaging（`.difypkg`）してインストール
remote debug が通ったら、次は **同じものがインストールでも動くか**を潰します。

- `.difypkg` を生成: `dify plugin package <plugin_dir>`（例: `dify plugin package app/sharepoint_list`）
- Dify の Plugin Management → Via Local File でアップロード

ここで “manifest/YAML/import” の事故が一気に出ます（後述）。

【スクショ③】プラグイン詳細（ツール一覧が見える画面）  
<!-- screenshot:03 Plugin Management > SharePoint List プラグイン詳細。要マスク: 固有名/内部URL -->

【スクショ④】プラグイン設定（client_id / client_secret / tenant_id）  
<!-- screenshot:04 プラグイン設定画面。要マスク: client_id/tenant_id/client_secret/リダイレクトURI等 -->

【スクショ⑤】Save & Authorize の成功/失敗表示  
<!-- screenshot:05 Save & Authorize 実行後の結果。要マスク: ユーザー名/メール/環境固有情報 -->

【スクショ⑥】Install Plugin → Via Local File（.difypkg投入）  
<!-- screenshot:06 Install Plugin ダイアログ。要マスク: ローカルパス等 -->

【スクショ⑦】`bad signature` エラー表示（該当する場合）  
<!-- screenshot:07 未署名/署名不一致で出るエラー。要マスク: 環境固有情報 -->

【スクショ⑧】プラグインインストールを「管理者のみ許可」する設定箇所  
<!-- screenshot:08 Dify の権限/管理設定。要マスク: 組織/ユーザー情報。画面パスは環境差あり -->

#### 署名なし（開発/検証向け）
未署名の `.difypkg` を入れたいのに、Dify 側で署名検証が有効になっていると、インストール時に `bad signature` として拒否されることがあります。開発・検証環境で一時的に回避する場合は、`plugin_daemon` の環境変数に以下を設定し、コンテナ（サービス）を再起動します。

```dotenv
FORCE_VERIFYING_SIGNATURE=false
```

注意: 署名検証を無効化すると、未レビューのプラグインも入ってしまう可能性がありセキュリティリスクがあります。**本番では推奨しません**。やむを得ず使う場合でも、Dify UI 側の運用として **プラグインインストールを管理者のみ許可**する設定を強く推奨します。

#### 署名あり（自作プラグインを自分で署名して配布）
署名検証を無効化せずに自作プラグインを配布したい場合は、`.difypkg` を自分で署名し、Dify 側に公開鍵を配布して検証させる構成にします。

このリポジトリでは、署名の流れ（鍵生成→署名→検証）が `bin/make_plugin.sh` にまとまっています。手動で行う場合のイメージは以下です（値はダミー）。

1) `.difypkg` を作る

```bash
dify plugin package app/sharepoint_list
```

2) 鍵ペア生成（初回のみ）

```bash
dify signature generate -f custom_plugins
```

3) `.difypkg` に署名（署名済みファイルが生成される）

```bash
dify signature sign sharepoint_list.difypkg -p custom_plugins.private.pem
```

4) 署名検証（配布前チェック）

```bash
dify signature verify sharepoint_list.signed.difypkg -p custom_plugins.public.pem
```

5) Dify 側（`plugin_daemon`）で第三者署名検証を有効化し、公開鍵を配置して参照させる

設定例（`plugin_daemon` の環境変数の例）:

```yaml
THIRD_PARTY_SIGNATURE_VERIFICATION_ENABLED: true
THIRD_PARTY_SIGNATURE_VERIFICATION_PUBLIC_KEYS: /app/storage/public_keys/custom_plugins.public.pem
```

公開鍵（`custom_plugins.public.pem`）は、上記パスに置けるように **ボリューム/マウント等で配置**し、`plugin_daemon` を再起動します。

### 3.3 Cursor の使い方（コツ）
- **変更は小さく**（1エラー＝1修正＝1検証）
- “ロジック本体”を `internal/` に寄せ、**ユニットテストで固める**
- `ruff` / `pytest` を回して「直したつもり」を減らす（Cursorからコマンド実行できるのが便利）

```bash
uv run ruff check .
uv run pytest tests/sharepoint_list
```

#### Cursor / Debug / Review の使い分け（今回の運用）
- **Plan モード**: 仕様・入力I/F・例示（UIに出る説明）を詰める
- **Build**: 実装（小さく変更→テスト）
- **Debug モード**: エラー解析（仮説→最小ログ→再現→確証）
- **レビュー**: Codex CLI（GPT 5.1 Codex xhigh）で観点レビューし、指摘に沿って修正も実施

---

## 4. 実録：ハマりどころと解決の型（原因→確認→直し方）
この章が本題です。よくある事故を「型」でまとめます。

### 4.1 OAuth で `int has no attribute encode`（Dify側の保存処理で失敗する）
**症状**: OAuth認可直後に 400 `invalid_param`  
**原因**: credentials に `int` を混ぜた（例：`expires_at` を int のまま返した）  
**確認**: 「Difyが credentials を暗号化保存する際 `.encode()` を呼ぶ」前提の挙動と一致  
**直し方**: credentials 内は **すべて文字列**に寄せる（`expires_at` を `str(...)` に）

→ “OAuthが通らない”は Graph 以前に、**プラグインの型**で失敗することがあります。

### 4.2 Graph 401 `Access token is empty`
**症状**: Graph から `InvalidAuthenticationToken: Access token is empty.`  
**原因**: Dify 側の OAuth credentials が空のまま（再認可が未完了/保存されてない等）  
**確認**: Tool 実行時に `runtime.credentials["access_token"]` をチェック  
**直し方**: access_token が空/空白なら即エラーにして **再認可を促す**（曖昧に進めない）

### 4.3 シングルテナント化で `Authorization code is missing`
**症状**: callback で `code` が来ず missing 扱い  
**原因**: Azure AD アプリを「組織内のみ」にしたのに、認可URLが `/common` のまま  
**確認**: `AADSTS50194: ... /common endpoint is not supported ...` が返っている  
**直し方**: `tenant_id` を設定できるようにし、  
`https://login.microsoftonline.com/{tenant}/oauth2/v2.0/...` を使う

→ 認証は“アプリの設定変更”で突然壊れます。**multi-tenant / single-tenant とエンドポイントはセット**です。

補足: OAuth の credential 設計では、**`client_secret` をユーザーごとの credentials に保存しない**（system credentials のみ）方針にすると安全です。

### 4.4 YAMLで詰まる（packaging/起動前に落ちる）
ありがちトップ3：
- **manifest の tags がバリデーションで落ちる** → まずは tags を外して先に進む
- `human_description` に `:` が入って **YAMLの構文扱い** → 文字列をクォート/ブロックに
- provider/tool YAML の `author` が揃ってない → `plugin_unique_identifier` 系で詰む

“YAMLで詰まる”は、コードを疑う前に **YAMLの型と引用符**を疑うのが近道です。

### 4.5 `.difypkg` では `ModuleNotFoundError: No module named 'app'`
**症状**: ローカルでは動くのに、インストールすると import で失敗する  
**原因**: パッケージ実行時の import ルートがローカルと違う  
**直し方**: プラグイン配下で完結する import に揃える（例：`from internal import ...`）

→ “動いたのにインストールで失敗する”は **import/依存/相対パス**が多いです。

### 4.6 `select_fields` の引用符で OData が壊れる
**症状**: `"Title"` のようにクォート付きで渡すと OData パースエラー  
**直し方**: 入口で外側クォートを剥がす（UI/LLM経由だと「余計なクォート」が混ざりがち）

### 4.7 SharePoint 列名：表示名（日本語）と内部名（_x30...）問題
**症状**: `ステータス` でフィルタ/更新したいのに `Field not recognized`  
**原因**: Graph API の `fields/<name>` は内部名で参照が必要  
**直し方**: Microsoft Graph の **`/columns` エンドポイント**で列定義を取得し、`displayName -> name`（表示名→内部名）を対応付けてから、`fields/<internalName>` として Graph に渡す

この対応を **取得/一覧だけでなく、作成/更新にも適用**して初めてUXが揃います。

### 4.8 Choice列の「選択肢取得」
**症状**: `columnType` を `$select` すると 400（存在しない扱い）、または `columnType=None` で誤判定  
**直し方**:
- `$select` は `name,displayName,choice` に絞る
- `choice` オブジェクトがあれば choice 列として扱う（`columnType` に依存しない）

### 4.9 list_items フィルタ：未インデックス列で 400
**症状**: `cannot be referenced in filter or orderby as it is not indexed`  
**直し方（ベストエフォート）**: `Prefer: HonorNonIndexedQueriesWarning=true` を付ける  
**運用上の結論**: それでも拒否される環境があるので、**SharePoint側で対象列をインデックス化**するのが確実

インデックス化（UI）手順の例:
- 対象リスト → **List settings** → **Indexed columns** → **Create a new index**
- フィルタに使う列（例: ステータス）を選んで作成

### 4.10 フィルタ仕様を「JSON配列」に寄せた理由
単一の `filter_field/filter_value` 方式はすぐ限界が来ます。最終的に以下に寄せました。

```json
[
  {"field":"ステータス","op":"eq","value":"処理中"},
  {"field":"createdDateTime","op":"ge","value":"2025-12-15T00:00:00Z","type":"datetime"}
]
```

ポイント：
- **複数条件は and 結合**（まずはここまで）
- `createdDateTime` はトップレベル、それ以外は `fields/<internalName>`
- 表示名は内部名へ解決（日本語OK）
- 未インデックス列フィルタは 400 になり得るので、**UI説明に“インデックス推奨”を明記**

補足（Agent/LLM からの利用を想定した設計意図）:

Agent からツールを呼ぶ前提だと、OData の `$filter` 文字列をそのまま組み立てさせる方式は、クォートやエスケープ、フィールド参照ルール（`createdDateTime` はトップレベル等）のミスが起きやすく、運用でブレが出ます。

そこで入力を **JSON配列（field/op/value/type）** に寄せることで、

- 入力の形を固定できる（UI例示と揃えやすい）
- バリデーションで早期にエラーにできる
- 表示名→内部名解決などの“業務システム側の癖”をツール側に閉じ込められる

というメリットがあり、Agent からの呼び出しでも安定しました。

---

## 5. 最終仕様（現時点のおすすめ）
最終形は README の通り、概ねこうです。

- 入力は **`list_url` 1つ**（AllItems.aspx）
- `fields_json` は内部名が基本だが、表示名でも内部名に解決して送れる
- `list_items.filters` は JSON配列/単体オブジェクト（文字列として渡す）
- `list_items` は `createdDateTime desc` 固定（安定したページングのため）
- デバッグログは `plugin_daemon` の環境変数 `SHAREPOINT_LIST_DEBUG_LOG=1` を設定し、コンテナ再起動で有効化
  - 出力先は `SHAREPOINT_LIST_DEBUG_LOG_PATH`（未指定時 `/tmp/sharepoint_list.debug.ndjson`）で調整できます。

例（一覧）:

```json
{
  "list_url": "https://<tenant>.sharepoint.com/sites/<site>/Lists/<list>/AllItems.aspx",
  "page_size": 20,
  "filters": "[{\"field\":\"ステータス\",\"op\":\"eq\",\"value\":\"処理中\"}]"
}
```

【スクショ⑩】list_items の入力例（list_url / filters / page_size）  
<!-- screenshot:10 sharepoint_list_list_items 実行UI。要マスク: list_url（tenant含む） -->

【スクショ⑪】get_choices の入力と出力例（choices が返る）  
<!-- screenshot:11 sharepoint_list_get_choices 実行UI。要マスク: list_url/組織情報 -->

---

## 6. コピペ用チェックリスト（再現性を上げる）

### OAuth（Azure AD）
- Redirect URI が Dify の callback と一致している
- 権限（`openid offline_access User.Read Sites.ReadWrite.All`）が付いている
- アカウント種別を変えたら、`/common` ではなく **tenant 固定**にする（`tenant_id`）

### packaging（`.difypkg`）
- `manifest.yaml` の `plugins.*` に列挙した YAML が実在する
- YAML の `:` はクォート/ブロックで逃がす
- import はプラグインルート基準で完結させる

### SharePoint List
- フィルタ/ソートに使う列は **SharePoint側でインデックス化**
- 表示名（日本語）を受けたいなら Microsoft Graph の **`/columns`** で列定義（`displayName -> name`）を取得し、内部名へ解決する

### 「エラー潰し」テンプレ（超重要）
- **エラー文言をそのままメモ**（どこで出たか：認証/packaging/実行時）
- **入口で型と空を疑う**（文字列？空？クォート？）
- **再現→最小修正→テスト/ログ→確証**のループに落とす（勢いで修正しない）

---

## 7. 次にやるなら（発展）
- filters の **OR/括弧**対応（やるなら入力スキーマから設計する）
- 列定義（displayName→name）の **キャッシュ**（API回数削減）
- エラーの分類（401/403/429/400の “ユーザーが直せる説明”）

---

## おわりに
業務プラグイン開発は「APIを叩く」よりも、**OAuthと配布形態（packaging）と業務システム固有の癖**で時間が溶けがちです。  
逆に言えば、ここを“型”にしてしまうと、次のプラグインは驚くほど速く作れます。

