# Repo Implementation Workflow

## Objective
- 設計で確定した契約を、YAML・Python・テストへ一貫反映する。

## Step -1: Environment preflight
1. 実行前にツール依存を確認する。

```bash
uv run ruff --version
uv run pytest --version
dify --version
```

2. いずれかが失敗した場合は、実装に進まず環境不足として記録する。

## Step 0: Confirm scaffold completeness for new plugins
1. 新規plugin作成時は次を先に揃える。
   - `_assets/icon.svg`
   - `README.md`
   - `PRIVACY.md`
   - `.env.example`
   - `requirements.txt`
2. `manifest.yaml` と配布補助ファイルの参照関係を確定する。

## Step 1: Implement schema and metadata changes
1. `manifest.yaml` を更新する。
2. 参照される provider/tool/model/strategy YAML を更新する。
3. `manifest.yaml` の `plugins.*` と実在ファイルの対応を再確認する。
4. `dify plugin package` の required fields を満たす。
   - `Resource.Memory`
   - `Meta.Version`
   - `Meta.Arch`
   - `Meta.Runner.Language`
   - `Meta.Runner.Version`
   - `Meta.Runner.Entrypoint`
   - `CreatedAt`

## Step 2: Implement runtime behavior
1. provider/tool/model/strategy のPython実装を更新する。
2. 例外処理とメッセージ方針を統一する。
3. 機密情報や内部パスをユーザー出力に露出しない。
4. LLM provider実装では契約ゲートを満たす。
   - abstract methods を解消する。
   - `LLMResultChunkDelta` の必須項目（`index`, `message` など）を満たす。
   - payload strictness（bool coercion / json_schema要件 / verbosity配置）をbaseline契約へ合わせる。

## Step 3: Implement tests
1. 対応する `tests/<plugin>` を更新または追加する。
2. 正常系と失敗系を最小1件ずつ入れる。
3. 既知不具合の回帰ケースを追加する。
4. baseline主要責務（entrypoint/error, llm stream flag, messages, payloads, bool coercion, provider runtime/schema）を網羅する。
5. line-count sanity check を実行し、深度不足（ratio < 0.40）を可視化する。

## Step 4: Run verification commands
```bash
uv run ruff check app/<plugin> tests/<plugin>
uv run pytest -q --no-cov tests/<plugin>
uv run pytest -q tests/<plugin>
dify plugin package ./app/<plugin>
diff -rq --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.venv' app/<baseline_plugin> app/<plugin>
diff -rq --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.venv' tests/<baseline_plugin> tests/<plugin>
wc -l tests/<baseline_plugin>/*.py tests/<plugin>/*.py
```

LLM providerでは、上記コマンドに加えて以下の preflight を必ず実行する。
- abstract methods が空であること
- chunk schema が成立すること（signature-adaptive 実行）
- payload strictness が期待どおり例外を返すこと
- `NO_CHUNK_METHOD` と `BOOL_STRICT_FAIL` が出ないこと

`openai_gpt5_responses` と `gpt5_agent_strategies` をまたぐ変更は次を使う。

```bash
uv run ruff check app/openai_gpt5_responses app/gpt5_agent_strategies tests/openai_gpt5_responses tests/gpt5_agent_strategies
uv run pytest -q --no-cov tests/openai_gpt5_responses tests/gpt5_agent_strategies
uv run pytest -q tests/openai_gpt5_responses tests/gpt5_agent_strategies
```

## Step 5: Validate completion
1. 変更ファイルが設計時の対象に一致する。
2. YAMLとPythonの契約不整合がない。
3. `dify plugin package` が成功している。
4. lint/test/package結果を記録できる。
5. coverage失敗時は閾値問題と機能回帰問題を分離して説明できる。
6. 残課題を明示できる。
7. LLM provider時は abstract/chunk/payload の再現証跡を添付できる。
8. one-pass運用では hard-fail 0件 + 最低80点（推奨90点以上）まで達する。

## Step 6: Collaboration artifacts (ai-agent-collaboration-exec)
1. 協調実行時は次を成果物として保存する。
   - pipeline spec JSON
   - subagent prompts
   - contract output
2. サブエージェント評価時は required artifacts と hash結果を保存する。
3. `handoff_SHA256SUMS.txt` がある場合は追加検証結果も保存する。
4. 保存先は `docs/ai-agent-reviews/` と `memory-bank/06-project/context/*_artifacts/` を標準とする。
