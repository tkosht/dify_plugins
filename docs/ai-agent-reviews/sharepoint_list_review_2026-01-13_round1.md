# SharePoint List consistency review (2026-01-13, round1)

## Scope
- Docs: app/sharepoint_list/README.md, docs/03.detail_design/sharepoint_list_list_items_filters.md, tool YAMLs
- Code: app/sharepoint_list/internal/*, app/sharepoint_list/tools/*.py
- Tests: tests/sharepoint_list/*

## Findings (inconsistencies)
1) select_fields のツールYAML記述がREADME/実装/テストと不一致
- READMEは select_fields で表示名許可・クォート除去・厳格検証を説明
  - app/sharepoint_list/README.md:31-36
- 実装とテストは表示名の解決とクォート除去を確認
  - app/sharepoint_list/internal/operations.py:346-361, 451-482
  - tests/sharepoint_list/test_operations_select.py:47-80, 165-178
- ただし get_item.yaml は「内部名のみ」と記述
  - app/sharepoint_list/tools/get_item.yaml:34-43

2) fields_json のツールYAML記述がREADME/実装/テストと不一致
- READMEは fields_json に表示名指定可と説明
  - app/sharepoint_list/README.md:26-29
- 実装とテストは表示名の内部名解決を確認
  - app/sharepoint_list/internal/operations.py:435-448
  - tests/sharepoint_list/test_operations_fields.py:4-15
- ただし create_item.yaml / update_item.yaml は「内部名のみ」と記述
  - app/sharepoint_list/tools/create_item.yaml:24-33
  - app/sharepoint_list/tools/update_item.yaml:34-43

## Consistency confirmations (doc/code/test align)
- list_url の仕様と解析ロジックは一致
  - app/sharepoint_list/README.md:21-24
  - app/sharepoint_list/internal/validators.py:35-68
  - tests/sharepoint_list/test_validators_list_url.py:7-19
- filters の仕様（JSON/演算子/createdDateTime top-level/Preferヘッダ/datetime引用）と実装・テストは一致
  - app/sharepoint_list/README.md:38-50, 77-82
  - docs/03.detail_design/sharepoint_list_list_items_filters.md:31-46, 64-71
  - app/sharepoint_list/internal/filters.py:32-67
  - app/sharepoint_list/internal/operations.py:760-797
  - tests/sharepoint_list/test_operations_filters.py:156-189, 259-289
  - tests/sharepoint_list/test_filters.py:38-63
- デバッグログ環境変数・既定パスは一致
  - app/sharepoint_list/README.md:110-112
  - app/sharepoint_list/internal/operations.py:14-15, 65-89
  - tests/sharepoint_list/test_operations_debug.py:16-40, 54-93

## Open questions
- なし
