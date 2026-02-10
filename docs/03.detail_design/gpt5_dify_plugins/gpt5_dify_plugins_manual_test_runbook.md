# GPT-5 Dify Plugins 手動検証ランブック（実装準拠）

最終更新: 2026-02-10

対象:

- Plugin A: `app/openai_gpt5_responses`
- Plugin B: `app/gpt5_agent_strategies`

## 1. 目的

Dify 上の実動作を手動確認し、以下を判定する。

- GPT-5 系モデル呼び出しが成功する
- Agent Strategy（Function Calling / ReAct）が tool 呼び出し込みで完走する
- 不正入力時に fail-closed で停止し、原因追跡ができる

## 2. 前提条件

- Dify Plugin Management にアクセスできる
- Dify Debug Plugin の `Host/Port/Debug Key` を取得済み
- OpenAI API キーを利用可能
- ローカルに `uv` と `python3` がある
- `.difypkg` 再検証を行う場合は `dify` CLI が利用可能

## 3. 事前準備

### 3.1 Plugin A

```bash
cd /home/devuser/workspace/app/openai_gpt5_responses
cp .env.example .env
```

`.env` を更新:

```dotenv
INSTALL_METHOD=remote
REMOTE_INSTALL_HOST=<DEBUG_PLUGIN_HOST>
REMOTE_INSTALL_PORT=<DEBUG_PLUGIN_PORT>
REMOTE_INSTALL_KEY=<DEBUG_PLUGIN_KEY>
```

依存導入:

```bash
uv pip install -r requirements.txt
```

### 3.2 Plugin B

```bash
cd /home/devuser/workspace/app/gpt5_agent_strategies
cp .env.example .env
```

`.env` を更新:

```dotenv
INSTALL_METHOD=remote
REMOTE_INSTALL_HOST=<DEBUG_PLUGIN_HOST>
REMOTE_INSTALL_PORT=<DEBUG_PLUGIN_PORT>
REMOTE_INSTALL_KEY=<DEBUG_PLUGIN_KEY>
```

依存導入:

```bash
uv pip install -r requirements.txt
```

## 4. ローカル回帰（Dify 接続前）

```bash
cd /home/devuser/workspace
uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies
uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies
```

期待結果:

- すべて PASS
- coverage fail-under（85%）を下回らない

## 5. Plugin A 手動検証（OpenAI GPT-5 Responses）

### 5.1 起動

```bash
cd /home/devuser/workspace/app/openai_gpt5_responses
uv run python -m main
```

監査ログ確認を行う場合:

```bash
cd /home/devuser/workspace/app/openai_gpt5_responses
OPENAI_GPT5_AUDIT_LOG=true uv run python -m main
```

期待ログ:

- `openai_gpt5_audit {"event":"responses_api_request", ...}`
- `openai_gpt5_audit {"event":"responses_api_success", ...}`
- 失敗時は `responses_api_error` と `status_code` / `request_id` を含む

### 5.2 Dify 側設定

- Provider: `OpenAI GPT-5 Responses`
- Credentials:
  - `openai_api_key`（必須）
  - `openai_organization`（任意）
  - `openai_api_base`（任意）
  - `request_timeout_seconds`（任意、既定 300）
  - `max_retries`（任意、既定 1）

### 5.3 テストケース

1. A-01 正常: `gpt-5.2-pro` で短文応答
- 入力: 「3行で自己紹介して」
- 期待: 応答成功（認証/接続エラーなし）

2. A-02 正常: stream 切替
- 条件1: `enable_stream=true`
- 条件2: `enable_stream=false`
- 期待: いずれも応答成功し、応答方式が切り替わる

3. A-03 正常: JSON schema 応答
- 条件: `response_format=json_schema` + 妥当な `json_schema`
- 期待: 構造化出力が返る

4. A-04 異常: schema 未指定
- 条件: `response_format=json_schema` かつ `json_schema` 空
- 期待: 入力検証エラーで失敗

5. A-05 異常: 無効 API キー
- 条件: `openai_api_key` を無効値に変更
- 期待: 認証エラーで失敗

6. A-06 異常: 存在しない model
- 条件: 未存在モデル名を指定
- 期待: model not found 系で失敗

7. A-07 正常: `reasoning_summary` 切替
- 条件: `reasoning_summary=auto/concise/detailed` を順に指定
- 期待: いずれも実行成功（サポート外値では入力検証エラー）

8. A-08 異常: bool-like 不正値
- 条件: `enable_stream=yes` または `parallel_tool_calls=no`
- 期待: bool-like 検証エラーで失敗

## 6. Plugin B 手動検証（GPT-5 Agent Strategies）

### 6.1 起動

```bash
cd /home/devuser/workspace/app/gpt5_agent_strategies
uv run python -m main
```

### 6.2 Dify 側設定

- Strategy Provider: `GPT-5 Agent`
- Strategy:
  - `gpt5_function_calling`
  - `gpt5_react`
- `model` は Plugin A の GPT-5 系を指定
- `tools` は最低 1 つ設定

### 6.3 テストケース

1. B-01 正常: Function Calling で tool invoke
- 入力: 「使えるツールで必要情報を取得して要約して」
- 期待: tool 実行ログと最終回答を確認

2. B-02 正常: ReAct で tool invoke
- 入力: B-01 と同等
- 期待: tool 実行を経て最終回答まで到達

3. B-03 制御: `maximum_iterations=1`
- 期待: 早期停止し無限ループしない

4. B-04 制御: `maximum_iterations=6`
- 期待: 複数ラウンドで推論と tool 呼び出しが継続可能

5. B-05 安全: 不正 tool arguments
- 条件: ツール引数を JSON 不正にする
- 期待: fail-closed（危険な実行に進まない）

6. B-06 表示: `emit_intermediate_thoughts=true/false`
- 条件1: `true`
- 条件2: `false`
- 期待: `false` 時は `<think>` がユーザー表示に出ない

7. B-07 正常: `prompt_policy_overrides` JSON 上書き
- 条件: `tool_preamble_policy` など既知キーを JSON で指定
- 期待: 指定キーのみ上書きされ、未知キーは無視される

## 7. 連携シナリオ（A+B）

1. Agent App で以下を設定:
- Model Provider: Plugin A
- Agent Strategy: Plugin B
2. tool が必要な質問を実行
3. 期待:
- モデル応答
- tool invoke
- 最終回答
が一連で完了

## 8. `.difypkg` 再検証

```bash
dify plugin package /home/devuser/workspace/app/openai_gpt5_responses
dify plugin package /home/devuser/workspace/app/gpt5_agent_strategies
```

生成 `.difypkg` を Dify へ `Install Plugin -> Via Local File` で導入し、5章〜7章を再実行する。

## 9. 障害切り分け（stream disconnected）

1. Plugin A/B を片方ずつ起動して再試行
2. `.env` の `REMOTE_INSTALL_HOST/PORT/KEY` を再確認
3. 同一ケースを 30 秒間隔で 2 回再試行
4. `enable_stream=false` で再試験し stream 固有障害かを判定
5. 記録項目:
- 発生日時
- モデル名
- 入力
- エラーメッセージ全文
- `OPENAI_GPT5_AUDIT_LOG=true` の監査ログ

## 10. 判定基準（合格）

1. A-01, A-02, A-03, A-07 が成功
2. A-04, A-05, A-06, A-08 が期待どおり失敗
3. B-01, B-02, B-03, B-04, B-05, B-06, B-07 が期待どおり
4. 7章の連携シナリオが完了
5. `.difypkg` 再検証で挙動差分がない

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
A-07:
A-08:

[Plugin B]
B-01:
B-02:
B-03:
B-04:
B-05:
B-06:
B-07:

[Integration]
A+B:

[Package]
package_retest:

[Notes]
```
