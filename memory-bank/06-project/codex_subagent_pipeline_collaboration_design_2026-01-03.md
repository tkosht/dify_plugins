# codex-subagent パイプライン協調設計（Draft→Critique→Revise）

date: 2026-01-03
status: proposed
scope: `.claude/skills/codex-subagent/scripts/codex_exec.py` に pipeline 協調を追加する設計

## 目的
- サブエージェントを「協調」させるため、段階実行（Draft→Critique→Revise）を実装する
- 共有メモリ型に近い「文脈の受け渡し」を安全に実現する
- ログと再現性を最優先し、失敗時の制御を親が確実に行えるようにする

## 前提・制約
- 既定サンドボックスは `read-only`（子は書き込み不可）
- 共有状態は親のみが最小限の書き込みで管理する
- 既存の `single/parallel/competition` の構造に適合させる

## 基本アーキテクチャ
- 親（`codex_exec.py`）が pipeline を順次実行する
- 各段階は **Context Capsule** を介して受け渡し
- 子は read-only のまま Capsule を読み取り、JSON で結果を返す

## Pipeline Stage を親が知る方法
1) **既定レジストリ方式（基本）**
   - `PIPELINE_STAGE_TEMPLATES = {"draft": ..., "critique": ..., "revise": ...}` のような固定マップを持つ
   - CLI は `--pipeline-stages draft,critique,revise` の **ID 指定**のみ
2) **Spec ファイル方式（拡張）**
   - `--pipeline-spec path/to/pipeline_spec.json` を指定し、Stage 定義を丸ごと渡す
3) **Planner stage（動的生成）**
   - `planner` が `PipelineSpec` を JSON で生成
   - 親が **Schema 検証 + 上限制約** を通過したもののみ採用

### 優先順位・衝突解決
- **優先順位**: `--pipeline-spec` ＞ `--pipeline-stages` ＞ 既定（`draft,critique,revise`）
- **同時指定の扱い**:
  - `--pipeline-spec` と `--pipeline-stages` の併用は **エラー**（exit code 3）
  - `--pipeline-spec` 指定時は `--allow-dynamic-stages` を無視（Spec 内で明示する）
- **未知の stage ID** は即エラー（exit code 3）

### Schema 定義の管理
- JSON Schema は **専用ファイル**で管理し、バージョン管理下に置く
  - 例: `.claude/skills/codex-subagent/schemas/`
    - `pipeline_spec.schema.json`
    - `stage_spec.schema.json`
    - `stage_result.schema.json`
    - `capsule.schema.json`
- ラッパーは起動時に Schema を読み込み、必須フィールド/型/制約を検証

## 動的に stage を増やす設計
- `--allow-dynamic-stages` が明示された場合のみ有効
- `max_stages` / `max_total_prompt_chars` / `allowed_stage_ids` を親で強制
- `StageSpec` の JSON Schema 検証を通過したもののみ追加
- 追加 stage は `timeout_seconds` / `task_type` を親が強制上書き可能
- `planner` を使う場合は **明示的に stage 列へ含める**（自動挿入しない）
- 動的追加は **追加のみ**（既存 stage の削除/置換は禁止）

## 共有メモリ（Context Capsule）
### 方式
- **embed**: Capsule をプロンプトに埋め込む（短い場合）
- **file**: 親が `.codex/sessions/codex_exec/<scope>/artifacts/<pipeline_run_id>/capsule.json` に保存し、子が read-only で読む
- **auto**: サイズに応じて embed/file を自動切替

### capsule_size と保存方式の関係
- `capsule_size_bytes` は **正規化 JSON の UTF-8 バイト数**と定義
- `--capsule-store=auto` の場合:
  - `capsule_size_bytes <= 20_000` → embed
  - `capsule_size_bytes > 20_000` → file
- `--capsule-path` の挙動:
  - `embed` では **指定不可**（指定時はエラー）
  - `file` では **任意**（未指定なら既定パス）
  - `auto` では **任意**（file に切り替わった場合にのみ利用）

### Capsule（例）
```json
{
  "schema_version": "1.1",
  "pipeline_run_id": "uuid",
  "task": {
    "goal": "...",
    "constraints": ["read-only", "no secrets"],
    "inputs": ["paths", "notes"]
  },
  "facts": [
    {"source": "path:line", "claim": "..."}
  ],
  "open_questions": ["..."],
  "assumptions": ["..."],
  "draft": {
    "content": "..."
  },
  "critique": {
    "issues": [{"type": "risk|gap|bug", "detail": "..."}],
    "fix_plan": ["..."]
  },
  "revise": {
    "final": "...",
    "deltas": ["..."],
    "verification": ["..."]
  }
}
```

## Stage 出力プロトコル
### StageResult（必須/任意/型）
- **必須**
  - `schema_version`: string
  - `stage_id`: string
  - `status`: `"ok" | "retryable_error" | "fatal_error"`
  - `output_is_partial`: boolean
  - `capsule_patch`: array（JSON Patch）
- **任意**
  - `summary`: string
  - `next_stages`: array（StageSpec、`allow-dynamic-stages` 時のみ許可）
  - `warnings`: array[string]
- **失敗時の扱い**
  - `status != "ok"` または `output_is_partial=true` → **パッチ不適用・次段へ渡さない**
  - JSON パース/Schema 検証に失敗 → **stage 失敗**
- **制約**
  - `output_is_partial=true` の場合、`status` は `retryable_error` または `fatal_error` のいずれか
  - `status="ok"` の場合、`output_is_partial=false` を必須とする
  - `capsule_patch` は **必須だが空配列を許容**（失敗/部分出力時は空配列のみ許可）
  - Schema は `capsule_patch` を `minItems: 0` とし、空配列を受理する

### capsule_patch 形式と適用
- 形式: **JSON Patch (RFC 6902)** を採用
- 許可 op: `add`, `replace`, `remove`（`move/copy/test` は禁止）
- 許可 path: `/facts`, `/draft`, `/critique`, `/revise`, `/open_questions`, `/assumptions` を **prefix** として許可
  - 例: `/facts/-`（配列末尾への追加）や `/draft/content` のような子パスを許可
- 適用手順:
  1) Capsule をコピー
  2) Patch 適用
  3) 成功時のみ更新
  4) 失敗時は stage 失敗として扱う

## 失敗時の扱い
- `timeout/非0/例外` は stage 失敗 → `exit_code=2`
- `output_is_partial=true` の場合は **次段へ渡さない**
- `max_retries` と `timeout_multiplier` は親が管理（例: 1.5x）

## ログと再現性
- 既存ログに追加するメタ:
  - `pipeline_run_id`, `stage_id`, `capsule_hash`, `capsule_path`
- `competition` と同様に候補全件を保存
- Capsule をハッシュ化して再実行性を担保

### capsule_hash の正規化とアルゴリズム
- **正規化**: `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)` を UTF-8 化
- **除外**: `pipeline_run_id` のような一意値はハッシュ対象外
- **アルゴリズム**: SHA-256（hex）

## CLI 追加案
- `--mode pipeline`
- `--pipeline-stages draft,critique,revise`
- `--pipeline-spec <path>`
- `--allow-dynamic-stages`
- `--capsule-store embed|file|auto`
- `--capsule-path <path>`
- `--max-stages N`

## 実装時点の JSON 出力（暫定）
- `pipeline_run_id`
- `success`
- `stage_results`（StageResult 配列）
- `capsule`
- `capsule_hash`
- `capsule_store`
- `capsule_path`

## 終了コード
- `0=全成功`, `2=サブエージェント失敗`, `3=ラッパー内部エラー`

## テスト方針（最小セット）
- **スモーク**: pipeline 3段を短いプロンプトで実行し `exit_code=0`
- **失敗系**: timeout を意図的に発生させ `exit_code=2` を確認
- **動的 stage**: `allow-dynamic-stages` ON/OFF の挙動差分
- **Schema 検証**: StageSpec/StageResult/Capsule の妥当性検証
- **パッチ適用**: JSON Patch の適用成功/失敗パターン
- **境界**: `max_stages` / `capsule_size_bytes` 超過の拒否
- **ログ整合**: `pipeline_run_id` / `capsule_hash` 記録を検証

## 未確定事項
- `pipeline` の JSON 出力形式の最終決定
- `planner` stage を既定で有効化するか
