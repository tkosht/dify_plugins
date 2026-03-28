#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


@dataclass(frozen=True)
class WaivedVulnerability:
    id: str
    package: str
    reason: str
    removal_criteria: str


WAIVED_VULNERABILITIES = (
    WaivedVulnerability(
        id="CVE-2026-27205",
        package="flask",
        reason="official dify-plugin still pins Flask~=3.0.3",
        removal_criteria=(
            "remove after upstream dify-plugin releases no longer resolve "
            "Flask~=3.0.3"
        ),
    ),
    WaivedVulnerability(
        id="CVE-2026-25645",
        package="requests",
        reason="official dify-plugin still pins requests~=2.32.3",
        removal_criteria=(
            "remove after upstream dify-plugin releases allow "
            "requests>=2.33.0"
        ),
    ),
)

DEFAULT_AUDIT_PYTHON = (
    os.getenv("PIP_AUDIT_PYTHON") or os.getenv("UV_PYTHON") or "3.11"
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run pip-audit with repository waivers and fail when a waiver "
            "becomes stale."
        )
    )
    parser.add_argument(
        "requirements",
        nargs="+",
        help="One or more requirements.txt files to audit.",
    )
    return parser.parse_args(argv)


def build_pip_audit_command(
    requirements_path: Path,
    *,
    ignore_ids: tuple[str, ...] = (),
    json_output: bool = False,
) -> list[str]:
    command = [
        "uvx",
        "--python",
        DEFAULT_AUDIT_PYTHON,
        "--with",
        "pip-audit",
        "pip-audit",
        "-r",
        str(requirements_path),
    ]
    if json_output:
        command.extend(["-f", "json"])
    for vuln_id in ignore_ids:
        command.extend(["--ignore-vuln", vuln_id])
    return command


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )


def emit(stream: TextIO, content: str) -> None:
    if not content:
        return
    stream.write(content)
    if not content.endswith("\n"):
        stream.write("\n")


def extract_json_payload(output: str) -> dict[str, object]:
    start = output.find("{")
    if start < 0:
        raise ValueError("pip-audit JSON payload not found in stdout")
    try:
        payload = json.loads(output[start:])
    except json.JSONDecodeError as exc:
        raise ValueError("invalid pip-audit JSON payload") from exc
    if not isinstance(payload, dict):
        raise ValueError("pip-audit JSON payload must be an object")
    return payload


def collect_present_vulnerabilities(
    payload: dict[str, object],
) -> dict[str, set[str]]:
    present: dict[str, set[str]] = {}
    dependencies = payload.get("dependencies")
    if not isinstance(dependencies, list):
        raise ValueError("pip-audit JSON payload is missing dependencies")

    for dependency in dependencies:
        if not isinstance(dependency, dict):
            continue
        package_name = dependency.get("name")
        vulnerabilities = dependency.get("vulns")
        if not isinstance(package_name, str) or not isinstance(
            vulnerabilities, list
        ):
            continue
        for vulnerability in vulnerabilities:
            if not isinstance(vulnerability, dict):
                continue
            vuln_id = vulnerability.get("id")
            if isinstance(vuln_id, str):
                present.setdefault(vuln_id, set()).add(package_name)
    return present


def summarize_present_waivers(
    requirements_path: Path,
    present: dict[str, set[str]],
    out: TextIO,
) -> None:
    active_waivers = []
    for waiver in WAIVED_VULNERABILITIES:
        packages = sorted(present.get(waiver.id, set()))
        if packages:
            active_waivers.append(f"{waiver.id} ({', '.join(packages)})")

    if active_waivers:
        print(
            f"Observed active waivers for {requirements_path}: "
            f"{', '.join(active_waivers)}",
            file=out,
        )
        return

    print(
        f"No active waived vulnerabilities remain for {requirements_path}.",
        file=out,
    )


def audit_requirements(
    requirements_paths: list[Path],
    *,
    runner: Callable[
        [list[str]], subprocess.CompletedProcess[str]
    ] = run_command,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    waived_ids = tuple(waiver.id for waiver in WAIVED_VULNERABILITIES)
    present_vulnerabilities: dict[str, set[str]] = {}

    for requirements_path in requirements_paths:
        print(f"==> pip-audit gate: {requirements_path}", file=out)

        allowed_run = runner(
            build_pip_audit_command(requirements_path, ignore_ids=waived_ids)
        )
        emit(out, allowed_run.stdout)
        emit(err, allowed_run.stderr)
        if allowed_run.returncode != 0:
            print(
                f"pip-audit failed for {requirements_path} even after "
                "applying configured waivers.",
                file=err,
            )
            return allowed_run.returncode or 1

        raw_run = runner(
            build_pip_audit_command(requirements_path, json_output=True)
        )
        if raw_run.returncode not in {0, 1}:
            emit(out, raw_run.stdout)
            emit(err, raw_run.stderr)
            print(
                f"pip-audit JSON probe failed for {requirements_path}.",
                file=err,
            )
            return raw_run.returncode or 1

        try:
            payload = extract_json_payload(raw_run.stdout)
            current_vulnerabilities = collect_present_vulnerabilities(payload)
        except ValueError as exc:
            emit(out, raw_run.stdout)
            emit(err, raw_run.stderr)
            print(
                f"Failed to parse pip-audit JSON for {requirements_path}: "
                f"{exc}",
                file=err,
            )
            return 1

        for vuln_id, packages in current_vulnerabilities.items():
            present_vulnerabilities.setdefault(vuln_id, set()).update(packages)
        summarize_present_waivers(
            requirements_path, current_vulnerabilities, out
        )

    stale_waivers = [
        waiver
        for waiver in WAIVED_VULNERABILITIES
        if waiver.id not in present_vulnerabilities
    ]
    if stale_waivers:
        print(
            "Configured pip-audit waivers are no longer needed. Remove them "
            "from bin/pip_audit_gate.py and the corresponding research note:",
            file=err,
        )
        for waiver in stale_waivers:
            print(
                f"- {waiver.id} ({waiver.package}): {waiver.reason}; "
                f"{waiver.removal_criteria}",
                file=err,
            )
        return 1

    print(
        "pip-audit gate passed. All configured waivers are still required.",
        file=out,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    requirements_paths = [Path(path) for path in args.requirements]
    return audit_requirements(requirements_paths)


if __name__ == "__main__":
    raise SystemExit(main())
