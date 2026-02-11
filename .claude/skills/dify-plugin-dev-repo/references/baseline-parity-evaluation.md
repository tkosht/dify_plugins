# Repo Baseline Parity Evaluation

## Objective
- 新規または大幅改修pluginを既存baselineと比較し、完成度を定量評価する。

## Baseline selection rule
1. 同じpluginタイプの既存実装を1つ選ぶ。
2. 選定根拠を記録する。
3. 例: OpenAI Responses provider は `app/openai_gpt5_responses` をbaselineにする。

## Canonical evidence priority
1. `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_011017.md` を最優先参照する。
2. `memory-bank/06-project/context/openai_responses_provider_subagent_handoff_2026-02-12_011017.md` を handoff 正本として参照する。
3. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_file_set.txt` を受け渡し対象一覧の正本にする。
4. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/*` を正本 artifacts とする。
5. `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_0006.md` は historical strict-failure として参照する。
6. `2026-02-11` / `2026-02-10` 記録は補助比較に使う。

## Comparison commands
```bash
diff -rq --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.venv' app/<baseline_plugin> app/<target_plugin>
diff -rq --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.venv' tests/<baseline_plugin> tests/<target_plugin>
wc -l tests/<baseline_plugin>/*.py tests/<target_plugin>/*.py
```

## Scoring dimensions (100 points)
1. Interface contract parity: 30点
2. Runtime behavior and Dify integration parity: 30点
3. Test depth and reproducibility: 25点
4. Release readiness (package/install): 10点
5. Documentation and distribution files: 5点

## One-pass excellence target
1. 通常合格目安は80点以上。
2. one-pass運用では90点以上を推奨目標とする。
3. one-pass運用では hard-fail 条件0件を必須とする。
4. one-pass運用では parent authoritative gate を唯一の採点根拠に固定する。

## Pass/fail rule
1. 合計80点以上を合格目安とする。
2. `Release readiness` が0点なら総合点に関係なく不合格。
3. 必須補助ファイル欠落は不合格。
4. 比較結果に重大差分がある場合は理由を明記する。
5. LLM providerで abstract/chunk/payload の必須再現証跡が不足した場合は不合格。
6. line-count比で target test 総行数が baseline の40%未満なら不合格。
7. `ruff check` 失敗時は release readiness 不合格とする。
8. Dify runtime integration 不整合（`ModelProvider` / `Plugin(DifyPluginEnv)` 契約差異）は runtime parity 不合格とする。
9. `sha256sum -c SHA256SUMS.txt` 失敗時は証跡不整合として不合格とする。
10. `handoff_SHA256SUMS.txt` が存在する場合、検証失敗は証跡不整合として不合格とする。
11. parent gate結果とsubagent自己報告が矛盾する場合、parent gate結果のみ採点に使用する。
12. one-pass運用では hard-fail 条件が1件でもあれば総合点に関係なく不合格とする。
13. payload strictness（`bool` / `response_format.strict` / `json_schema`）の再現証跡で fail が1件でもあれば不合格とする。
14. packager required fields 欠落があれば不合格とする。
15. `__abstractmethods__` が空でない場合は不合格とする。
16. chunk再現証跡は signature-adaptive で実施し、最終的に `NO_CHUNK_METHOD` が出た場合は不合格とする。
17. payload strictness 再現証跡で `BOOL_STRICT_FAIL` が出た場合は不合格とする。
18. baseline主要責務（entrypoint/error, llm stream flag, messages, payloads, bool coercion, provider runtime/schema）が欠落する場合は不合格とする。

## Hard-fail conditions
1. `ruff check` fail
2. `dify plugin package` fail
3. test-depth ratio `< 0.40`
4. runtime integration gap (`ModelProvider` / `Plugin(DifyPluginEnv)`)
5. evidence integrity fail (`sha256sum -c` fail or required artifacts missing)
6. payload strictness repro fail (`bool` / `response_format.strict` / `json_schema`)
7. packager required fields missing
8. unresolved abstract methods (`__abstractmethods__ != []`)
9. chunk repro missing (`NO_CHUNK_METHOD`)
10. payload strict bool repro fail (`BOOL_STRICT_FAIL`)

## One-pass gate sequence
1. fail-fast preflight: `ruff` と `dify plugin package` を先行実行する。
2. preflight成功後に `pytest --no-cov` / `pytest` /（subagent評価時）`sha256sum -c` を同一環境で連続実行する。
3. `handoff_SHA256SUMS.txt` がある場合は追加で `sha256sum -c handoff_SHA256SUMS.txt` を実行する。
4. diff判定では `__pycache__`, `.pytest_cache`, `.venv`, 一時ラッパなどのノイズ生成物を除外する。
5. parent gateを唯一の採点根拠とし、subagent自己報告は参考情報に限定する。

## Mandatory reproducible evidence (LLM providers)
1. Abstract methods check
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python - <<'PY'
import sys
sys.path.insert(0, 'app')
from <target_plugin>.models.llm.llm import <llm_class_name>
print(sorted(<llm_class_name>.__abstractmethods__))
PY
```

2. Chunk schema validation repro (signature-adaptive)
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python - <<'PY'
import inspect
import sys
sys.path.insert(0, 'app')
from <target_plugin>.models.llm.llm import <llm_class_name>

class Impl(<llm_class_name>):
    @property
    def _invoke_error_mapping(self):
        return {}

    def get_num_tokens(self, model, credentials, prompt_messages, tools=None):
        return 0

obj = object.__new__(Impl)
chunk_fn = getattr(obj, '_chunk', None)
if chunk_fn is None:
    raise SystemExit('NO_CHUNK_METHOD')

sig = inspect.signature(chunk_fn)
kwargs = {}
for name in sig.parameters:
    if name == 'model':
        kwargs[name] = 'demo'
    elif name == 'text':
        kwargs[name] = 'ok'
    elif name in {'finish_reason', 'usage'}:
        kwargs[name] = None
    elif name == 'index':
        kwargs[name] = 0

result = chunk_fn(**kwargs)
print('CHUNK_OK', type(result).__name__)
PY
```

3. Payload strictness repro
```bash
UV_CACHE_DIR=/tmp/uv-cache uv run python - <<'PY'
import sys
sys.path.insert(0, 'app')
from <target_plugin>.internal import payloads

try:
    payloads.coerce_bool_strict('stream', 'yes')
    raise SystemExit('BOOL_STRICT_FAIL')
except ValueError:
    print('bool strictness ok')

try:
    payloads.build_request_payload({'response_format': 'json_schema'})
    raise SystemExit('expected ValueError')
except Exception:
    print('json_schema strictness ok')
PY
```

4. line-count sanity check
```bash
wc -l tests/<baseline_plugin>/*.py tests/<target_plugin>/*.py
```

5. Dify runtime integration check
```bash
rg -n 'ModelProvider|Plugin\\(DifyPluginEnv|DifyPluginEnv' app/<target_plugin>
```

## Mandatory anti-cheat evidence (subagent evaluations)
1. isolated workspace facts
2. baseline artifact absent evidence
3. git history/remote absence evidence
4. leakage scan evidence
5. applied prompt hard-constraints summary
6. parent authoritative gate logs
7. required artifacts paths (`subagent_result_final.json`, `parent_gate_results.txt`, `repro_evidence.txt`, `SHA256SUMS.txt`, `hash_check_results.txt`)
8. hash verification result (`sha256sum -c SHA256SUMS.txt`)
9. optional handoff hash verification result（`handoff_SHA256SUMS.txt` がある場合）
10. events/stderr artifacts 完備確認（`subagent_events*.jsonl`, `subagent_stderr*.log`）
11. reproducibility recommended set 完備確認（`run_metadata.env`, `subagent_prompt_codex.txt`, `TASK_SPEC.md`, source snapshot, `.difypkg`）

## Reporting template
1. Baseline / Target path
2. Score breakdown
3. Critical gaps
4. Required follow-up actions
5. Reproducible evidence outputs (abstract/chunk/payload/line-count/integration)
6. Anti-cheat evidence outputs
7. Parent authoritative verdict
8. Artifact integrity verdict
9. Collaboration artifacts（pipeline spec / subagent prompts / contract output）
