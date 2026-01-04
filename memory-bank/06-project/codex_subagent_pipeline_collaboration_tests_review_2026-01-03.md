# codex-subagent パイプライン協調 テストレビュー

date: 2026-01-03
scope: tests/codex_subagent/* の設計整合レビュー
sources:
  - memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md
  - tests/codex_subagent/test_pipeline_spec.py
  - tests/codex_subagent/test_pipeline_cli.py
  - tests/codex_subagent/test_pipeline_patch.py
  - tests/codex_subagent/test_pipeline_execute.py

## 対象
- 設計: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md`
- テスト: `tests/codex_subagent/` 配下4ファイル

## 現状カバー（要約）
- StageResult 制約の一部（`status`/`output_is_partial`/空パッチ許容）
- JSON Patch の基本操作（add/replace/remove）
- 3段 pipeline の成功と、失敗時に途中停止する挙動
- pipeline spec の読み込み/存在/不正JSON
- capsule path の既定/カスタム/`embed` 禁止

## 指摘事項（設計との未整合・不足）

### 重大
1) **終了コード/timeout 失敗系の検証不足**
   - 設計は `timeout/非0/例外` を `exit_code=2` と定義し、`0/2/3` の終了コードを規定。
   - テストは `execute_pipeline` の成功/停止のみで、CLI/終了コード/timeout の検証が未実施。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:134` `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:159`

2) **動的 stage（allow-dynamic-stages）系のテスト欠如**
   - 設計は `allow-dynamic-stages` の ON/OFF 差分、`next_stages` 許可条件、`max_stages`/`allowed_stage_ids` の強制、追加のみの制約を定義。
   - 現行テストに動的 stage の検証がない。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:48` `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:112`

3) **Schema 検証（StageSpec/StageResult/Capsule）の未検証**
   - 設計は JSON Schema の読み込みと必須フィールド/型/制約の検証、失敗時の stage 失敗を要求。
   - テストは StageResult の一部制約のみで、Schema 読み込み/検証失敗のケースがない。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:39` `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:116`

### 中
4) **JSON Patch 制約の網羅不足**
   - 許可 op は `add/replace/remove`、`move/copy/test` は禁止。許可 path は `/facts` `/draft` `/critique` `/revise` `/open_questions` `/assumptions` の prefix。
   - テストは prefix の一部とインデックス不正のみ。禁止 op/残り prefix、そしてパッチ適用失敗を pipeline 側で stage 失敗扱いとする検証が不足。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:123`

5) **capsule_size_bytes 境界と auto+capsule_path の挙動不足**
   - 設計は `<=20_000` で embed、`>20_000` で file。`auto` かつ `capsule_path` は file 側に切り替わった場合のみ使用。
   - テストは 10k/30k のみで境界値 20,000 が未検証。`auto` と `capsule_path` の組み合わせも未検証。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:62`

6) **ログ整合の未検証**
   - `pipeline_run_id`/`capsule_hash`/`capsule_path` をログに記録する設計。
   - テストでログ出力内容の検証がない。
   - 参照: `memory-bank/06-project/codex_subagent_pipeline_collaboration_design_2026-01-03.md:139`

### 軽微
7) **StageResult 制約テストの入力重複**
   - `output_is_partial` と `status` の制約テストが同一の不正入力で実施されており、バリデーション順に依存する可能性がある。
   - 参照: `tests/codex_subagent/test_pipeline_spec.py:13`

## 追加推奨テスト（設計の最小セット対応）
- `timeout`/非0/例外を発生させ `exit_code=2` を検証（CLI か実行層の責務を確定した上で実施）。
- `allow-dynamic-stages` の ON/OFF で `next_stages` の許可/拒否を検証。
- `max_stages`/`allowed_stage_ids`/追加のみの制約を検証。
- JSON Schema 読み込み成功/失敗、StageSpec/StageResult/Capsule の不正入力検証。
- JSON Patch 禁止 op（`move/copy/test`）と prefix 境界（`/open_questions`/`/assumptions`/`/critique`/`/revise`）の検証。
- `capsule_size_bytes` の境界値 20,000 と `auto`+`capsule_path` の挙動検証。
- ログに `pipeline_run_id`/`capsule_hash`/`capsule_path` が残ることの検証。

## 確認事項（未決定/要確認）
- 終了コードの責務範囲（CLI か execute_pipeline か）
- Schema ファイル配置/読み込みの実装状況
- ログ形式が確定しているか
