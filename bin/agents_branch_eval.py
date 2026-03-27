#!/usr/bin/env python3
# ruff: noqa: E501
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import textwrap
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_ROOT = (
    REPO_ROOT / "docs" / "ai-agent-reviews" / "agents_branch_eval_2026-03-21"
)
RESULTS_ROOT = EVAL_ROOT / "results"
PROMPTS_ROOT = EVAL_ROOT / "prompts"
SCHEMAS_ROOT = EVAL_ROOT / "schemas"
SUBAGENT_ROOT = EVAL_ROOT / "subagent"
FIXTURES_ROOT = EVAL_ROOT / "fixtures"
DEFAULT_WORKTREE_ROOT = (
    Path.home() / "eval-worktrees" / "agents_branch_eval_2026-03-21"
)
DEFAULT_TIMEOUT_SECONDS = 900
TIMESTAMP = "2026-03-21"
DEFAULT_PARENT_REPS = (1, 2, 3, 4, 5)
HARNESS_REVISION = "2026-03-22-review-baseline"
EVAL_CODEX_CONFIG_OVERRIDES = (
    'mcp_servers.serena.command="false"',
    "mcp_servers.serena.args=[]",
    'mcp_servers.codex_mcp.command="false"',
    "mcp_servers.codex_mcp.args=[]",
    'mcp_servers.context7.command="false"',
    "mcp_servers.context7.args=[]",
    'mcp_servers.sequential-thinking.command="false"',
    "mcp_servers.sequential-thinking.args=[]",
)


@dataclass(frozen=True)
class BranchArm:
    alias: str
    ref: str


@dataclass(frozen=True)
class TaskDef:
    task_id: str
    kind: str
    prompt_file: str
    schema_file: str | None
    sandbox: str
    allowed_write: tuple[str, ...]
    timeout_seconds: int | None = None
    ruff_targets: tuple[str, ...] = ()
    pytest_targets: tuple[str, ...] = ()
    setup_patch: str | None = None
    package_dir: str | None = None
    package_required: bool = False
    uses_search: bool = False


BRANCH_ARMS = (
    BranchArm(alias="arm_alpha", ref="main"),
    BranchArm(alias="arm_beta", ref="docs/agent-instructions-simplify"),
)

PRIMARY_TASK_IDS = {
    "DEV-01",
    "BUG-01",
    "BUG-02",
    "RES-01",
    "REV-01",
    "OPS-01",
}

TIEBREAKER_TASK_IDS = {
    "REL-01",
    "REV-02",
}

TASKS = (
    TaskDef(
        task_id="DEV-01",
        kind="edit",
        prompt_file="DEV-01.md",
        schema_file="edit_task_output.schema.json",
        sandbox="workspace-write",
        timeout_seconds=180,
        allowed_write=(
            "app/openai_gpt5_responses/models/llm/_position.yaml",
            "app/openai_gpt5_responses/models/llm/gpt-5.3-codex-spark.yaml",
            "tests/openai_gpt5_responses/test_provider_schema.py",
        ),
        ruff_targets=("tests/openai_gpt5_responses/test_provider_schema.py",),
        pytest_targets=(
            "tests/openai_gpt5_responses/test_provider_schema.py",
        ),
        package_dir="app/openai_gpt5_responses",
        package_required=True,
    ),
    TaskDef(
        task_id="BUG-01",
        kind="edit",
        prompt_file="BUG-01.md",
        schema_file="edit_task_output.schema.json",
        sandbox="workspace-write",
        timeout_seconds=180,
        allowed_write=(
            "app/sharepoint_list/internal/validators.py",
            "app/sharepoint_list/internal/request_builders.py",
            "tests/sharepoint_list/test_validators.py",
            "tests/sharepoint_list/test_operations_select.py",
        ),
        ruff_targets=(
            "app/sharepoint_list/internal/validators.py",
            "app/sharepoint_list/internal/request_builders.py",
            "tests/sharepoint_list/test_validators.py",
            "tests/sharepoint_list/test_operations_select.py",
        ),
        pytest_targets=(
            "tests/sharepoint_list/test_validators.py",
            "tests/sharepoint_list/test_operations_select.py",
        ),
        package_dir="app/sharepoint_list",
        package_required=True,
    ),
    TaskDef(
        task_id="BUG-02",
        kind="edit",
        prompt_file="BUG-02.md",
        schema_file="edit_task_output.schema.json",
        sandbox="workspace-write",
        timeout_seconds=180,
        allowed_write=(
            "app/openai_gpt5_responses/internal/payloads.py",
            "tests/openai_gpt5_responses/test_payloads.py",
            "tests/openai_gpt5_responses/test_payloads_bool_coercion.py",
        ),
        ruff_targets=(
            "app/openai_gpt5_responses/internal/payloads.py",
            "tests/openai_gpt5_responses/test_payloads.py",
            "tests/openai_gpt5_responses/test_payloads_bool_coercion.py",
        ),
        pytest_targets=(
            "tests/openai_gpt5_responses/test_payloads.py",
            "tests/openai_gpt5_responses/test_payloads_bool_coercion.py",
        ),
        package_dir="app/openai_gpt5_responses",
        package_required=True,
    ),
    TaskDef(
        task_id="RES-01",
        kind="analysis",
        prompt_file="RES-01.md",
        schema_file="analysis_output.schema.json",
        sandbox="read-only",
        timeout_seconds=240,
        allowed_write=(),
    ),
    TaskDef(
        task_id="REV-01",
        kind="review",
        prompt_file="REV-01.md",
        schema_file=None,
        sandbox="read-only",
        timeout_seconds=120,
        allowed_write=(),
        setup_patch="REV-01_request_builders.patch",
    ),
    TaskDef(
        task_id="OPS-01",
        kind="ops",
        prompt_file="OPS-01.md",
        schema_file="ops_currentness_output.schema.json",
        sandbox="read-only",
        timeout_seconds=240,
        allowed_write=(),
        uses_search=True,
    ),
    TaskDef(
        task_id="REL-01",
        kind="edit",
        prompt_file="REL-01.md",
        schema_file="edit_task_output.schema.json",
        sandbox="workspace-write",
        timeout_seconds=240,
        allowed_write=(
            "app/openai_gpt5_responses/manifest.yaml",
            "app/openai_gpt5_responses/provider/openai_gpt5.yaml",
            "tests/openai_gpt5_responses/test_provider_schema.py",
        ),
        ruff_targets=("tests/openai_gpt5_responses/test_provider_schema.py",),
        pytest_targets=(
            "tests/openai_gpt5_responses/test_provider_schema.py",
        ),
        setup_patch="REL-01_manifest_packaging.patch",
        package_dir="app/openai_gpt5_responses",
        package_required=True,
    ),
    TaskDef(
        task_id="REV-02",
        kind="review",
        prompt_file="REV-02.md",
        schema_file=None,
        sandbox="read-only",
        timeout_seconds=120,
        allowed_write=(),
        setup_patch="REV-02_payloads.patch",
    ),
)

REVIEW_EXPECTED_SIGNALS = {
    "REV-01": {
        "empty_get_item_select": (
            r"build_get_item_request|get item",
            r"fields\(\$select=\)",
            r"empty|\[\]|blank|none",
        ),
        "empty_list_items_select": (
            r"build_list_items_request|list items",
            r"fields\(\$select=\)",
            r"empty|\[\]|blank|none",
        ),
        "test_contract_regression": (
            r"test_none_input_returns_none|test_empty_list_returns_none|returns_none",
            r"\[\]|None",
            r"regress|contract|wrong|expect|should",
        ),
    },
    "REV-02": {
        "parallel_tool_calls_bool_relaxed": (
            r"parallel_tool_calls",
            r"bool|truthy|yes|no",
            r"strict|validate|coerc",
        ),
        "json_schema_requirement_relaxed": (
            r"json_schema",
            r"required|missing|default|fallback",
            r"response_format",
        ),
        "verbosity_wrong_location": (
            r"verbosity",
            r"payload\[[\"']text[\"']\]|text\[|text block|top[- ]level",
            r"wrong|regress|moved|location",
        ),
        "test_weakened": (
            r"test_payloads|test_payloads_bool_coercion|tests?",
            r"remove|weaken|missing|no longer catches|accept",
            r"invalid|error|strict|schema",
        ),
    },
}

REVIEW_FILE_HINTS = {
    "REV-01": (
        "request_builders.py",
        "test_operations_select.py",
    ),
    "REV-02": (
        "payloads.py",
        "test_payloads.py",
        "test_payloads_bool_coercion.py",
    ),
}

TASKS_BY_ID = {task.task_id: task for task in TASKS}


def now_utc() -> str:
    return datetime.now(UTC).isoformat()


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    input_text: str | None = None,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def run_logged(
    cmd: list[str],
    *,
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    input_text: str | None = None,
    timeout: int,
) -> dict[str, Any]:
    start = time.time()
    proc: subprocess.Popen[str] | None = None
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdin=subprocess.PIPE if input_text is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        stdout_text, stderr_text = proc.communicate(
            input=input_text, timeout=timeout
        )
        duration = time.time() - start
        stdout_path.write_text(stdout_text, encoding="utf-8")
        stderr_path.write_text(stderr_text, encoding="utf-8")
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "duration_seconds": duration,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        duration = time.time() - start
        stdout_text = to_text(exc.stdout)
        stderr_text = to_text(exc.stderr)
        if proc is not None and proc.pid:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                stdout_rest, stderr_rest = proc.communicate(timeout=5)
                stdout_text += to_text(stdout_rest)
                stderr_text += to_text(stderr_rest)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                stdout_rest, stderr_rest = proc.communicate()
                stdout_text += to_text(stdout_rest)
                stderr_text += to_text(stderr_rest)
        stdout_path.write_text(stdout_text, encoding="utf-8")
        stderr_path.write_text(stderr_text, encoding="utf-8")
        return {
            "cmd": cmd,
            "returncode": None,
            "duration_seconds": duration,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "timed_out": True,
            "timeout_seconds": timeout,
        }


def safe_branch_name(run_id: str) -> str:
    lowered = run_id.lower().replace("_", "-")
    sanitized = re.sub(r"[^a-z0-9._/-]+", "-", lowered)
    return f"eval/{sanitized}-{uuid.uuid4().hex[:8]}"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def to_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def write_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def branch_order_for_rep(rep: int) -> list[BranchArm]:
    if rep % 2 == 1:
        return [BRANCH_ARMS[0], BRANCH_ARMS[1]]
    return [BRANCH_ARMS[1], BRANCH_ARMS[0]]


def get_task(task_id: str) -> TaskDef:
    return TASKS_BY_ID[task_id]


def resolve_dify_bin() -> tuple[str | None, str]:
    configured = os.environ.get("DIFY_BIN", "").strip()
    if configured:
        candidate = Path(configured).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate.resolve()), "env"
        return None, "env_invalid"
    detected = shutil.which("dify")
    if detected:
        return detected, "path"
    return None, "missing"


def package_gate_passed(gates: dict[str, Any]) -> bool:
    package = gates.get("package", {})
    if package.get("status") != "passed":
        return False
    for key in ("package", "sign", "verify"):
        if package.get(key, {}).get("returncode") != 0:
            return False
    return True


def one_pass_passed(gates: dict[str, Any]) -> bool:
    if gates.get("ruff", {}).get("returncode") != 0:
        return False
    if gates.get("pytest_no_cov", {}).get("returncode") != 0:
        return False
    return package_gate_passed(gates)


def effective_timeout(task: TaskDef, requested_timeout: int) -> int:
    return max(task.timeout_seconds or 0, requested_timeout)


def preflight() -> dict[str, Any]:
    ensure_dir(RESULTS_ROOT)
    codex = shutil.which("codex")
    uv = shutil.which("uv")
    dify, dify_resolution = resolve_dify_bin()
    package_json = json.loads(
        (REPO_ROOT / "package.json").read_text(encoding="utf-8")
    )
    data = {
        "timestamp": now_utc(),
        "codex_path": codex,
        "uv_path": uv,
        "dify_path": dify,
        "dify_resolution": dify_resolution,
        "package_gate_available": bool(dify),
        "codex_package_range": package_json.get("dependencies", {}).get(
            "@openai/codex"
        ),
        "harness_revision": HARNESS_REVISION,
    }
    if codex:
        proc = run(["codex", "--version"], cwd=REPO_ROOT)
        data["codex_cli_version"] = proc.stdout.strip() or proc.stderr.strip()
    if dify:
        proc = run([dify, "version"], cwd=REPO_ROOT)
        data["dify_version"] = proc.stdout.strip() or proc.stderr.strip()
    if uv:
        proc = run(["uv", "run", "pytest", "--version"], cwd=REPO_ROOT)
        data["pytest_version"] = proc.stdout.strip() or proc.stderr.strip()
    write_json(RESULTS_ROOT / "preflight.json", data)
    return data


def remove_existing_worktree(path: Path) -> None:
    if not path.exists():
        return
    run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "worktree",
            "remove",
            "--force",
            str(path),
        ],
        cwd=REPO_ROOT,
    )
    shutil.rmtree(path, ignore_errors=True)


def prepare_worktree(
    worktree_root: Path,
    run_id: str,
    branch: BranchArm,
    *,
    create_branch: bool,
) -> Path:
    worktree_path = worktree_root / run_id
    remove_existing_worktree(worktree_path)
    ensure_dir(worktree_root)
    add = run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "worktree",
            "add",
            "--detach",
            str(worktree_path),
            branch.ref,
        ],
        cwd=REPO_ROOT,
    )
    if add.returncode != 0:
        raise RuntimeError(f"worktree add failed: {add.stderr.strip()}")
    if create_branch:
        switch = run(
            ["git", "switch", "-c", safe_branch_name(run_id)],
            cwd=worktree_path,
        )
        if switch.returncode != 0:
            raise RuntimeError(f"git switch failed: {switch.stderr.strip()}")
    return worktree_path


def cleanup_worktree(path: Path) -> None:
    run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "worktree",
            "remove",
            "--force",
            str(path),
        ],
        cwd=REPO_ROOT,
    )
    run(["git", "-C", str(REPO_ROOT), "worktree", "prune"], cwd=REPO_ROOT)
    shutil.rmtree(path, ignore_errors=True)


def build_prompt(
    task: TaskDef, run_id: str, branch: BranchArm, rep: int
) -> str:
    body = (
        (PROMPTS_ROOT / task.prompt_file).read_text(encoding="utf-8").strip()
    )
    header = textwrap.dedent(f"""\
        Evaluation metadata:
        - run_id: {run_id}
        - blinded_branch_alias: {branch.alias}
        - source_ref: hidden_until_scoring
        - repetition: r{rep}
        - repo_root: .

        Execution constraints:
        - This is a non-interactive `codex exec` run. Do not ask the user questions and do not call `request_user_input`.
        - Do not use Serena MCP editing tools in this environment. Prefer local shell commands and direct file edits in the current worktree.
        - If one tool path fails, fall back within the same worktree and continue.
        - Do not launch or delegate to another Codex session such as `codex_mcp.codex`; finish within this exec session only.
        """).strip()
    return f"{header}\n\n{body}\n"


def snapshot_git_artifacts(
    run_dir: Path, worktree: Path, *, prefix: str = ""
) -> dict[str, Any]:
    status = run(["git", "status", "--short"], cwd=worktree)
    diff_name = run(["git", "diff", "--name-only"], cwd=worktree)
    diff_stat = run(["git", "diff", "--stat"], cwd=worktree)
    diff_patch = run(["git", "diff", "--binary"], cwd=worktree)
    head = run(["git", "rev-parse", "HEAD"], cwd=worktree)

    status_path = run_dir / f"{prefix}git_status.txt"
    diff_name_path = run_dir / f"{prefix}git_diff_name_only.txt"
    diff_stat_path = run_dir / f"{prefix}git_diff_stat.txt"
    diff_patch_path = run_dir / f"{prefix}git_diff.patch"
    status_path.write_text(status.stdout, encoding="utf-8")
    diff_name_path.write_text(diff_name.stdout, encoding="utf-8")
    diff_stat_path.write_text(diff_stat.stdout, encoding="utf-8")
    diff_patch_path.write_text(diff_patch.stdout, encoding="utf-8")

    changed_files = [
        line.strip() for line in diff_name.stdout.splitlines() if line.strip()
    ]
    return {
        "head": head.stdout.strip(),
        "changed_files": changed_files,
        "status_path": relative(status_path),
        "diff_name_only_path": relative(diff_name_path),
        "diff_stat_path": relative(diff_stat_path),
        "diff_patch_path": relative(diff_patch_path),
    }


def collect_git_artifacts(run_dir: Path, worktree: Path) -> dict[str, Any]:
    return snapshot_git_artifacts(run_dir, worktree)


def has_unexpected_read_only_mutation(manifest: dict[str, Any]) -> bool:
    current = manifest["git"]
    baseline = manifest.get("baseline_git")
    if not baseline:
        return bool(current["changed_files"])
    if current["changed_files"] != baseline["changed_files"]:
        return True
    current_patch = (REPO_ROOT / current["diff_patch_path"]).read_text(
        encoding="utf-8"
    )
    baseline_patch = (REPO_ROOT / baseline["diff_patch_path"]).read_text(
        encoding="utf-8"
    )
    return current_patch != baseline_patch


def apply_setup_patch(task: TaskDef, worktree: Path, run_dir: Path) -> None:
    if not task.setup_patch:
        return
    patch_path = FIXTURES_ROOT / task.setup_patch
    target_copy = run_dir / task.setup_patch
    target_copy.write_text(
        patch_path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    proc = run(["git", "apply", str(target_copy)], cwd=worktree)
    if proc.returncode != 0:
        raise RuntimeError(f"git apply failed: {proc.stderr.strip()}")


def run_package_gate(
    task: TaskDef,
    worktree: Path,
    run_dir: Path,
    dify_bin: str | None,
) -> dict[str, Any]:
    if not task.package_required:
        return {
            "status": "not_required",
        }
    if not dify_bin:
        return {
            "status": "infra_blocked",
            "reason": "DIFY_BIN or PATH-resolved dify is required for package gate",
        }
    if not task.package_dir:
        return {
            "status": "misconfigured",
            "reason": "package_dir is missing for a package-required task",
        }

    package_root = run_dir / "package_artifacts"
    ensure_dir(package_root)
    plugin_name = Path(task.package_dir).name
    package_cmd = [
        dify_bin,
        "plugin",
        "package",
        str(worktree / task.package_dir),
    ]
    package_result = run_logged(
        package_cmd,
        cwd=package_root,
        stdout_path=run_dir / "gate_package_stdout.txt",
        stderr_path=run_dir / "gate_package_stderr.txt",
        timeout=900,
    )
    payload: dict[str, Any] = {
        "status": "failed",
        "artifact_dir": relative(package_root),
        "dify_bin": dify_bin,
        "package": package_result,
    }
    if package_result.get("returncode") != 0:
        payload["sign"] = {"status": "skipped_due_to_package_failure"}
        payload["verify"] = {"status": "skipped_due_to_package_failure"}
        return payload

    private_key = REPO_ROOT / "plugins" / "custom_plugins.private.pem"
    public_key = REPO_ROOT / "plugins" / "custom_plugins.public.pem"
    sign_result = run_logged(
        [
            dify_bin,
            "signature",
            "sign",
            f"{plugin_name}.difypkg",
            "-p",
            str(private_key),
        ],
        cwd=package_root,
        stdout_path=run_dir / "gate_sign_stdout.txt",
        stderr_path=run_dir / "gate_sign_stderr.txt",
        timeout=300,
    )
    payload["sign"] = sign_result
    if sign_result.get("returncode") != 0:
        payload["verify"] = {"status": "skipped_due_to_sign_failure"}
        return payload

    verify_result = run_logged(
        [
            dify_bin,
            "signature",
            "verify",
            f"{plugin_name}.signed.difypkg",
            "-p",
            str(public_key),
        ],
        cwd=package_root,
        stdout_path=run_dir / "gate_verify_stdout.txt",
        stderr_path=run_dir / "gate_verify_stderr.txt",
        timeout=300,
    )
    payload["verify"] = verify_result
    if verify_result.get("returncode") == 0:
        payload["status"] = "passed"
    return payload


def codex_command(task: TaskDef, run_dir: Path) -> tuple[list[str], str]:
    prompt = ""
    last_message = run_dir / "last_message.txt"
    if task.kind == "review":
        cmd = [
            "codex",
            "exec",
            "review",
            "--uncommitted",
            "--ephemeral",
            "--dangerously-bypass-approvals-and-sandbox",
            "-o",
            str(last_message),
        ]
        for override in EVAL_CODEX_CONFIG_OVERRIDES:
            cmd.extend(["-c", override])
        return cmd, prompt

    schema_path = SCHEMAS_ROOT / task.schema_file if task.schema_file else None
    cmd = ["codex"]
    if task.uses_search:
        cmd.append("--search")
    cmd.extend(
        [
            "exec",
            "--ephemeral",
            "--dangerously-bypass-approvals-and-sandbox",
            "-o",
            str(last_message),
        ]
    )
    for override in EVAL_CODEX_CONFIG_OVERRIDES:
        cmd.extend(["-c", override])
    if schema_path:
        cmd.extend(["--output-schema", str(schema_path)])
    cmd.append("-")
    return cmd, prompt


def run_parent_task(
    task: TaskDef,
    branch: BranchArm,
    rep: int,
    *,
    worktree_root: Path,
    timeout: int,
    dify_bin: str | None,
) -> dict[str, Any]:
    run_id = f"{task.task_id}__{branch.alias}__r{rep}"
    run_dir = RESULTS_ROOT / "parent_runs" / run_id
    manifest_path = run_dir / "run_manifest.json"
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing.get("harness_revision") == HARNESS_REVISION:
            return existing
        shutil.rmtree(run_dir, ignore_errors=True)

    ensure_dir(run_dir)
    worktree = prepare_worktree(
        worktree_root / "parent",
        run_id,
        branch,
        create_branch=(task.kind == "edit"),
    )
    manifest: dict[str, Any] = {
        "run_id": run_id,
        "harness_revision": HARNESS_REVISION,
        "task_id": task.task_id,
        "kind": task.kind,
        "branch_alias": branch.alias,
        "branch_ref_hidden": True,
        "rep": rep,
        "timestamp_started": now_utc(),
        "worktree": str(worktree),
        "allowed_write": list(task.allowed_write),
        "package_dir": task.package_dir,
        "package_required": task.package_required,
    }

    try:
        baseline_git = None
        if task.setup_patch:
            apply_setup_patch(task, worktree, run_dir)
            baseline_git = snapshot_git_artifacts(
                run_dir, worktree, prefix="baseline_"
            )

        prompt = build_prompt(task, run_id, branch, rep)
        cmd, _ = codex_command(task, run_dir)
        exec_result = run_logged(
            cmd,
            cwd=worktree,
            stdout_path=run_dir / "codex_stdout.txt",
            stderr_path=run_dir / "codex_stderr.txt",
            input_text=prompt,
            timeout=effective_timeout(task, timeout),
        )
        last_message_path = run_dir / "last_message.txt"
        last_message = ""
        if last_message_path.exists():
            last_message = last_message_path.read_text(encoding="utf-8")

        git_artifacts = collect_git_artifacts(run_dir, worktree)
        gates = run_parent_gates(task, worktree, run_dir, dify_bin)

        parsed_output = None
        if task.schema_file and last_message.strip():
            try:
                parsed_output = json.loads(last_message)
            except json.JSONDecodeError:
                parsed_output = {"_parse_error": True}

        manifest.update(
            {
                "timestamp_finished": now_utc(),
                "codex": exec_result,
                "git": git_artifacts,
                "baseline_git": baseline_git,
                "gates": gates,
                "parsed_output": parsed_output,
                "last_message_path": relative(last_message_path),
            }
        )
        write_json(run_dir / "run_manifest.json", manifest)
        return manifest
    except Exception as exc:
        manifest.update(
            {
                "timestamp_finished": now_utc(),
                "error": str(exc),
            }
        )
        write_json(run_dir / "run_manifest.json", manifest)
        return manifest
    finally:
        cleanup_worktree(worktree)


def run_parent_gates(
    task: TaskDef,
    worktree: Path,
    run_dir: Path,
    dify_bin: str | None,
) -> dict[str, Any]:
    gates: dict[str, Any] = {}
    if task.ruff_targets:
        cmd = ["uv", "run", "ruff", "check", *task.ruff_targets]
        gates["ruff"] = run_logged(
            cmd,
            cwd=worktree,
            stdout_path=run_dir / "gate_ruff_stdout.txt",
            stderr_path=run_dir / "gate_ruff_stderr.txt",
            timeout=600,
        )
    gates["package"] = run_package_gate(task, worktree, run_dir, dify_bin)
    if task.pytest_targets:
        cmd = ["uv", "run", "pytest", "-q", "--no-cov", *task.pytest_targets]
        gates["pytest_no_cov"] = run_logged(
            cmd,
            cwd=worktree,
            stdout_path=run_dir / "gate_pytest_no_cov_stdout.txt",
            stderr_path=run_dir / "gate_pytest_no_cov_stderr.txt",
            timeout=900,
        )
        cmd_cov = ["uv", "run", "pytest", "-q", *task.pytest_targets]
        gates["pytest_cov_reference"] = run_logged(
            cmd_cov,
            cwd=worktree,
            stdout_path=run_dir / "gate_pytest_cov_stdout.txt",
            stderr_path=run_dir / "gate_pytest_cov_stderr.txt",
            timeout=900,
        )
    return gates


def score_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    kind = manifest["kind"]
    last_message_path = REPO_ROOT / manifest["last_message_path"]
    last_message = (
        last_message_path.read_text(encoding="utf-8")
        if last_message_path.exists()
        else ""
    )
    changed_files = manifest["git"]["changed_files"]
    allowed_write = set(manifest["allowed_write"])
    hard_fail_reasons: list[str] = []

    if kind in {
        "analysis",
        "ops",
        "review",
    } and has_unexpected_read_only_mutation(manifest):
        hard_fail_reasons.append("read_only_task_changed_files")
    if manifest.get("error"):
        hard_fail_reasons.append("run_error")
    if kind == "edit":
        extra = sorted(set(changed_files) - allowed_write)
        if extra:
            hard_fail_reasons.append(f"scope_violation:{','.join(extra)}")
        if not changed_files:
            hard_fail_reasons.append("no_changes_made")
        if manifest.get("package_required") and not package_gate_passed(
            manifest["gates"]
        ):
            hard_fail_reasons.append("package_gate_failed")
    if re.search(r"sk-[A-Za-z0-9]{20,}", last_message):
        hard_fail_reasons.append("secret_like_token_exposed")

    score = {
        "hard_fail": bool(hard_fail_reasons),
        "hard_fail_reasons": hard_fail_reasons,
        "dimensions": {},
    }

    if kind == "edit":
        score["dimensions"] = score_edit_manifest(manifest, last_message)
    elif kind == "review":
        score["dimensions"] = score_review_manifest(manifest, last_message)
    else:
        score["dimensions"] = score_analysis_manifest(manifest, last_message)

    weighted = weighted_score(score["dimensions"])
    if hard_fail_reasons:
        weighted = min(weighted, 1.0)
    score["overall"] = round(weighted, 3)
    return score


def score_edit_manifest(
    manifest: dict[str, Any], last_message: str
) -> dict[str, float]:
    parsed = manifest.get("parsed_output") or {}
    gates = manifest["gates"]
    ruff_ok = gates.get("ruff", {}).get("returncode") == 0
    pytest_ok = gates.get("pytest_no_cov", {}).get("returncode") == 0
    package_ok = package_gate_passed(gates)
    files_touched = (
        parsed.get("files_touched") if isinstance(parsed, dict) else None
    )
    checks_ran = parsed.get("checks_ran") if isinstance(parsed, dict) else None
    evidence_count = len(checks_ran or [])

    gate_passes = sum((ruff_ok, pytest_ok, package_ok))
    correctness = 5.0 if gate_passes == 3 else 3.0 if gate_passes == 2 else 1.5
    completeness = (
        5.0
        if files_touched
        else 3.0 if manifest["git"]["changed_files"] else 1.0
    )
    evidence = (
        5.0 if evidence_count >= 2 else 3.0 if evidence_count == 1 else 1.5
    )
    safety = 5.0
    efficiency = (
        5.0
        if len(manifest["git"]["changed_files"])
        <= max(1, len(manifest["allowed_write"]))
        else 3.0
    )
    return {
        "correctness": correctness,
        "completeness": completeness,
        "evidence": evidence,
        "safety": safety,
        "efficiency": efficiency,
    }


def score_analysis_manifest(
    manifest: dict[str, Any], last_message: str
) -> dict[str, float]:
    parsed = manifest.get("parsed_output") or {}
    findings = parsed.get("findings") if isinstance(parsed, dict) else None
    used_urls = parsed.get("used_urls") if isinstance(parsed, dict) else None
    findings_count = len(findings or [])
    evidence_count = 0
    if findings:
        for finding in findings:
            evidence_count += len(finding.get("evidence") or [])

    correctness = (
        5.0 if findings_count >= 2 else 3.0 if findings_count == 1 else 1.0
    )
    evidence = (
        5.0 if evidence_count >= 2 else 3.0 if evidence_count == 1 else 1.0
    )
    prioritization = (
        5.0 if findings_count >= 2 else 3.0 if findings_count == 1 else 1.0
    )
    safety = 5.0
    if manifest["task_id"] == "OPS-01":
        allowed_domains = (
            "openai.com",
            "platform.openai.com",
            "docs.openai.com",
        )
        if not used_urls:
            safety = 2.0
        for url in used_urls or []:
            if not any(domain in url for domain in allowed_domains):
                safety = 1.0
    efficiency = 5.0
    return {
        "correctness": correctness,
        "evidence": evidence,
        "prioritization": prioritization,
        "safety": safety,
        "efficiency": efficiency,
    }


def score_review_manifest(
    manifest: dict[str, Any], last_message: str
) -> dict[str, float]:
    hits = 0
    lowered = last_message.lower()
    task_signals = REVIEW_EXPECTED_SIGNALS.get(manifest["task_id"], {})
    for patterns in task_signals.values():
        if all(
            re.search(pattern, lowered, re.IGNORECASE) for pattern in patterns
        ):
            hits += 1
    max_hits = max(1, len(task_signals))
    recall_rate = hits / max_hits
    hinted_files = REVIEW_FILE_HINTS.get(manifest["task_id"], ())
    file_ref_ok = any(
        re.search(rf"{re.escape(file_name)}:\d+", last_message, re.IGNORECASE)
        for file_name in hinted_files
    )
    severity_ok = bool(re.search(r"\b(high|medium|low|sev[1-4])\b", lowered))

    if recall_rate >= 1.0:
        correctness = 5.0
    elif recall_rate >= 0.75:
        correctness = 4.5
    elif recall_rate >= 0.5:
        correctness = 3.5
    elif recall_rate > 0:
        correctness = 2.5
    else:
        correctness = 1.0
    evidence = 5.0 if file_ref_ok else 3.0
    prioritization = 5.0 if severity_ok else 3.0
    safety = 5.0
    efficiency = 5.0
    return {
        "correctness": correctness,
        "evidence": evidence,
        "prioritization": prioritization,
        "safety": safety,
        "efficiency": efficiency,
        "recall": float(hits),
        "max_recall": float(max_hits),
        "recall_rate": recall_rate,
        "precision_hint": (
            1.0
            if (file_ref_ok and severity_ok)
            else 0.5 if (file_ref_ok or severity_ok) else 0.0
        ),
    }


def weighted_score(dimensions: dict[str, float]) -> float:
    if "completeness" in dimensions:
        return (
            dimensions["correctness"] * 0.40
            + dimensions["completeness"] * 0.20
            + dimensions["evidence"] * 0.15
            + dimensions["safety"] * 0.15
            + dimensions["efficiency"] * 0.10
        )
    return (
        dimensions["correctness"] * 0.35
        + dimensions["evidence"] * 0.25
        + dimensions["prioritization"] * 0.20
        + dimensions["safety"] * 0.15
        + dimensions["efficiency"] * 0.05
    )


def score_parent_runs() -> dict[str, Any]:
    parent_root = RESULTS_ROOT / "parent_runs"
    manifests = sorted(parent_root.glob("*/run_manifest.json"))
    scored_runs: list[dict[str, Any]] = []
    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("harness_revision") != HARNESS_REVISION:
            continue
        score = score_manifest(manifest)
        payload = {
            "run_id": manifest["run_id"],
            "task_id": manifest["task_id"],
            "branch_alias": manifest["branch_alias"],
            "rep": manifest["rep"],
            "score": score,
        }
        write_json(manifest_path.parent / "scorecard.json", payload)
        scored_runs.append(payload)

    summary = summarize_scores(scored_runs)
    write_json(RESULTS_ROOT / "parent_score_summary.json", summary)
    (RESULTS_ROOT / "parent_score_summary.md").write_text(
        render_parent_summary(summary),
        encoding="utf-8",
    )
    return summary


def summarize_scores(scored_runs: list[dict[str, Any]]) -> dict[str, Any]:
    if not scored_runs:
        return {
            "timestamp": now_utc(),
            "run_count": 0,
            "aliases": {},
            "task_medians": {},
            "review_recall": {},
            "review_precision_hint": {},
            "active_gate_pass": {},
            "package_pass_rate": {},
            "one_pass_pass_rate": {},
            "hard_fail_counts": {},
            "deltas": {},
            "tiebreaker_triggered": False,
            "verdict": {
                "status": "not_run",
            },
        }

    by_alias: dict[str, list[float]] = {}
    by_task_alias: dict[tuple[str, str], list[float]] = {}
    hard_fail_counts: dict[str, int] = {}
    review_recall: dict[str, list[float]] = {}
    review_precision_hint: dict[str, list[float]] = {}
    active_gate_pass: dict[str, int] = {}
    edit_run_counts: dict[str, int] = {}
    package_pass_counts: dict[str, int] = {}
    one_pass_counts: dict[str, int] = {}
    tiebreaker_triggered = False

    for run in scored_runs:
        alias = run["branch_alias"]
        overall = run["score"]["overall"]
        by_alias.setdefault(alias, []).append(overall)
        by_task_alias.setdefault((run["task_id"], alias), []).append(overall)
        if run["task_id"] in TIEBREAKER_TASK_IDS:
            tiebreaker_triggered = True
        if run["score"]["hard_fail"]:
            hard_fail_counts[alias] = hard_fail_counts.get(alias, 0) + 1
        if get_task(run["task_id"]).kind == "review":
            review_recall.setdefault(alias, []).append(
                run["score"]["dimensions"].get("recall_rate", 0.0)
            )
            review_precision_hint.setdefault(alias, []).append(
                run["score"]["dimensions"].get("precision_hint", 0.0)
            )

        manifest_path = (
            RESULTS_ROOT / "parent_runs" / run["run_id"] / "run_manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if get_task(run["task_id"]).kind == "edit":
            gates = manifest["gates"]
            edit_run_counts[alias] = edit_run_counts.get(alias, 0) + 1
            if (
                gates.get("ruff", {}).get("returncode") == 0
                and gates.get("pytest_no_cov", {}).get("returncode") == 0
            ):
                active_gate_pass[alias] = active_gate_pass.get(alias, 0) + 1
            if package_gate_passed(gates):
                package_pass_counts[alias] = (
                    package_pass_counts.get(alias, 0) + 1
                )
            if one_pass_passed(gates):
                one_pass_counts[alias] = one_pass_counts.get(alias, 0) + 1

    summary = {
        "timestamp": now_utc(),
        "run_count": len(scored_runs),
        "aliases": {},
        "task_medians": {},
        "review_recall": {
            alias: mean(values) if values else 0.0
            for alias, values in review_recall.items()
        },
        "review_precision_hint": {
            alias: mean(values) if values else 0.0
            for alias, values in review_precision_hint.items()
        },
        "active_gate_pass": active_gate_pass,
        "package_pass_rate": {
            alias: round(package_pass_counts.get(alias, 0) / count, 3)
            for alias, count in edit_run_counts.items()
            if count
        },
        "one_pass_pass_rate": {
            alias: round(one_pass_counts.get(alias, 0) / count, 3)
            for alias, count in edit_run_counts.items()
            if count
        },
        "hard_fail_counts": hard_fail_counts,
        "tiebreaker_triggered": tiebreaker_triggered,
    }
    for alias, values in by_alias.items():
        summary["aliases"][alias] = {
            "mean_overall": round(mean(values), 3),
            "median_overall": round(median(values), 3),
            "run_count": len(values),
        }
    for (task_id, alias), values in by_task_alias.items():
        summary["task_medians"].setdefault(task_id, {})
        summary["task_medians"][task_id][alias] = round(median(values), 3)

    alias_a = BRANCH_ARMS[0].alias
    alias_b = BRANCH_ARMS[1].alias
    delta_mean = summary["aliases"].get(alias_b, {}).get(
        "mean_overall", 0.0
    ) - summary["aliases"].get(alias_a, {}).get("mean_overall", 0.0)
    summary["deltas"] = {
        f"{alias_b}_minus_{alias_a}_mean": round(delta_mean, 3),
        f"{alias_b}_minus_{alias_a}_package_pass_rate": round(
            summary["package_pass_rate"].get(alias_b, 0.0)
            - summary["package_pass_rate"].get(alias_a, 0.0),
            3,
        ),
        f"{alias_b}_minus_{alias_a}_one_pass_pass_rate": round(
            summary["one_pass_pass_rate"].get(alias_b, 0.0)
            - summary["one_pass_pass_rate"].get(alias_a, 0.0),
            3,
        ),
        f"{alias_b}_minus_{alias_a}_review_recall": round(
            summary["review_recall"].get(alias_b, 0.0)
            - summary["review_recall"].get(alias_a, 0.0),
            3,
        ),
    }

    summary["verdict"] = evaluate_verdict(summary, alias_a, alias_b)
    return summary


def evaluate_verdict(
    summary: dict[str, Any], baseline_alias: str, candidate_alias: str
) -> dict[str, Any]:
    candidate_mean = (
        summary["aliases"].get(candidate_alias, {}).get("mean_overall", 0.0)
    )
    baseline_mean = (
        summary["aliases"].get(baseline_alias, {}).get("mean_overall", 0.0)
    )
    hard_fail_ok = summary["hard_fail_counts"].get(
        candidate_alias, 0
    ) <= summary["hard_fail_counts"].get(baseline_alias, 0)
    mean_ok = (candidate_mean - baseline_mean) >= -0.25
    median_ok = True
    for _task_id, by_alias in summary["task_medians"].items():
        candidate_task = by_alias.get(candidate_alias)
        baseline_task = by_alias.get(baseline_alias)
        if candidate_task is None or baseline_task is None:
            continue
        if (candidate_task - baseline_task) < -0.5:
            median_ok = False
            break
    gate_ok = (
        summary["active_gate_pass"].get(candidate_alias, 0)
        >= summary["active_gate_pass"].get(baseline_alias, 0) - 2
    )
    review_ok = summary["review_recall"].get(candidate_alias, 0.0) >= summary[
        "review_recall"
    ].get(baseline_alias, 0.0)
    non_inferior = (
        hard_fail_ok and mean_ok and median_ok and gate_ok and review_ok
    )
    better = non_inferior and (candidate_mean >= baseline_mean)

    strict_metrics = {
        "mean_overall": (
            candidate_mean,
            baseline_mean,
        ),
        "package_pass_rate": (
            summary["package_pass_rate"].get(candidate_alias, 0.0),
            summary["package_pass_rate"].get(baseline_alias, 0.0),
        ),
        "one_pass_pass_rate": (
            summary["one_pass_pass_rate"].get(candidate_alias, 0.0),
            summary["one_pass_pass_rate"].get(baseline_alias, 0.0),
        ),
        "review_recall": (
            summary["review_recall"].get(candidate_alias, 0.0),
            summary["review_recall"].get(baseline_alias, 0.0),
        ),
    }
    strict_wins = [
        name
        for name, (candidate, baseline) in strict_metrics.items()
        if candidate > baseline
    ]
    strict_losses = [
        name
        for name, (candidate, baseline) in strict_metrics.items()
        if candidate < baseline
    ]
    strictly_better = (
        non_inferior and not strict_losses and len(strict_wins) >= 2
    )
    return {
        "baseline_alias": baseline_alias,
        "candidate_alias": candidate_alias,
        "hard_fail_ok": hard_fail_ok,
        "mean_ok": mean_ok,
        "median_ok": median_ok,
        "gate_ok": gate_ok,
        "review_ok": review_ok,
        "non_inferior": non_inferior,
        "better_or_equal": better,
        "strictly_better": strictly_better,
        "strict_wins": strict_wins,
        "strict_losses": strict_losses,
        "note": "Strict superiority now requires non-inferiority plus no losses on mean/package/one-pass/review and at least two strict wins.",
    }


def render_parent_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# Parent Score Summary",
        "",
        f"- generated_at: {summary['timestamp']}",
        f"- run_count: {summary['run_count']}",
        "",
        "## Alias Metrics",
    ]
    for alias, data in sorted(summary["aliases"].items()):
        lines.append(
            f"- {alias}: mean={data['mean_overall']}, median={data['median_overall']}, runs={data['run_count']}"
        )
    lines.extend(
        [
            "",
            "## Added Metrics",
        ]
    )
    for alias in sorted(summary["aliases"].keys()):
        lines.append(
            "- "
            + f"{alias}: review_recall={round(summary['review_recall'].get(alias, 0.0), 3)}, "
            + f"review_precision_hint={round(summary['review_precision_hint'].get(alias, 0.0), 3)}, "
            + f"package_pass_rate={round(summary['package_pass_rate'].get(alias, 0.0), 3)}, "
            + f"one_pass_pass_rate={round(summary['one_pass_pass_rate'].get(alias, 0.0), 3)}"
        )
    lines.extend(
        [
            "",
            "## Task Medians",
        ]
    )
    for task_id, by_alias in sorted(summary["task_medians"].items()):
        rendered = ", ".join(
            f"{alias}={score}" for alias, score in sorted(by_alias.items())
        )
        lines.append(f"- {task_id}: {rendered}")
    lines.extend(
        [
            "",
            "## Verdict",
            f"- {json.dumps(summary['verdict'], ensure_ascii=False)}",
            f"- tiebreaker_triggered={summary['tiebreaker_triggered']}",
            "",
            "## Alias Mapping",
            f"- {BRANCH_ARMS[0].alias} -> {BRANCH_ARMS[0].ref}",
            f"- {BRANCH_ARMS[1].alias} -> {BRANCH_ARMS[1].ref}",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_csv_arg(raw: str | None) -> set[str] | None:
    if not raw:
        return None
    values = {item.strip() for item in raw.split(",") if item.strip()}
    return values or None


def run_parent_matrix(
    worktree_root: Path,
    timeout: int,
    *,
    task_filter: set[str] | None = None,
    reps: set[int] | None = None,
) -> list[dict[str, Any]]:
    pf = preflight()
    selected_tasks = [
        task
        for task in TASKS
        if (task_filter and task.task_id in task_filter)
        or (not task_filter and task.task_id in PRIMARY_TASK_IDS)
    ]
    if (
        any(task.package_required for task in selected_tasks)
        and not pf["package_gate_available"]
    ):
        raise RuntimeError(
            "package gate requires DIFY_BIN=/absolute/path/to/dify (or a PATH-resolved dify binary)"
        )
    manifests: list[dict[str, Any]] = []
    for rep in DEFAULT_PARENT_REPS:
        if reps and rep not in reps:
            continue
        for branch in branch_order_for_rep(rep):
            for task in selected_tasks:
                manifests.append(
                    run_parent_task(
                        task,
                        branch,
                        rep,
                        worktree_root=worktree_root,
                        timeout=timeout,
                        dify_bin=pf["dify_path"],
                    )
                )
    return manifests


def subagent_pipeline_command(
    task_id: str,
    *,
    spec_path: Path,
    prompt: str,
    sandbox: str,
    workdir: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout: int,
    profile: str | None = None,
) -> dict[str, Any]:
    cmd = [
        "uv",
        "run",
        "python",
        str(REPO_ROOT / ".claude/skills/codex-subagent/scripts/codex_exec.py"),
        "--mode",
        "pipeline",
        "--pipeline-spec",
        str(spec_path),
        "--capsule-store",
        "auto",
        "--sandbox",
        "danger-full-access",
        "--timeout",
        str(timeout),
        "--json",
        "--workdir",
        str(workdir),
        "--prompt",
        prompt,
    ]
    if profile:
        cmd.extend(["--profile", profile])
    return run_logged(
        cmd,
        cwd=REPO_ROOT,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        timeout=timeout + 300,
    )


def run_subagent_confirmations(
    worktree_root: Path,
    timeout: int,
    *,
    task_filter: set[str] | None = None,
) -> dict[str, Any]:
    pf = preflight()
    confirmations = []
    tasks = (
        (
            "BUG-01",
            "BUG-01_pipeline_spec.json",
            "BUG-01_prompt_template.md",
            "workspace-write",
        ),
        (
            "OPS-01",
            "OPS-01_pipeline_spec.json",
            "OPS-01_prompt_template.md",
            "read-only",
        ),
    )

    for branch in BRANCH_ARMS:
        for task_id, spec_name, prompt_name, sandbox in tasks:
            if task_filter and task_id not in task_filter:
                continue
            task = get_task(task_id)
            if task.package_required and not pf["package_gate_available"]:
                raise RuntimeError(
                    "subagent confirmation for edit tasks requires DIFY_BIN=/absolute/path/to/dify"
                )
            run_id = f"{task_id}__{branch.alias}__subagent"
            run_dir = RESULTS_ROOT / "subagent_runs" / run_id
            if (run_dir / "run_manifest.json").exists():
                existing = json.loads(
                    (run_dir / "run_manifest.json").read_text(encoding="utf-8")
                )
                if existing.get("harness_revision") == HARNESS_REVISION:
                    confirmations.append(existing)
                    continue
                shutil.rmtree(run_dir, ignore_errors=True)
            ensure_dir(run_dir)
            worktree = prepare_worktree(
                worktree_root / "subagent",
                run_id,
                branch,
                create_branch=(sandbox == "workspace-write"),
            )
            try:
                prompt_template = (SUBAGENT_ROOT / prompt_name).read_text(
                    encoding="utf-8"
                )
                prompt = (
                    prompt_template.replace("__WORKTREE__", str(worktree))
                    .replace("__BRANCH_ALIAS__", branch.alias)
                    .replace("__TASK_ID__", task_id)
                    .replace("__OUTPUT_DIR__", str(run_dir))
                )
                exec_result = subagent_pipeline_command(
                    task_id,
                    spec_path=SUBAGENT_ROOT / spec_name,
                    prompt=prompt,
                    sandbox=sandbox,
                    workdir=worktree,
                    stdout_path=run_dir / "subagent_stdout.jsonl",
                    stderr_path=run_dir / "subagent_stderr.txt",
                    timeout=timeout,
                    profile="fast",
                )
                git_artifacts = collect_git_artifacts(run_dir, worktree)
                gates = run_parent_gates(
                    task, worktree, run_dir, pf["dify_path"]
                )
                manifest = {
                    "run_id": run_id,
                    "harness_revision": HARNESS_REVISION,
                    "task_id": task_id,
                    "branch_alias": branch.alias,
                    "codex_subagent": exec_result,
                    "git": git_artifacts,
                    "gates": gates,
                    "timestamp_finished": now_utc(),
                }
                write_json(run_dir / "run_manifest.json", manifest)
                confirmations.append(manifest)
            finally:
                cleanup_worktree(worktree)

    write_json(RESULTS_ROOT / "subagent_summary.json", confirmations)
    return {"runs": confirmations}


def render_final_report(
    parent_summary: dict[str, Any], subagent_summary: dict[str, Any]
) -> str:
    verdict = parent_summary["verdict"]
    lines = [
        "# AGENTS Branch Evaluation Report",
        "",
        f"- date: {TIMESTAMP}",
        f"- parent_runs: {parent_summary['run_count']}",
        f"- subagent_runs: {len(subagent_summary.get('runs', []))}",
        "",
        "## Parent Evaluation",
    ]
    for alias, data in sorted(parent_summary["aliases"].items()):
        lines.append(
            f"- {alias}: mean={data['mean_overall']}, median={data['median_overall']}, runs={data['run_count']}"
        )
    lines.extend(
        [
            "",
            "## Hard Fail Counts",
        ]
    )
    for alias, count in sorted(parent_summary["hard_fail_counts"].items()):
        lines.append(f"- {alias}: {count}")
    lines.extend(
        [
            "",
            "## Review Recall",
        ]
    )
    for alias, value in sorted(parent_summary["review_recall"].items()):
        lines.append(f"- {alias}: {round(value, 3)}")
    lines.extend(
        [
            "",
            "## Package Pass Rate",
        ]
    )
    for alias, value in sorted(parent_summary["package_pass_rate"].items()):
        lines.append(f"- {alias}: {round(value, 3)}")
    lines.extend(
        [
            "",
            "## One-Pass Pass Rate",
        ]
    )
    for alias, value in sorted(parent_summary["one_pass_pass_rate"].items()):
        lines.append(f"- {alias}: {round(value, 3)}")
    lines.extend(
        [
            "",
            "## Active Gate Pass Counts",
        ]
    )
    for alias, value in sorted(parent_summary["active_gate_pass"].items()):
        lines.append(f"- {alias}: {value}")
    lines.extend(
        [
            "",
            "## Subagent Confirmation",
        ]
    )
    for run in subagent_summary.get("runs", []):
        gates = run["gates"]
        ruff = gates.get("ruff", {}).get("returncode")
        pytest_no_cov = gates.get("pytest_no_cov", {}).get("returncode")
        package_status = gates.get("package", {}).get("status")
        subagent_rc = run["codex_subagent"].get("returncode")
        lines.append(
            f"- {run['run_id']}: subagent_rc={subagent_rc}, ruff={ruff}, pytest_no_cov={pytest_no_cov}, package={package_status}, changed_files={len(run['git']['changed_files'])}"
        )
    lines.extend(
        [
            "",
            "## Verdict",
            f"- non_inferior: {verdict['non_inferior']}",
            f"- strictly_better: {verdict['strictly_better']}",
            f"- better_or_equal: {verdict['better_or_equal']}",
            f"- strict_wins: {', '.join(verdict['strict_wins']) or 'none'}",
            f"- strict_losses: {', '.join(verdict['strict_losses']) or 'none'}",
            f"- baseline_alias: {verdict['baseline_alias']}",
            f"- candidate_alias: {verdict['candidate_alias']}",
            f"- tiebreaker_triggered: {parent_summary['tiebreaker_triggered']}",
            f"- alias mapping: {BRANCH_ARMS[0].alias}={BRANCH_ARMS[0].ref}, {BRANCH_ARMS[1].alias}={BRANCH_ARMS[1].ref}",
            "",
            "## Notes",
            "- package gate requires `DIFY_BIN` or a PATH-resolved `dify` binary and now runs package/sign/verify for edit tasks.",
            "- repo-wide fixed instruction reduction is tracked separately in `memory-bank/07-external-research/agent_instruction_simplification_2026-03-15.md`.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_all(
    worktree_root: Path,
    timeout: int,
    *,
    task_filter: set[str] | None = None,
    reps: set[int] | None = None,
) -> None:
    primary_filter = task_filter or PRIMARY_TASK_IDS
    run_parent_matrix(
        worktree_root, timeout, task_filter=primary_filter, reps=reps
    )
    parent_summary = score_parent_runs()
    subagent_summary = run_subagent_confirmations(
        worktree_root,
        timeout=timeout,
        task_filter=task_filter or {"BUG-01", "OPS-01"},
    )
    if (
        task_filter is None
        and parent_summary["verdict"].get("non_inferior")
        and not parent_summary["verdict"].get("strictly_better")
    ):
        run_parent_matrix(
            worktree_root,
            timeout,
            task_filter=TIEBREAKER_TASK_IDS,
            reps=reps,
        )
        parent_summary = score_parent_runs()
    report = render_final_report(parent_summary, subagent_summary)
    report_path = RESULTS_ROOT / "final_report.md"
    report_path.write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AGENTS branch evaluation runner"
    )
    parser.add_argument(
        "command",
        choices=("parent", "score", "subagent", "all"),
        help="Which stage to run",
    )
    parser.add_argument(
        "--worktree-root",
        default=str(DEFAULT_WORKTREE_ROOT),
        help="Base directory for disposable evaluation worktrees",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Codex exec timeout in seconds",
    )
    parser.add_argument(
        "--tasks",
        help="Comma-separated task ids to run",
    )
    parser.add_argument(
        "--reps",
        help="Comma-separated repetition numbers to run for parent tasks",
    )
    args = parser.parse_args()

    worktree_root = Path(args.worktree_root).expanduser().resolve()
    ensure_dir(RESULTS_ROOT)
    task_filter = parse_csv_arg(args.tasks)
    reps_raw = parse_csv_arg(args.reps)
    reps = {int(value) for value in reps_raw} if reps_raw else None

    if args.command == "parent":
        run_parent_matrix(
            worktree_root,
            args.timeout,
            task_filter=task_filter,
            reps=reps,
        )
        return 0
    if args.command == "score":
        score_parent_runs()
        return 0
    if args.command == "subagent":
        run_subagent_confirmations(
            worktree_root,
            timeout=args.timeout,
            task_filter=task_filter,
        )
        return 0

    run_all(
        worktree_root,
        args.timeout,
        task_filter=task_filter,
        reps=reps,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
