from __future__ import annotations

import io
import json
import threading
import time
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from service.api import create_app
from service.core import (
    Failure,
    Limits,
    crop,
    geometry,
    normalize,
    response,
    validate_read,
)
from service.ocr import check_models, run
from service.storage import Store

ENGINE = {
    "name": "test-double",
    "version": "1",
    "model_id": "synthetic",
    "confidence_kind": "unavailable",
    "reading_order": "engine_order",
}
TOKEN = "test-token-" + "x" * 32
EXEC = "run_" + "1" * 32
HEADERS = {"Authorization": "Bearer " + TOKEN, "X-Execution-Id": EXEC}


def png(width=200, height=100, mode="RGB", color="white"):
    out = io.BytesIO()
    Image.new(mode, (width, height), color).save(out, format="PNG")
    return out.getvalue()


def fake(operation, data, mime, region, scale, limits, models, deadline):
    original = (
        normalize(data, mime, limits) if operation == "register" else data
    )
    with Image.open(io.BytesIO(original)) as image:
        spec = geometry(
            *image.size,
            region,
            scale,
            limits,
            overview=operation == "register",
        )
    return {"original": original, "geometry": spec, "blocks": []}


def client(tmp_path, runner=fake, limits=Limits(), clock=time.time):
    return TestClient(
        create_app(
            tmp_path,
            tmp_path,
            tmp_path / "no-manifest",
            {"appA": TOKEN, "appB": "other-" + TOKEN},
            limits,
            runner=runner,
            engine=ENGINE,
            clock=clock,
        )
    )


def register(c, data=None, headers=HEADERS, **kwargs):
    return c.post(
        "/v1/images",
        headers=headers,
        files={"file": ("never-log-original.png", data or png(), "image/png")},
        **kwargs,
    )


def read(c, image_id, headers=HEADERS, **extra):
    return c.post(
        "/v1/read-region",
        headers=headers,
        json={
            "image_id": image_id,
            "region": [0, 0, 1, 1],
            "scale": 1,
            **extra,
        },
    )


def test_T01_T10_T14_registration_pages(tmp_path):
    with client(tmp_path) as c:
        first = register(c)
        assert first.status_code == 201
        body = first.json()
        assert body["width"] == 200 and body["overview"]["status"] == "no_text"
        assert body["overview"]["needs_review"] is True
        second = c.post(
            "/v1/images",
            headers=HEADERS,
            data={"page_number": "2"},
            files={"file": ("x", png(), "image/png")},
        )
        assert second.json()["page_number"] == 2
        assert second.json()["image_id"] != body["image_id"]
        assert read(c, body["image_id"]).status_code == 200


def test_T02_exif_and_alpha():
    out = io.BytesIO()
    image = Image.new("RGB", (60, 30), "red")
    exif = image.getexif()
    exif[274] = 6
    image.save(out, format="JPEG", exif=exif)
    result = normalize(out.getvalue(), "image/jpeg", Limits())
    with Image.open(io.BytesIO(result)) as clean:
        assert clean.size == (30, 60) and not clean.getexif()
    assert normalize(result, "image/png", Limits()) == result
    result = normalize(png(2, 2, "RGBA", (0, 0, 0, 0)), "image/png", Limits())
    with Image.open(io.BytesIO(result)) as clean:
        assert clean.getpixel((0, 0)) == (255, 255, 255)


@pytest.mark.parametrize(
    "scale,out",
    [(0.5, (500, 100)), (1, (1000, 200)), (2, (2000, 400)), (4, (4000, 800))],
)
def test_T03_T04_geometry(scale, out):
    spec = geometry(2000, 1000, [0.15, 0.30, 0.65, 0.50], scale, Limits())
    assert spec["crop_pixels"] == [300, 300, 1300, 500]
    assert tuple(spec["output_size"].values()) == out


def test_T05_T06_all_vertices_inverse():
    spec = geometry(2000, 1000, [0.15, 0.30, 0.65, 0.50], 2, Limits())
    result = response(
        "img_" + "a" * 32,
        1,
        spec,
        [
            {
                "text": "-12.5 mm",
                "confidence": 0.99,
                "polygon": [(100, 50), (900, 60), (800, 150), (100, 140)],
            }
        ],
        ENGINE,
        "req_" + "b" * 32,
        Limits(),
    )
    assert result["blocks"][0]["bbox"] == [0.175, 0.325, 0.375, 0.375]
    assert geometry(10, 10, [0.29, 0, 0.3, 1], 1, Limits())["crop_pixels"] == [
        2,
        0,
        3,
        10,
    ]


def test_T07_original_crop_is_stable():
    original = normalize(png(101, 51), "image/png", Limits())
    a = geometry(101, 51, [0.1, 0.2, 0.7, 0.9], 4, Limits())
    b = geometry(101, 51, [0.1, 0.2, 0.7, 0.9], 0.5, Limits())
    assert crop(original, a).size == (244, 144)
    assert crop(original, b).size == (31, 18)
    assert normalize(original, "image/png", Limits()) == original


@pytest.mark.parametrize(
    "value", [True, False, "0.1", None, float("nan"), float("inf"), -0.1, 1.1]
)
def test_T08_strict_numbers(value):
    with pytest.raises(Failure):
        validate_read(
            {"image_id": "img_" + "a" * 32, "region": [value, 0, 1, 1]}
        )


@pytest.mark.parametrize(
    "extra",
    [
        {"execution_id": "x"},
        {"base_url": "https://evil.invalid"},
        {"service_token": "canary"},
        {"X-Execution-Id": "other"},
        {"url": "file:///etc/passwd"},
    ],
)
def test_ST03_ST04_extra_keys(extra):
    with pytest.raises(Failure, match="INVALID_REQUEST"):
        validate_read(
            {"image_id": "img_" + "a" * 32, "region": [0, 0, 1, 1], **extra}
        )


def test_T09_output_limit_before_resize():
    with pytest.raises(Failure) as exc:
        geometry(16000, 2000, [0, 0, 1, 1], 4, Limits())
    assert (
        exc.value.status == 422
        and exc.value.details["suggested_scale_max"] <= 0.512
    )


def test_T11_unreadable_T13_response_budgets():
    spec = geometry(100, 100, [0, 0, 1, 1], 1, Limits())
    block = {
        "text": "",
        "confidence": None,
        "polygon": [(0, 0), (10, 0), (10, 10), (0, 10)],
    }
    result = response(
        "img_" + "a" * 32,
        None,
        spec,
        [block],
        ENGINE,
        "req_" + "b" * 32,
        Limits(),
    )
    assert result["status"] == "needs_review" and len(result["blocks"]) == 1
    block["text"] = "日本語" * 200
    result = response(
        "img_" + "a" * 32,
        None,
        spec,
        [block] * 10,
        ENGINE,
        "req_" + "b" * 32,
        replace(Limits(), response_chars=1500, response_bytes=1800),
    )
    assert result["truncated"] and result["needs_review"]
    assert (
        len(result["text"]) + sum(len(b["text"]) for b in result["blocks"])
        <= 1500
    )
    assert (
        len(
            json.dumps(
                result, ensure_ascii=False, separators=(",", ":")
            ).encode()
        )
        <= 1800
    )


def test_ST01_ST02_ST09_authorization_cleanup(tmp_path):
    with client(tmp_path) as c:
        image = register(c).json()["image_id"]
        assert register(c, headers={}).status_code == 401
        assert (
            read(
                c, image, headers={"Authorization": "Bearer " + TOKEN}
            ).status_code
            == 403
        )
        other = {**HEADERS, "X-Execution-Id": "run_" + "2" * 32}
        assert read(c, image, headers=other).status_code == 404
        app = {**HEADERS, "Authorization": "Bearer other-" + TOKEN}
        assert read(c, image, headers=app).status_code == 404
        assert (
            c.delete("/v1/images", headers=other).json()["deleted_images"] == 0
        )
        assert read(c, image).status_code == 200
        assert (
            c.delete("/v1/images", headers=HEADERS).json()["deleted_images"]
            == 1
        )
        assert read(c, image).status_code == 404
        assert register(c).status_code == 404


def test_ST09_ttl_not_extended(tmp_path):
    now = [1000.0]
    with client(tmp_path, clock=lambda: now[0]) as c:
        image = register(c).json()["image_id"]
        now[0] += 899
        assert read(c, image).status_code == 200
        now[0] += 2
        assert read(c, image).status_code == 404
        c.app.state.store.sweep()
        assert not c.app.state.store.images
        assert register(c).status_code == 404


def test_ST11_restart_and_single_process(tmp_path):
    with client(tmp_path) as c:
        register(c)
        with pytest.raises(RuntimeError, match="one service owner"):
            Store(tmp_path, Limits())
    with client(tmp_path) as c:
        assert register(c).status_code == 404


def test_F08_service_calls(tmp_path):
    with client(tmp_path, limits=replace(Limits(), calls=2)) as c:
        image = register(c).json()["image_id"]
        assert [read(c, image).status_code for _ in range(3)] == [
            200,
            200,
            429,
        ]


def test_ST10_delete_during_ocr(tmp_path):
    entered, release = threading.Event(), threading.Event()

    def slow(*args):
        if args[0] == "read":
            entered.set()
            release.wait(2)
        return fake(*args)

    with client(tmp_path, runner=slow) as c:
        image = register(c).json()["image_id"]
        replies = []
        t = threading.Thread(target=lambda: replies.append(read(c, image)))
        t.start()
        assert entered.wait(2)
        assert c.delete("/v1/images", headers=HEADERS).status_code == 200
        release.set()
        t.join(3)
        assert replies[0].status_code == 404 and not c.app.state.store.images


@pytest.mark.parametrize(
    "mime,data",
    [
        ("image/png", b"not png"),
        ("image/png", png() + b"evil"),
        ("image/jpeg", png()),
        ("image/gif", png()),
    ],
)
def test_ST05_invalid_images(mime, data):
    with pytest.raises(Failure):
        normalize(data, mime, Limits())


def test_ST05_dimensions_and_upload():
    with pytest.raises(Failure) as exc:
        normalize(
            png(200, 100), "image/png", replace(Limits(), source_pixels=1)
        )
    assert exc.value.status == 413
    with pytest.raises(Failure):
        normalize(png(), "image/png", replace(Limits(), upload_bytes=1))


def test_ST07_missing_models_fail_closed(tmp_path):
    with pytest.raises(Failure, match="OCR_UNAVAILABLE"):
        check_models(tmp_path, tmp_path / "missing")


def hanging_worker(*args):
    import os

    os.setsid()
    time.sleep(5)


def test_T12_timeout_kills_worker(tmp_path):
    start = time.monotonic()
    with pytest.raises(Failure, match="OCR_TIMEOUT"):
        run(
            "register",
            b"",
            "image/png",
            [0, 0, 1, 1],
            1,
            Limits(),
            tmp_path,
            start + 0.2,
            target=hanging_worker,
        )
    assert time.monotonic() - start < 2


def test_ST08_no_content_logging(tmp_path, capsys, caplog):
    with client(tmp_path) as c:
        register(c)
        c.post(
            "/v1/read-region",
            headers=HEADERS,
            content='{"canary":"OCR-CANARY-SECRET"}',
        )
    output = capsys.readouterr()
    assert TOKEN not in output.out + output.err + caplog.text
    assert "OCR-CANARY-SECRET" not in output.out + output.err + caplog.text
    assert "never-log-original" not in output.out + output.err + caplog.text
