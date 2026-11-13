# Read Region

PNG/JPEG を登録し、画像全体の OCR、元画像の座標による領域切り出しと OCR、実行後の後片付けを行う内部サービスです。Tesseract と固定の日本語・英語モデルを使います。

**Dify との実接続は未完了で、本番利用できません。** Dify 1.18.0 / SDK 0.10.2 ではワークフロー実行ごとの信頼できるコンテキストが未確認のため、標準のプラグインツール 3 つはすべて `CONTEXT_REQUIRED` で停止します。下記の合成画像での OCR 成功は、精度向上や Agent の成功を示すものではありません。検証状況は [results.md](verification/results.md) を参照してください。

## ローカル確認

リポジトリのルートで実行します。

```sh
uv sync --project app/read_region --frozen
uv run --project app/read_region pytest app/read_region/tests -c app/read_region/pyproject.toml
uv run --project app/read_region ruff check app/read_region
uv run --project app/read_region black --check app/read_region
```

ビルド時はネットワークから固定依存関係を取得し、OCR モデルのハッシュを検証します。

```sh
docker build -t read-region-local:20261113 app/read_region
```

次はネットワークなしで合成画像の全体と手動指定領域を比較する確認です。

```sh
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges \
  --tmpfs /tmp:rw,size=512m \
  -v "$PWD/app/read_region/scripts/real_ocr.py:/app/real_ocr.py:ro" \
  -v "$PWD/app/read_region/fixtures:/fixtures:ro" \
  --entrypoint python read-region-local:20261113 \
  /app/real_ocr.py /fixtures/synthetic-japanese.png /fixtures/ground-truth.json
```

## サービスの設定

Git の外に、アプリケーションごとの scope を 32 文字以上のランダムなサービス token に対応付ける JSON ファイルを用意します。権限は `0600` とし、UID 10001 だけが読めるようにします。認証情報を LLM の引数やログに入れないでください。状態ディレクトリは UID 10001 所有の非公開領域とし、再起動後も保持します。暗号化とバックアップ除外は組織の方針に従います。ワーカーは必ず 1 つだけ起動します。

以下は loopback に限定する起動例です。プラグイン接続前に、組織が承認した内部 TLS エンドポイントの背後に配置してください。

```sh
docker run --rm --name read-region-local \
  --read-only --cap-drop ALL --security-opt no-new-privileges \
  --tmpfs /tmp:rw,size=512m \
  --mount type=bind,src=/approved/private/read-region-state,dst=/state \
  --mount type=bind,src=/approved/private/read-region-credentials.json,dst=/run/credentials.json,readonly \
  -e READ_REGION_CREDENTIALS_FILE=/run/credentials.json \
  -p 127.0.0.1:18080:8000 read-region-local:20261113
```

HTTP サービスの外向き通信には、上記のオフライン確認とは別に、承認済みのサービス単位の通信ポリシーが必要です。共通の Dify ネットワークは変更しません。利用可能な環境ではコンテナのメモリ・PID 制限を設定してください。この開発ホストでは cgroup 制限を使えませんでした。固定モデルが欠落または不一致なら 503 を返し、実行時にダウンロードしません。外部 OCR、外部 API、外部ストレージは使いません。認証と運用上の詳細は [security.md](verification/security.md) と [environment.md](verification/environment.md) を参照してください。

## Dify と復旧

公式 CLI 0.6.10 でパッケージを作成できます。作成・検証は対象 Dify へのインストールを意味しません。

```sh
app/read_region/.local-bin/dify plugin package app/read_region/plugin \
  -o app/read_region/read_region-0.1.0.difypkg
```

既存 Chatflow とプラグインのバージョンを保持し、Dify、Agent の方式、モデル、既存 PDF 入出力、共有ネットワークやログ設定を変更しないでください。`prepare_images` と `cleanup_images` は固定の前後ノードに置き、Agent に渡すツールは `read_region` だけです。実際の Chatflow に接続する前に、信頼できるコンテキスト連携について P0（同一実行内の安定性、異なる実行・アプリの拒否、不明引数の拒否、ファイル取得、JSON の反復、後片付け）を満たす必要があります。認証情報はプロバイダー側で設定します。

戻すときは、実験用に複製した Chatflow から 3 ツールのノード・参照を外して元の経路に戻します。他のアプリが使っていないことを確認してからプラグインをアンインストールしてください。実行終了後、対象サービスだけを `docker stop read-region-local` で停止します。状態と認証情報は継続利用の必要がなくなった後、保持方針に従って処理し、他のシステムのデータは保持します。
