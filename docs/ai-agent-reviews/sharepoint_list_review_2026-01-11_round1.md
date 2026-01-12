# sharepoint_list 整合性レビュー (2026-01-11 / round1)

## 対象
- app/sharepoint_list/README.md
- app/sharepoint_list/PRIVACY.md
- app/sharepoint_list/manifest.yaml
- app/sharepoint_list/provider/sharepoint_list.yaml
- app/sharepoint_list/provider/sharepoint_list.py
- app/sharepoint_list/tools/{create_item,update_item,get_item,list_items,get_choices}.yaml
- app/sharepoint_list/internal/{validators,operations,filters,request_builders}.py
- docs/03.detail_design/sharepoint_list_list_items_filters.md
- docs/note_sharepoint_list_devlog.md
- tests/sharepoint_list/*

## 結論
- 総合判定: NG
- 主因: ツールI/O仕様の記述不一致、デバッグログ出力先の仕様不一致、テスト未カバー事項

## 主要な不整合
1) create/update/get の fields_json / select_fields の仕様記述不一致
   - YAML: 内部名のみと記載
     - app/sharepoint_list/tools/create_item.yaml:31
     - app/sharepoint_list/tools/update_item.yaml:41
     - app/sharepoint_list/tools/get_item.yaml:41
   - README/実装: 表示名→内部名解決を実施
     - app/sharepoint_list/README.md:28
     - app/sharepoint_list/README.md:83
     - app/sharepoint_list/internal/operations.py:441-447
     - app/sharepoint_list/internal/operations.py:462-479

2) デバッグログの出力先仕様が文書/実装で不一致
   - 文書: 環境変数で NDJSON 出力（/tmp/sharepoint_list.debug.ndjson）
     - app/sharepoint_list/README.md:112
     - app/sharepoint_list/PRIVACY.md:2
     - docs/note_sharepoint_list_devlog.md:300-301
   - 実装: list_items が固定パスへも出力
     - app/sharepoint_list/internal/operations.py:690

## 判断不可（仕様不足）
- list_url バリデーション失敗時のエラーメッセージ仕様
  - README に記載なし・tests もメッセージ検証なし
  - app/sharepoint_list/README.md:21
  - app/sharepoint_list/internal/validators.py:35
  - tests/sharepoint_list/test_validators_list_url.py:6-31

## テスト未カバー（仕様に対する直接検証不足）
- list_url の webUrl 補完挙動
  - app/sharepoint_list/README.md:24
  - app/sharepoint_list/internal/operations.py:182
  - tests/sharepoint_list/test_operations_crud.py:343-370（webUrl 補完の直接検証なし）
- list_items の orderby 固定 / デフォルト page_size
  - app/sharepoint_list/README.md:16
  - app/sharepoint_list/internal/operations.py:636-790
  - tests/sharepoint_list/test_requests.py:190-218（request_builders 単体で orderby 指定のみ検証）

## 整合している項目
- list_items の select_fields/filters/page_size/page_token/order 仕様
  - app/sharepoint_list/README.md:16,40
  - app/sharepoint_list/tools/list_items.yaml:31-75
  - app/sharepoint_list/internal/operations.py:653-790
  - app/sharepoint_list/internal/filters.py:70
  - app/sharepoint_list/internal/request_builders.py:165
  - tests/sharepoint_list/test_operations_filters.py:156
  - tests/sharepoint_list/test_operations_crud.py:246-300

## 実行コマンド
- uv run pytest tests/codex_subagent/test_pipeline_spec.py --no-cov
- uv run python .claude/skills/codex-subagent/scripts/codex_exec.py --mode pipeline --pipeline-spec docs/ai-agent-reviews/sharepoint_list_pipeline_spec_2026-01-11.json --capsule-store auto --sandbox read-only --json --timeout 1200 --prompt "<see docs/ai-agent-reviews/sharepoint_list_prompt_2026-01-11.txt>"

## テスト実行
- 対象テストの実行は行っていない（read-only 制約）
