# Ragas + OpenAI / Azure OpenAI 利用ノート (2026-03-11)

このドキュメントは、`notebooks/ragas.ipynb` の完成と、OpenAI / Azure OpenAI 利用に関するやり取りを記録したものです。

## 1. Ragas Notebook の構成

### 1.1 完成した Notebook の構成

- **Cell 0 (markdown)**: 前提説明（`OPENAI_API_KEY`、`RAGAS_OPENAI_MODEL`、実行順）
- **Cell 1**: 空
- **Cell 2**: セットアップ（`load_dotenv`, `AsyncOpenAI`, `llm_factory`）
- **Cell 3**: サンプル入力（`question`, `answer`, `contexts`）
- **Cell 4**: 評価実行（`RubricsScoreWithoutReference`, `ascore`, 結果表示）

### 1.2 ragas 0.4.3 の API 形状

- `RubricsScoreWithoutReference` は `LangchainLLMWrapper` を**受け付けない**
- `InstructorBaseRagasLLM`（`llm_factory` 経由）が必須
- 初期化: `from openai import AsyncOpenAI` + `from ragas.llms import llm_factory`
- `llm = llm_factory(model, client=AsyncOpenAI(...))`

---

## 2. Azure OpenAI への切り替え

### 2.1 環境変数（`.env`）

```bash
OPENAI_API_KEY=<Azure の API キー>
OPENAI_BASE_URL=https://<resource-name>.openai.azure.com/openai/deployments/<deployment-name>
RAGAS_OPENAI_MODEL=<deployment-name>
```

### 2.2 レガシー API（api-version が必要な場合）

```python
client_kwargs["default_query"] = {"api-version": "2024-02-15-preview"}
```

### 2.3 AsyncAzureOpenAI を使う場合（推奨）

```python
from openai import AsyncAzureOpenAI

client = AsyncAzureOpenAI(
    azure_endpoint="https://YOUR-RESOURCE.openai.azure.com/",
    azure_deployment="gpt-4o-mini",
    api_version="2024-02-15-preview",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)
llm = llm_factory("gpt-4o-mini", client=client)
```

- `api_version` は自動付与
- `api-key` ヘッダーを自動設定
- Azure AD トークン対応

---

## 3. embedding_deployment の指定

### 3.1 チャットと埋め込みで別デプロイを使う場合

チャット用と埋め込み用で**別クライアント**を用意する。

```python
# チャット用
llm_client = AsyncAzureOpenAI(..., azure_deployment="gpt-4o-mini")
# 埋め込み用
embedding_client = AsyncAzureOpenAI(..., azure_deployment="text-embedding-3-small")

llm = llm_factory("gpt-4o-mini", client=llm_client)
embeddings = embedding_factory("openai", model="text-embedding-3-small", client=embedding_client)
```

### 3.2 注意

- `RubricsScoreWithoutReference` は埋め込みを使わない
- `faithfulness` など埋め込みを使うメトリクスでは `embeddings` を渡す必要がある

---

## 4. max_tokens / max_completion_tokens エラー

### 4.1 現象

```
Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.
```
（400 エラー、gpt-5-mini 使用時）

### 4.2 原因

GPT-5 系は Reasoning token 対応のため、`max_tokens` ではなく `max_completion_tokens` が必須。

### 4.3 ragas の対応

ragas 0.4.3 では `_map_openai_params` で gpt-5 系・o 系モデル向けに `max_tokens` → `max_completion_tokens` を自動変換している。

### 4.4 対処

- ragas を 0.4.3 以上に更新
- または `llm_factory(..., max_completion_tokens=4096)` を明示指定

---

## 5. provider="azure" によるエラー

### 5.1 現象

```
ValueError: Failed to initialize azure client with instructor adapter.
Error: Failed to patch azure client with Instructor: 'AsyncAzureOpenAI' object has no attribute 'message'
```

### 5.2 原因

`provider="azure"` のとき、ragas が `_patch_client_for_provider` を呼び、`client.messages.create` を参照する。  
OpenAI / Azure OpenAI クライアントは `client.chat.completions` を持ち、`client.messages` は**存在しない**（LiteLLM 用の API）。

### 5.3 対処

**`provider="openai"` のまま使う**（推奨）。  
`AsyncAzureOpenAI` は `AsyncOpenAI` のサブクラスで、`from_openai` で正しく動作する。

```python
# provider は指定しない（デフォルト "openai"）か、明示的に "openai"
llm = llm_factory("gpt-5-mini", client=client)
```

`_map_openai_params` は `provider in ("openai", "azure")` の両方で同じパラメータマッピングを行う。

---

## 6. LiteLLM を使うべきか

### 6.1 現状（OpenAI SDK）でよい場合

- OpenAI と Azure OpenAI のどちらか（または両方）で十分
- 構成をシンプルに保ちたい

### 6.2 LiteLLM を検討する場合

- 複数プロバイダ（OpenAI / Azure / Anthropic など）を切り替えたい
- 本番でルーティングやフェイルオーバーを入れたい

ragas は `LiteLLMStructuredLLM` で LiteLLM をサポートしている。

---

## 7. `InstructorRetryException` / `max_tokens` 長さ上限による中断

### 7.1 現象

`azure/gpt-5-mini` ではなく `gpt-5-mini` を使うように直したあと、次の例外が出ることがある。

```text
InstructorRetryException: <failed_attempts>

<generation number="1">
<exception>
    The output is incomplete due to a max_tokens length limit.
</exception>
...
```

### 7.2 この例外が出る実際の経路

`notebooks/ragas.ipynb` は `RubricsScoreWithoutReference(llm=llm)` を使っており、内部では次の順で処理される。

1. `metric.ascore(...)`
2. `RubricScorePrompt.to_string(...)` で評価 prompt を文字列化
3. `await llm.agenerate(prompt_str, RubricScoreOutput)` を実行
4. `llm_factory("gpt-5-mini", client=AsyncOpenAI(...))` で生成された `InstructorLLM` が `self.client.chat.completions.create(...)` を呼ぶ
5. Instructor が OpenAI JSON mode で構造化出力を要求する
6. OpenAI 応答の `finish_reason == "length"` だと `IncompleteOutputException("The output is incomplete due to a max_tokens length limit.")` を送出
7. Instructor の retry 層がこれを失敗履歴として集め、再試行上限に達すると `InstructorRetryException` に変換する

重要なのは、これは **Azure/OpenAI の接続初期化エラーではなく、生成自体は始まったあとに「出力が途中で切れた」ために起きる例外** だという点。

### 7.3 ローカル実環境で確認できた事実

- `notebooks/ragas.ipynb` では `llm_factory(openai_model, client=client)` のみを呼んでおり、`max_tokens` / `max_completion_tokens` は明示していない
- `.venv` 実環境では `ragas==0.4.3`, `openai==2.26.0`, `instructor==1.14.4`
- `ragas.llms.base.InstructorModelArgs` の既定値は `temperature=0.01`, `top_p=0.1`, `max_tokens=1024`
- `llm_factory("gpt-5-mini", client=AsyncOpenAI(...))` をそのまま作ると、`InstructorLLM._map_provider_params()` の結果は以下になる

```python
{'temperature': 1.0, 'max_completion_tokens': 1024}
```

つまり、**gpt-5-mini に対しては既定の `max_tokens=1024` がそのまま `max_completion_tokens=1024` に変換されて送られている**。

### 7.4 なぜ `gpt-5-mini` で起きやすいか

`ragas 0.4.3` の `_map_openai_params()` 自体が、GPT-5 / o-series について次の前提で分岐している。

- `max_tokens` は `max_completion_tokens` に変換する
- `temperature` は `1.0` に固定する
- `top_p` は外す
- **構造化出力では既定の 1024 が足りないことがあり、4096+ を検討すべき**

今回の notebook の rubric 評価 prompt は、ローカル計測でだいたい次の規模だった。

- rubric prompt 本体: 約 682 tokens
- Instructor JSON mode が追加する schema 指示: 約 165 tokens
- 合計 prompt 長: 約 847 tokens

出力モデル `RubricScoreOutput` 自体は `feedback: str` と `score: int` だけで小さいが、rubric の説明文・few-shot 例・JSON schema 指示が入るため prompt はそこそこ長い。ここに GPT-5 系の構造化出力が重なると、**既定の `max_completion_tokens=1024` では完走できず `finish_reason="length"` になる**。

補足:

- `IncompleteOutputException` は validation error 扱いではなく一般例外扱い
- そのため Instructor は「壊れた JSON を直させる再質問」ではなく、**ほぼ同じリクエストをそのまま再試行**する
- 予算不足が原因なら、再試行しても同じ失敗を繰り返しやすい

### 7.5 直接の原因

今回の主因は **モデル名ではなく completion token 予算不足**。

- `azure/gpt-5-mini` → `gpt-5-mini` の修正で「モデル名/プロバイダ解決」の問題は解消
- その次の段階で、`gpt-5-mini` 向け既定値 `max_completion_tokens=1024` が露出
- その予算では rubric 評価の構造化出力が最後まで返りきらず、Instructor が `InstructorRetryException` に包み直している

### 7.6 対処

最優先は completion token 予算を増やすこと。

```python
llm = llm_factory(
    "gpt-5-mini",
    client=client,
    max_completion_tokens=4096,
)
```

`ragas 0.4.3` では次も実質同義で使える。

```python
llm = llm_factory(
    "gpt-5-mini",
    client=client,
    max_tokens=4096,
)
```

追加で有効な対処:

- rubric prompt を短くする
- `feedback` を簡潔に返す custom prompt / custom metric にする
- rubric 専用評価だけ `gpt-4o-mini` など別モデルに切り替える
- 例外発生時に `e.failed_attempts` を見て、各試行がすべて length-limit 失敗か確認する

### 7.7 切り分け時の見方

この例外は次のように読めばよい。

- `ValueError: Failed to initialize ...` 系: クライアント初期化/adapter 問題
- `Unsupported parameter: max_tokens ...` 系: GPT-5 系へのパラメータ名不一致
- `InstructorRetryException` + `The output is incomplete due to a max_tokens length limit.`: **生成は始まっているが、completion token 上限で途中打ち切り**

### 7.8 環境メモ

初回確認時点では `uv.lock` 上は `instructor==1.14.5` だが、`.venv` の `instructor.__version__` は `1.14.4` を返していた。

その後 `uv sync --locked` を実行すると、パッケージ metadata と `uv pip show` / `uv tree` は `instructor==1.14.5` に揃った。  
ただし `instructor/__init__.py` 自体に `__version__ = "1.14.4"` がハードコードされており、**`import instructor; instructor.__version__` だけは 1.14.4 を返す**。

つまり、これは uv 環境の未同期が一部あったことに加えて、**Instructor 1.14.5 配布物の `__version__` 定数が古い**ことが重なって見えていた。

---

## 8. 関連ファイル

- `notebooks/ragas.ipynb` - 完成したサンプル Notebook
- `pyproject.toml` - ragas, langchain-openai, openai の依存
- `ragas/llms/base.py` - `_get_instructor_client`, `_patch_client_for_provider`, `_map_openai_params`

---

## 9. 参照

- [OpenAI API: max_tokens to max_completion_tokens](https://community.openai.com/t/why-was-max-tokens-changed-to-max-completion-tokens/938077)
- [Azure OpenAI reasoning models](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/reasoning)
- ragas 0.4.3 `_map_openai_params` (gpt-5, o-series の max_completion_tokens マッピング)
