# sharepoint_list 成果物契約出力 (2026-01-11)

## 必須出力
- 変更ファイル一覧（今回の評価は read-only のため「変更なし」を明記）
- 実行コマンド一覧（評価に使用したコマンド）
- テスト結果（実行有無と結果）
- 失敗時の原因と次の一手

## Capsule 構造
- /draft: 評価方針・一次結果
- /critique: レビュー指摘・リスク
- /revise: 統合結論・ギャップ一覧
- /facts: 実行ログ・根拠（オブジェクト配列）
- /open_questions: 未解決事項
- /assumptions: 仮定（最小）

## ループ条件
- /critique に重大指摘が残る
- /open_questions が残る
- /facts と不整合
- テスト/CI 未通過

## 終了条件
- 重大指摘ゼロ
- /open_questions が解消または受理
- /facts 整合
- テスト/CI 通過
