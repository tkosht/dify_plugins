import time
from dataclasses import replace

import pytest

from service.core import Failure, Limits, geometry, response, validate_read


def test_huge_json_integer_is_invalid_region():
    with pytest.raises(Failure) as exc:
        validate_read(
            {"image_id": "img_" + "a" * 32, "region": [10**400, 0, 1, 1]}
        )
    assert exc.value.status == 422


def test_many_blocks_linear_bounded_response():
    block = {
        "text": "abc",
        "confidence": 0.9,
        "polygon": [(0, 0), (10, 0), (10, 10), (0, 10)],
    }
    start = time.monotonic()
    result = response(
        "img_" + "a" * 32,
        None,
        geometry(10, 10, [0, 0, 1, 1], 1, Limits()),
        [block] * 12_000,
        {
            "name": "test",
            "version": "1",
            "model_id": "test",
            "confidence_kind": "unavailable",
            "reading_order": "engine_order",
        },
        "req_" + "b" * 32,
        Limits(),
    )
    assert result["truncated"] and len(result["blocks"]) <= 500
    assert time.monotonic() - start < 0.5


def test_past_deadline_cannot_return_created(tmp_path):
    from test_service import client, fake, register

    def late(*args):
        result = fake(*args)
        time.sleep(0.15)
        return result

    with client(
        tmp_path, runner=late, limits=replace(Limits(), request_seconds=0.1)
    ) as c:
        assert register(c).status_code == 504
        assert not c.app.state.store.images
