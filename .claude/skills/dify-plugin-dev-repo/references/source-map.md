# Repo Source Map

## Core implementation sources
- `app/sharepoint_list/**`: OAuth付きTool plugin実装、tool YAML/実装、filter・validatorの実装例。
- `app/openai_gpt5_responses/**`: provider + llm model catalog + payload/message整形のbaseline実装。
- `app/gpt5_agent_strategies/**`: strategy plugin設計、安全ガード、tool invoke保護の実装例。
- `app/nanobana/**`: tool pluginの最小構成とガイド付き実装例。
- baseline比較時は同種pluginを1つ決め、差分確認の基準とする。
  - 例: OpenAI Responses provider の新規作成時は `app/openai_gpt5_responses/**` をbaselineにする。

## Test sources
- `tests/sharepoint_list/**`: SharePoint pluginのバリデーション、リクエスト、操作系の回帰例。
- `tests/openai_gpt5_responses/**`: provider/runtime/payload/messages の回帰例。
- `tests/gpt5_agent_strategies/**`: flow/policy/strategy invoke/safety の回帰例。

## Canonical decision and evidence sources
- `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_011017.md`
- `memory-bank/06-project/context/openai_responses_provider_subagent_handoff_2026-02-12_011017.md`
- `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_file_set.txt`
- `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/subagent_result_final.json`
- `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/parent_gate_results.txt`
- `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/repro_evidence.txt`
- `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/SHA256SUMS.txt`
- `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/hash_check_results.txt`
- `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_SHA256SUMS.txt`
- `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_hash_check_results.txt`

## Historical fallback sources
- `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_0006.md`
- `.claude/skills/dify-plugin-dev-generic/references/openai_responses_provider_subagent_handoff_2026-02-12_0006.md`
- `.claude/skills/dify-plugin-dev-generic/references/openai_responses_provider_subagent_parity_evaluation_2026-02-11.md`
- `.claude/skills/dify-plugin-dev-generic/references/openai_responses_provider_subagent_parity_evaluation_2026-02-10.md`

## Usage rule
1. 実装判断は `app/*` と `tests/*` を主根拠とする。
2. 手順・落とし穴は `memory-bank` と skill references を補助根拠として使う。
3. parent gate結果を採点正本とし、subagent自己報告は参考情報扱いにする。
4. canonical evidence は `2026-02-12_011017` を優先し、`2026-02-12_0006`/`2026-02-11`/`2026-02-10` は補助参照とする。
5. packager required fields 欠落、`NO_CHUNK_METHOD`、`BOOL_STRICT_FAIL`、`test-depth ratio < 0.40` は hard-fail として扱う。
6. diff比較では `__pycache__`, `.pytest_cache`, `.venv`, 一時ラッパ生成物を除外する。
