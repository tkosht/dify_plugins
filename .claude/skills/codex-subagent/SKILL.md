---
name: codex-subagent
description: "Auto-trigger when the user asks to run a Codex exec subagent (single/parallel/competition) for code generation, review, analysis, or documentation, or when adjusting codex-subagent wrapper policy (logging/TTY/timeout/profile guardrails)."
allowed-tools:
  - Bash(codex:*)
  - Bash(uv run python:*)
  - Bash(timeout:*)
  - Read
  - Write
  - Glob
metadata:
  version: 0.2.0
  owner: codex
  maturity: draft
  tags: [skill, codex, subagent, codex-exec, orchestrator]
---

## Overview
codex-subagent は `codex exec` を「サブエージェント」として複数回実行し、結果を選別/統合/協調するための実行オーケストレーターです。

- 実体: `.claude/skills/codex-subagent/scripts/codex_exec.py`（実行）、`codex_query.py`（ログ検索）、`codex_feedback.py`（人間評価）
- 既定サンドボックス: `read-only`（安全・再現性優先）
- ログ: `.codex/sessions/codex_exec/{human|auto}/YYYY/MM/DD/run-*.jsonl`（TTY で自動分類）

## Quick Start
```bash
# SINGLE: 1回実行（小さく速い）
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode single --task-type analysis --sandbox read-only \
  --prompt "$PROMPT"

# PARALLEL: N回実行→マージ（情報収集・列挙）
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode parallel --count 3 --merge dedup --task-type analysis \
  --sandbox read-only --json --prompt "$PROMPT"

# COMPETITION: N回実行→評価→最良選択（品質重視）
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode competition --count 3 --task-type code_review --strategy best_single \
  --sandbox read-only --json --prompt "$PROMPT"

# PIPELINE: Draft→Critique→Revise の協調実行
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode pipeline --pipeline-stages draft,critique,revise \
  --capsule-store auto --sandbox read-only --json --prompt "$PROMPT"
```

## Execution Modes
- `single`: 1回だけ `codex exec` を実行し、そのまま出力。
- `parallel`: 同一プロンプトを `--count N` 回並列実行し、`--merge` で統合。
- `competition`: 同一プロンプトを `--count N` 回実行し、`--task-type` と `--strategy` で最良案を選択（必要に応じて LLM 評価も実行）。
- `pipeline`: 複数 stage を順次実行し、Context Capsule を介して協調させる。

代表的なパラメータ:
- `--task-type`: `code_gen|code_review|analysis|documentation`
- `--merge`: `concat|dedup|priority|consensus`（parallel）
- `--strategy`: `best_single|voting|hybrid|conservative`（competition）

## Context Engineering
- プロンプトは「1タスク=1プロンプト」を原則とし、出力形式（箇条書き/JSON/ファイル一覧など）を明示。
- 事実ベースで記述し、根拠はファイルパス・ログ・コマンドのいずれかで示す（根拠が出せない内容は「不明」）。
- `--profile fast/very-fast` は既定で使わない。使う場合はタスクを極小化し、推測を禁止する前置きを含める（`codex_exec.py` が警告とガードレールを注入）。

## Result Handling
- `codex_exec.py --json` ではモードごとに JSON を返す（例: `single` は `{output, stderr, success, returncode, timed_out, timeout_seconds, output_is_partial, error_message, evaluation...}`）。
- タイムアウト時は `success=false` / `timed_out=true` / `error_message="Timeout after <N>s"` となる。`output`/`stderr` は取得できた範囲で保持され、`output_is_partial=true` として扱う（`.claude/skills/codex-subagent/scripts/codex_exec.py` はプロセスグループを終了して残留を回避）。
- `codex exec` が非0終了した場合は stdout は保持され、stderr は `stderr` に入り、`error_message` にも反映される（`--json` で確認）。
- `competition` のログは候補全件を保存し、`selected=true` の1件が最終採用案（デバッグ/再現性のため）。
- `pipeline` の JSON 出力は `{pipeline_run_id, success, stage_results, capsule, capsule_hash, capsule_store, capsule_path}` を返す。
- 終了コード: `0=全成功`, `2=サブエージェント失敗`, `3=ラッパー内部エラー`。`parallel` は候補のいずれかが失敗した時点で `2`。
- ログ保存時は `prompt` と `output` を一定長でトランケートする（ログ肥大化回避）。本体の stdout はトランケートしない。

## Guardrails
- 機密情報や認証情報を扱わない
- 破壊的コマンドは避ける
- 既定は `--sandbox read-only`（書き込みが必要な場合は親エージェント側で実施）
- ログ分類は既定で自動（TTY 判定）。必要なら `--log-scope human|auto` で上書きする
- 指示と矛盾/不明点がある場合は、最小の確認質問で先に潰す

---

*Updated to match the actual codex-subagent orchestrator implementation on 2025-12-31*
