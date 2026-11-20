import json

import pytest

from region_contract import Failure
from strategy_core import execute

APP = "app-known"
RUN = "run_" + "a" * 32
IMAGE = "img_" + "b" * 32
CONFIG = {"adapter": {"app_id": APP}}


def ocr_result(args, request=0):
    return {
        "image_id": args["image_id"],
        "request_id": "req_" + f"{request:032x}",
        "page_number": 1,
        "status": "ok",
        "text": "温度 -12.5 mm",
        "geometry": {
            "coordinate_space": "normalized_original_after_exif",
            "source_size": {"width": 100, "height": 100},
            "requested_region": [
                args[k] for k in ("x_min", "y_min", "x_max", "y_max")
            ],
            "crop_pixels": [0, 0, 100, 100],
            "requested_scale": args["scale"],
            "output_size": {"width": 200, "height": 200},
            "effective_scale": {"x": 2, "y": 2},
        },
        "engine": {
            "name": "test-double",
            "version": "1",
            "model_id": "synthetic",
        },
    }


class AdapterDouble:
    instances = []
    fail_prepare = False

    def __init__(self, credentials, context):
        self.context = context
        self.cleaned = False
        self.reads = []
        self.__class__.instances.append(self)

    def prepare(self, files):
        if self.fail_prepare:
            raise Failure(504, "OCR_TIMEOUT")
        return {
            "available_images": [
                {"image_id": IMAGE, "overview": ocr_result(arguments())}
            ]
        }

    def read(self, args):
        self.reads.append(args)
        return ocr_result(args, len(self.reads))

    def cleanup(self):
        self.cleaned = True


def parameters():
    return {
        "workflow_run_id": RUN,
        "query": "read value",
        "images": [],
        "model": {"provider": "local/fake", "model": "deterministic"},
    }


def arguments():
    return {
        "image_id": IMAGE,
        "x_min": 0,
        "y_min": 0,
        "x_max": 1,
        "y_max": 1,
        "scale": 2,
    }


def call(args):
    return {
        "content": None,
        "tool_calls": [
            {
                "id": "call1",
                "type": "function",
                "function": {
                    "name": "read_region",
                    "arguments": json.dumps(args),
                },
            }
        ],
    }


def test_full_overview_tool_next_model_answer_and_cleanup():
    observed = []

    def model(messages, tools, config):
        raw = json.dumps(messages)
        assert RUN not in raw and APP not in raw
        assert {x["function"]["name"] for x in tools} == {"read_region"}
        observed.append(messages.copy())
        return (
            call(arguments())
            if len(observed) == 1
            else {"content": "温度 -12.5 mm"}
        )

    result = execute(
        parameters(), APP, CONFIG, model=model, adapter_factory=AdapterDouble
    )
    assert result["region_calls"] == 1 and result["answer"] == "温度 -12.5 mm"
    instance = AdapterDouble.instances[-1]
    assert instance.context.workflow_run_id == RUN and instance.cleaned
    assert observed[1][-1]["role"] == "tool"


@pytest.mark.parametrize(
    "extra",
    ["execution_id", "workflow_run_id", "app_id", "service_token", "base_url"],
)
def test_spoofed_context_extra_model_arguments_rejected_before_dispatch(extra):
    args = {**arguments(), extra: "forged"}
    with pytest.raises(Failure, match="INVALID_TOOL_ARGUMENTS"):
        execute(
            parameters(),
            APP,
            CONFIG,
            model=lambda *a: call(args),
            adapter_factory=AdapterDouble,
        )
    instance = AdapterDouble.instances[-1]
    assert instance.cleaned and instance.reads == []


def test_cross_run_image_refused_and_cleaned():
    with pytest.raises(Failure):
        execute(
            parameters(),
            APP,
            CONFIG,
            model=lambda *a: call(
                {**arguments(), "image_id": "img_" + "c" * 32}
            ),
            adapter_factory=AdapterDouble,
        )
    assert (
        AdapterDouble.instances[-1].cleaned
        and not AdapterDouble.instances[-1].reads
    )


def test_app_scope_mismatch_refused_before_prepare():
    before = len(AdapterDouble.instances)
    with pytest.raises(Failure, match="CONTEXT_REQUIRED"):
        execute(
            parameters(),
            "other-app",
            CONFIG,
            model=lambda *a: {},
            adapter_factory=AdapterDouble,
        )
    assert len(AdapterDouble.instances) == before


def test_partial_registration_timeout_still_cleans_up():
    AdapterDouble.fail_prepare = True
    try:
        with pytest.raises(Failure, match="OCR_TIMEOUT"):
            execute(
                parameters(),
                APP,
                CONFIG,
                model=lambda *a: {},
                adapter_factory=AdapterDouble,
            )
        assert AdapterDouble.instances[-1].cleaned
    finally:
        AdapterDouble.fail_prepare = False


def test_cleanup_failure_preserves_primary_error_with_explicit_signal():
    class FailingCleanup(AdapterDouble):
        def cleanup(self):
            self.cleaned = True
            raise RuntimeError("private cleanup failure details")

    with pytest.raises(Failure) as exc:
        execute(
            parameters(),
            APP,
            CONFIG,
            model=lambda *a: call({**arguments(), "execution_id": "forged"}),
            adapter_factory=FailingCleanup,
        )
    assert exc.value.code == "INVALID_TOOL_ARGUMENTS"
    assert exc.value.details == {"cleanup_failed": True}
    assert "private" not in str(exc.value)


def test_cleanup_failure_prevents_successful_answer():
    class FailingCleanup(AdapterDouble):
        def cleanup(self):
            raise RuntimeError("private details")

    with pytest.raises(Failure, match="CLEANUP_FAILED"):
        execute(
            parameters(),
            APP,
            CONFIG,
            model=lambda *a: {"content": "answer"},
            adapter_factory=FailingCleanup,
        )


def test_model_exception_cleans_and_reports_safe_error():
    def failed(*args):
        raise RuntimeError("private model details")

    with pytest.raises(Failure, match="STRATEGY_FAILED") as exc:
        execute(
            parameters(),
            APP,
            CONFIG,
            model=failed,
            adapter_factory=AdapterDouble,
        )
    assert "private" not in str(exc.value)
    assert AdapterDouble.instances[-1].cleaned


def test_private_configuration_rejects_model_endpoint_or_key(
    tmp_path, monkeypatch
):
    from strategy_core import load_application

    p = tmp_path / "config.json"
    p.write_text(
        json.dumps(
            {
                "applications": {
                    APP: {
                        "adapter": {"app_id": APP},
                        "model": {
                            "api_key": "secret-canary",
                            "endpoint": "https://invalid",
                        },
                    }
                }
            }
        )
    )
    monkeypatch.setenv("READ_REGION_STRATEGY_CONFIG_FILE", str(p))
    with pytest.raises(Failure, match="CONTEXT_REQUIRED"):
        load_application(APP)


def test_sdk_strategy_configuration_and_schema_boundary():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "plugin"
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import yaml; from dify_plugin.entities.agent import AgentStrategyProviderConfiguration; p=AgentStrategyProviderConfiguration.model_validate(yaml.safe_load(open('provider/region_ocr.yaml'))); assert {x.name for x in p.strategies[0].parameters} == {'workflow_run_id','query','images','model'}; assert next(x for x in p.strategies[0].parameters if x.name=='model').type.value=='model-selector'",
        ],
        cwd=root,
        check=True,
        capture_output=True,
    )


def test_overview_only_answer_keeps_noncontent_source_reference():
    result = execute(
        parameters(),
        APP,
        CONFIG,
        model=lambda *a: {"content": "answer"},
        adapter_factory=AdapterDouble,
    )
    assert result["region_calls"] == 0
    assert len(result["source_evidence"]) == 1
    ref = result["source_evidence"][0]
    assert ref["kind"] == "overview" and ref["image_id"] == IMAGE
    assert ref["request_id"] == "req_" + "0" * 32
    assert ref["geometry"]["source_size"] == {"width": 100, "height": 100}
    assert ref["engine"]["model_id"] == "synthetic"
    raw = json.dumps(result["source_evidence"])
    assert all(
        x not in raw
        for x in ["温度", RUN, "never-project-canary", "execution_id"]
    )


def test_eight_region_reads_retain_bounded_exact_trace():
    class TenImages(AdapterDouble):
        def prepare(self, files):
            return {
                "available_images": [
                    {
                        "image_id": "img_" + f"{i:032x}",
                        "overview": ocr_result(
                            {**arguments(), "image_id": "img_" + f"{i:032x}"}
                        ),
                    }
                    for i in range(10)
                ]
            }

    count = [0]

    def model(*args):
        if count[0] == 8:
            return {"content": "answer"}
        i = count[0]
        count[0] += 1
        return call({**arguments(), "image_id": "img_" + f"{i:032x}"})

    result = execute(
        parameters(), APP, CONFIG, model=model, adapter_factory=TenImages
    )
    refs = result["source_evidence"]
    assert result["region_calls"] == 8 and len(refs) == 18
    assert [r["request_id"] for r in refs[10:]] == [
        "req_" + f"{i:032x}" for i in range(1, 9)
    ]
    assert len(json.dumps(result, ensure_ascii=False).encode()) < 256 * 1024
