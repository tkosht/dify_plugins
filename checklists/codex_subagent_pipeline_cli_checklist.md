# codex-subagent pipeline CLI 実装チェックリスト

date: 2026-01-03
status: complete
scope: pipeline CLI 実装（TDD）

## 目的
- pipeline モードの CLI 追加と最小動作の実装
- 仕様/テスト/ドキュメントの整合

## チェックリスト
- [x] テスト追加（prompt/StageResult パース）
- [x] テスト実行コマンドの更新
- [x] pipeline helper 実装（prompt/StageResult 解析/カプセル管理）
- [x] pipeline CLI 追加（args/ログ/JSON 出力）
- [x] 設計ドキュメント更新（JSON 出力の暫定整理）
- [x] SKILL.md 更新（pipeline モード明記）
- [x] 追加テスト実行（全 pipeline 系）
- [x] チェックリスト完了・status 更新

## 定性評価（暫定）
- 適合性: pipeline CLI の最小機能が揃っている
- リスク: LLM 出力の JSON 逸脱時に stage 失敗で停止するため、実運用ではプロンプト調整が必要
