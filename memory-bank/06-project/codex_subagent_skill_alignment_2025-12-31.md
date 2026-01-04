# codex-subagent SKILL.md Alignment 2025-12-31

Tags: codex-subagent, skills, docs, logging, tty, timeout, profile

## Problem
- `.codex/skills/codex-subagent/SKILL.md` の内容が「SKILL.md 設計テンプレ」として書かれており、実装（`codex_exec.py`）および運用ポリシー（ログ分離/タイムアウト/fast回避）と不整合だった。
- テンプレ用途の SKILL.md を再利用可能な形で分離しつつ、codex-subagent 自体の定義は「実体どおり」に揃える必要があった。

## Key Decisions
- Option A: `.codex/skills/codex-subagent/SKILL.md` を「codex exec サブエージェント実行オーケストレーター」として書き換える。
- 旧テンプレ（SKILL.md雛形）は `skill-authoring` の参照として分離し、混線を防ぐ。

## Changes
- `codex-subagent` の定義を実体どおりに更新:
  - `.claude/skills/codex-subagent/SKILL.md`（= `.codex/skills/codex-subagent/SKILL.md`）
  - 実装に合わせてモードを `single/parallel/competition` に揃え、ログ/タイムアウト/fast方針を明記
- テンプレを分離:
  - `.claude/skills/skill-authoring/references/subagent_skill_md_template.md`
  - `skill-authoring` から参照導線を追加
- ログ分類の UX/整合:
  - `.claude/skills/codex-subagent/scripts/codex_query.py` / `codex_feedback.py` に `--log-scope` エイリアスと `CODEX_SUBAGENT_LOG_SCOPE` 既定適用を追加
  - `--log-dir` に scoped path（`.../human` / `.../auto`）を渡した場合の扱いを改善
- ドキュメントの明確化:
  - `.claude/commands/tasks/codex-subagent.md` に「タイムアウト時 stdout が空になる」/「fast時ガードレール注入」補足を追加

## Facts (Evidence)
- TTY 判定（ログ分類）は `codex_exec.py` 内で `sys.stdin.isatty() or sys.stdout.isatty() or sys.stderr.isatty()` を使用（いずれか True → `human` / 全て False → `auto`）。
- タイムアウト時は `subprocess.run(..., timeout=<N>)` によりプロセスが強制終了し、stdout は空として記録される（部分出力は残らない）。
- タイムアウトした実行ログ（success=false, output_len=0）が2件存在:
  - `.codex/sessions/codex_exec/2025/12/31/run-20251231T082256-87866a0d.jsonl`（run_id `87866a0d-...`, execution_time `120`）
  - `.codex/sessions/codex_exec/2025/12/31/run-20251231T082717-aa500488.jsonl`（run_id `aa500488-...`, execution_time `240`）

## Verification
- `uv run python .claude/skills/codex-subagent/scripts/codex_query.py --scope all --limit 20`
- JSONL を python3 で最小項目のみ抽出（run_id / success / execution_time / output_len）
- `codex_exec.py` を用いた subagent 整合性セルフチェック（analysis）

## Outcome
- codex-subagent の SKILL.md と実装・ドキュメントの役割が分離され、運用上の混線（「テンプレ」なのか「実行スキル」なのか）が解消された。
- ログ分類・タイムアウト・profile 方針が、SKILL/実装/ドキュメントで一貫して説明できる状態になった。

