# SharePoint List Plugin: list_items filters 設計ノート

## 概要
`sharepoint_list_list_items` ツールの `filters`（JSON配列）から、Microsoft Graph の SharePoint List Items API に渡す `$filter` を生成するルールをまとめます。

## 入力仕様（filters）
`filters` は **JSON配列（またはJSONオブジェクト1件）**を文字列として渡します。

各要素（または単体オブジェクト）のスキーマ:

```json
{
  "field": "ステータス",
  "op": "eq",
  "value": "処理中",
  "type": "string"
}
```

- **field**（必須）: 列の内部名 or 表示名（日本語表示名も可）
- **op**（必須）: 演算子
- **value**（必須）: 値（string/number/bool 等）
- **type**（任意）: 値型ヒント（`string|number|bool|datetime`）

## 対応演算子
- **比較**: `eq`, `ne`, `gt`, `ge`, `lt`, `le`
- **文字列関数**: `contains`, `startswith`, `endswith`

## `$filter` 生成ルール
### フィールド参照
- `field == "createdDateTime"` の場合は、トップレベルとして `createdDateTime` を参照します。
  - 例: `createdDateTime ge 2025-12-15T00:00:00Z`
- それ以外の列は、SharePoint List Items の `fields/<internalName>` を参照します。
  - 例: `fields/_x30b9__x30c6__x30fc__x30bf__x30 eq '処理中'`

### 表示名→内部名の解決
`field` に表示名が渡された場合は、Graph の列定義（`/columns`）を取得して `displayName -> name` の対応表を作成し、内部名へ解決します。

### 値のリテラル化
- `type == number`: クォートせず数値として扱う（`3`, `3.14`）
- `type == bool`: `true` / `false`
- `type == datetime`: クォートせず文字列をそのまま（既存の `created_after/before` と整合）
- 上記以外（未指定含む）: 文字列として単引用符で囲む

### 文字列エスケープ
OData の単引用符エスケープとして、文字列内の `'` は `''` に置換します。

例:
- 入力: `O'Reilly`
- 出力: `'O''Reilly'`

### AND結合
複数の条件は `and` で結合します（OR/括弧は現行未対応）。

例:

```text
createdDateTime ge 2025-12-15T00:00:00Z and fields/Status eq 'InProgress'
```

## Prefer ヘッダ付与
SharePoint List は **未インデックス列へのサーバーフィルタ**を 400 で拒否する場合があります。

本プラグインでは `$filter` に `fields/` を含む（=リスト列フィルタ）場合に、ベストエフォートで以下を付与します。

```text
Prefer: HonorNonIndexedQueriesWarning=true
```

ただし環境によってはヘッダ付与しても拒否されるため、運用として **対象列のインデックス化**を推奨します。

## 実装対応箇所
- `filters` パース・式生成: `app/sharepoint_list/internal/filters.py`
- list_items の組み立て: `app/sharepoint_list/internal/operations.py`
- tool I/F: `app/sharepoint_list/tools/list_items.yaml`, `app/sharepoint_list/tools/list_items.py`

