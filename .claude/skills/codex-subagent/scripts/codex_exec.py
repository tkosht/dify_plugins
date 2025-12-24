#!/usr/bin/env python3
"""
codex_exec.py - Codex exec サブエージェント実行ラッパー

実行モード:
- SINGLE: 単一実行
- PARALLEL: 並列実行（結果を結合）
- COMPETITION: 複数実行 → 評価 → 最良選択

使用例:
    # 単一実行
    python codex_exec.py --mode single --prompt "Hello World"

    # 並列実行（3並列）
    python codex_exec.py --mode parallel --prompt "タスク" --count 3

    # コンペモード
    python codex_exec.py --mode competition --prompt "コード生成" --count 3
        --task-type code_gen
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import subprocess
import sys
import time
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

# ============================================================================
# Logging Configuration
# ============================================================================

LOG_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "sessions"
    / "codex_exec"
)
MAX_OUTPUT_SIZE = 10 * 1024  # 10KB
SCHEMA_VERSION = "1.0"
LLM_EVAL_SAMPLE_RATE = 0.2  # 20% sampling for LLM evaluation


class ExecutionMode(str, Enum):
    SINGLE = "single"
    PARALLEL = "parallel"
    COMPETITION = "competition"


class SandboxMode(str, Enum):
    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"
    FULL_ACCESS = "danger-full-access"


class TaskType(str, Enum):
    CODE_GEN = "code_gen"
    CODE_REVIEW = "code_review"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"


class SelectionStrategy(str, Enum):
    BEST_SINGLE = "best_single"
    VOTING = "voting"
    HYBRID = "hybrid"
    CONSERVATIVE = "conservative"


class MergeStrategy(str, Enum):
    CONCAT = "concat"
    DEDUP = "dedup"
    PRIORITY = "priority"
    CONSENSUS = "consensus"


@dataclass
class CodexResult:
    """codex exec の実行結果"""

    agent_id: str
    output: str
    tokens_used: int = 0
    execution_time: float = 0.0
    success: bool = True
    error_message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationScore:
    """評価スコア"""

    correctness: float = 0.0  # 40%
    completeness: float = 0.0  # 25%
    quality: float = 0.0  # 20%
    efficiency: float = 0.0  # 15%

    @property
    def total(self) -> float:
        return (
            self.correctness * 0.40
            + self.completeness * 0.25
            + self.quality * 0.20
            + self.efficiency * 0.15
        )


@dataclass
class EvaluatedResult:
    """評価済み結果"""

    result: CodexResult
    score: EvaluationScore
    task_score: float = 0.0
    combined_score: float = 0.0


@dataclass
class MergeConfig:
    """マージ設定"""

    min_votes: int = 2
    min_ratio: float = 0.6
    priority_weight: float = 1.0
    confidence_weight: float = 1.0


# ============================================================================
# Logging Data Structures
# ============================================================================


@dataclass
class ExecutionLog:
    """実行ログ（JSONL形式で保存）"""

    schema_version: str = SCHEMA_VERSION
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    execution: dict[str, Any] = field(default_factory=dict)
    results: list[dict[str, Any]] = field(default_factory=list)
    evaluation: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


def get_git_info() -> dict[str, str]:
    """Git情報を取得"""
    info = {}
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            info["git_branch"] = result.stdout.strip()

        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            info["git_commit"] = result.stdout.strip()
    except Exception:
        pass
    return info


def write_log(log: ExecutionLog) -> Path | None:
    """ログをJSONL形式で書き込み"""
    try:
        now = datetime.now(UTC)
        log_dir = LOG_DIR / now.strftime("%Y/%m/%d")
        log_dir.mkdir(parents=True, exist_ok=True)

        filename = (
            f"run-{now.strftime('%Y%m%dT%H%M%S')}-{log.run_id[:8]}.jsonl"
        )
        log_path = log_dir / filename

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(log), ensure_ascii=False) + "\n")

        return log_path
    except Exception as e:
        print(f"Warning: Failed to write log: {e}", file=sys.stderr)
        return None


def truncate_output(output: str, max_size: int = MAX_OUTPUT_SIZE) -> str:
    """出力をトランケート"""
    if len(output) <= max_size:
        return output
    return (
        output[:max_size] + f"\n... (truncated, original {len(output)} chars)"
    )


# ============================================================================
# LLM-as-Judge (using codex exec)
# ============================================================================


async def evaluate_with_llm(
    output: str,
    prompt: str,
    task_type: TaskType,
    timeout: int = 60,
) -> dict[str, Any] | None:
    """codex exec を使った LLM 評価"""
    eval_prompt = f"""You are an expert code evaluator. Evaluate the following output.

Task Type: {task_type.value}
Original Prompt: {prompt[:500]}

Output to Evaluate:
{truncate_output(output, 2000)}

Rate this output on a 1-5 scale for each criterion:
- CORRECTNESS: Does it meet requirements? No errors?
- COMPLETENESS: Are all requested items present?
- QUALITY: Is it readable, maintainable?
- EFFICIENCY: Is execution fast, tokens minimal?

Respond in JSON format ONLY (no explanation):
{{
  "correctness": N,
  "completeness": N,
  "quality": N,
  "efficiency": N,
  "rationale": "brief assessment",
  "strengths": ["..."],
  "weaknesses": ["..."]
}}"""

    try:
        result = await run_codex_exec_async(
            prompt=eval_prompt,
            sandbox=SandboxMode.READ_ONLY,
            timeout=timeout,
            agent_id="llm_judge",
        )

        if result.success and result.output:
            # JSON を抽出
            json_match = re.search(r"\{[^{}]*\}", result.output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
    except Exception as e:
        print(f"Warning: LLM evaluation failed: {e}", file=sys.stderr)

    return None


def should_run_llm_eval(
    mode: ExecutionMode,
    heuristic_score: float,
    force_llm_eval: bool = False,
) -> bool:
    """LLM評価を実行すべきか判定"""
    if force_llm_eval:
        return True

    # Competition モードは常に実行
    if mode == ExecutionMode.COMPETITION:
        return True

    # エッジケース（スコアが極端）
    if heuristic_score < 2.5 or heuristic_score > 4.5:
        return True

    # サンプリング（20%）
    return random.random() < LLM_EVAL_SAMPLE_RATE


# ============================================================================
# Core Execution Functions
# ============================================================================


def run_codex_exec(
    prompt: str,
    sandbox: SandboxMode = SandboxMode.READ_ONLY,
    timeout: int = 120,
    agent_id: str = "agent_0",
    workdir: str | None = None,
) -> CodexResult:
    """単一の codex exec を実行"""
    start_time = time.time()

    cmd = ["codex", "exec", "--sandbox", sandbox.value]
    if workdir:
        cmd.extend(["--cd", workdir])
    cmd.append(prompt)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        execution_time = time.time() - start_time

        # トークン数を出力から抽出（概算）
        output = result.stdout
        tokens_used = len(output.split()) * 2  # 概算

        return CodexResult(
            agent_id=agent_id,
            output=output,
            tokens_used=tokens_used,
            execution_time=execution_time,
            success=result.returncode == 0,
            error_message=result.stderr if result.returncode != 0 else "",
        )
    except subprocess.TimeoutExpired:
        return CodexResult(
            agent_id=agent_id,
            output="",
            execution_time=timeout,
            success=False,
            error_message=f"Timeout after {timeout}s",
        )
    except Exception as e:
        return CodexResult(
            agent_id=agent_id,
            output="",
            success=False,
            error_message=str(e),
        )


async def run_codex_exec_async(
    prompt: str,
    sandbox: SandboxMode = SandboxMode.READ_ONLY,
    timeout: int = 120,
    agent_id: str = "agent_0",
    workdir: str | None = None,
) -> CodexResult:
    """非同期で codex exec を実行"""
    start_time = time.time()

    cmd = ["codex", "exec", "--sandbox", sandbox.value]
    if workdir:
        cmd.extend(["--cd", workdir])
    cmd.append(prompt)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )
        execution_time = time.time() - start_time

        output = stdout.decode("utf-8")
        tokens_used = len(output.split()) * 2

        return CodexResult(
            agent_id=agent_id,
            output=output,
            tokens_used=tokens_used,
            execution_time=execution_time,
            success=process.returncode == 0,
            error_message=(
                stderr.decode("utf-8") if process.returncode != 0 else ""
            ),
        )
    except TimeoutError:
        return CodexResult(
            agent_id=agent_id,
            output="",
            execution_time=timeout,
            success=False,
            error_message=f"Timeout after {timeout}s",
        )
    except Exception as e:
        return CodexResult(
            agent_id=agent_id,
            output="",
            success=False,
            error_message=str(e),
        )


async def execute_parallel(
    prompts: list[str],
    sandbox: SandboxMode = SandboxMode.READ_ONLY,
    timeout: int = 120,
    workdir: str | None = None,
) -> list[CodexResult]:
    """複数のプロンプトを並列実行"""
    tasks = [
        run_codex_exec_async(
            prompt=p,
            sandbox=sandbox,
            timeout=timeout,
            agent_id=f"agent_{i}",
            workdir=workdir,
        )
        for i, p in enumerate(prompts)
    ]
    return await asyncio.gather(*tasks)


async def execute_competition(
    prompt: str,
    count: int = 3,
    sandbox: SandboxMode = SandboxMode.READ_ONLY,
    timeout: int = 120,
    task_type: TaskType = TaskType.CODE_GEN,
    strategy: SelectionStrategy = SelectionStrategy.BEST_SINGLE,
    workdir: str | None = None,
) -> EvaluatedResult:
    """コンペモード: 複数実行 → 評価 → 最良選択"""
    # 同一プロンプトで複数回実行
    prompts = [prompt] * count
    results = await execute_parallel(prompts, sandbox, timeout, workdir)

    # 成功した結果のみ評価
    successful = [r for r in results if r.success]
    if not successful:
        # 全て失敗した場合、最初の結果を返す
        return EvaluatedResult(
            result=(
                results[0]
                if results
                else CodexResult(
                    agent_id="none",
                    output="",
                    success=False,
                    error_message="No results",
                )
            ),
            score=EvaluationScore(),
        )

    # 各結果を評価
    evaluated = [evaluate_result(r, task_type) for r in successful]

    # 選択戦略に基づいて最良を選択
    best = select_best(evaluated, strategy)
    return best


def evaluate_result(
    result: CodexResult, task_type: TaskType
) -> EvaluatedResult:
    """結果を評価してスコアを付与"""
    output = result.output
    score = EvaluationScore()

    # 基本的なヒューリスティック評価
    # CORRECTNESS: 出力があり、エラーがない
    if result.success and output:
        score.correctness = 4.0
        if len(output) > 100:
            score.correctness = 4.5
    elif result.success:
        score.correctness = 3.0
    else:
        score.correctness = 1.0

    # COMPLETENESS: 出力の長さと構造
    if output:
        # コードブロックの存在
        has_code = "```" in output
        # 見出しの存在
        has_headers = re.search(r"^#+\s", output, re.MULTILINE) is not None

        score.completeness = 3.0
        if has_code:
            score.completeness += 0.5
        if has_headers:
            score.completeness += 0.5
        if len(output) > 500:
            score.completeness += 0.5

    # QUALITY: 構造化と可読性
    if output:
        score.quality = 3.5
        # リストの存在
        if re.search(r"^[-*]\s", output, re.MULTILINE):
            score.quality += 0.3
        # 番号付きリスト
        if re.search(r"^\d+\.\s", output, re.MULTILINE):
            score.quality += 0.2

    # EFFICIENCY: 実行時間とトークン効率
    if result.execution_time < 30:
        score.efficiency = 4.5
    elif result.execution_time < 60:
        score.efficiency = 4.0
    elif result.execution_time < 120:
        score.efficiency = 3.0
    else:
        score.efficiency = 2.0

    # タスク別追加評価
    task_score = evaluate_task_specific(result, task_type)

    # 総合スコア（汎用60% + タスク別40%）
    combined = score.total * 0.6 + task_score * 0.4

    return EvaluatedResult(
        result=result,
        score=score,
        task_score=task_score,
        combined_score=combined,
    )


def evaluate_task_specific(result: CodexResult, task_type: TaskType) -> float:
    """タスク別の評価"""
    output = result.output

    if task_type == TaskType.CODE_GEN:
        score = 3.0
        # 関数/クラス定義の存在
        if re.search(r"(def |class |function |const |let )", output):
            score += 0.5
        # テストの言及
        if re.search(r"(test|spec|assert)", output, re.IGNORECASE):
            score += 0.5
        # エラーハンドリング
        if re.search(r"(try|except|catch|error)", output, re.IGNORECASE):
            score += 0.3
        return min(score, 5.0)

    elif task_type == TaskType.CODE_REVIEW:
        score = 3.0
        # 問題指摘
        if re.search(r"(bug|issue|problem|concern)", output, re.IGNORECASE):
            score += 0.5
        # 改善提案
        if re.search(
            r"(suggest|recommend|consider|should)", output, re.IGNORECASE
        ):
            score += 0.5
        # 行番号参照
        if re.search(r"line\s*\d+", output, re.IGNORECASE):
            score += 0.3
        return min(score, 5.0)

    elif task_type == TaskType.ANALYSIS:
        score = 3.0
        # 根拠の明示
        if re.search(r"(because|since|due to|reason)", output, re.IGNORECASE):
            score += 0.5
        # 構造化された分析
        if re.search(r"(overview|summary|conclusion)", output, re.IGNORECASE):
            score += 0.5
        return min(score, 5.0)

    elif task_type == TaskType.DOCUMENTATION:
        score = 3.0
        # セクション構造
        if output.count("#") >= 3:
            score += 0.5
        # 使用例
        if re.search(r"(example|usage|sample)", output, re.IGNORECASE):
            score += 0.5
        # コードブロック
        if "```" in output:
            score += 0.3
        return min(score, 5.0)

    return 3.0


def select_best(
    evaluated: list[EvaluatedResult],
    strategy: SelectionStrategy,
) -> EvaluatedResult:
    """選択戦略に基づいて最良の結果を選択"""
    if not evaluated:
        raise ValueError("No evaluated results")

    if strategy == SelectionStrategy.BEST_SINGLE:
        # 総合スコア最大
        return max(evaluated, key=lambda e: e.combined_score)

    elif strategy == SelectionStrategy.VOTING:
        # 平均スコアが高いもの（同一出力が複数あれば加点）
        output_counts: dict[str, int] = Counter(
            e.result.output for e in evaluated
        )
        for e in evaluated:
            vote_bonus = (output_counts[e.result.output] - 1) * 0.1
            e.combined_score += vote_bonus
        return max(evaluated, key=lambda e: e.combined_score)

    elif strategy == SelectionStrategy.HYBRID:
        # CORRECTNESS >= 4.0 かつ総合上位
        qualified = [e for e in evaluated if e.score.correctness >= 4.0]
        if qualified:
            return max(qualified, key=lambda e: e.combined_score)
        return max(evaluated, key=lambda e: e.combined_score)

    elif strategy == SelectionStrategy.CONSERVATIVE:
        # 実行時間が短く、合格ラインを満たすもの
        qualified = [e for e in evaluated if e.combined_score >= 3.5]
        if qualified:
            return min(qualified, key=lambda e: e.result.execution_time)
        return min(evaluated, key=lambda e: e.result.execution_time)

    return evaluated[0]


def _normalize(text: str) -> str:
    """テキストの正規化"""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s-]", "", text)
    return text


def merge_outputs(
    results: list[CodexResult],
    strategy: MergeStrategy,
    config: MergeConfig | None = None,
) -> str:
    """複数の出力をマージ"""
    if config is None:
        config = MergeConfig()

    outputs = [r.output for r in results if r.success and r.output]

    if not outputs:
        return ""

    if strategy == MergeStrategy.CONCAT:
        # 全て結合（セパレータ付き）
        return "\n\n---\n\n".join(outputs)

    elif strategy == MergeStrategy.DEDUP:
        # 重複除去
        seen = set()
        unique = []
        for o in outputs:
            normalized = _normalize(o)
            if normalized not in seen:
                seen.add(normalized)
                unique.append(o)
        return "\n\n---\n\n".join(unique)

    elif strategy == MergeStrategy.PRIORITY:
        # 最初の成功結果を優先
        return outputs[0]

    elif strategy == MergeStrategy.CONSENSUS:
        # 最も多い出力を採用
        normalized_outputs = [_normalize(o) for o in outputs]
        counts = Counter(normalized_outputs)
        top_normalized, top_count = counts.most_common(1)[0]

        if top_count >= config.min_votes:
            ratio = top_count / len(outputs)
            if ratio >= config.min_ratio:
                # 合意された出力の元のテキストを返す
                for o in outputs:
                    if _normalize(o) == top_normalized:
                        return o

        # フォールバック: 最初の出力
        return outputs[0]

    return outputs[0] if outputs else ""


def format_output(
    result: EvaluatedResult,
    verbose: bool = False,
) -> str:
    """結果を整形して出力"""
    lines = []

    if verbose:
        lines.append(f"Agent ID: {result.result.agent_id}")
        lines.append(f"Execution Time: {result.result.execution_time:.2f}s")
        lines.append(f"Tokens: {result.result.tokens_used}")
        lines.append(f"Score: {result.combined_score:.2f}")
        lines.append(f"  - Correctness: {result.score.correctness:.1f}")
        lines.append(f"  - Completeness: {result.score.completeness:.1f}")
        lines.append(f"  - Quality: {result.score.quality:.1f}")
        lines.append(f"  - Efficiency: {result.score.efficiency:.1f}")
        lines.append(f"  - Task Score: {result.task_score:.1f}")
        lines.append("")
        lines.append("--- Output ---")

    lines.append(result.result.output)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="codex exec サブエージェント実行ラッパー"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=[m.value for m in ExecutionMode],
        default=ExecutionMode.SINGLE.value,
        help="実行モード",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="実行するプロンプト",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="並列/コンペモードでの実行回数",
    )
    parser.add_argument(
        "--sandbox",
        type=str,
        choices=[s.value for s in SandboxMode],
        default=SandboxMode.READ_ONLY.value,
        help="サンドボックスモード",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="タイムアウト（秒）",
    )
    parser.add_argument(
        "--task-type",
        type=str,
        choices=[t.value for t in TaskType],
        default=TaskType.CODE_GEN.value,
        help="タスク種別（コンペモード用）",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=[s.value for s in SelectionStrategy],
        default=SelectionStrategy.BEST_SINGLE.value,
        help="選択戦略（コンペモード用）",
    )
    parser.add_argument(
        "--merge",
        type=str,
        choices=[m.value for m in MergeStrategy],
        default=MergeStrategy.CONCAT.value,
        help="マージ戦略（並列モード用）",
    )
    parser.add_argument(
        "--workdir",
        type=str,
        default=None,
        help="作業ディレクトリ",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="詳細出力",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON形式で出力",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        default=True,
        help="ログを記録（デフォルト: 有効）",
    )
    parser.add_argument(
        "--no-log",
        action="store_true",
        help="ログを無効化",
    )
    parser.add_argument(
        "--llm-eval",
        action="store_true",
        help="LLM評価を強制実行",
    )

    args = parser.parse_args()

    # --no-log が指定されていたらログを無効化
    enable_logging = args.log and not args.no_log

    mode = ExecutionMode(args.mode)
    sandbox = SandboxMode(args.sandbox)
    task_type = TaskType(args.task_type)
    strategy = SelectionStrategy(args.strategy)
    merge_strat = MergeStrategy(args.merge)

    if mode == ExecutionMode.SINGLE:
        result = run_codex_exec(
            prompt=args.prompt,
            sandbox=sandbox,
            timeout=args.timeout,
            workdir=args.workdir,
        )

        # ヒューリスティック評価
        evaluated = evaluate_result(result, task_type)
        heuristic_eval = {
            "correctness": evaluated.score.correctness,
            "completeness": evaluated.score.completeness,
            "quality": evaluated.score.quality,
            "efficiency": evaluated.score.efficiency,
            "combined_score": evaluated.combined_score,
        }

        # LLM 評価（条件付き）
        llm_eval = None
        if should_run_llm_eval(mode, evaluated.combined_score, args.llm_eval):
            llm_eval = asyncio.run(
                evaluate_with_llm(result.output, args.prompt, task_type)
            )

        # ログ出力
        if enable_logging:
            log = ExecutionLog(
                execution={
                    "mode": mode.value,
                    "prompt": truncate_output(args.prompt, 1000),
                    "sandbox": sandbox.value,
                    "task_type": task_type.value,
                    "count": 1,
                },
                results=[
                    {
                        "agent_id": result.agent_id,
                        "output": truncate_output(result.output),
                        "tokens_used": result.tokens_used,
                        "execution_time": result.execution_time,
                        "success": result.success,
                    }
                ],
                evaluation={
                    "heuristic": heuristic_eval,
                    "human": None,
                    "llm": llm_eval,
                },
                metadata=get_git_info(),
            )
            log_path = write_log(log)
            if args.verbose and log_path:
                print(f"Log saved: {log_path}", file=sys.stderr)

        if args.json:
            print(
                json.dumps(
                    {
                        "agent_id": result.agent_id,
                        "output": result.output,
                        "tokens_used": result.tokens_used,
                        "execution_time": result.execution_time,
                        "success": result.success,
                        "error_message": result.error_message,
                        "evaluation": {
                            "heuristic": heuristic_eval,
                            "llm": llm_eval,
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            if args.verbose:
                print(f"Execution Time: {result.execution_time:.2f}s")
                print(f"Success: {result.success}")
                print(f"Score: {evaluated.combined_score:.2f}")
                print("--- Output ---")
            print(result.output)

    elif mode == ExecutionMode.PARALLEL:
        prompts = [args.prompt] * args.count
        results = asyncio.run(
            execute_parallel(
                prompts=prompts,
                sandbox=sandbox,
                timeout=args.timeout,
                workdir=args.workdir,
            )
        )
        merged = merge_outputs(results, merge_strat)

        # 各結果の評価
        evaluated_results = [
            evaluate_result(r, task_type) for r in results if r.success
        ]
        avg_score = (
            sum(e.combined_score for e in evaluated_results)
            / len(evaluated_results)
            if evaluated_results
            else 0
        )

        # ログ出力
        if enable_logging:
            log = ExecutionLog(
                execution={
                    "mode": mode.value,
                    "prompt": truncate_output(args.prompt, 1000),
                    "sandbox": sandbox.value,
                    "task_type": task_type.value,
                    "count": args.count,
                    "merge_strategy": merge_strat.value,
                },
                results=[
                    {
                        "agent_id": r.agent_id,
                        "output": truncate_output(r.output),
                        "tokens_used": r.tokens_used,
                        "execution_time": r.execution_time,
                        "success": r.success,
                    }
                    for r in results
                ],
                evaluation={
                    "heuristic": {"average_score": avg_score},
                    "human": None,
                    "llm": None,
                },
                metadata=get_git_info(),
            )
            log_path = write_log(log)
            if args.verbose and log_path:
                print(f"Log saved: {log_path}", file=sys.stderr)

        if args.json:
            print(
                json.dumps(
                    {
                        "results": [
                            {
                                "agent_id": r.agent_id,
                                "output": r.output,
                                "success": r.success,
                                "execution_time": r.execution_time,
                            }
                            for r in results
                        ],
                        "merged_output": merged,
                        "evaluation": {"average_score": avg_score},
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            if args.verbose:
                for r in results:
                    print(
                        f"[{r.agent_id}] Time: {r.execution_time:.2f}s, "
                        f"Success: {r.success}"
                    )
                print(f"Average Score: {avg_score:.2f}")
                print("--- Merged Output ---")
            print(merged)

    elif mode == ExecutionMode.COMPETITION:
        best = asyncio.run(
            execute_competition(
                prompt=args.prompt,
                count=args.count,
                sandbox=sandbox,
                timeout=args.timeout,
                task_type=task_type,
                strategy=strategy,
                workdir=args.workdir,
            )
        )

        heuristic_eval = {
            "correctness": best.score.correctness,
            "completeness": best.score.completeness,
            "quality": best.score.quality,
            "efficiency": best.score.efficiency,
            "task_score": best.task_score,
            "combined_score": best.combined_score,
        }

        # LLM 評価（Competition モードは常に実行）
        llm_eval = None
        if should_run_llm_eval(mode, best.combined_score, args.llm_eval):
            llm_eval = asyncio.run(
                evaluate_with_llm(best.result.output, args.prompt, task_type)
            )

        # ログ出力
        if enable_logging:
            log = ExecutionLog(
                execution={
                    "mode": mode.value,
                    "prompt": truncate_output(args.prompt, 1000),
                    "sandbox": sandbox.value,
                    "task_type": task_type.value,
                    "count": args.count,
                    "strategy": strategy.value,
                },
                results=[
                    {
                        "agent_id": best.result.agent_id,
                        "output": truncate_output(best.result.output),
                        "tokens_used": best.result.tokens_used,
                        "execution_time": best.result.execution_time,
                        "success": best.result.success,
                        "selected": True,
                    }
                ],
                evaluation={
                    "heuristic": heuristic_eval,
                    "human": None,
                    "llm": llm_eval,
                },
                metadata=get_git_info(),
            )
            log_path = write_log(log)
            if args.verbose and log_path:
                print(f"Log saved: {log_path}", file=sys.stderr)

        if args.json:
            print(
                json.dumps(
                    {
                        "agent_id": best.result.agent_id,
                        "output": best.result.output,
                        "combined_score": best.combined_score,
                        "scores": {
                            "correctness": best.score.correctness,
                            "completeness": best.score.completeness,
                            "quality": best.score.quality,
                            "efficiency": best.score.efficiency,
                            "task_score": best.task_score,
                        },
                        "execution_time": best.result.execution_time,
                        "success": best.result.success,
                        "llm_evaluation": llm_eval,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(format_output(best, verbose=args.verbose))


if __name__ == "__main__":
    main()
