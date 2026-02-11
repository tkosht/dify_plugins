# OpenAI Responses Provider Subagent Parity Evaluation (2026-02-10)

## Objective

- `dify-plugin-dev-generic` を使ったサブエージェント実装結果 (`openai_responses_provider`) を、baseline (`openai_gpt5_responses`) と比較して定量評価する。
- 評価結果を「そのまま再実装に着手できる」決定完了仕様として記録し、開発元エージェント間で再利用可能にする。

## Scope and Baseline

- Target plugin:
  - `app/openai_responses_provider`
  - `tests/openai_responses_provider`
- Baseline plugin:
  - `app/openai_gpt5_responses`
  - `tests/openai_gpt5_responses`
- Scoring policy:
  - `.claude/skills/dify-plugin-dev-generic/references/baseline-parity-evaluation.md`
  - 配点: Interface 30 / Runtime 30 / Test 25 / Release 10 / Docs 5
  - 合格目安: 80点以上

## Anti-Cheat Execution Constraints (Observed)

- Isolated workspace を使用:
  - `/tmp/openai_responses_provider_subagent_20260211_021117_clean`
- Baseline artifact を事前に隔離環境から除外:
  - `app/openai_gpt5_responses` 不在
  - `tests/openai_gpt5_responses` 不在
  - `openai_gpt5_responses*.difypkg` 不在
- サブエージェントへ禁止制約を明示:
  - `git log/show` 禁止
  - 外部URL/外部ネットワーク参照禁止
  - 作業ディレクトリ外アクセス禁止
- 生成物に baseline 参照文字列が残っていないことを確認:
  - `rg -n "openai_gpt5_responses" app/openai_responses_provider tests/openai_responses_provider` -> hit なし

## Verification Commands and Results

実施環境: `/home/devuser/workspace` (親エージェント再実行結果)

1. Lint

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/openai_responses_provider tests/openai_responses_provider
```

- Result: success (`All checks passed!`)

2. Functional regression (no coverage gate)

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q --no-cov tests/openai_responses_provider
```

- Result: success (`10 passed`)

3. Project default test gate (with coverage)

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q tests/openai_responses_provider
```

- Result: fail
- Detail: tests は `10 passed` だが、repo 全体 coverage gate (`fail-under=85`) で失敗 (`TOTAL 12.25%`)

4. Packaging

```bash
dify plugin package app/openai_responses_provider
```

- Result: success (`openai_responses_provider.difypkg`)

## Scorecard (100 points)

| Dimension | Max | Score | Rationale |
|---|---:|---:|---|
| Interface contract parity | 30 | 18 | provider/model 契約は概ね揃うが、baseline 比で schema と model 定義情報量が不足 |
| Runtime behavior parity | 30 | 7 | LLM 実装に抽象メソッド未実装、chunk 生成契約違反、payload 契約差異あり |
| Test depth and reproducibility | 25 | 6 | 7カテゴリは存在するが深度不足。baseline 1706行に対して target 378行 |
| Release readiness | 10 | 7 | lint/no-cov/package は成功。default pytest は coverage gate で失敗 |
| Documentation and distribution files | 5 | 5 | 必須配布ファイルは揃っている |
| **Total** | **100** | **43** | **Fail (<80)** |

## Critical Gaps (Evidence-Based)

### 1) LLM class が抽象メソッド未実装

- Symptom:
  - `OpenAIResponsesLargeLanguageModel.__abstractmethods__ == {'_invoke_error_mapping', 'get_num_tokens'}`
- Impact:
  - SDK 契約として不完全。実ランタイムで初期化/呼び出し時の破綻リスク。
- Evidence:
  - `app/openai_responses_provider/models/llm/llm.py:31`
  - Baseline comparison: `app/openai_gpt5_responses/models/llm/llm.py:81` (abstract methods 解消済み)

### 2) `LLMResultChunkDelta` 必須項目 `index` 未設定

- Symptom:
  - `_chunk()` と `_tool_call_chunk()` で `LLMResultChunkDelta(message=...)` のみを生成。
  - 実測で `ValidationError: index Field required`
- Impact:
  - stream chunk が有効な Dify schema を満たさず、実運用で失敗。
- Evidence:
  - `app/openai_responses_provider/models/llm/llm.py:219`
  - `app/openai_responses_provider/models/llm/llm.py:247`
  - Required signature 参照: `LLMResultChunkDelta(*, index, message, usage=None, finish_reason=None)`
  - Baseline chunk builder: `app/openai_gpt5_responses/models/llm/llm.py:257`

### 3) Payload builder が strict validation 契約と不一致

- Symptom:
  - `coerce_bool()` は permissive で ValueError を出さない (`yes/on` を許容)
  - `response_format=json_schema` の必須 schema チェックが不十分
  - `verbosity` を top-level (`request["verbosity"]`) に配置
- Impact:
  - API契約逸脱、異常値の黙殺、期待しないリクエスト構造生成。
- Evidence:
  - Target permissive: `app/openai_responses_provider/internal/payloads.py:13`
  - Target verbosity placement: `app/openai_responses_provider/internal/payloads.py:64`
  - Baseline strict bool: `app/openai_gpt5_responses/internal/payloads.py:20`
  - Baseline schema required: `app/openai_gpt5_responses/internal/payloads.py:149`
  - Baseline text block: `app/openai_gpt5_responses/internal/payloads.py:147`

### 4) Stream handling の完成度不足

- Symptom:
  - `response.completed` から usage/final finish_reason を終端 chunk に反映していない。
  - エラー詳細抽出と監査イベントの粒度が baseline より大きく不足。
- Impact:
  - usage 計上、終了理由、監査性の劣化。
- Evidence:
  - Target stream implementation: `app/openai_responses_provider/models/llm/llm.py:111`
  - Baseline stream completion/usage: `app/openai_gpt5_responses/models/llm/llm.py:458`
  - Baseline stream error extraction: `app/openai_gpt5_responses/models/llm/llm.py:137`

### 5) Provider/model schema の情報不足

- Symptom:
  - `provider` の `models.llm.predefined` が3モデル固定で baseline より狭い
  - model yaml で `model_properties.context_size` 未定義
  - `reasoning_effort` options が baseline より不足 (`none/minimal/xhigh` 欠落)
- Impact:
  - baseline 同等の互換性/選択性を満たせない。
- Evidence:
  - Target provider models list: `app/openai_responses_provider/provider/openai_responses_provider.yaml:99`
  - Baseline wildcard + position: `app/openai_gpt5_responses/provider/openai_gpt5.yaml:103`
  - Target options: `app/openai_responses_provider/models/llm/gpt-5.2.yaml:26`
  - Baseline options: `app/openai_gpt5_responses/models/llm/gpt-5.2.yaml:38`

### 6) Dependencies 不足

- Symptom:
  - target requirements は `openai>=1.0.0` のみ
- Impact:
  - baseline 相当の実行互換 (`dify-plugin`, `httpx`) を担保できない。
- Evidence:
  - `app/openai_responses_provider/requirements.txt:1`
  - Baseline: `app/openai_gpt5_responses/requirements.txt:1`

### 7) Test depth が baseline 比で不足

- Symptom:
  - test line count: baseline 1706 / target 378
  - stream/runtime の異常系・契約テストが大幅不足
- Impact:
  - 回帰検出力と再現性が低い。
- Evidence:
  - `tests/openai_responses_provider/test_llm_stream_flag.py:1` (52 lines)
  - `tests/openai_gpt5_responses/test_llm_stream_flag.py:1` (842 lines)

## Reproducible Evidence

```bash
# Diff (cache除外)
diff -rq -x '__pycache__' -x '*.pyc' app/openai_gpt5_responses app/openai_responses_provider
diff -rq -x '__pycache__' -x '*.pyc' tests/openai_gpt5_responses tests/openai_responses_provider

# Test depth comparison
wc -l tests/openai_gpt5_responses/*.py tests/openai_responses_provider/*.py

# Abstract methods check
UV_CACHE_DIR=/tmp/uv-cache uv run python - <<'PY'
import sys
sys.path.insert(0,'app')
from openai_responses_provider.models.llm.llm import OpenAIResponsesLargeLanguageModel
print(sorted(OpenAIResponsesLargeLanguageModel.__abstractmethods__))
PY

# Chunk schema violation repro
UV_CACHE_DIR=/tmp/uv-cache uv run python - <<'PY'
import sys
sys.path.insert(0,'app')
from openai_responses_provider.models.llm.llm import OpenAIResponsesLargeLanguageModel
class Impl(OpenAIResponsesLargeLanguageModel):
    @property
    def _invoke_error_mapping(self): return {}
    def get_num_tokens(self, model, credentials, prompt_messages, tools=None): return 0
obj = object.__new__(Impl)
obj._chunk(model='demo', prompt_messages=[], text='hi')
PY
```

## Remediation Spec (Decision-Complete)

### Priority P0 (must fix before parity re-score)

1. Complete LLM interface contract
- Files:
  - `app/openai_responses_provider/models/llm/llm.py`
- Required changes:
  - `_invoke_error_mapping` property を実装
  - `get_num_tokens()` を実装
  - `_chunk()` / `_tool_call_chunk()` で `LLMResultChunkDelta(index=..., message=..., finish_reason=..., usage=...)` を明示
  - stream chunk index を monotonically increment する state を追加

2. Align payload validation with baseline contract
- Files:
  - `app/openai_responses_provider/internal/payloads.py`
- Required changes:
  - `coerce_bool_strict(field_name=...)` 導入（許容値以外は ValueError）
  - `response_format=json_schema` の場合 `json_schema` 必須化
  - `verbosity` は `payload["text"]["verbosity"]` に格納
  - `text.format` を `text` / `json_schema` で baseline と同等化

3. Ensure runtime-safe result construction
- Files:
  - `app/openai_responses_provider/models/llm/llm.py`
- Required changes:
  - blocking `_invoke` で `LLMResult.usage` を valid `LLMUsage` へ整合
  - stream 終端で completion event から usage/final reason を反映

### Priority P1 (parity uplift)

4. Expand model/provider schema parity
- Files:
  - `app/openai_responses_provider/provider/openai_responses_provider.yaml`
  - `app/openai_responses_provider/models/llm/*.yaml`
  - `app/openai_responses_provider/models/llm/_position.yaml`
- Required changes:
  - predefined models を baseline 同等に拡張 (`gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-5-codex`, `gpt-5.1-codex`)
  - `reasoning_effort` options を `none/minimal/low/medium/high/xhigh` へ一致
  - `model_properties.mode/context_size` を baseline 準拠

5. Dependency parity
- Files:
  - `app/openai_responses_provider/requirements.txt`
- Required changes:
  - `dify-plugin>=0.6.0,<0.7.0`
  - `openai>=2.17.0,<3`
  - `httpx>=0.28.0,<1`

### Priority P2 (test depth parity)

6. Strengthen tests to baseline-equivalent depth
- Files:
  - `tests/openai_responses_provider/test_llm_stream_flag.py`
  - `tests/openai_responses_provider/test_payloads.py`
  - `tests/openai_responses_provider/test_payloads_bool_coercion.py`
  - `tests/openai_responses_provider/test_messages.py`
  - `tests/openai_responses_provider/test_provider_runtime.py`
  - `tests/openai_responses_provider/test_entrypoints_and_errors.py`
- Required changes:
  - invalid bool input で ValueError
  - json_schema mandatory check
  - stream error events (`error/response.failed/response.incomplete`) 変換
  - usage/final chunk 検証
  - import fallback (`without app package`) 検証
  - audit log redaction 検証

## Acceptance Criteria

1. Interface completeness
- `OpenAIResponsesLargeLanguageModel.__abstractmethods__ == frozenset()`

2. Runtime schema validity
- stream chunk 生成で `LLMResultChunkDelta` validation error が発生しない

3. Payload contract
- bool strict coercion が baseline 同等
- `response_format=json_schema` で schema 必須
- `text.verbosity` 形式一致

4. Tests and packaging
- `uv run ruff check app/openai_responses_provider tests/openai_responses_provider` success
- `uv run pytest -q --no-cov tests/openai_responses_provider` success
- `dify plugin package app/openai_responses_provider` success
- coverage gate 失敗は全体閾値由来と機能失敗を切り分け報告

5. Parity threshold
- re-score >= 80/100

## Follow-up Tasks for Skill Maintainer

1. `dify-plugin-dev-generic` の parity 評価テンプレに、以下の「必須再現証跡」を追加:
- abstractmethods check
- chunk schema validation repro
- payload strictness repro

2. `dify-plugin-dev-generic` の実装ワークフローに、以下の gate を明文化:
- `LLMResultChunkDelta` required fields verification
- baseline line-count比による test depth sanity check

3. 今回ファイルを canonical evidence として扱う:
- `.claude/skills/dify-plugin-dev-generic/references/openai_responses_provider_subagent_parity_evaluation_2026-02-10.md`
