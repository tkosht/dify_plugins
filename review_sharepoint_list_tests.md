# SharePoint List: ドキュメント・テストレビュー

## 対象
- 対象機能: `app/sharepoint_list`
- 対象テスト: `tests/sharepoint_list/*`

## 参照ファイル
- `app/sharepoint_list/README.md`
- `app/sharepoint_list/tools/*.yaml`
- `app/sharepoint_list/internal/*.py`
- `tests/sharepoint_list/*.py`

## ドキュメントとテストの不整合
1. `filters` 入力形式の記述差異
   - README/ツール定義: JSON 配列/単一 JSON オブジェクトを許容
   - テスト: 単一 JSON オブジェクトを許容する実装前提
   - 状態: 不整合は解消済み
   - 参照: `app/sharepoint_list/README.md` / `app/sharepoint_list/tools/list_items.yaml` / `tests/sharepoint_list/test_filters.py`

## テスト実装レビュー（正当性）
- `tests/sharepoint_list/test_validators.py`
  - `validate_target` / `parse_fields_json` / `ensure_item_id` / `parse_site_url` / `is_guid` の期待値は実装に一致
- `tests/sharepoint_list/test_filters.py`
  - `parse_filters` / `build_filter_fragment` / `format_odata_value` の期待値は実装に一致
  - JSON 配列/単一オブジェクト両対応は実装通りだが、ツール定義の記述とは不一致（上記参照）
- `tests/sharepoint_list/test_requests.py`
  - Request builder の URL/params/バリデーションの期待値は実装に一致
- `tests/sharepoint_list/test_http_client.py`
  - ローカルスタブサーバによる実通信で、401/403/429/5xx/4xx の例外種別、リトライ回数、送信ヘッダ/ボディの期待値が実装に一致
  - Timeout/ConnectionError は実通信で再現（遅延/未使用ポート）。モックは使用していない
  - 追加カバレッジ: 404、Retry-After HTTP-date、max_attempts=1、max_attempts=0 の最終フォールバック
- `tests/sharepoint_list/test_operations_filters.py`
  - `filters` の JSON 配列/単一オブジェクト受理、`createdDateTime` のトップレベル扱い、`fields/<internalName>` 変換、`Prefer` ヘッダ付与条件は実装に一致
- `tests/sharepoint_list/test_operations_select.py`
  - `parse_select_fields` のクォート処理/空入力、表示名→内部名解決、`$expand=fields($select=...)` の挙動は実装に一致
- `tests/sharepoint_list/test_operations_crud.py`
  - `create_item` / `update_item` / `get_item` / `list_items` の基本動線、`page_token` / `page_size` の扱い、`resolve_site_id` / `resolve_list_id` の分岐は実装に一致
- `tests/sharepoint_list/test_operations_choices.py`
  - choice 列の取得、表示名解決、非 choice / 不明列のエラーは実装に一致
- `tests/sharepoint_list/test_operations_debug.py`
  - デバッグログの有効化/無効化、ログ出力の NDJSON 形式、Authorization/アクセストークン非出力は実装に一致
- `tests/sharepoint_list/test_operations_*.py`
  - `unittest.mock` によるパッチを使用（Graph API 呼び出しの切り離し）。AGENTS ポリシー上、unit テストでのモック使用は事前承認が必要

## ドキュメント記載の挙動でテスト未検証の領域
- OAuth フローの実動作（認可コード取得/更新/`/me`）はテスト未整備
  - 参照: `app/sharepoint_list/provider/sharepoint_list.py`
- `list_items` のツール層（`Tool` 実装）での入力エラー/メッセージ出力はテスト未整備
  - 参照: `app/sharepoint_list/tools/list_items.py`
- `build_list_filter_request` のリスト名に `'` を含むケースの安全性（クォート）未検証
  - 参照: `app/sharepoint_list/internal/request_builders.py`

## テスト計画（優先度付き）

### P0（最優先）
1. `filters` 入力形式の契約確認テスト
   - ステータス: `list_items` の `operations` 層で実装済み（`tests/sharepoint_list/test_operations_filters.py`）
   - 残件: ツール層まで含めた契約確認は未対応
2. `list_items` フィルタの実データ検証
   - ステータス: `operations` 層の組み立てはテスト済み
   - 残件: 実 Graph API を使った統合検証は未対応
3. `select_fields` の表示名→内部名解決
   - ステータス: `operations` 層で実装済み（`tests/sharepoint_list/test_operations_select.py`）
   - 残件: 実 Graph API を使った統合検証は未対応

### P1（重要）
1. CRUD の最小動線（Create→Get→Update→Get→List）
   - ステータス: `operations` 層で実装済み（`tests/sharepoint_list/test_operations_crud.py`）
   - 残件: 実 Graph API を使った統合検証は未対応
2. `get_choices` の choice 列検証
   - ステータス: `operations` 層で実装済み（`tests/sharepoint_list/test_operations_choices.py`）
   - 残件: 実 Graph API を使った統合検証は未対応
3. OAuth ハッピーパス
   - トークン取得・更新・/me の取得

### P2（補完）
1. `parse_select_fields` の単体テスト
   - ステータス: 実装済み（`tests/sharepoint_list/test_operations_select.py`）
2. リスト名に `'` を含む場合の `$filter` 組み立て
   - 残件
3. デバッグログの出力条件と秘匿情報非出力の確認
   - ステータス: 実装済み（`tests/sharepoint_list/test_operations_debug.py`）

## 実行前提（統合テスト用）
- テスト用 SharePoint テナント・サイト・リスト
- 列: `Title` / `ステータス`（choice）/ `優先度`（number）/ `Flag`（bool）
- `ステータス` / `優先度` はインデックス化
- 実行制御は環境変数で分離

## 残件の代替確認（Dify Plugin 実機テスト前提）

### 代替確認が可能な残件
- `operations` 層の実 Graph API 統合検証
  - 代替: Dify Plugin 経由の E2E（Create→Get→Update→Get→List、filters、select_fields、choices）
  - カバー対象: `app/sharepoint_list/internal/operations.py` の主要経路
- OAuth フローの実動作（認可コード取得/更新/`/me`）
  - 代替: Dify プラグイン設定画面の OAuth 接続テスト（Save & Authorize→再接続）
  - カバー対象: `app/sharepoint_list/provider/sharepoint_list.py`
- ツール層の入力エラー/メッセージ出力
  - 代替: Dify 画面/LLM からのツール実行で不正入力を与える手動検証
  - カバー対象: `app/sharepoint_list/tools/*.py`
- リスト名に `'` を含む場合の `$filter` 安全性
  - 代替: 実機で `'` を含むリストを作成し、`list_identifier` を表示名で指定して解決を試す
  - カバー対象: `app/sharepoint_list/internal/request_builders.py`

### 代替確認が難しい残件（テストが必要）
- `tests/sharepoint_list/test_http_client.py`
  - 429/5xx/timeout などの再現が E2E では困難なため、単体テストでの担保が必要
  - 現状はローカルスタブサーバで担保済み

## テスト実行結果（最新）
- `uv run pytest tests/sharepoint_list`
  - 158件すべて成功
  - Coverage 93.35%（fail-under 85% を満たす）

## 再レビュー結果（対応要否）
以下は別AIレビューの残存軽微点に対する判断です。
- L270（未カバー）: `raise last_exception` は到達困難な分岐で実質デッドコードに近い。追加対応は不要
- `_find_unused_port()` の1箇所使用: 可読性のため現状維持で妥当
- jitter テストの許容範囲: 現状の `1.0 <= wait <= 1.25` は仕様通りで安定。変更不要

結論: 前回の改善は適切に反映済みで、追加対応なしで採用可能
