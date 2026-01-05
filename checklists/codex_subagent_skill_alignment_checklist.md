# codex-subagent SKILL.md 整合チェックリスト

## 目的
- `.codex/skills/codex-subagent/SKILL.md`（= `.claude/skills/codex-subagent/SKILL.md`）が、実装・ドキュメント・運用ポリシーと整合している状態を維持する。
- 「SKILL.mdテンプレ用途」は別ファイルへ分離し、混線を防ぐ。

## 対象
- SKILL: `.codex/skills/codex-subagent/SKILL.md`
- 実装: `.claude/skills/codex-subagent/scripts/{codex_exec.py,codex_query.py,codex_feedback.py}`
- ドキュメント: `.claude/commands/tasks/codex-subagent.md`

## 実行チェック（Checklist）
- [ ] ブランチが `main/master` 以外である
- [ ] 変更対象のAGENTS/ローカル規約を確認済み（必要最小のロード）
- [ ] `codex-subagent` の実装が提供する機能を列挙（モード/ログ/タイムアウト/プロファイル）
- [ ] SKILL.md の記述が「テンプレ」ではなく「実装の説明」になっている
- [ ] テンプレ用途の文書が別ファイルへ分離され、参照導線がある
- [ ] `/codex-subagent` ドキュメントの説明が実装と一致している
- [ ] `codex_query.py` / `codex_feedback.py` がログ分類（human/auto/all）を一貫して扱える
- [ ] 代表的な検証コマンドを実行し、エラー無く動作する
  - [ ] `uv run python .claude/skills/codex-subagent/scripts/codex_query.py --scope all --limit 5`
- [ ] subagent（`codex_exec.py`）で整合性セルフチェックを実行し、残差分が無い
- [ ] 変更内容を memory-bank に記録した

## 5点評価（定性可）
- Security（0/5）: 秘密情報に触れていないか
- User Value（0/5）: ユーザー運用を悪化させていないか（UX含む）
- Long-term（0/5）: 将来の運用/保守で破綻しないか
- Fact-based（0/5）: 主張に根拠（ファイルパス/ログ）があるか
- Consistency（0/5）: SKILL/実装/ドキュメントで矛盾が無いか

## 改善ループ
1. subagent で「整合性チェック」→ 指摘を最小差分で修正
2. `codex_query.py` でログ/結果を確認（scope=all）
3. Checklist と memory-bank を更新して終了

