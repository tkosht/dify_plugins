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


def test_audit_requirements_passes_when_waivers_still_needed() -> None:
    requirements = [
        Path("app/openai_gpt5_responses/requirements.txt"),
        Path("app/gpt5_agent_strategies/requirements.txt"),
    ]
    queued_results = [
        _completed_process(
            ["allowed-openai"],
            stdout="No known vulnerabilities found, 2 ignored\n",
        ),
        _completed_process(
            ["raw-openai"],
            returncode=1,
            stdout=(
                "Found 2 known vulnerabilities in 2 packages\n"
                + _build_payload(
                    {
                        "flask": ["CVE-2026-27205"],
                        "requests": ["CVE-2026-25645"],
                    }
                )
            ),
        ),
        _completed_process(
            ["allowed-gpt5"],
            stdout="No known vulnerabilities found, 2 ignored\n",
        ),
        _completed_process(
            ["raw-gpt5"],
            returncode=1,
            stdout=(
                "Found 2 known vulnerabilities in 2 packages\n"
                + _build_payload(
                    {
                        "flask": ["CVE-2026-27205"],
                        "requests": ["CVE-2026-25645"],
                    }
                )
            ),
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

    assert exit_code == 0
    assert "All configured waivers are still required." in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_audit_requirements_fails_when_waiver_becomes_stale() -> None:
    requirements = [
        Path("app/openai_gpt5_responses/requirements.txt"),
        Path("app/gpt5_agent_strategies/requirements.txt"),
    ]
    queued_results = [
        _completed_process(
            ["allowed-openai"],
            stdout="No known vulnerabilities found, 1 ignored\n",
        ),
        _completed_process(
            ["raw-openai"],
            returncode=1,
            stdout=(
                "Found 1 known vulnerability in 1 package\n"
                + _build_payload({"flask": ["CVE-2026-27205"]})
            ),
        ),
        _completed_process(
            ["allowed-gpt5"],
            stdout="No known vulnerabilities found, 1 ignored\n",
        ),
        _completed_process(
            ["raw-gpt5"],
            returncode=1,
            stdout=(
                "Found 1 known vulnerability in 1 package\n"
                + _build_payload({"flask": ["CVE-2026-27205"]})
            ),
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

    assert exit_code == 1
    assert "CVE-2026-25645" in stderr.getvalue()
    assert "requests" in stderr.getvalue()


def test_audit_requirements_propagates_blocking_failure() -> None:
    requirements = [Path("app/openai_gpt5_responses/requirements.txt")]
    queued_results = [
        _completed_process(
            ["allowed-openai"],
            returncode=1,
            stdout="Found 1 known vulnerability\n",
            stderr="pip-audit failed\n",
        )
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

    assert exit_code == 1
    assert "pip-audit failed" in stderr.getvalue()
    assert "applying configured waivers" in stderr.getvalue()
