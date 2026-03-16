# AGENTS / instruction simplification review response (2026-03-16 / round2)

## Summary
- 判定: round2 の `F-05` を反映した。
- 体制: Reviewer が `CLAUDE.md` 履歴と measurement rule を確認し、Executor が research note / round1 response を更新し、Verifier が before / after bytes を再計算した。

## Finding Disposition

| ID | Status | Response | Files |
| --- | --- | --- | --- |
| F-05 | Fixed | `Claude Code` 行を `effective always-loaded bytes` basis に補正し、matrix と floor の計測基準を分離して明文化した。あわせて round1 response の `F-03 Fixed` 根拠を同じ基準へ更新した。 | `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md`, `docs/ai-agent-reviews/agent_instruction_simplification_review_2026-03-15_round1_response.md` |

## Verification
- `git show HEAD:CLAUDE.md` は `@AGENTS.md` 1 行で、before も adapter 形式だった。
- `git log -p --follow -- CLAUDE.md` で、旧 `CLAUDE.md` も `AGENTS.md` 参照 adapter だったことを確認した。
- Before effective load: `CLAUDE.md` 11B + `AGENTS.md` 21,707B = 21,718B ≒ 21.7KB
- After effective load: `CLAUDE.md` 79B + `AGENTS.md` 5,140B = 5,219B ≒ 5.2KB
- runtime smoke は今回の round2 スコープ外として未実施。

## Residual Risks
- `gemini` / `codex` / `cursor` の repo-local instruction load smoke は引き続き未検証。
