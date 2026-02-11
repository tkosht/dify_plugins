# Generic Implementation Workflow

## Objective
- 任意リポジトリでDifyプラグイン変更を安全に実装し、検証可能な状態にする。

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
2. `manifest.yaml` から参照する補助ファイルを先に確定する。

## Step 1: Update metadata and schemas
1. `manifest.yaml` を更新する。
2. provider/tool/model/strategy YAML を更新する。
3. `manifest.yaml` の参照パスと実ファイル存在を確認する。
4. `dify plugin package` の required fields を満たす。
   - `Resource.Memory`
   - `Meta.Version`
   - `Meta.Arch`
   - `Meta.Runner.Language`
   - `Meta.Runner.Version`
   - `Meta.Runner.Entrypoint`
   - `CreatedAt`

## Step 2: Update runtime code
1. 対応するPythonエントリポイントを更新する。
2. 例外処理を明確化する。
3. 機密情報を出力しない。
4. LLM provider実装では契約ゲートを満たす。
   - abstract methods を解消する。
   - `LLMResultChunkDelta` の必須項目（`index`, `message` など）を満たす。
   - payload strictness（bool coercion / json_schema要件 / verbosity配置）をbaseline契約へ合わせる。

## Step 3: Update tests
1. 対応する test ディレクトリを特定する。
2. 正常系と失敗系を追加する。
3. 既知不具合の回帰ケースを追加する。
4. baseline主要責務（entrypoint/error, llm stream flag, messages, payloads, bool coercion, provider runtime/schema）を網羅する。
5. line-count sanity check を実行し、深度不足（ratio < 0.40）を可視化する。

## Step 4: Preflight gates (fail-fast)
1. 実装完了前に fail-fast チェックを行う。
2. 次のいずれかが失敗したら、Step 1-3へ戻して修正する。

```bash
uv run ruff check <plugin-path> <test-path>
dify plugin package <plugin-path>
```

3. LLM providerでは次の契約検証を preflight に含める。
   - `__abstractmethods__` が空であること
   - chunk schema が成立すること（signature-adaptive 実行）
   - payload strictness が期待どおり例外を返すこと
   - `NO_CHUNK_METHOD` / `BOOL_STRICT_FAIL` が出ないこと

## Step 5: Run full gates
```bash
uv run ruff check <plugin-path> <test-path>
uv run pytest -q --no-cov <test-path>
uv run pytest -q <test-path>
dify plugin package <plugin-path>
diff -rq --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.venv' <baseline-plugin-path> <plugin-path>
diff -rq --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.venv' <baseline-test-path> <test-path>
wc -l <baseline-test-path>/*.py <test-path>/*.py
```

プロジェクト標準コマンドがある場合はそちらを優先する。

## Step 6: Confirm implementation readiness
1. 設計時に定義した受け入れ条件を満たす。
2. packageが成功している。
3. lint/test/package結果を添えて報告できる。
4. coverage失敗時は閾値問題と機能回帰問題を分離して説明できる。
5. 既知制約と残リスクを説明できる。
6. LLM provider時は abstract/chunk/payload の再現証跡を添付できる。
7. one-pass運用時は hard-fail 0件 + 最低80点（推奨90点以上）を満たしてから最終化する。
8. one-pass未達時は「実装完了」と扱わず、修正ループへ戻す。

## Step 7: Collaboration artifacts (ai-agent-collaboration-exec)
1. 協調実行時は次を成果物として保存する。
   - pipeline spec JSON
   - subagent prompts
   - contract output
2. サブエージェント評価時は required artifacts と hash結果を保存する。
3. `handoff_SHA256SUMS.txt` がある場合は追加検証結果も保存する。
4. 保存先は `docs/ai-agent-reviews/` と `memory-bank/06-project/context/*_artifacts/` を標準とする。
