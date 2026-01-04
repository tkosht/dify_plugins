# codex-subagent パイプライン協調 テストレビュー（再レビュー）

date: 2026-01-03
scope: tests/codex_subagent/* の設計整合レビュー（更新後）
sources:
  - memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md
  - tests/codex_subagent/test_pipeline_spec.py
  - tests/codex_subagent/test_pipeline_cli.py
  - tests/codex_subagent/test_pipeline_patch.py
  - tests/codex_subagent/test_pipeline_execute.py
  - tests/codex_subagent/test_pipeline_helpers.py
  - tests/codex_subagent/test_pipeline_prompt.py

## 対象
- 設計: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md`
- テスト: `tests/codex_subagent/` 配下6ファイル

## 現状カバー（要約）
- StageResult 制約（`status`/`output_is_partial`/空パッチ許容/`capsule_patch` 必須）
- JSON Patch の許可 prefix と禁止 op、基本操作（add/replace/remove）
- 3段 pipeline の成功/停止、動的 stage の許可/拒否、`max_stages` 制約
- pipeline spec の読み込み/存在/不正JSON
- capsule path の既定/カスタム/`embed` 禁止、`auto`+境界値 20,000 と path 利用条件
- prompt 構築（embed/file）、StageResult のパース失敗
- `capsule_hash`/`capsule_path` を含むログ生成、exit code マッピングの単体

## 指摘事項（設計との未整合・不足）

### 重大
1) **終了コードの実行経路検証不足**
   - 設計は `timeout/非0/例外` を `exit_code=2`、`0/2/3` の終了コードを規定。
   - 現在は exit code マッピング関数の単体テストのみで、CLI/実行フロー上での反映が未検証。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:134` `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:159`

2) **Schema 検証（StageSpec/Capsule/StageResult）の欠落**
   - 設計は JSON Schema 読み込みと検証失敗時の stage 失敗を要求。
   - StageResult の必須項目/制約は一部検証済みだが、専用 Schema ファイル読込/検証自体のテストがない。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:39` `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:116`

3) **動的 stage の残り制約（allowed_stage_ids / max_total_prompt_chars / 追加のみ）未検証**
   - `allow_dynamic` の許可/拒否と `max_stages` はカバー済みだが、設計が要求する残制約が未検証。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:48`

### 中
4) **パッチ適用失敗時の pipeline 側扱い未検証**
   - `apply_capsule_patch` の失敗は単体で検証済みだが、`execute_pipeline` 経由で stage 失敗扱いとなることが未検証。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:123`

5) **ログ整合の `pipeline_run_id` 確認不足**
   - `capsule_hash`/`capsule_path` は検証されているが、`pipeline_run_id` 記録の確認がない。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:139`

## 改善済みの点（前回からの反映）
- JSON Patch の許可 prefix/禁止 op の検証追加。
- `capsule_size_bytes` 境界値 20,000 と `auto`+`capsule_path` の挙動検証追加。
- 動的 stage の許可/拒否と `max_stages` の検証追加。
- ログに `capsule_hash`/`capsule_path` を含む検証追加。
- prompt（embed/file）と StageResult パース失敗の検証追加。

## 追加推奨テスト
- timeout/非0/例外発生時に CLI または実行層で `exit_code=2` が最終出力に反映されることの検証。
- JSON Schema の読み込み成功/失敗、StageSpec/Capsule/StageResult の不正入力検証。
- `allowed_stage_ids`/`max_total_prompt_chars`/追加のみ（削除・置換禁止）の制約検証。
- パッチ適用失敗時に pipeline が stage 失敗として停止・伝播することの検証。
- ログ出力に `pipeline_run_id` が含まれることの検証。

## 確認事項
- 終了コードの責務（CLI 層か execute_pipeline 層か）
- Schema ファイルの配置/読み込みの実装状況
- ログ形式の確定状況
