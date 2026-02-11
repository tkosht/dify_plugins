# Generic Source Map Pattern

## Local source discovery order
1. 実装ソース
   - `<repo>/**/manifest.yaml`
   - `<repo>/**/provider/*.yaml`
   - `<repo>/**/tools/*.yaml`
   - `<repo>/**/models/**/*.yaml`
   - `<repo>/**/strategies/*.yaml`
   - `<repo>/**/*.py`（plugin runtime）
2. テストソース
   - `<repo>/tests/**`
3. 既存ドキュメント
   - `README*`, `GUIDE*`, `docs/**`
4. 履歴・ナレッジ
   - `memory-bank/**` または同等のナレッジ保管領域
   - `references/anti-cheat-subagent-evaluation-protocol.md`
   - `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_011017.md` (canonical)
   - `memory-bank/06-project/context/openai_responses_provider_subagent_handoff_2026-02-12_011017.md` (canonical handoff)
   - `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_file_set.txt`
   - `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/subagent_result_final.json`
   - `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/parent_gate_results.txt`
   - `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/repro_evidence.txt`
   - `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/SHA256SUMS.txt`
   - `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/hash_check_results.txt`
   - `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_SHA256SUMS.txt`
   - `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_hash_check_results.txt`
   - `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_0006.md` (historical strict-failure)
   - `.claude/skills/dify-plugin-dev-generic/references/openai_responses_provider_subagent_handoff_2026-02-12_0006.md`
   - `.claude/skills/dify-plugin-dev-generic/references/openai_responses_provider_subagent_parity_evaluation_2026-02-11.md` (fallback)
   - `.claude/skills/dify-plugin-dev-generic/references/openai_responses_provider_subagent_parity_evaluation_2026-02-10.md`

## Minimum evidence set
- 対象pluginの `manifest.yaml`
- 対象拡張（provider/tool/model/strategy）のYAML
- 対応Python実装
- 少なくとも1つの関連テスト
- 同一タイプのbaseline plugin（比較対象）

## Subagent evaluation artifacts
- Required authoritative files
  - `subagent_result_final.json`
  - `parent_gate_results.txt`
  - `repro_evidence.txt`
  - `SHA256SUMS.txt`
  - `hash_check_results.txt`
  - `subagent_events.jsonl` または `subagent_events_rerun.jsonl`
  - `subagent_stderr.log` または `subagent_stderr_rerun.log`
- Reproducibility recommended set
  - `run_metadata.env`
  - `subagent_prompt_codex.txt`
  - `TASK_SPEC.md`
  - `subagent_report.json`
  - `subagent_last_message.txt`
  - `subagent_exit_code.txt`
  - `subagent_status.txt`
  - `openai_responses_provider_source_snapshot.tar.gz`
  - `openai_responses_provider.difypkg`
  - `handoff_file_set.txt`
  - `handoff_SHA256SUMS.txt`
  - `handoff_hash_check_results.txt`

## Adaptation hints from this repository
- 署名/識別子エラーは `author` 整合と署名設定を優先確認する。
- `plugins.*` に列挙したYAML不整合は packaging失敗の主要因になる。
- debug接続不達は `.env` の remote install値転記ミスを優先確認する。
- OpenAI Responses provider系では abstract/chunk/payload 契約不整合が完成度低下の主要因になる。
- OpenAI Responses provider系では Dify runtime integration 差異（provider/main契約）が parity fail の主要因になる。
- OpenAI Responses provider系では packager required fields 欠落が release readiness fail の主要因になる。
- OpenAI Responses provider系では `NO_CHUNK_METHOD` と `BOOL_STRICT_FAIL` を hard-fail として扱う。
- chunk再現は signature-adaptive で行い、引数不一致 `TypeError` は再試行して最終判定する。
- baseline主要責務（entrypoint/error, llm stream flag, messages, payloads, bool coercion, provider runtime/schema）を網羅しない場合は test depth fail とする。
- parent gate結果とsubagent自己報告が矛盾した場合、parent gate結果を採点正本にする。
- canonical evidence は `2026-02-12_011017` を優先し、`2026-02-12_0006`/`2026-02-11`/`2026-02-10` は補助参照とする。
- one-pass運用では hard-fail 0件 + 90点目標を満たすまで最終化しない。

## Rule
- 判断は必ずローカルの実コードとテストに紐づける。
- 外部情報を使う場合も、ローカル再現可能な形で検証してから採用する。
- 新規pluginでは baseline parity 比較を省略しない。
- サブエージェント評価時は anti-cheat protocol を省略しない。
- parent gate結果を採点正本とし、subagent自己報告は参考情報扱いにする。
