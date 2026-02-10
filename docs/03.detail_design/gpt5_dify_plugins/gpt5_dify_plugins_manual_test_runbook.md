# GPT-5 Dify Plugins 手動検証ランブック

最終更新: 2026-02-09
対象:
- Plugin A: `app/openai_gpt5_responses`
- Plugin B: `app/gpt5_agent_strategies`

## 1. 目的
人手で Dify 上の実動作を確認し、以下を満たすことを判定する。
- GPT-5 系モデル呼び出しが実行できる。
- Agent Strategy（Function Calling / ReAct）がツール呼び出しを含めて実行できる。
- 異常入力時に安全に失敗し、原因が追跡できる。

## 2. 前提条件
- Dify の Plugin Management にアクセスできる。
- Dify の Debug Plugin から `Host/Port/Debug Key` を取得済み。
- OpenAI API キーを利用できる。
- ローカルに `uv` と `python3` がある。
- （package 検証まで行う場合）`dify` CLI が使える。

## 3. 事前準備
### 3.1 Plugin A
```bash
cd /home/devuser/workspace/app/openai_gpt5_responses
cp .env.example .env
```

`.env` を以下で更新する。
```dotenv
INSTALL_METHOD=remote
REMOTE_INSTALL_HOST=<DEBUG_PLUGIN_HOST>
REMOTE_INSTALL_PORT=<DEBUG_PLUGIN_PORT>
REMOTE_INSTALL_KEY=<DEBUG_PLUGIN_KEY>
```

依存を導入する。
```bash
uv pip install -r requirements.txt
```

### 3.2 Plugin B
```bash
cd /home/devuser/workspace/app/gpt5_agent_strategies
cp .env.example .env
```

`.env` を以下で更新する。
```dotenv
INSTALL_METHOD=remote
REMOTE_INSTALL_HOST=<DEBUG_PLUGIN_HOST>
REMOTE_INSTALL_PORT=<DEBUG_PLUGIN_PORT>
REMOTE_INSTALL_KEY=<DEBUG_PLUGIN_KEY>
```

依存を導入する。
```bash
uv pip install -r requirements.txt
```

## 4. ローカル回帰（Dify 接続前）
以下は毎回先に実行する。
```bash
cd /home/devuser/workspace
uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies
uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies
```

期待結果:
- すべて `PASS`
- coverage fail-under（85%）を下回らない

## 5. Plugin A 手動検証（OpenAI GPT-5 Responses）
### 5.1 起動
```bash
cd /home/devuser/workspace/app/openai_gpt5_responses
uv run python -m main
```

監査ログで「指定モデルで Responses API リクエストが送信されたか」を確認したい場合:
```bash
cd /home/devuser/workspace/app/openai_gpt5_responses
OPENAI_GPT5_AUDIT_LOG=true uv run python -m main
```

期待するログ（機密は出ない）:
- `openai_gpt5_audit {"event":"responses_api_request", ... "model":"<selected_model>", ...}`
- `openai_gpt5_audit {"event":"responses_api_success", ... "model":"<selected_model>", ...}`
- 失敗時は `responses_api_error` と `status_code` / `request_id` が出る

### 5.2 Dify 側設定
- Provider: `OpenAI GPT-5 Responses`
- Credentials:
  - `openai_api_key`（必須）
  - `openai_organization`（任意）
  - `openai_api_base`（任意）
  - `request_timeout_seconds`（任意、既定300）
  - `max_retries`（任意、既定1）

### 5.3 テストケース
1. A-01 正常: `gpt-5.2-pro` で短文応答
- 入力: 「3行で自己紹介して」
- 期待: 正常応答（HTTP/認証エラーなし）

2. A-02 正常: stream 切替
- 条件1: `enable_stream=true`
- 条件2: `enable_stream=false`
- 期待: どちらも応答成功し、UI 上で応答方式が切り替わる

3. A-03 正常: JSON schema 応答
- 条件: `response_format=json_schema` + 妥当な `json_schema`
- 期待: 構造化出力になる

4. A-04 異常: schema 未指定
- 条件: `response_format=json_schema` かつ `json_schema` 空
- 期待: 入力検証エラーで失敗

5. A-05 異常: 無効 API キー
- 条件: `openai_api_key` を無効値に変更
- 期待: 認証エラーで失敗

6. A-06 異常: 存在しない model
- 条件: 未存在モデル名を指定
- 期待: model not found 系で失敗

## 6. Plugin B 手動検証（GPT-5 Agent Strategies）
### 6.1 起動
```bash
cd /home/devuser/workspace/app/gpt5_agent_strategies
uv run python -m main
```

### 6.2 Dify 側設定
- Strategy Provider: `GPT-5 Agent`
- Strategy を順に検証:
  - `gpt5_function_calling`
  - `gpt5_react`
- `model` は Plugin A の GPT-5 系を指定
- `tools` は最低1つ設定

### 6.3 テストケース
1. B-01 正常: Function Calling で tool invoke
- 入力: 「使えるツールで必要情報を取得して要約して」
- 期待: tool 実行ログが出て最終回答まで到達

2. B-02 正常: ReAct で tool invoke
- 入力: B-01 と同等
- 期待: tool 実行を経て最終回答まで到達

3. B-03 制御: `maximum_iterations=1`
- 期待: 早期停止する（無限ループしない）

4. B-04 制御: `maximum_iterations=6`
- 期待: 複数ラウンドの推論が可能

5. B-05 安全: 不正 tool arguments
- 条件: ツール引数を JSON 不正にする
- 期待: fail-closed（危険な実行に進まない）

## 7. 連携シナリオ（A+B）
1. Agent App で:
- Model Provider: Plugin A
- Agent Strategy: Plugin B
2. Tool が必要な質問を実行。
3. 期待:
- モデル応答
- tool invoke
- 最終回答
が一連で完了する。

## 8. `.difypkg` 再検証
```bash
dify plugin package /home/devuser/workspace/app/openai_gpt5_responses
dify plugin package /home/devuser/workspace/app/gpt5_agent_strategies
```

作成した `.difypkg` を Dify へ `Install Plugin -> Via Local File` で導入し、5章〜7章を再実行する。

## 9. 障害時の切り分け（stream disconnected）
1. Plugin A/B を同時起動せず、片方ずつ起動して再試行する。
2. `.env` の `REMOTE_INSTALL_HOST/PORT/KEY` を再確認する。
3. 同一ケースを 30 秒間隔で 2 回再試行する。
4. `enable_stream=false` で再試験し、stream 固有かを判定する。
5. 記録する:
- 発生日時
- モデル名
- 入力
- エラーメッセージ全文
- `OPENAI_GPT5_AUDIT_LOG=true` の監査ログ（request/success/error）

## 10. 判定基準（合格）
1. A-01, A-02, A-03 が成功する。
2. A-04, A-05, A-06 が期待どおりに失敗する。
3. B-01, B-02, B-03, B-04, B-05 が期待どおり。
4. 7章の連携シナリオが完了する。
5. `.difypkg` 再検証で挙動差分がない。

## 11. 実行記録テンプレート
```text
[Run Metadata]
date:
tester:
dify_env:

[Plugin A]
A-01:
A-02:
A-03:
A-04:
A-05:
A-06:

[Plugin B]
B-01:
B-02:
B-03:
B-04:
B-05:

[Integration]
A+B:

[Package]
package_retest:

[Notes]
```
