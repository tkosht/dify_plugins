# Repo Design Workflow

## Objective
- このリポジトリの既存プラグイン構造に合わせて、変更前に設計判断を固定する。

## Step 1: Scope the target plugin
1. 対象を `app/sharepoint_list` / `app/openai_gpt5_responses` / `app/gpt5_agent_strategies` / `app/nanobana` から選定する。
2. 変更タイプを確定する。
   - metadata/runtime: `manifest.yaml`
   - provider contract/runtime: `provider/*.yaml`, `provider/*.py`
   - tools: `tools/*.yaml`, `tools/*.py`
   - model catalog: `models/llm/*.yaml`, `models/llm/llm.py`
   - strategy set: `strategies/*.yaml`, `strategies/*.py`
3. ユーザー向け挙動の変更点を1文で定義する。

## Step 2: Define interface contracts
1. 入力パラメータ、既定値、バリデーション規則を決める。
2. 失敗時のエラーメッセージ方針を決める。
3. 互換性方針を決める。
   - 既存フィールドを維持するか
   - deprecate手順を入れるか

## Step 3: Align YAML and Python responsibilities
1. `manifest.yaml` の `plugins.*` と実ファイル配置の対応を確定する。
2. provider/tool/strategy/model YAML と Python実装の責務分離を明示する。
3. 認証情報や機密情報の取り扱い境界を確認する。

## Step 4: Plan test impact
1. 変更に対応する最小テスト集合を選ぶ。
2. 回帰観点を先に定義する。
3. 既知バグの再発防止観点を入れる。
4. 新規pluginでは baselineとの比較観点を先に固定する。

## Step 5: Produce design deliverables
1. 変更対象ファイル一覧を確定する。
2. 新規pluginで必要な配布補助ファイルを明示する。
   - `_assets/icon.svg`, `README.md`, `PRIVACY.md`, `.env.example`, `requirements.txt`
3. 実装順序を固定する。
4. 検証コマンドを固定する。
