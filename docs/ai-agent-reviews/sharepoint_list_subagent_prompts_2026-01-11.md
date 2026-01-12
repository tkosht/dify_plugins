# sharepoint_list subagent prompts (2026-01-11)

## Executor（draft/revise）
- 役割: 実装/テストの変更は行わず、整合性評価のみ実施（読み取り専用）
- 目的: app/sharepoint_list のドキュメント・コード・テストの整合性チェック
- 対象リポ: /home/devuser/workspace
- 対象パス:
  - app/sharepoint_list/README.md
  - app/sharepoint_list/PRIVACY.md
  - app/sharepoint_list/manifest.yaml
  - app/sharepoint_list/provider/sharepoint_list.yaml
  - app/sharepoint_list/provider/sharepoint_list.py
  - app/sharepoint_list/tools/create_item.yaml
  - app/sharepoint_list/tools/update_item.yaml
  - app/sharepoint_list/tools/get_item.yaml
  - app/sharepoint_list/tools/list_items.yaml
  - app/sharepoint_list/tools/get_choices.yaml
  - app/sharepoint_list/internal/validators.py
  - app/sharepoint_list/internal/operations.py
  - app/sharepoint_list/internal/filters.py
  - app/sharepoint_list/internal/request_builders.py
  - docs/03.detail_design/sharepoint_list_list_items_filters.md
  - docs/note_sharepoint_list_devlog.md
  - tests/sharepoint_list/test_validators.py
  - tests/sharepoint_list/test_validators_list_url.py
  - tests/sharepoint_list/test_operations_crud.py
  - tests/sharepoint_list/test_operations_fields.py
  - tests/sharepoint_list/test_operations_select.py
  - tests/sharepoint_list/test_operations_filters.py
  - tests/sharepoint_list/test_operations_choices.py
  - tests/sharepoint_list/test_operations_debug.py
  - tests/sharepoint_list/test_filters.py
  - tests/sharepoint_list/test_requests.py
- 書き込み範囲: なし（read-only）
- 制約: 推測禁止。不明は「不明」。根拠は必ずファイルパス+行番号で記載
- 記録先: /facts と /draft /revise
- 成果物契約出力: docs/ai-agent-reviews/sharepoint_list_contract_output_2026-01-11.md に準拠

## Reviewer（review）
- 役割: 独立レビュー
- 実行: 読み取りのみ
- 書き込み範囲: docs/ai-agent-reviews のみ（ただし本件は read-only 運用）
- 記録先: /critique
- 要求: 重大な不整合・不足テスト・ドキュメントの齟齬を根拠付きで列挙

## Verifier（今回未使用）
- 役割: テスト再実行・再現確認
- 実行: 未使用（要請があれば追加）
- 記録先: /facts

## Timeout Policy
- タスク難易度を下げない。
- timeout が発生したら同一スコープで再実行（上限2回）。
