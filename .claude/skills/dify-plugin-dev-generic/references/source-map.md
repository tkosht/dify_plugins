# Generic Source Map Pattern

## Local source discovery order
1. 実装ソース
   - `<repo>/**/manifest.yaml`
   - `<repo>/**/provider/*.yaml`
   - `<repo>/**/tools/*.yaml`
   - `<repo>/**/models/**/*.yaml`
   - `<repo>/**/strategies/*.yaml`
   - `<repo>/**/*.py`（plugin runtime）
2. テストソース
   - `<repo>/tests/**`
3. 既存ドキュメント
   - `README*`, `GUIDE*`, `docs/**`
4. 履歴・ナレッジ
   - `memory-bank/**` または同等のナレッジ保管領域

## Minimum evidence set
- 対象pluginの `manifest.yaml`
- 対象拡張（provider/tool/model/strategy）のYAML
- 対応Python実装
- 少なくとも1つの関連テスト
- 同一タイプのbaseline plugin（比較対象）

## Adaptation hints from this repository
- 署名/識別子エラーは `author` 整合と署名設定を優先確認する。
- `plugins.*` に列挙したYAML不整合は packaging失敗の主要因になる。
- debug接続不達は `.env` の remote install値転記ミスを優先確認する。

## Rule
- 判断は必ずローカルの実コードとテストに紐づける。
- 外部情報を使う場合も、ローカル再現可能な形で検証してから採用する。
- 新規pluginでは baseline parity 比較を省略しない。
