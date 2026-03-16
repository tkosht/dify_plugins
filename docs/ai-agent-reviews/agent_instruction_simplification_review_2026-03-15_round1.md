# AGENTS / instruction simplification review (2026-03-15 / round1)

## 対象
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `.cursor/rules/rules.mdc`
- `.cursor/rules/core.mdc`
- `.cursor/rules/project.mdc`
- `memory-bank/00-core/knowledge_access_principles_mandatory.md`
- `memory-bank/00-core/knowledge_loading_functions.md`
- `memory-bank/00-core/mandatory_rules_checklist.md`
- `memory-bank/00-core/repository_directory_conventions.md`
- `memory-bank/00-core/session_initialization_script.md`
- `memory-bank/02-organization/tmux_organization_success_patterns.md`
- `memory-bank/11-checklist-driven/checklist_driven_execution_framework.md`
- `memory-bank/11-checklist-driven/templates/codex_mcp_collaboration_checklist_template.md`
- `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md`

## 前提
- `package-lock.json` / `package.json` / `uv.lock` はレビュー対象外として除外した。
- `.codex/version.json` は実質的な設計判断を含まないため、レビュー対象外として扱った。
- レビューは差分・現行ファイル・公式 docs 照合ベースで行い、実機で各ツールの instruction load までは検証していない。

## 結論
- 総合判定: Request Changes
- 方向性は妥当。`AGENTS.md` を正本に寄せ、`Always / OnDemand / Deprecated` へ整理する構成はよくできている。
- ただし、Gemini 向け導線、deprecated 手順の残存、整理結果の監査可能性に未解消の欠陥がある。

## 指摘
F-01 (重大) `GEMINI.md` が `AGENTS.md` を実 import しておらず、Gemini 向けの薄いアダプタとして不完全
- 根拠: `AGENTS.md:9` と `AGENTS.md:29` は `GEMINI.md` をツール別アダプタとして扱っているが、実体は `GEMINI.md:1-4` の説明文のみで、`CLAUDE.md:4` のような `@AGENTS.md` 参照がない。
- 影響: Gemini CLI 利用時に repo-local instruction の正本が読み込まれず、`AGENTS.md` に集約した規範が効かない可能性がある。
- 改善提案: `GEMINI.md` も `CLAUDE.md` と同じく `@AGENTS.md` を使う実 import 形にそろえ、説明文は最小限に抑える。

F-02 (中) 現役導線として案内している tmux playbook に deprecated 手順が残っている
- 根拠: `AGENTS.md:59-70` は `tmux_organization_success_patterns.md` を `OnDemand` 文書として現役案内しつつ、`smart_knowledge_load()` は deprecated と明示している。一方で `memory-bank/02-organization/tmux_organization_success_patterns.md:8` は歴史的手順が残ると注記するだけで、`memory-bank/02-organization/tmux_organization_success_patterns.md:70-71` には `smart_knowledge_load "organization" "team-coordination"` が残っている。
- 影響: 元依頼の「有効/無効の整理」が未完了で、利用者や後続 AI が deprecated フローを現役手順と誤認する。
- 改善提案: 現行運用に合わせて該当手順を削除または差し替え、必要なら「歴史的サンプル」節へ隔離する。

F-03 (中) コンテキストサイズと指示の有効/無効整理が、監査可能な成果物としては不足している
- 根拠: `AGENTS.md:53-70` は `Always / OnDemand / Deprecated` を定義しているが、定性的な区分に留まる。`memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md:12-16` は変更前の固定指示量を示す一方、変更後の固定読込量やツール別の常時読込対象一覧は示していない。
- 影響: 元依頼の「コンテキストサイズと指示の有効無効の関係性整理」が、後から検証可能な形で残っていない。`現状の体験を維持しつつ最小化できたか` を第三者が確認しづらい。
- 改善提案: before/after の固定読込対象、推定サイズ、ツール別の有効文書を 1 表にまとめた補助メモを追加し、`AGENTS.md` か外部調査メモから参照できるようにする。

F-04 (低) 外部調査メモの一部主張が、再利用用メモとしては直接ソースへの結び付きが弱い
- 根拠: `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md:18-33` はよく整理されているが、`memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md:19-21` の Codex に関する具体主張は、列挙された URL だけでは直接検証しづらい。
- 影響: 今後このメモを根拠として再利用する際、どの記述が一次情報に直接依拠しているか追跡しにくい。
- 改善提案: 具体仕様は直接ソースへ差し替え、要約文ごとにどの URL を根拠にしたか分かる構造へ寄せる。

## 改善提案
- `GEMINI.md` を実 import 形式に修正し、`CLAUDE.md` と同じレベルの薄いアダプタへ統一する。
- `tmux_organization_success_patterns.md` の deprecated 手順を現行運用へ合わせて整理する。
- instruction simplification の before/after を監査可能な表で残し、ツール別の常時読込対象を明示する。
- 外部調査メモの URL と主張の対応関係を強化する。

## Open Questions
- このリポジトリで `GEMINI.md` を正式サポート対象として維持するか。維持するなら `CLAUDE.md` と同等の import 方式へそろえる必要がある。
- 修正完了後、このレビューの要点を `memory-bank/06-project/` または `memory-bank/03-patterns/` に再利用知識として要約反映するか。

## 参照した一次情報
- OpenAI Codex agent loop: https://openai.com/index/unrolling-the-codex-agent-loop/
- Gemini CLI context docs: https://google-gemini.github.io/gemini-cli/docs/core/context/
- Gemini CLI import docs: https://google-gemini.github.io/gemini-cli/docs/core/memport/
- Anthropic Claude Code memory docs: https://docs.anthropic.com/en/docs/claude-code/memory
- Cursor rules docs: https://docs.cursor.com/en/context/rules
