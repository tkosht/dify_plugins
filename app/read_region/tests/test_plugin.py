from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

import adapter
from adapter import (
    Adapter,
    Destination,
    TrustedContext,
    file_path,
    resolve_context,
)
from region_contract import Failure

CREDS = {
    "service_origin": "https://ocr.internal.invalid:8443",
    "service_ips": "10.20.1.2",
    "service_token": "test-" + "x" * 32,
    "file_origin": "https://files.internal.invalid",
    "file_ips": "10.20.1.3",
    "file_prefix": "/files/",
    "app_id": "app-A",
}


def test_context_stock_dify_fails_closed():
    with pytest.raises(Failure, match="CONTEXT_REQUIRED"):
        resolve_context(
            SimpleNamespace(
                app_id="app-A",
                session_id="run-x",
                conversation_id="c",
                message_id="m",
                workflow_run_id="forged",
            )
        )
    with pytest.raises(Failure, match="CONTEXT_REQUIRED"):
        Adapter(CREDS, TrustedContext("other-app", "run_" + "a" * 32))


@pytest.mark.parametrize(
    "url",
    [
        "http://files.internal.invalid/files/a",
        "file:///files/a",
        "https://127.0.0.1/files/a",
        "https://169.254.169.254/latest/meta-data",
        "https://files.internal.invalid.evil.invalid/files/a",
        "https://files.internal.invalid/admin/a",
        "https://files.internal.invalid/files/%2e%2e/a",
        "https://files.internal.invalid/files/%252e%252e/a",
        "https://files.internal.invalid/files/a#x",
        "https://user:pass@files.internal.invalid/files/a",
        "https://files.internal.invalid:8443/files/a",
    ],
)
def test_ST04_file_endpoint_rejections(url):
    with pytest.raises(Failure):
        file_path(
            url,
            Destination.parse(CREDS["file_origin"], CREDS["file_ips"]),
            "/files/",
        )


def test_ST04_file_allowed_signed_query_not_logged():
    dest = Destination.parse(CREDS["file_origin"], CREDS["file_ips"])
    assert (
        file_path(
            "https://files.internal.invalid/files/abc/image-preview?signature=test",
            dest,
            "/files/",
        )
        == "/files/abc/image-preview?signature=test"
    )


def test_mock_adapter_context_separate_from_model(monkeypatch):
    seen = []

    def exchange(target, method, path, headers, body, maximum, deadline):
        seen.append((target, method, path, headers, body))
        return b'{"status":"needs_review"}'

    monkeypatch.setattr(adapter, "exchange", exchange)
    a = Adapter(CREDS, TrustedContext("app-A", "run_" + "b" * 32))
    assert (
        a.read(
            {
                "image_id": "img_" + "a" * 32,
                "x_min": 0,
                "y_min": 0,
                "x_max": 1,
                "y_max": 1,
            }
        )["status"]
        == "needs_review"
    )
    assert seen[0][3]["X-Execution-Id"] == "run_" + "b" * 32
    assert set(json.loads(seen[0][4])) == {"image_id", "region", "scale"}
    with pytest.raises(Failure):
        a.read(
            {
                "image_id": "img_" + "a" * 32,
                "x_min": 0,
                "y_min": 0,
                "x_max": 1,
                "y_max": 1,
                "execution_id": "override",
            }
        )
    assert len(seen) == 1


def test_plugin_yaml_sdk_validation():
    root = Path(__file__).resolve().parents[1] / "plugin"
    provider = yaml.safe_load((root / "provider/read_region.yaml").read_text())
    # Provider YAML refers to tool paths; validate complete entities with SDK types.
    provider["tools"] = [
        yaml.safe_load((root / p).read_text()) for p in provider["tools"]
    ]
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import yaml; from dify_plugin.entities.tool import ToolProviderConfiguration; ToolProviderConfiguration.model_validate(yaml.safe_load(open('provider/read_region.yaml')))",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )
    read = next(
        t for t in provider["tools"] if t["identity"]["name"] == "read_region"
    )
    assert {p["name"] for p in read["parameters"]} == {
        "image_id",
        "x_min",
        "y_min",
        "x_max",
        "y_max",
        "scale",
    }
    assert all(p["form"] == "llm" for p in read["parameters"])
