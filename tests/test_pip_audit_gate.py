from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "bin" / "pip_audit_gate.py"
SPEC = importlib.util.spec_from_file_location("pip_audit_gate", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
pip_audit_gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pip_audit_gate
SPEC.loader.exec_module(pip_audit_gate)


def _build_payload(vulnerabilities: dict[str, list[str]]) -> str:
    dependencies = []
    for package_name, vuln_ids in vulnerabilities.items():
        dependencies.append(
            {
                "name": package_name,
                "version": "1.0.0",
                "vulns": [
                    {"id": vuln_id, "fix_versions": []} for vuln_id in vuln_ids
                ],
            }
        )
    return json.dumps({"dependencies": dependencies, "fixes": []})


def _completed_process(
    command: list[str],
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=command,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def test_extract_json_payload_strips_preamble() -> None:
    payload = pip_audit_gate.extract_json_payload(
        "Found 2 known vulnerabilities\n" '{"dependencies": [], "fixes": []}'
    )
    assert payload == {"dependencies": [], "fixes": []}


def test_collect_present_vulnerabilities_maps_ids_to_packages() -> None:
    payload = json.loads(
        _build_payload(
            {
                "flask": ["CVE-2026-27205"],
                "requests": ["CVE-2026-25645"],
            }
        )
    )

    present = pip_audit_gate.collect_present_vulnerabilities(payload)

    assert present == {
        "CVE-2026-27205": {"flask"},
        "CVE-2026-25645": {"requests"},
    }


def test_build_pip_audit_command_omits_ignore_vuln_without_waivers() -> None:
    command = pip_audit_gate.build_pip_audit_command(Path("requirements.txt"))

    assert command == [
        "uvx",
        "--python",
        pip_audit_gate.DEFAULT_AUDIT_PYTHON,
        "--with",
        "pip-audit",
        "pip-audit",
        "-r",
        "requirements.txt",
    ]
    assert "--ignore-vuln" not in command


def test_audit_requirements_passes_without_waivers() -> None:
    requirements = [
        Path("app/openai_gpt5_responses/requirements.txt"),
        Path("app/gpt5_agent_strategies/requirements.txt"),
    ]
    queued_results = [
        _completed_process(
            ["audit-openai"],
            stdout="No known vulnerabilities found\n",
        ),
        _completed_process(
            ["audit-gpt5"],
            stdout="No known vulnerabilities found\n",
        ),
    ]
    recorded_commands: list[list[str]] = []

    def runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        recorded_commands.append(command)
        return queued_results.pop(0)

    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = pip_audit_gate.audit_requirements(
        requirements,
        runner=runner,
        out=stdout,
        err=stderr,
    )

    assert exit_code == 0
    assert len(recorded_commands) == len(requirements)
    assert queued_results == []
    assert all("--ignore-vuln" not in command for command in recorded_commands)
    assert all("-f" not in command for command in recorded_commands)
    assert "No waivers configured." in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_audit_requirements_propagates_blocking_failure_without_waivers() -> (
    None
):
    requirements = [Path("app/openai_gpt5_responses/requirements.txt")]
    queued_results = [
        _completed_process(
            ["audit-openai"],
            returncode=2,
            stdout="Found 1 known vulnerability\n",
            stderr="pip-audit failed\n",
        ),
    ]

    def runner(_: list[str]) -> subprocess.CompletedProcess[str]:
        return queued_results.pop(0)

    stdout = io.StringIO()
    stderr = io.StringIO()
    exit_code = pip_audit_gate.audit_requirements(
        requirements,
        runner=runner,
        out=stdout,
        err=stderr,
    )

    assert exit_code == 2
    assert "pip-audit failed" in stderr.getvalue()
    assert "applying configured waivers" not in stderr.getvalue()
