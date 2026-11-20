"""Internal-only HTTP interface. Never mount on a public/shared network."""

from __future__ import annotations

import asyncio
import contextlib
import hmac
import json
import re
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile

from service.core import Failure, Limits, response, validate_read
from service.ocr import check_models, run
from service.storage import Store


class BodyBoundary:
    def __init__(self, app: Any, limits: Limits) -> None:
        self.app, self.limits = app, limits

    async def __call__(
        self, scope: dict[str, Any], receive: Any, send: Any
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        scope["deadline"] = time.monotonic() + self.limits.request_seconds
        scope["request_id"] = "req_" + uuid.uuid4().hex
        total = 0

        async def bounded_receive() -> dict[str, Any]:
            nonlocal total
            message = await receive()
            total += len(message.get("body", b""))
            if total > self.limits.upload_bytes + 65_536:
                raise Failure(413, "INPUT_TOO_LARGE")
            return message

        try:
            await asyncio.wait_for(
                self.app(scope, bounded_receive, send),
                timeout=self.limits.request_seconds,
            )
        except Failure as exc:
            await error(exc, scope["request_id"])(scope, receive, send)
        except TimeoutError:
            await error(Failure(504, "OCR_TIMEOUT"), scope["request_id"])(
                scope, receive, send
            )


def error(exc: Failure, request_id: str) -> JSONResponse:
    return JSONResponse(
        {
            "error": {
                "code": exc.code,
                "message": exc.code,
                "request_id": request_id,
                "retryable": exc.code in {"BUSY", "OCR_UNAVAILABLE"},
                **exc.details,
            }
        },
        status_code=exc.status,
    )


def create_app(
    state_dir: Path,
    model_dir: Path,
    manifest: Path,
    tokens: dict[str, str],
    limits: Limits = Limits(),
    *,
    runner: Callable[..., dict[str, Any]] = run,
    engine: dict[str, str] | None = None,
    clock: Callable[[], float] = time.time,
) -> FastAPI:
    if (
        not tokens
        or any(not scope or len(token) < 32 for scope, token in tokens.items())
        or len(set(tokens.values())) != len(tokens)
    ):
        raise RuntimeError(
            "distinct service credentials of at least 32 characters required"
        )
    store = Store(state_dir, limits, clock)
    compute = threading.BoundedSemaphore(1)
    rejected: list[float] = []
    try:
        engine_info = engine or check_models(model_dir, manifest)
    except Failure:
        engine_info = None

    async def sweep() -> None:
        while True:
            await asyncio.sleep(min(30, limits.ttl_seconds))
            store.sweep()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        task = asyncio.create_task(sweep())
        try:
            yield
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            store.close()

    app = FastAPI(
        title="Local region OCR",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(BodyBoundary, limits=limits)
    app.state.store = store

    @app.exception_handler(Failure)
    async def failure_handler(request: Request, exc: Failure) -> JSONResponse:
        return error(exc, request.scope["request_id"])

    @app.exception_handler(Exception)
    async def internal_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return error(
            Failure(500, "INTERNAL_ERROR"),
            request.scope.get("request_id", "req_" + uuid.uuid4().hex),
        )

    def authenticate(request: Request) -> str:
        if request.query_params:
            raise Failure(422, "INVALID_REQUEST")
        header = request.headers.get("authorization", "")
        scope = next(
            (
                s
                for s, t in tokens.items()
                if hmac.compare_digest(header, "Bearer " + t)
            ),
            None,
        )
        if scope is None:
            now = time.monotonic()
            rejected[:] = [t for t in rejected if t > now - 60]
            if len(rejected) >= 60:
                raise Failure(429, "BUSY")
            rejected.append(now)
            raise Failure(401, "UNAUTHENTICATED")
        execution = request.headers.get("x-execution-id", "")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{15,127}", execution):
            raise Failure(403, "CONTEXT_REQUIRED")
        return store.key(scope, execution)

    async def process(
        request: Request,
        operation: str,
        data: bytes,
        mime: str,
        region: list[float],
        scale: float,
    ) -> dict[str, Any]:
        if engine_info is None:
            raise Failure(503, "OCR_UNAVAILABLE")
        if not compute.acquire(blocking=False):
            raise Failure(429, "BUSY")

        def bounded_work() -> dict[str, Any]:
            try:
                return runner(
                    operation,
                    data,
                    mime,
                    region,
                    scale,
                    limits,
                    model_dir,
                    request.scope["deadline"],
                )
            finally:
                compute.release()

        # The worker owns its hard deadline even if the client disconnects.
        return await asyncio.to_thread(bounded_work)

    @app.get("/healthz")
    async def health() -> dict[str, str]:
        if engine_info is None:
            raise Failure(503, "OCR_UNAVAILABLE")
        return {"status": "ok"}

    @app.post("/v1/images", status_code=201)
    async def register(request: Request) -> JSONResponse:
        key = authenticate(request)
        try:
            form = await request.form(
                max_files=1, max_fields=1, max_part_size=limits.upload_bytes
            )
        except Failure:
            raise
        except Exception:
            raise Failure(400, "INVALID_REQUEST") from None
        try:
            if (
                len(form.multi_items()) != len(form)
                or set(form) - {"file", "page_number"}
                or not isinstance(form.get("file"), UploadFile)
            ):
                raise Failure(422, "INVALID_REQUEST")
            file = form["file"]
            page: int | None = None
            if "page_number" in form:
                value = form["page_number"]
                if not isinstance(value, str) or not re.fullmatch(
                    r"[1-9][0-9]{0,8}", value
                ):
                    raise Failure(422, "INVALID_REQUEST")
                page = int(value)
            data = await file.read(limits.upload_bytes + 1)
            if len(data) > limits.upload_bytes:
                raise Failure(413, "INPUT_TOO_LARGE")
            expires = store.begin(key)
            result = await process(
                request,
                "register",
                data,
                file.content_type or "",
                [0, 0, 1, 1],
                1,
            )
            if time.monotonic() >= request.scope["deadline"]:
                raise Failure(504, "OCR_TIMEOUT")
            image_id = store.put(
                key, result["original"], result["geometry"], page
            )
            overview = await asyncio.to_thread(
                response,
                image_id,
                page,
                result["geometry"],
                result["blocks"],
                engine_info,
                request.scope["request_id"],
                limits,
            )
            body = {
                "image_id": image_id,
                **result["geometry"]["source_size"],
                "page_number": page,
                "expires_at": datetime.fromtimestamp(
                    expires, timezone.utc
                ).isoformat(),
                "overview": overview,
            }
            # Registration includes the overview; enforce the same whole-response cap.
            while (
                len(
                    json.dumps(
                        body, ensure_ascii=False, separators=(",", ":")
                    ).encode()
                )
                > limits.response_bytes
            ):
                if not overview["blocks"]:
                    raise Failure(500, "INTERNAL_ERROR")
                overview["blocks"].pop()
                overview["text"] = "\n".join(
                    b["text"] for b in overview["blocks"] if b["text"]
                )
                overview.update(
                    truncated=True, needs_review=True, status="needs_review"
                )
                if "RESPONSE_TRUNCATED" not in overview["warnings"]:
                    overview["warnings"].append("RESPONSE_TRUNCATED")
            if time.monotonic() >= request.scope["deadline"]:
                store.delete(key)
                raise Failure(504, "OCR_TIMEOUT")
            store.authorize(key, image_id)
            return JSONResponse(body, status_code=201)
        finally:
            await form.close()

    @app.post("/v1/read-region")
    async def read_region(request: Request) -> dict[str, Any]:
        key = authenticate(request)
        try:

            def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
                if len(dict(pairs)) != len(pairs):
                    raise ValueError("duplicate keys")
                return dict(pairs)

            body = json.loads(
                await request.body(),
                object_pairs_hook=unique,
                parse_constant=lambda _: (_ for _ in ()).throw(
                    ValueError("constant")
                ),
            )
        except Exception:
            raise Failure(422, "INVALID_REQUEST") from None
        query = validate_read(body)
        image = store.read(key, query["image_id"])
        result = await process(
            request,
            "read",
            image["original"],
            "image/png",
            query["region"],
            query["scale"],
        )
        answer = await asyncio.to_thread(
            response,
            query["image_id"],
            image["page"],
            result["geometry"],
            result["blocks"],
            engine_info,
            request.scope["request_id"],
            limits,
        )
        if time.monotonic() >= request.scope["deadline"]:
            raise Failure(504, "OCR_TIMEOUT")
        store.authorize(key, query["image_id"])
        return answer

    @app.delete("/v1/images")
    async def cleanup(request: Request) -> dict[str, Any]:
        key = authenticate(request)
        if await request.body():
            raise Failure(422, "INVALID_REQUEST")
        return {"deleted_images": store.delete(key), "execution_revoked": True}

    return app
