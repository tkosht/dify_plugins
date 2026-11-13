# 実機検証の手順

Dify workspaceの管理者と、検証環境へのアクセスを許可された担当者が実施します。対象は現在の `agen-i/pdf_text_pages` 0.1.6配布物です。ローカル試験の合格と、Difyでの直接接続・LLMの回答精度は分けて判定します。以下の実機試験は未実施です。

## 導入と入力の確認

既存の `tkosht/pdf_text_pages` からは名前空間が変わります。新しい配布物を導入し、Chatflowのツール・変数を選び直してください。同一プラグインの通常更新や認証情報の引継ぎが成立するとは限りません。対象packageとハッシュは [BUILD_RECORD](../dist/BUILD_RECORD-0.1.6.json) で確認します。

1. Plugins画面で作者名・名前・版を確認します。Provider/tool画面に認証要求、配信JSON、固定接続先等の追加入力が出ないことを確認します。
2. `pdf_files` 一つへ単一File変数、`sys.files`、任意のファイルリストを割り当てます。従来の `pdf_file` を使うノードは変数を選び直します。リスト化・後処理ノード・JSON追加入力は不要です。
3. 入力0件で `text` 空文字・`files` 空配列・`documents=[]` のJSONを返し、通常の質問へ進めることを確認します。
4. PDFと画像等を混在させ、PDFの全ページPNGと元ファイルが入力順に並ぶこと、本文はPDFだけであること、JSONの `page.image_index` が実際の `files` 位置と一致することを確認します。非画像の元ファイルも返却しますが、後続モデルがその形式を扱えるかは別に確認します。
5. 正規PDFから得た `text` をLLM USERへ、`files` をVisionへ直接接続します。実入力traceに両方があることを確認し、LLMの自己申告だけでは合格にしません。

設定不足・不適合で失敗した場合は、値・URL・署名を含まないノードエラーと対象版を記録します。管理者は既存の配信設定とプラグインへの継承を確認してください。任意URLの許可、認証情報の削除、新しい必須設定の追加で通信制限を回避しないでください。

## T13の前提と通信境界

認証要求のない画面・T15の直接接続と、T13の通信制限は別に判定します。許可された検証環境で、不許可URL/route、取得失敗、署名queryを含む例外を試し、不許可先への通信がなく、機密値がノードエラー・通常ログへ出ないことを確認します。画面でURL/path文字列をFileへ変換できず拒否された場合は、その結果だけを記録し、redirect/proxy/TLS/実受信量/累積期限の試験完了とは扱いません。

- Dify・plugin-daemon・LLM provider pluginの実版、OS/CPU/Python、daemonのメモリ・期限・同時実行数、モデルと画像detail設定を記録します。公式composeの例を導入先の実版とみなしません。
- 既存配信設定とcoreの解決済みbase、プラグインへの継承、必要route、resolver/network/CAを管理者が確認します。API専用設定やremote/TOML補完がプラグインにも一致して渡る保証はありません。
- ソースdebugが必要な場合だけ、Plugins画面に表示された到達可能host:portとworkspace keyをローカルで設定します。keyをチャットや共有ログへ貼らず、`.env` 本文も共有しません。最終配布物の画面確認にdebug接続は不要です。
- インストールとワークフロー実行の権限を確認します。本番設定やDify版を変更する場合は、環境の管理手順に従います。

## T01–T07 / T15

開始→本プラグイン→標準LLM→回答の4nodeを作り、開始でPDFを許可します。`pdf_files`へ単一File変数（core自動list化）またはsys.files等/任意listを指定します。二入力口の併用は廃止しました。Template/code/list変換nodeとJSON入力を追加しません。LLM USERは質問とtool.text、Visionはtool.filesを直接指定します。

`docs/samples/mixed.pdf`（4物理page）と`beta.pdf`（1page）を使い、単一File選択・添付list・任意list・同名別PDF・同じPDF重複を実行します。実行traceで以下を確認し、必要な証拠だけ機密を除いて保存します。

1. 1件の完成text、全pageのimage files、文書順/ページ順/一意ID。混在mixedは本文→画像だけ→白紙→回転日本語で4page、空本文も保持。
2. tool.filesのDify型がArray[File]であり、標準LLM Vision選択に表示されること。PNG MIME、filename metadataの採用、実ファイル数/順序を確認。
3. tool.jsonの実集約型（objectそのものか1objectのarray等）を記録。LLMには接続しない。
4. LLM実input traceでtextとimagesの両方が送られたことを確認。『画像を見た』というLLM自己申告だけを疎通証拠にしない。
5. 返却途中の通信障害を検証workspaceで再現できる場合は、部分結果がLLMへ正常入力されずtool/node failureになることを確認。

## T08–T10

fixtureの期待値: ALPHA/mixed物理page1は本文`ALPHA ... amount 42 kg`、青い矢印は右向き。BETA/beta物理page1は本文`BETA ... amount 42 kg`、青い矢印は左向き。mixed物理page2は緑の矩形を含むimage-only、page3は生成したblank、page4は90度回転した日本語『日本語の凡例：42キログラム』です。プラグインは空本文からpage種別を断定しません。

質問例: 『固有語ALPHA/BETAのある資料について、本文の数量と矢印の向きを対応づけ、資料名とPDF物理ページを根拠として答えてください。』両文書の固有語/数量/矢印/根拠pageを別々に採点し、モデル名・detail・DPI・画像数・入力prompt・正誤を記録します。

T09はテスト用Chatflowだけでimage順を入れ替え、textは同じにします。productionの利用者に並べ替えnodeを要求する仕様ではありません。画像内pixel IDで対応できたか、順序依存の誤対応、縮小後ID誤読を記録します。T10は本文の数量と図の方向を同じpageへ正しく結びつける回答を評価します。全回答の常時正確性を保証したものとして扱いません。

## T11–T14

非機密の破損/暗号化PDF、許可先からのHTTP失敗、上限前後、同時invoke、owned child timeout/memory failureを検証workspaceで実行します。対象位置を示す失敗、部分成功なし、本文/filename/URL/query非露出、temp cleanup、直後の正常request成功を確認してください。容量/モデル上限は顧客環境で具体値を確認し、SECURITYの初期値を保証値と扱わないでください。

既存配信設定の不足・不適合は意図した通信前fail-closedであり、疎通不良のために任意URLを許可する回避策へ変更しません。daemon/network運用は顧客管理者が扱います。


## 記録する結果

各試験の対象package・ハッシュ・環境・入力条件・期待値・結果・未実施理由を記録し、[VERIFICATION](../VERIFICATION.md)の受入表と対応付けます。新規導入、名前空間移行、T13、T15だけで全体完了とは扱わず、対象環境の表示・精度・上限・回復まで確認してください。
