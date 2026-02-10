# Repo Implementation Workflow

## Objective
- 設計で確定した契約を、YAML・Python・テストへ一貫反映する。

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

## Step 2: Implement runtime behavior
1. provider/tool/model/strategy のPython実装を更新する。
2. 例外処理とメッセージ方針を統一する。
3. 機密情報や内部パスをユーザー出力に露出しない。

## Step 3: Implement tests
1. 対応する `tests/<plugin>` を更新または追加する。
2. 正常系と失敗系を最小1件ずつ入れる。
3. 既知不具合の回帰ケースを追加する。
4. baselineと同等責務のテスト深度を確認する。
   - stream/error/schema の主要パスを落とさない。

## Step 4: Run verification commands
```bash
uv run ruff check app/<plugin> tests/<plugin>
uv run pytest -q --no-cov tests/<plugin>
uv run pytest -q tests/<plugin>
dify plugin package ./app/<plugin>
diff -rq app/<baseline_plugin> app/<plugin>
diff -rq tests/<baseline_plugin> tests/<plugin>
```

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
