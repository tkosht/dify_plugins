import json
import time

import pytest

import adapter
from adapter import Destination, exchange
from region_contract import Failure


@pytest.mark.parametrize(
    "status,code",
    [
        (400, "INVALID_IMAGE"),
        (401, "UNAUTHENTICATED"),
        (403, "CONTEXT_REQUIRED"),
        (404, "IMAGE_NOT_AVAILABLE"),
        (413, "INPUT_TOO_LARGE"),
        (415, "UNSUPPORTED_MEDIA_TYPE"),
        (422, "INVALID_REGION"),
        (429, "BUDGET_EXCEEDED"),
        (429, "BUSY"),
        (500, "INTERNAL_ERROR"),
        (502, "OCR_FAILED"),
        (503, "OCR_UNAVAILABLE"),
        (504, "OCR_TIMEOUT"),
    ],
)
def test_safe_service_error_categories(monkeypatch, status, code):
    body = json.dumps(
        {
            "error": {
                "code": code,
                "message": "CANARY-SECRET-URL-TOKEN",
                "request_id": "req_" + "a" * 32,
                "retryable": False,
            }
        }
    ).encode()
    install_response(monkeypatch, status, body)
    with pytest.raises(Failure) as exc:
        exchange(
            Destination("example.invalid", 443, ("10.0.0.2",)),
            "POST",
            "/v1/read-region",
            {},
            b"{}",
            256 * 1024,
            time.monotonic() + 1,
        )
    assert (exc.value.status, exc.value.code) == (status, code)
    assert "CANARY" not in str(exc.value) and exc.value.details == {}


@pytest.mark.parametrize(
    "status,body",
    [
        (401, b'{"error":{"code":"evil"}}'),
        (404, b"SECRET STACK TRACE"),
        (503, b"x" * 5000),
        (302, b"location=https://evil.invalid?token=secret"),
        (
            401,
            json.dumps(
                {
                    "error": {
                        "code": "OCR_TIMEOUT",
                        "message": "secret",
                        "request_id": "req_" + "a" * 32,
                        "retryable": True,
                    }
                }
            ).encode(),
        ),
        (
            401,
            json.dumps(
                {
                    "error": {
                        "code": "UNAUTHENTICATED",
                        "message": "secret",
                        "request_id": "req_" + "a" * 32,
                        "retryable": True,
                        "debug": "secret",
                    }
                }
            ).encode(),
        ),
    ],
)
def test_unknown_malformed_or_oversized_errors_are_generic(
    monkeypatch, status, body
):
    install_response(monkeypatch, status, body)
    with pytest.raises(Failure) as exc:
        exchange(
            Destination("example.invalid", 443, ("10.0.0.2",)),
            "POST",
            "/v1/read-region",
            {},
            b"{}",
            256 * 1024,
            time.monotonic() + 1,
        )
    assert (exc.value.status, exc.value.code) == (502, "UPSTREAM_FAILED")
    assert exc.value.details == {}


def install_response(monkeypatch, status, body):
    class Response:
        def __init__(self):
            self.status = status
            self.offset = 0

        def read(self, n):
            result = body[self.offset : self.offset + n]
            self.offset += len(result)
            return result

    class Connection:
        sock = None

        def __init__(self, *args):
            pass

        def request(self, *args):
            pass

        def getresponse(self):
            return Response()

        def close(self):
            pass

    monkeypatch.setattr(adapter, "PinnedHTTPS", Connection)
