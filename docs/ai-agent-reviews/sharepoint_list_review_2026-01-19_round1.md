# sharepoint_list 整合性レビュー (2026-01-19 / round1)

## 対象
- app/sharepoint_list/README.md
- app/sharepoint_list/PRIVACY.md
- app/sharepoint_list/manifest.yaml
- app/sharepoint_list/provider/sharepoint_list.yaml
- app/sharepoint_list/tools/*.yaml
- app/sharepoint_list/tools/*.py
- app/sharepoint_list/internal/*.py
- docs/03.detail_design/sharepoint_list_list_items_filters.md
- docs/note_sharepoint_list_devlog.md
- tests/sharepoint_list/*

## 整合性サマリ
| 項目 | Docs | Code | Tests | 判定 | メモ |
| --- | --- | --- | --- | --- | --- |
| ツール一覧と主要パラメータ | 一致 | 一致 | 一致 | Match | get_choices 実装/テストも確認済み |
| list_url 検証と list_id 解決 | 一致 | 一致 | 一部 | Partial | webUrl パスマッチ/非ASCIIフォールバックのテスト根拠なし |
| select_fields 仕様 | 一致 | 一致 | 一致 | Match | 引用符除去/未知フィールド/欠落補完まで整合 |
| filters 仕様 | 一致 | 一致 | 一致 | Match | createdDateTime top-level、fields/、Prefer ヘッダまで整合 |
| list_items pagination / orderby / page_size | 一致 | 一致 | 一致 | Match | orderby createdDateTime desc と page_size 上限100を確認 |
| デバッグログ環境変数とプライバシー記述 | 一致 | 一致 | 一部 | Partial | 認証ヘッダ非記録のテスト根拠なし |
| get_choices 仕様 | 一致 | 一致 | 一致 | Match | 非choice列エラーも整合 |
| エラー種別 | 一致 | 一致 | 一致 | Match | GraphError/認証系/RateLimit の実装とテストあり |

## 主な根拠（抜粋）
- ツール一覧/主要パラメータ
  - README: tools と必須パラメータ定義: app/sharepoint_list/README.md:12-17
  - Tool YAML: create/update/get/list/get_choices の必須パラメータ: app/sharepoint_list/tools/create_item.yaml:12-34; update_item.yaml:13-44; get_item.yaml:13-44; list_items.yaml:13-96; get_choices.yaml:13-34
  - Tool 実装: list_items の page_size 既定/上限、get_item/create/update の必須項目: app/sharepoint_list/tools/list_items.py:49-83; get_item.py:41-53; create_item.py:41-55; update_item.py:41-60; get_choices.py:39-63
- list_url / list_id 解決
  - README list_url 仕様と webUrl フォールバック記述: app/sharepoint_list/README.md:21-24
  - parse_list_url と resolve_list_id の実装: app/sharepoint_list/internal/validators.py:35-68; app/sharepoint_list/internal/operations.py:118-238
  - テスト: AllItems/GUID/invalid URL と displayName 解決: tests/sharepoint_list/test_validators_list_url.py:7-31; tests/sharepoint_list/test_operations_crud.py:340-390
- select_fields
  - README の引用符除去/GraphError/欠落補完: app/sharepoint_list/README.md:31-36
  - parse_select_fields と _validate_requested_fields: app/sharepoint_list/internal/operations.py:346-361; 386-421
  - テスト: 引用符除去、displayName 解決、欠落補完、未知フィールド: tests/sharepoint_list/test_operations_select.py:47-90; 234-404; 440-501; 503-567
- filters
  - README と設計doc: app/sharepoint_list/README.md:38-88; docs/03.detail_design/sharepoint_list_list_items_filters.md:7-71
  - filters 実装 + list_items での mapping/Prefer: app/sharepoint_list/internal/filters.py:7-17;32-67;70-106; app/sharepoint_list/internal/operations.py:759-797
  - テスト: filters JSON/演算子/createdDateTime top-level/Prefer/and 結合: tests/sharepoint_list/test_filters.py:8-64;80-95; tests/sharepoint_list/test_operations_filters.py:156-418
- list_items pagination/orderby/page_size
  - README & devlog: app/sharepoint_list/README.md:16; docs/note_sharepoint_list_devlog.md:299
  - 実装: page_size cap/next_page_token 抽出/orderby: app/sharepoint_list/internal/operations.py:779-780; 1007-1014; app/sharepoint_list/internal/request_builders.py:145-179
  - テスト: page_token/next_page_token/page_size cap/orderby: tests/sharepoint_list/test_operations_crud.py:173-300; tests/sharepoint_list/test_requests.py:190-217
- デバッグログ/プライバシー
  - README/devlog/PRIVACY: app/sharepoint_list/README.md:110-112; docs/note_sharepoint_list_devlog.md:300-301; app/sharepoint_list/PRIVACY.md:2
  - 実装: env var 参照と NDJSON 出力、Authorization ヘッダ除外: app/sharepoint_list/internal/operations.py:11-16;28-43;65-89
  - テスト: debug log 出力: tests/sharepoint_list/test_operations_choices.py:143-177
- get_choices
  - README/tools/実装/テスト: app/sharepoint_list/README.md:101; app/sharepoint_list/tools/get_choices.yaml:13-34; app/sharepoint_list/tools/get_choices.py:39-63; app/sharepoint_list/internal/operations.py:544-595;623-628; tests/sharepoint_list/test_operations_choices.py:45-103
- エラー種別
  - README: app/sharepoint_list/README.md:103-108
  - 実装: http_client の例外定義 + GraphError alias + tools での捕捉: app/sharepoint_list/internal/http_client.py:26-63; app/sharepoint_list/internal/operations.py:18-20; app/sharepoint_list/tools/list_items.py:98-133
  - テスト: GraphAPIError 属性/401/403/429 時の例外: tests/sharepoint_list/test_http_client.py:45-63;191-222
  - GraphError 例外: tests/sharepoint_list/test_operations_select.py:503-567

## ギャップ / 追加検証候補
- list_url の webUrl パスマッチ/非ASCIIフォールバックはコードにあるがテスト根拠が見当たらない。
- PRIVACY の「認証ヘッダやトークンはログに含めない」はコード上の Authorization 除外で裏付け可能だが、テスト根拠は未確認。

