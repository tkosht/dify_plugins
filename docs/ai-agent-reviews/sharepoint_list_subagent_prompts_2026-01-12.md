# Subagent Prompts (sharepoint_list / 2026-01-12)

## Pipeline 設計（必須）
- 既定パイプラインの踏襲は禁止。タスクに合わせて初期/動的ステージを設計し、理由と最適化観点を /draft.proposal に記録する。
- 動的追加が必要な場合は allow_dynamic_stages: true を前提にし、next_stages 追加条件を明記する。
- Reviewer はパイプライン設計がタスク最適化されていない場合、/critique で **NG** と明示する。

## Executor
- 役割: Executor（ドキュメント・コード・テスト整合性の事実抽出）
- 目的: app/sharepoint_list のドキュメント/コード/テストの相互整合性を確認し、根拠付きで一致/不一致/不明を整理する
- 対象: /home/devuser/workspace
- 対象パス（これらのみ）:
  - app/sharepoint_list/README.md
  - app/sharepoint_list/manifest.yaml
  - app/sharepoint_list/provider/sharepoint_list.yaml
  - app/sharepoint_list/tools/create_item.yaml
  - app/sharepoint_list/tools/get_choices.yaml
  - app/sharepoint_list/tools/get_item.yaml
  - app/sharepoint_list/tools/list_items.yaml
  - app/sharepoint_list/tools/update_item.yaml
  - docs/03.detail_design/sharepoint_list_list_items_filters.md
  - app/sharepoint_list/main.py
  - app/sharepoint_list/provider/sharepoint_list.py
  - app/sharepoint_list/internal/filters.py
  - app/sharepoint_list/internal/operations.py
  - app/sharepoint_list/internal/request_builders.py
  - app/sharepoint_list/internal/validators.py
  - app/sharepoint_list/internal/http_client.py
  - app/sharepoint_list/tools/create_item.py
  - app/sharepoint_list/tools/get_choices.py
  - app/sharepoint_list/tools/get_item.py
  - app/sharepoint_list/tools/list_items.py
  - app/sharepoint_list/tools/update_item.py
  - tests/sharepoint_list/test_validators.py
  - tests/sharepoint_list/test_validators_list_url.py
  - tests/sharepoint_list/test_filters.py
  - tests/sharepoint_list/test_operations_filters.py
  - tests/sharepoint_list/test_operations_select.py
  - tests/sharepoint_list/test_operations_fields.py
  - tests/sharepoint_list/test_operations_choices.py
  - tests/sharepoint_list/test_operations_crud.py
  - tests/sharepoint_list/test_requests.py
  - tests/sharepoint_list/test_http_client.py
- 書き込み範囲: なし（read-only）。ファイル変更は禁止。
- 制約:
  - 機密情報を扱わない（.env/.env.example は読まない）
  - 推測禁止。不明は「不明」
  - 根拠はファイルパスと行番号
- 記録先: /facts と /open_questions
- 成果物契約出力: references/contract_output.md に従う

## Reviewer
- 役割: Reviewer（独立レビュー）
- 実行: 読み取りのみ
- 書き込み範囲: docs/ai-agent-reviews/ のみ（レビュー .md）
- 記録先: /critique
- 要求: 指摘・リスク・未解消事項を根拠付きで列挙する（パイプライン設計の適合性も含む）

## Verifier
- 役割: Verifier（再確認）
- 実行: 読み取りのみ（必要時に /facts 追記）
- 書き込み範囲: 原則なし
- 記録先: /facts
- 要求: 重大指摘や open_questions の対象のみ再確認し、根拠を追記する

## Timeout Policy
- タスク難易度や要求水準を下げない。
- timeout が発生したら、同一スコープで再実行する（再実行上限を明示）。
- 再実行しても進められない場合は、タスクを停止しフレームワークのデバッグ/改善に移行する。
