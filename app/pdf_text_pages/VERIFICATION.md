# 検証記録

## 対象と確認範囲

現在のソースは `agen-i/pdf_text_pages` 0.1.6です。PDFを全ページ変換し、それ以外の入力ファイルは元のバイト列・ファイル名・MIMEを保って入力順に返します。PDFの `documents` と各ページの `image_index` は、混在後の `files` に対応します。PDFがない場合の `text` は空文字です。入力0件では設定検査・通信・変換を開始しません。

現在の `agen-i` 配布物の新規導入・名前空間移行・混在入力・LLM直接接続は未検証です。

Linux amd64、Python 3.12、SDK 0.10.2、pypdfium2 5.14.0（PDFium 156.0.8076.0）、Pillow 12.3.0を対象にしています。最低Dify宣言は1.17.1です。導入先daemonの実版・設定継承・対象環境での直接接続は未確認です。

## ローカル試験と配布物

0.1.6の変換・取得・空入力・混在出力を含む試験は **148 passed / 16 warnings** でした。ソースリポジトリの `docs/phase8-test-results-0.1.6.txt` に対象と結果を記録しています。テスト出力は配布物には同梱しません。SDK由来の警告は、対象daemonとの互換性を保証するものではありません。

```bash
uv run pytest
uv run ruff check pdf_core provider tools tests main.py
uv run ruff format --check pdf_core provider tools tests main.py
```

現在の配布物は [BUILD_RECORD](dist/BUILD_RECORD-0.1.6.json) と [SOURCE_SHA256](dist/SOURCE_SHA256-0.1.6.txt) で識別します。作者名・文書・通知の変更前に得た試験結果を、現在の配布物の実機受入へ流用しません。ソースと配布物の対応、パッケージ化、ローカル試験、Dify上の受入を分けて確認します。

## 通信と安全性の検証範囲

入力Fileと独立した既存配信設定を使い、許可origin・限定route・DNS snapshot・固定IP・peer・Host/SNI・TLSを検査します。proxy・redirectを使わず、実受信量と累積期限を制限します。既存の外部file baseから内部APIへ対応付ける場合も同じpath/queryを保持し、公開側への接続失敗後に別originへ切り替えません。未対応のbase path等は通信前に拒否します。

ローカル試験では、通信拒否、DNS・接続・TLS・HTTPの段階診断、上限境界、native子プロセスの期限・メモリ超過、強制終了後の回復を検証しています。エラーと通常ログへURL・署名query・資格情報を出さないことを確認します。実環境のDNS・ネットワーク・CA・設定継承まで確認したものではありません。

HTTPの管理画面への到達とdebug socketへの到達は別です。ソースdebugを使う開発者は、管理画面に表示された接続先とローカルのdebug設定を確認してください。配布物の導入・実機確認にはdebug key/socketは不要です。本検証でDify本番設定・版の更新、OpenAI呼出し、顧客資料入力は実施していません。

## Dify 1.17.1・固定SDKの一次資料

以下は固定版の公開コードに基づく確認です。導入先の設定一致や実機成功を証明する資料ではありません。

- [Dify1.17.1 selector](https://github.com/langgenius/dify/blob/8387590ace4a094de812b7847fc6a4c3a27cd52b/web/app/components/workflow/nodes/_base/components/form-input-item.helpers.ts#L157-L165)：file/files両方でFile/Array[File]変数を許可。
- [core invoke cast](https://github.com/langgenius/dify/blob/8387590ace4a094de812b7847fc6a4c3a27cd52b/api/core/tools/__base/tool.py#L49-L96)、[FILES cast](https://github.com/langgenius/dify/blob/8387590ace4a094de812b7847fc6a4c3a27cd52b/api/core/plugin/entities/parameters.py#L193-L196)：nonlistを一要素listへ、list[]はそのまま。[converter](https://github.com/langgenius/dify/blob/8387590ace4a094de812b7847fc6a4c3a27cd52b/api/core/plugin/utils/converter.py#L7-L13)→[SDK0.10.2 list dict/File変換](https://github.com/langgenius/dify-plugin-sdks/blob/3345471536c6a438884ac4942a2425b6627567f9/src/dify_plugin/interfaces/tool/tool.py#L261-L276)。pluginはstrict list受入を維持し、singleを独自coerceしません。
- [Graphon0.7.0初期files](https://github.com/langgenius/graphon/blob/11e2dee8cbd6dc2e6bf1c2059d9bbf4d0437ebe5/src/graphon/nodes/tool/tool_node.py#L48-L54)、[成功outputs](https://github.com/langgenius/graphon/blob/11e2dee8cbd6dc2e6bf1c2059d9bbf4d0437ebe5/src/graphon/nodes/tool/tool_node.py#L295-L303)：state.files初期[]→ArrayFileSegment。TEXT空+JSONだけ/no file-producing messageのlocal証拠から標準files[]へのsource裏づけ。target実測とは分けます。

- [Dify provider](https://github.com/langgenius/dify/blob/8387590ace4a094de812b7847fc6a4c3a27cd52b/api/core/tools/builtin_tool/provider.py#L131-L166): 非空schemaでAPI_KEY/need_credentials。[plugin provider](https://github.com/langgenius/dify/blob/8387590ace4a094de812b7847fc6a4c3a27cd52b/api/core/tools/plugin_tool/provider.py#L11)は継承。
- [graphon0.7.0 File](https://github.com/langgenius/graphon/blob/11e2dee8cbd6dc2e6bf1c2059d9bbf4d0437ebe5/src/graphon/file/models.py#L202-L214): to_plugin_parameterはfor_external=False。[Dify file_runtime](https://github.com/langgenius/dify/blob/8387590ace4a094de812b7847fc6a4c3a27cd52b/api/core/app/workflow/file_runtime.py#L64-L161): upload/tool/datasourceの全plugin入力がINTERNAL_FILES_URL or FILES_URL、REMOTE_URLは素通し。[bind_file_uri](https://github.com/langgenius/dify/blob/8387590ace4a094de812b7847fc6a4c3a27cd52b/api/core/tools/signature.py#L13-L50): raw base+route。末尾slashを除去するvalidatorは確認されず、二重slashも元baseのまま照合。
- [Dify aliases](https://github.com/langgenius/dify/blob/8387590ace4a094de812b7847fc6a4c3a27cd52b/api/configs/feature/__init__.py#L419-L435)、[pydantic-settings2.14.2 default](https://github.com/pydantic/pydantic-settings/blob/d703bd717e5e07439fa89da2245eee6139413e9e/pydantic_settings/main.py#L573)、[env lookup](https://github.com/pydantic/pydantic-settings/blob/d703bd717e5e07439fa89da2245eee6139413e9e/pydantic_settings/sources/providers/env.py#L90-L94): primary存在時は空でもaliasへ戻らず、absent時だけ既存alias。
- [compose API](https://github.com/langgenius/dify/blob/8387590ace4a094de812b7847fc6a4c3a27cd52b/docker/docker-compose.yaml#L8-L68)、[daemon](https://github.com/langgenius/dify/blob/8387590ace4a094de812b7847fc6a4c3a27cd52b/docker/docker-compose.yaml#L573-L600): shared.env+.env、API専用api.env、公式daemon0.6.10-local。[daemon subprocess](https://github.com/langgenius/dify-plugin-daemon/blob/1310a18b2f6bc6f18768a0a6265484830891433c/internal/core/local_runtime/subprocess.go#L35-L45): daemon環境継承。[core設定補完](https://github.com/langgenius/dify/blob/8387590ace4a094de812b7847fc6a4c3a27cd52b/api/configs/app_config.py#L104-L117): remote/dotenv/TOMLとplugin環境の解決一致は別途確認。
- [plugin identifier](https://github.com/langgenius/dify-plugin-daemon/blob/1310a18b2f6bc6f18768a0a6265484830891433c/pkg/entities/plugin_entities/identity.go#L13-L45)、[update](https://github.com/langgenius/dify-plugin-daemon/blob/1310a18b2f6bc6f18768a0a6265484830891433c/internal/service/install_plugin.go#L183-L228): version/checksumで更新候補を識別。[SDK meta.version](https://github.com/langgenius/dify-plugin-sdks/blob/3345471536c6a438884ac4942a2425b6627567f9/src/dify_plugin/core/entities/plugin/setup.py#L175-L185): manifest仕様版。

上記の単一File変換は `pdf_files` 一つの入力で利用します。従来の二入力口は現在の仕様ではありません。配布物の作者名を `agen-i` に変更したため、既存 `tkosht` からの移行は通常更新と区別します。詳細は [README](README.md#導入) を参照してください。

## 受入条件への対応

| ID | ローカルで得た証拠 | 実機未実施 |
|---|---|---|
| T01 | 固定SDK single dict→File、adapter TEXT/PNG BLOB/JSON | UI単一File割当、LLM直接接続 |
| T02/T03 | list dict→list[File]、順序と全page/ID/画像位置 | sys.files/任意list UI割当 |
| T04/T05 | 一つのlistの入力順、同名/同一PDFの重複を独立docに保持 | 実UI操作 |
| T06 | 4page mixedの本文/画像-only/blank/日本語、空本文2pageを保持 | モデル解釈 |
| T07 | 日本語文字抽出、横長/90度回転、独立renderとの元page body pixel一致、label追加余白pixel一致 | 顧客資料/モデル縮小挙動 |
| T08/T09/T10 | ALPHA右矢印/BETA左矢印fixtureと期待値、768px縮小label人間視認 | LLM入力trace/回答採点、画像順入替え精度 |
| T11 | corrupt/encrypted、native text/render injected failureが位置付きerror、部分成功なし、秘密非露出 | Dify返却途中通信障害時のnode failure |
| T12 | file/inputbyte/page/DPI/幅/高さ/画素/outputbyte/textの閾値前/同値/後、actual byte cap、deadline/memory failure | daemon enforced memoryとDify/LLM最大量適合 |
| T13 | allowlist/path/userinfo/port/scheme/encoding拒否、HTTPredirect/proxy無効、TLS SNI/Host/hostname検証、署名query非露出、slow-drip headers cumulative deadline | 正規File配信先/認証方式 |
| T14 | timeout/実memory exit/TERM無視child→KILL/reap/temp cleanup/後続正常、cross-process BUSY/recovery、output中slot保持 | replica間daemon総parallelism、突然host停止後運用 |
| T15 | 標準TEXT/BLOB/JSONを生成、利用者追加変換なしの設計 | 同一difypkg→標準LLM text/files直結 |

## 合成fixtureと可視確認

`tests/fixtures.py`がReportLab4.4.10/Pillowで合成PDFを作成します。ReportLabは開発依存でproduction requirementsへ含めません。`docs/samples/mixed.pdf`は4page、`beta.pdf`は1pageです。期待値は`docs/LIVE_TESTS.md`にあります。初期fixtureでは両矢印が右でしたが、T08の異なる図という要件へ合わせてBETAだけ左へ変更しました。この変更はテスト/サンプルの意味に限定しproduction code candidateを変更していません。

`docs/samples/page-*.png`は150DPI、`page-*-768.png`は幅768pxへ縮小した可視sampleです。`label-768.png`を実際に開き、`BC6EDBE57C9374F2B9BFA3207365DCD3D-D001-P0001`を全文読み取れました。回転日本語page4も可視確認しました。これは人間によるローカル縮小視認の証拠で、LLM認識結果ではありません。sample metadataは非機密生成結果だけを含みます。


## 実機検証の残り

新規導入・名前空間移行、認証要求のない画面、正規配信設定の継承、T13の実到達先・通信制限、T15のLLM直接接続は未検証です。T01–T06の実UI、T07の対象表示・縮小、T08–T10のLLM精度、T11の返却途中障害、T12の対象上限・daemon制限、T14の運用・回復も [LIVE_TESTS](docs/LIVE_TESTS.md) に従って確認してください。ローカル試験の合格やインストール成功だけで全項目の受入完了とは扱いません。
