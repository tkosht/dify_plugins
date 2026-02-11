# OpenAI Responses Provider Subagent Handoff File Set (2026-02-12 01:10 JST)

## 1. 目的
`dify-plugin-dev-generic` 開発元エージェントへ、今回のサブエージェント実行結果と比較評価を再現可能な形で連携するためのファイル集合を固定する。

## 2. 連携ファイル（必須）
以下は **authoritative 判定に必須**。欠落時は評価再現不可。

1. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/subagent_result_final.json`
2. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/parent_gate_results.txt`
3. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/repro_evidence.txt`
4. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/SHA256SUMS.txt`
5. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/hash_check_results.txt`
6. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/subagent_events.jsonl`
7. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/subagent_stderr.log`
8. `memory-bank/06-project/context/openai_responses_provider_subagent_parity_evaluation_2026-02-12_011017.md`

## 3. 連携ファイル（再現強化推奨）
以下は **実行条件の再構築** と **生成物レビュー** に有効。

1. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/run_metadata.env`
2. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/subagent_prompt_codex.txt`
3. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/TASK_SPEC.md`
4. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/subagent_report.json`
5. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/subagent_last_message.txt`
6. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/subagent_exit_code.txt`
7. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/subagent_status.txt`
8. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/openai_responses_provider_source_snapshot.tar.gz`
9. `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/openai_responses_provider.difypkg`

## 4. 整合性ファイル
- 連携対象一覧: `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_file_set.txt`
- 連携対象ハッシュ: `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_SHA256SUMS.txt`
- ハッシュ検証結果: `memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts/handoff_hash_check_results.txt`

## 5. 受け渡し時の最小検証
```bash
cd /home/devuser/workspace/memory-bank/06-project/context/openai_responses_provider_subagent_20260212_011017_artifacts
sha256sum -c handoff_SHA256SUMS.txt
```

期待結果:
- すべて `OK`
- `handoff_hash_check_results.txt` に失敗がない

## 6. 連携順序（推奨）
1. 評価本文を先に渡す: `openai_responses_provider_subagent_parity_evaluation_2026-02-12_011017.md`
2. authoritative artifacts を渡す（Section 2）
3. 再現強化ファイルを渡す（Section 3）
4. 最後に `handoff_SHA256SUMS.txt` で受領側検証

## 7. 補足
- isolated workspace 本体は `/tmp/openai_responses_provider_subagent_20260212_011017` に存在していたが、長期保持保証がないため、`openai_responses_provider_source_snapshot.tar.gz` を正本アーカイブとして扱う。
- 親エージェント採点ポリシー（parent authoritative gate 優先）は `parent_gate_results.txt` を唯一の判定根拠とする。
