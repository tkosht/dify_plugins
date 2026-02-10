# Generic Design Workflow

## Objective
- 任意リポジトリで再利用できるDifyプラグイン設計フローを確立する。

## Step 1: Locate plugin root
1. `manifest.yaml` を含むディレクトリを plugin root として確定する。
2. extension type を決める。
   - provider
   - tool
   - model
   - strategy
   - mixed

## Step 2: Define behavior contract
1. ユーザー入力、既定値、バリデーション規則を明記する。
2. 出力形式と失敗時エラー契約を明記する。
3. 後方互換の扱いを明記する。

## Step 3: Design file mapping
1. `manifest.yaml` の `plugins.*` と対応YAMLファイルを列挙する。
2. YAML契約とPython実装の責務を分離する。
3. テスト対象ファイルを先に決める。

## Step 4: Define acceptance criteria
1. 機能要件を満たす最小シナリオを定義する。
2. 失敗系の期待結果を定義する。
3. packaging/install時の成功条件を定義する。
4. 新規pluginで必要な配布補助ファイルを明示する。
5. baseline比較の合格条件を定義する。
