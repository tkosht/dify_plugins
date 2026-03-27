# AGENTS / instruction simplification review (2026-03-16 / round2)

## 対象
- `docs/ai-agent-reviews/agent_instruction_simplification_review_2026-03-15_round1_response.md`
- `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md`
- `CLAUDE.md`

## 前提
- `package-lock.json` / `package.json` / `uv.lock` はレビュー対象外として除外した。
- レビューは差分・現行ファイル・リポジトリ履歴確認ベースで行い、実機での instruction load smoke は行っていない。

## 結論
- 総合判定: Request Changes
- 残件は 1 件のみだが、F-03 を `Fixed` とする根拠がまだ不足している。

## 指摘
F-05 (中) `Claude Code` の before / after load matrix が apples-to-apples になっていない
- 根拠: `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md:17` は `Claude Code | CLAUDE.md | 11B | CLAUDE.md + @AGENTS.md | 5.2KB` としている。一方で現行 `CLAUDE.md:4` は `@AGENTS.md` を import しており、リポジトリ履歴上の変更前 `CLAUDE.md` も `@AGENTS.md` 1 行のみだった。
- 影響: before 側が `CLAUDE.md` 本体の 11B だけで計上され、実際に読まれていた旧 `AGENTS.md` 相当の読込量が落ちている。そのため `agent_instruction_simplification_review_2026-03-15_round1_response.md` の `F-03 Fixed` は、比較表の根拠としてまだ不十分。
- 改善提案: before 側にも `@AGENTS.md` 経由の実効読込量を反映して再計算するか、もしくは「ファイル本体サイズのみ比較」などの計測基準を before / after で統一して表を書き直す。

## 確認済み事項
- `GEMINI.md` に `@AGENTS.md` が追加され、薄いアダプタ化は解消している。
- tmux 文書は `Current Entry Point` と `Historical Appendix` に整理され、deprecated 手順は現役導線から外れている。
- research note に source-to-claim mapping が追加され、出典との対応は改善している。

## Residual Risks
- `gemini` / `codex` / `cursor` の repo-local instruction load について、実機 smoke は未検証のまま残っている。
