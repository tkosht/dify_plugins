# AGENTS / instruction simplification review response (2026-03-15 / round1)

## Summary
- 判定: review findings を採用し、round1 の指摘を反映した。
- 体制: Reviewer subagent を試行したが API stream disconnect が発生したため、Parent が `Reviewer / Executor / Verifier` を直列で代行した。別経路のローカル codex subagent では F-02 から F-04 の妥当性確認を取得した。

## Finding Disposition

| ID | Status | Response | Files |
| --- | --- | --- | --- |
| F-01 | Fixed | `GEMINI.md` を `@AGENTS.md` import 付きの薄いアダプタへ修正した。 | `GEMINI.md` |
| F-02 | Fixed | tmux 文書に `Current Entry Point` を追加し、deprecated / missing prerequisite を `Historical Appendix` 扱いへ分離した。 | `memory-bank/02-organization/tmux_organization_success_patterns.md` |
| F-03 | Fixed | before / after load matrix、repo-wide fixed-instruction floor、Always / OnDemand / Deprecated map を research note に追加し、`AGENTS.md` から参照可能にした。2026-03-16 に `Claude Code` 行を effective-load basis へ補正し、比較基準を明文化した。 | `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md`, `AGENTS.md` |
| F-04 | Fixed | 仕様主張ごとに `Claim / Source URL / Applied decision` を対応付けた。 | `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md` |

## Verification
- `GEMINI.md` は `@AGENTS.md` を含む。
- tmux 文書の現役節から `smart_knowledge_load()` と欠落 prerequisite を外し、historical-only items と appendix に隔離した。
- before / after size audit を research note に反映した。
- `Claude Code` の before / after は `CLAUDE.md` 単体ではなく adapter + canonical pair の実効読込量で再計算した。
- `AGENTS.md` から instruction simplification research note へ導線を追加した。

## Notes
- `gemini --help` はローカルバイナリ起動を確認済みだが、環境側で `~/.gemini/projects.json` 不在メッセージが出るため、repo-local instruction import の実機 smoke は `unverified` とした。
- `codex` / `cursor` の repo-local instruction load は今回静的監査を主ゲートとし、実機 smoke は未実施。
