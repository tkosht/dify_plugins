"""Thin transport adapter. Context comes from transport, never tool parameters."""

from __future__ import annotations

import http.client
import ipaddress
import json
import re
import socket
import ssl
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote, urlsplit

from region_contract import Failure, validate_read


@dataclass(frozen=True)
class TrustedContext:
    app_id: str
    workflow_run_id: str

    def execution_id(self, expected_app: str) -> str:
        if self.app_id != expected_app or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_-]{15,127}", self.workflow_run_id
        ):
            raise Failure(403, "CONTEXT_REQUIRED")
        return self.workflow_run_id


def resolve_context(session: Any) -> TrustedContext:
    # Stock Dify 1.18.0 / SDK 0.10.2 does not establish authenticated run context.
    # app/conversation/session/message IDs are deliberately never substituted.
    # A transport extension requires a separately reviewed, versioned change.
    raise Failure(403, "CONTEXT_REQUIRED")


@dataclass(frozen=True)
class Destination:
    host: str
    port: int
    ips: tuple[str, ...]

    @classmethod
    def parse(cls, origin: str, ips: str) -> Destination:
        parsed = urlsplit(origin)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise Failure(422, "INVALID_REQUEST")
        try:
            port = parsed.port or 443
            addresses = tuple(
                str(ipaddress.ip_address(s.strip())) for s in ips.split(",")
            )
            if not addresses or any(
                ipaddress.ip_address(s).is_link_local
                or ipaddress.ip_address(s).is_multicast
                or ipaddress.ip_address(s).is_unspecified
                for s in addresses
            ):
                raise ValueError("address")
        except ValueError:
            raise Failure(422, "INVALID_REQUEST") from None
        return cls(parsed.hostname.lower(), port, addresses)


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, target: Destination, timeout: float) -> None:
        super().__init__(
            target.host,
            target.port,
            timeout=timeout,
            context=ssl.create_default_context(),
        )
        self.target = target

    def connect(self) -> None:
        # The operator pins the exact approved IP; no DNS rebinding/proxy fallback.
        raw = socket.create_connection(
            (self.target.ips[0], self.port), self.timeout
        )
        self.sock = self._context.wrap_socket(raw, server_hostname=self.host)


def service_failure(status: int, data: bytes) -> Failure:
    allowed = {
        400: {"INVALID_IMAGE", "INVALID_REQUEST"},
        401: {"UNAUTHENTICATED"},
        403: {"CONTEXT_REQUIRED"},
        404: {"IMAGE_NOT_AVAILABLE"},
        413: {"INPUT_TOO_LARGE"},
        415: {"UNSUPPORTED_MEDIA_TYPE"},
        422: {"INVALID_REGION", "OUTPUT_LIMIT_EXCEEDED", "INVALID_REQUEST"},
        429: {"BUDGET_EXCEEDED", "BUSY"},
        500: {"INTERNAL_ERROR"},
        502: {"OCR_FAILED"},
        503: {"OCR_UNAVAILABLE"},
        504: {"OCR_TIMEOUT"},
    }
    try:
        body = json.loads(data)
        if not isinstance(body, dict) or set(body) != {"error"}:
            raise ValueError("error envelope")
        item = body["error"]
        required = {"code", "message", "request_id", "retryable"}
        optional = {"suggested_scale_max", "retry_after_seconds"}
        if (
            not isinstance(item, dict)
            or not required <= set(item)
            or set(item) - required - optional
        ):
            raise ValueError("error schema")
        if (
            item["code"] not in allowed.get(status, set())
            or not isinstance(item["message"], str)
            or len(item["message"]) > 512
            or not isinstance(item["request_id"], str)
            or not re.fullmatch(r"req_[0-9a-f]{32}", item["request_id"])
            or type(item["retryable"]) is not bool
        ):
            raise ValueError("error fields")
        if "suggested_scale_max" in item and (
            type(item["suggested_scale_max"]) not in (int, float)
            or not 0 <= item["suggested_scale_max"] <= 4
        ):
            raise ValueError("scale")
        if "retry_after_seconds" in item and (
            type(item["retry_after_seconds"]) is not int
            or not 0 <= item["retry_after_seconds"] <= 60
        ):
            raise ValueError("retry")
        # Return only a whitelisted code/status. Never propagate body, message,
        # URL, credential, traceback or server-supplied request metadata.
        return Failure(status, item["code"])
    except Exception:
        return Failure(502, "UPSTREAM_FAILED")


def exchange(
    target: Destination,
    method: str,
    path: str,
    headers: dict[str, str],
    body: bytes | None,
    maximum: int,
    deadline: float,
) -> bytes:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise Failure(504, "OCR_TIMEOUT")
    connection = PinnedHTTPS(target, min(remaining, 45))
    try:
        connection.request(method, path, body, headers)
        result = connection.getresponse()
        # No redirects, no response/error body or signed URL in exception output.
        success = result.status in (200, 201)
        bound = maximum if success else 4096
        data = bytearray()
        while True:
            if time.monotonic() >= deadline:
                raise Failure(504, "OCR_TIMEOUT")
            if connection.sock is not None:
                connection.sock.settimeout(
                    max(0.001, deadline - time.monotonic())
                )
            part = result.read(min(65_536, bound + 1 - len(data)))
            data.extend(part)
            if len(data) > bound:
                raise Failure(
                    413 if success else 502,
                    "INPUT_TOO_LARGE" if success else "UPSTREAM_FAILED",
                )
            if not part:
                break
        if not success:
            raise service_failure(result.status, bytes(data))
        return bytes(data)
    except Failure:
        raise
    except Exception:
        raise Failure(502, "UPSTREAM_FAILED") from None
    finally:
        connection.close()


def file_path(url: str, destination: Destination, prefix: str) -> str:
    try:
        parts = urlsplit(url)
        decoded = unquote(parts.path)
        if (
            parts.scheme != "https"
            or parts.hostname != destination.host
            or (parts.port or 443) != destination.port
            or parts.username
            or parts.password
            or parts.fragment
            or not prefix.startswith("/files/")
            or not decoded.startswith(prefix)
            or "%" in decoded
            or "\\" in decoded
            or any(p in (".", "..") for p in decoded.split("/"))
            or any(ord(c) < 32 or ord(c) == 127 for c in url)
            or len(url) > 8192
        ):
            raise ValueError("destination")
        return parts.path + ("?" + parts.query if parts.query else "")
    except (TypeError, ValueError):
        raise Failure(422, "INVALID_REQUEST") from None


class Adapter:
    def __init__(
        self, credentials: dict[str, Any], context: TrustedContext
    ) -> None:
        self.service = Destination.parse(
            credentials["service_origin"], credentials["service_ips"]
        )
        self.files = Destination.parse(
            credentials["file_origin"], credentials["file_ips"]
        )
        self.prefix = credentials["file_prefix"]
        self.execution = context.execution_id(credentials["app_id"])
        self.token = credentials["service_token"]
        if not isinstance(self.token, str) or len(self.token) < 32:
            raise Failure(401, "UNAUTHENTICATED")

    def call(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        content_type: str = "application/json",
    ) -> dict[str, Any]:
        raw = exchange(
            self.service,
            method,
            path,
            {
                "Authorization": "Bearer " + self.token,
                "X-Execution-Id": self.execution,
                "Content-Type": content_type,
            },
            body,
            256 * 1024,
            time.monotonic() + 60,
        )
        try:
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError("response")
            return result
        except Exception:
            raise Failure(502, "UPSTREAM_FAILED") from None

    def read(self, parameters: dict[str, Any]) -> dict[str, Any]:
        query = validate_read(parameters, flat=True)
        return self.call(
            "POST",
            "/v1/read-region",
            json.dumps(query, allow_nan=False).encode(),
        )

    def prepare(self, files: list[Any]) -> dict[str, Any]:
        from dify_plugin.file.file import File

        if (
            not isinstance(files, list)
            or not 1 <= len(files) <= 10
            or any(not isinstance(f, File) for f in files)
        ):
            raise Failure(422, "INVALID_REQUEST")
        if any(
            f.mime_type not in ("image/png", "image/jpeg")
            or (f.size is not None and (f.size < 0 or f.size > 15 * 1024**2))
            for f in files
        ):
            raise Failure(415, "UNSUPPORTED_MEDIA_TYPE")
        available: list[dict[str, Any]] = []
        try:
            for index, file in enumerate(files, 1):
                path = file_path(file.url, self.files, self.prefix)
                data = exchange(
                    self.files,
                    "GET",
                    path,
                    {},
                    None,
                    15 * 1024**2,
                    time.monotonic() + 45,
                )
                import uuid

                boundary = "rr_" + uuid.uuid4().hex
                body = (
                    f'--{boundary}\r\nContent-Disposition: form-data; name="page_number"\r\n\r\n{index}\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="image"\r\nContent-Type: {file.mime_type}\r\n\r\n'.encode()
                    + data
                    + f"\r\n--{boundary}--\r\n".encode()
                )
                available.append(
                    self.call(
                        "POST",
                        "/v1/images",
                        body,
                        "multipart/form-data; boundary=" + boundary,
                    )
                )
            # Avoid an unbounded 10 x 256 KiB tool result.
            result = {"available_images": available}
            if (
                len(json.dumps(result, ensure_ascii=False).encode())
                > 256 * 1024
            ):
                raise Failure(413, "INPUT_TOO_LARGE")
            return result
        except Exception:
            # Partial registration is revoked; service TTL remains the fallback.
            try:
                self.cleanup()
            except Exception:
                pass
            raise

    def cleanup(self) -> dict[str, Any]:
        return self.call("DELETE", "/v1/images")
