# codex exec フィジビリティ検証ログ

## Meta-Phase 0: 基盤確立

実施日: 2025-12-22

---

## Trial 1: 基本呼び出し（単純計算）

- **目的**: codex exec の基本動作確認
- **プロンプト**: "2+2を計算して、数字のみ回答"
- **実行時間**: ~10秒
- **成功/失敗**: ✅ 成功
- **出力品質**: 5/5（正確）
- **トークン使用**: 11,706
- **発見した課題**: なし

---

## Trial 2: コード生成（Hello World）

- **目的**: Python スクリプト生成
- **プロンプト**: "Hello World を出力する Python スクリプトを書いてください。コードのみ、説明不要。"
- **実行時間**: ~60秒
- **成功/失敗**: ✅ 成功（ただし意図しない副作用あり）
- **出力品質**: 4/5（機能するが副作用あり）
- **トークン使用**: 22,430
- **発見した課題**:
  1. **AGENTS.md の強い影響**: codex は workdir の AGENTS.md を読み込み、プロンプト指示より優先
  2. **意図しない副作用**: TDD 方式でテストを先に作成、ブランチ作成、ファイル作成
  3. **時間がかかる**: 単純なタスクでも 60秒程度（AGENTS.md プローブのオーバーヘッド）
- **改善案**:
  - プロンプトで AGENTS.md を無視するよう明示的に指示
  - または sandbox モードを read-only にして副作用を防ぐ

---

## Trial 3: 並列実行（3タスク同時）

- **目的**: 複数の codex exec を同時実行
- **プロンプト**: 1+1, 2+2, 3+3 の計算（各タスク）
- **実行時間**: ~同時実行で完了
- **成功/失敗**: ✅ 成功
- **出力品質**: 5/5（全て正確）
- **トークン使用**: 各約 11,700
- **発見した課題**:
  1. **trusted directory 制約**: codex exec は git リポジトリ内でのみ動作
  2. **トークンオーバーヘッド**: シンプルな計算でも約 11,700 トークン消費
- **改善案**:
  - 並列実行は問題なく動作
  - ただしコスト（トークン）に注意

---

## Trial 4: コンテキスト注入

- **目的**: ファイル内容をプロンプトに注入して処理
- **プロンプト**: pyproject.toml の内容を注入し、プロジェクト名を抽出
- **実行時間**: ~15秒
- **成功/失敗**: ✅ 成功
- **出力品質**: 5/5（正確に「base」を抽出）
- **トークン使用**: 12,197
- **発見した課題**: なし
- **改善案**: コンテキスト注入は正常に機能

---

## Trial 5: 構造化出力（JSON）

- **目的**: JSON 形式での出力要求
- **プロンプト**: 情報を JSON 形式で出力
- **実行時間**: ~15秒
- **成功/失敗**: ✅ 成功
- **出力品質**: 5/5（正確な JSON）
- **トークン使用**: 11,756
- **発見した課題**: なし
- **改善案**: 構造化出力は正常に機能

---

## 発見した知見サマリー

### 技術的制約

| 項目 | 制約 |
|------|------|
| 実行環境 | git リポジトリ内のみ（trusted directory） |
| トークン消費 | 最小でも約 11,700（AGENTS.md プローブ含む） |
| 実行時間 | 単純タスク: 10-15秒、複雑タスク: 60秒以上 |
| 並列実行 | ✅ 可能（競合なし） |

### AGENTS.md の影響

- **重要**: codex は workdir の AGENTS.md を自動的に読み込み、そのルールに従う
- **副作用**: TDD 方式の実行、ブランチ作成、不要なファイル作成
- **対策**:
  1. `--sandbox read-only` で副作用を防ぐ
  2. プロンプトで明示的に「AGENTS.md を無視」と指示
  3. 短い単純なタスクでは影響が少ない

### コンテキストエンジニアリング上の考慮

1. **プロンプト設計**: 「〜のみ回答」で余計な出力を抑制可能
2. **コンテキスト注入**: ファイル内容を直接プロンプトに埋め込み可能
3. **構造化出力**: JSON 形式での出力が安定して動作
4. **副作用制御**: 複雑なタスクでは sandbox 設定が重要

---

## Trial 6: サンドボックスモード比較検証

- **目的**: `--sandbox` オプションの各モードの挙動を比較
- **プロンプト**: "Hello World を出力する Python スクリプトを書いてください。コードのみ、説明不要。"
- **実行時間**: 各10-60秒
- **成功/失敗**: ✅ 全モード成功

### サンドボックスモード比較表

| sandbox モード | トークン消費 | ファイル作成 | AGENTS.md プローブ | 出力形式 |
|----------------|-------------|-------------|-------------------|---------|
| `danger-full-access` (既定) | 22,430 | ✅ 自動 | ✅ 完全実行 | コード実行 |
| `workspace-write` | 11,910 | ✅ 指示時のみ | △ 部分的 | コード実行 |
| `read-only` | **266** | ❌ 不可 | ❌ スキップ | テキスト出力 |

### 重要な発見

1. **read-only モードの劇的なトークン削減**:
   - 22,430 → 266 トークン（約**84分の1**）
   - AGENTS.md のプローブをスキップするため高速
   - コードはテキストとして返却（親エージェントが書き込み）

2. **workspace-write モードのバランス**:
   - ファイル書き込みは可能だが、明示的な指示が必要
   - AGENTS.md の影響は部分的（TDD強制などは発生しない）
   - トークン消費は read-only の約45倍

3. **推奨使用パターン**:
   - **コード生成・レビュー**: `--sandbox read-only`（親が書き込み制御）
   - **ファイル操作タスク**: `--sandbox workspace-write`（直接書き込み必要時）
   - **フル自律タスク**: `danger-full-access`（稀、コスト高）

---

## Meta-Phase 0 完了サマリー

### 検証済み機能

| 機能 | 状態 | 推奨設定 |
|------|------|---------|
| 基本実行 | ✅ | - |
| コード生成 | ✅ | `--sandbox read-only` |
| 並列実行 | ✅ | 3+ タスク同時可 |
| コンテキスト注入 | ✅ | `$(cat file)` 形式 |
| 構造化出力 (JSON) | ✅ | プロンプトで指定 |
| 副作用制御 | ✅ | sandbox モード選択 |

### コスト最適化戦略

```bash
# 推奨: read-only でコード取得、親が書き込み
codex exec --sandbox read-only "コード生成プロンプト"

# 必要時: workspace-write で直接書き込み
codex exec --sandbox workspace-write "ファイル作成指示を含むプロンプト"
```

---

## Meta-Phase 1: プロンプトテンプレート生成

実施日: 2025-12-22

### Trial 7: codex exec でプロンプトテンプレート生成

- **目的**: codex exec を使用して、プロンプトテンプレート集を生成
- **手法**: `--sandbox read-only` で生成、親が書き込み
- **成功/失敗**: ✅ 成功
- **トークン使用**: 24,443
- **生成物**: `.claude/skills/codex-subagent/references/prompt_templates.md`
- **内容**:
  - 汎用テンプレート
  - タスク別テンプレート（コード生成、コードレビュー、分析・調査、ドキュメント生成）
  - 各テンプレートに Role/Context/Task/Constraints/Output Format を含む

---

## Meta-Phase 2: 並列実行による成果物生成

実施日: 2025-12-22

### Trial 8: 3タスク並列実行（ドキュメント生成）

- **目的**: 複数の codex exec を並列実行し、Skill の参照ドキュメントを生成
- **手法**: `--sandbox read-only` で 3 タスク同時実行、`&` と `wait` で制御
- **成功/失敗**: ✅ 全タスク成功

### 並列タスク結果

| タスク | トークン消費 | 状態 | 生成物 |
|--------|-------------|------|--------|
| SKILL.md 生成 | 13,022 | ✅ | `.claude/skills/codex-subagent/SKILL.md` |
| evaluation_criteria.md 生成 | 22,273 | ✅ | `.claude/skills/codex-subagent/references/evaluation_criteria.md` |
| merge_strategies.md 生成 | 23,061 | ✅ | `.claude/skills/codex-subagent/references/merge_strategies.md` |

**合計トークン**: 58,356

### 重要な発見

1. **並列実行の安定性**:
   - 3 セッションが独立して動作、干渉なし
   - 各セッションが独自の Session ID を持つ
   - MCP サーバーは共有（serena は並列時に失敗するがタスクには影響なし）

2. **read-only モードでも探索的動作**:
   - codex は `rg` コマンド等でコードベースを探索
   - 書き込みは不可だが読み取りは可能
   - AGENTS.md の一部ルールは参照される

3. **品質の安定性**:
   - 全タスクで要件を満たす出力
   - Markdown フォーマット、表、コードブロックが正確
   - Mermaid フローチャートも生成

---

## Meta-Phase 2 完了サマリー

### Skill ディレクトリ構造

```
.claude/skills/codex-subagent/
├── SKILL.md                          # Skill 定義
└── references/
    ├── prompt_templates.md           # プロンプトテンプレート集
    ├── evaluation_criteria.md        # 評価基準カタログ
    └── merge_strategies.md           # マージ戦略ガイド
```

### 生成済み成果物

| ファイル | 目的 | 品質評価 |
|----------|------|----------|
| SKILL.md | Skill 定義（YAML + 本文） | 4/5（実用的） |
| prompt_templates.md | 4種類のプロンプトテンプレート | 5/5（包括的） |
| evaluation_criteria.md | 評価基準・選択戦略 | 5/5（詳細） |
| merge_strategies.md | マージ戦略・Python 実装例 | 5/5（実装可能） |

---

---

## Meta-Phase 3: codex_exec.py 実装（コンペ方式）

実施日: 2025-12-22

### 実装概要

Python ラッパースクリプト `codex_exec.py` を実装。

**ファイル**: `.claude/skills/codex-subagent/scripts/codex_exec.py`

### 実装した機能

| 機能 | 説明 |
|------|------|
| 実行モード | SINGLE, PARALLEL, COMPETITION |
| サンドボックス | read-only, workspace-write, danger-full-access |
| タスク種別 | code_gen, code_review, analysis, documentation |
| 選択戦略 | best_single, voting, hybrid, conservative |
| マージ戦略 | concat, dedup, priority, consensus |
| 出力形式 | テキスト / JSON |

### 主要コンポーネント

```python
# データクラス
@dataclass
class CodexResult:
    agent_id: str
    output: str
    tokens_used: int
    execution_time: float
    success: bool

@dataclass
class EvaluationScore:
    correctness: float  # 40%
    completeness: float  # 25%
    quality: float  # 20%
    efficiency: float  # 15%

# 主要関数
run_codex_exec()           # 単一実行（同期）
run_codex_exec_async()     # 単一実行（非同期）
execute_parallel()         # 並列実行
execute_competition()      # コンペモード
evaluate_result()          # 結果評価
select_best()              # 最良選択
merge_outputs()            # 出力マージ
```

### テスト結果

#### Trial 9: 単一実行テスト

```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode single \
  --prompt "2+2は？数字のみ回答" \
  --sandbox read-only \
  --json
```

**結果**:
```json
{
  "agent_id": "agent_0",
  "output": "4\n",
  "tokens_used": 2,
  "execution_time": 5.09,
  "success": true,
  "error_message": ""
}
```

#### Trial 10: コンペモードテスト

```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode competition \
  --prompt "Pythonでフィボナッチ数列を生成する関数を書いてください。コードのみ。" \
  --count 2 \
  --sandbox read-only \
  --task-type code_gen \
  --strategy best_single \
  --json
```

**結果**:
```json
{
  "agent_id": "agent_0",
  "output": "```python\ndef fibonacci(n):\n    if n < 0:\n        raise ValueError(\"n must be non-negative\")\n    seq = []\n    a, b = 0, 1\n    for _ in range(n):\n        seq.append(a)\n        a, b = b, a + b\n    return seq\n```\n",
  "combined_score": 3.95,
  "scores": {
    "correctness": 4.5,
    "completeness": 3.5,
    "quality": 3.5,
    "efficiency": 4.5,
    "task_score": 3.8
  },
  "execution_time": 7.42,
  "success": true
}
```

### 重要な発見

1. **並列実行の効率性**:
   - asyncio による並列実行が正常に動作
   - 2並列でも実行時間は単一とほぼ同等（~7秒）

2. **評価ロジックの有効性**:
   - ヒューリスティック評価が適切に機能
   - コードブロック、エラーハンドリング検出が動作
   - task_score による追加評価が有効

3. **選択戦略の動作**:
   - best_single: 総合スコア最大を選択
   - 実際のコンペでは agent_0 が選択された

---

## Meta-Phase 3 完了サマリー

### Skill ディレクトリ最終構造

```
.claude/skills/codex-subagent/
├── SKILL.md                          # Skill 定義
├── scripts/
│   └── codex_exec.py                 # 実行ラッパー（NEW）
└── references/
    ├── prompt_templates.md           # プロンプトテンプレート集
    ├── evaluation_criteria.md        # 評価基準カタログ
    └── merge_strategies.md           # マージ戦略ガイド
```

### 使用例

```bash
# 単一実行（シンプル）
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode single \
  --prompt "タスク内容" \
  --sandbox read-only

# コンペモード（品質重視）
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode competition \
  --prompt "コード生成タスク" \
  --count 3 \
  --task-type code_gen \
  --strategy best_single \
  --json

# 並列実行（情報収集）
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode parallel \
  --prompt "調査タスク" \
  --count 3 \
  --merge concat
```

---

## 全 Meta-Phase 完了ステータス

| Phase | 内容 | 状態 |
|-------|------|------|
| M-0 | sandbox モード検証 | ✅ 完了 |
| M-1 | プロンプトテンプレート生成 | ✅ 完了 |
| M-2 | 並列実行で成果物生成 | ✅ 完了 |
| M-3 | codex_exec.py 実装 | ✅ 完了 |

---

---

## Meta-Phase 4: Slash Command 作成

実施日: 2025-12-22

### 作成したファイル

**ファイル**: `.claude/commands/tasks/codex-subagent.md`

### コマンド仕様

```bash
/codex-subagent <task> [options]
```

| オプション | 説明 |
|-----------|------|
| `-s` | Single mode（高速） |
| `-p` | Parallel mode（情報収集） |
| `-c` | Competition mode（品質重視） |
| `-n N` | 実行回数指定 |
| `--json` | JSON 出力 |
| `-v` | 詳細出力 |

### タスク種別

| 種別 | キーワード |
|------|----------|
| CODE_GEN | gen, generate, create, implement |
| CODE_REVIEW | review, check, audit |
| ANALYSIS | analyze, investigate, research |
| DOCUMENTATION | doc, docs, document |

### 使用例

```bash
# 単純なコード生成
/codex-subagent gen "Python function to parse JSON"

# 品質重視のコード生成
/codex-subagent gen "authentication middleware" -c -n 5

# 並列分析
/codex-subagent analyze "performance bottlenecks" -p
```

---

## 全 Meta-Phase 完了ステータス（最終）

| Phase | 内容 | 状態 |
|-------|------|------|
| M-0 | sandbox モード検証 | ✅ 完了 |
| M-1 | プロンプトテンプレート生成 | ✅ 完了 |
| M-2 | 並列実行で成果物生成 | ✅ 完了 |
| M-3 | codex_exec.py 実装 | ✅ 完了 |
| M-4 | Slash Command 作成 | ✅ 完了 |

---

## 最終成果物一覧

### Skill ディレクトリ

```
.claude/skills/codex-subagent/
├── SKILL.md                          # Skill 定義
├── scripts/
│   └── codex_exec.py                 # Python ラッパー
└── references/
    ├── prompt_templates.md           # プロンプトテンプレート
    ├── evaluation_criteria.md        # 評価基準
    └── merge_strategies.md           # マージ戦略
```

### Slash Command

```
.claude/commands/tasks/codex-subagent.md  # Slash Command
```

---

## 今後の展開（オプション）

1. ~~実運用テストの蓄積~~ ✅ M-5 で実装
2. ~~評価ロジックの改善（LLM ベース評価の追加）~~ ✅ M-5 で実装
3. AGENTS.md への統合（codex-subagent セクション追加）
4. Pipeline モードの実装

---

## Meta-Phase 5: ログ蓄積・評価改善システム

実施日: 2025-12-22

### 目的

- 全 codex exec 実行のログを自動蓄積
- 人間フィードバックの収集
- LLM-as-Judge による意味的評価
- ヒューリスティック評価の継続的改善

### 実装内容

#### 1. codex_exec.py へのログ機能追加

| 追加項目 | 説明 |
|----------|------|
| `ExecutionLog` データクラス | JSONL 形式のログ構造 |
| `write_log()` 関数 | ログファイル書き込み |
| `--log` / `--no-log` フラグ | ログ有効化/無効化 |
| `--llm-eval` フラグ | LLM 評価強制実行 |

#### 2. LLM-as-Judge（codex exec 使用）

```python
async def evaluate_with_llm(output, prompt, task_type):
    """codex exec を使った LLM 評価"""
    # max プラン定額のためコスト $0
```

**トリガー条件**:
- Competition モード: 常に実行
- サンプリング: 20%
- エッジケース: ヒューリスティックスコア < 2.5 or > 4.5
- 明示リクエスト: `--llm-eval` フラグ

#### 3. 新規 CLI ツール

| ツール | 目的 | 行数 |
|--------|------|------|
| `codex_feedback.py` | 人間フィードバック追加 | ~100 |
| `codex_query.py` | ログ検索・統計 | ~150 |

### ストレージ構造

```
sessions/
└── codex_exec/
    └── 2025/
        └── 12/
            └── 22/
                └── run-{timestamp}-{uuid}.jsonl
```

### JSONL ログスキーマ

```json
{
  "schema_version": "1.0",
  "run_id": "49ceaac0-3018-4a66-9d2f-fea643ae080e",
  "timestamp": "2025-12-22T15:45:39.216627+00:00",
  "execution": {
    "mode": "single",
    "prompt": "Hello World",
    "sandbox": "read-only",
    "task_type": "code_gen",
    "count": 1
  },
  "results": [{
    "agent_id": "agent_0",
    "output": "...",
    "tokens_used": 38,
    "execution_time": 103.38,
    "success": true
  }],
  "evaluation": {
    "heuristic": {
      "correctness": 4.5,
      "completeness": 3.0,
      "quality": 3.8,
      "efficiency": 3.0,
      "combined_score": 3.456
    },
    "human": null,
    "llm": null
  },
  "metadata": {
    "git_branch": "main",
    "git_commit": "b69a196"
  }
}
```

### テスト結果

#### Trial 11: ログ機能テスト

```bash
uv run python .claude/skills/codex-subagent/scripts/codex_exec.py \
  --mode single \
  --prompt "Hello World" \
  --sandbox read-only \
  --verbose
```

**結果**:
- ✅ ログファイル生成: `sessions/codex_exec/2025/12/22/run-20251222T154539-49ceaac0.jsonl`
- ✅ ヒューリスティック評価記録

#### Trial 12: フィードバック追加テスト

```bash
uv run python .claude/skills/codex-subagent/scripts/codex_feedback.py \
  --score 4.0 \
  --notes "Test feedback - logging works correctly"
```

**結果**: ✅ `run-20251222T154539-49ceaac0.jsonl` にフィードバック追加

#### Trial 13: クエリ・統計テスト

```bash
uv run python .claude/skills/codex-subagent/scripts/codex_query.py --list
uv run python .claude/skills/codex-subagent/scripts/codex_query.py --stats
```

**結果**:
```
Run ID     Timestamp                 Mode         Task            Score    Human  LLM
------------------------------------------------------------------------------------------
49ceaac0   2025-12-22T15:45:39.216   single       code_gen        3.46     4.0    -

==================================================
CODEX EXEC LOG STATISTICS
==================================================

Total Runs: 1
Heuristic Scores: Average: 3.46
Human Feedback (1 entries): Average: 4.00
```

---

## 全 Meta-Phase 完了ステータス（最終更新）

| Phase | 内容 | 状態 |
|-------|------|------|
| M-0 | sandbox モード検証 | ✅ 完了 |
| M-1 | プロンプトテンプレート生成 | ✅ 完了 |
| M-2 | 並列実行で成果物生成 | ✅ 完了 |
| M-3 | codex_exec.py 実装 | ✅ 完了 |
| M-4 | Slash Command 作成 | ✅ 完了 |
| M-5 | ログ蓄積・評価改善システム | ✅ 完了 |

---

## 最終成果物一覧（更新）

### Skill ディレクトリ

```
.claude/skills/codex-subagent/
├── SKILL.md                          # Skill 定義
├── scripts/
│   ├── codex_exec.py                 # Python ラッパー（ログ・LLM評価付き）
│   ├── codex_feedback.py             # フィードバック追加 CLI
│   └── codex_query.py                # ログ検索・統計 CLI
└── references/
    ├── prompt_templates.md           # プロンプトテンプレート
    ├── evaluation_criteria.md        # 評価基準
    └── merge_strategies.md           # マージ戦略
```

### ログディレクトリ

```
sessions/
└── codex_exec/
    └── YYYY/MM/DD/run-*.jsonl        # 実行ログ
```
