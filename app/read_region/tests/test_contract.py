import json
from pathlib import Path

import jsonschema
import yaml

from service.core import Limits, geometry, response

ROOT = Path(__file__).resolve().parents[1]


def test_response_contract_no_text_and_truncation():
    schema = json.loads((ROOT / "contracts/response.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    engine = {
        "name": "test",
        "version": "1",
        "model_id": "test",
        "confidence_kind": "unavailable",
        "reading_order": "engine_order",
    }
    result = response(
        "img_" + "a" * 32,
        None,
        geometry(10, 10, [0, 0, 1, 1], 1, Limits()),
        [],
        engine,
        "req_" + "b" * 32,
        Limits(),
    )
    jsonschema.validate(result, schema)
    api = yaml.safe_load((ROOT / "contracts/openapi.yaml").read_text())
    assert set(api["paths"]) == {"/healthz", "/v1/images", "/v1/read-region"}
    assert api["openapi"] == "3.1.0"


def test_agent_contract_matches_yaml():
    schema = json.loads(
        (ROOT / "contracts/agent-input.schema.json").read_text()
    )
    tool = yaml.safe_load((ROOT / "plugin/tools/read_region.yaml").read_text())
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == {p["name"] for p in tool["parameters"]}
