"""Pure image geometry and explicit request/response bounds."""

from __future__ import annotations

import io
import json
import math
import struct
import warnings
from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from typing import Any

from PIL import Image, ImageOps

from plugin.region_contract import Failure, validate_read as validate_read


@dataclass(frozen=True)
class Limits:
    upload_bytes: int = 15 * 1024 * 1024
    source_pixels: int = 40_000_000
    source_side: int = 16_000
    execution_images: int = 10
    execution_pixels: int = 80_000_000
    global_pixels: int = 160_000_000
    output_pixels: int = 16_000_000
    output_side: int = 8192
    overview_side: int = 4096
    calls: int = 8
    ttl_seconds: float = 900
    ocr_seconds: float = 30
    request_seconds: float = 45
    response_chars: int = 20_000
    response_blocks: int = 500
    response_bytes: int = 256 * 1024
    ledger_entries: int = 100_000


def normalize(data: bytes, mime: str, limits: Limits) -> bytes:
    if len(data) > limits.upload_bytes:
        raise Failure(413, "INPUT_TOO_LARGE")
    if mime not in ("image/png", "image/jpeg"):
        raise Failure(415, "UNSUPPORTED_MEDIA_TYPE")
    try:
        # Check container closure; Pillow otherwise accepts appended payloads.
        if mime == "image/png":
            if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                raise Failure(400, "INVALID_IMAGE")
            offset = 8
            while offset + 12 <= len(data):
                size = struct.unpack(">I", data[offset : offset + 4])[0]
                kind = data[offset + 4 : offset + 8]
                offset += 12 + size
                if kind == b"IEND":
                    break
            if kind != b"IEND" or offset != len(data):
                raise Failure(400, "INVALID_IMAGE")
        elif not data.startswith(b"\xff\xd8") or not data.endswith(
            b"\xff\xd9"
        ):
            raise Failure(400, "INVALID_IMAGE")
        if mime == "image/jpeg":
            pos = 2
            while pos < len(data):
                if data[pos] != 255:
                    raise Failure(400, "INVALID_IMAGE")
                while pos < len(data) and data[pos] == 255:
                    pos += 1
                marker = data[pos]
                pos += 1
                if marker == 0xD9:
                    if pos != len(data):
                        raise Failure(400, "INVALID_IMAGE")
                    break
                length = int.from_bytes(data[pos : pos + 2], "big")
                if length < 2 or pos + length > len(data):
                    raise Failure(400, "INVALID_IMAGE")
                pos += length
                if marker == 0xDA:
                    while pos < len(data):
                        if data[pos] != 255:
                            pos += 1
                            continue
                        following = data[pos + 1]
                        if following == 0 or 0xD0 <= following <= 0xD7:
                            pos += 2
                            continue
                        break
            else:
                raise Failure(400, "INVALID_IMAGE")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                expected = "PNG" if mime == "image/png" else "JPEG"
                if (
                    image.format != expected
                    or getattr(image, "n_frames", 1) != 1
                ):
                    raise Failure(400, "INVALID_IMAGE")
                if (
                    image.width * image.height > limits.source_pixels
                    or max(image.size) > limits.source_side
                ):
                    raise Failure(413, "INPUT_TOO_LARGE")
                image.verify()
            with Image.open(io.BytesIO(data)) as image:
                image = ImageOps.exif_transpose(image)
                if "A" in image.getbands() or "transparency" in image.info:
                    rgba = image.convert("RGBA")
                    rgb = Image.new("RGB", rgba.size, "white")
                    rgb.paste(rgba, mask=rgba.getchannel("A"))
                else:
                    rgb = image.convert("RGB")
                result = io.BytesIO()
                # A new image discards EXIF, comments, profiles and filename.
                clean = Image.frombytes("RGB", rgb.size, rgb.tobytes())
                clean.save(result, format="PNG")
                return result.getvalue()
    except Failure:
        raise
    except Exception:
        raise Failure(400, "INVALID_IMAGE") from None


def geometry(
    width: int,
    height: int,
    region: list[float],
    scale: float,
    limits: Limits,
    *,
    overview: bool = False,
) -> dict[str, Any]:
    values = [Decimal(str(v)) for v in region]
    pixels = [
        int(
            (values[i] * (width if i % 2 == 0 else height)).to_integral_value(
                rounding=ROUND_FLOOR if i < 2 else ROUND_CEILING
            )
        )
        for i in range(4)
    ]
    cw, ch = pixels[2] - pixels[0], pixels[3] - pixels[1]
    maximum = min(
        limits.output_side / cw,
        limits.output_side / ch,
        math.sqrt(limits.output_pixels / (cw * ch)),
    )
    if overview:
        scale = min(1, limits.overview_side / max(width, height), maximum)
    out = [
        max(
            1,
            int(
                (
                    Decimal(size) * Decimal(str(scale)) + Decimal(".5")
                ).to_integral_value(rounding=ROUND_FLOOR)
            ),
        )
        for size in (cw, ch)
    ]
    if (
        out[0] * out[1] > limits.output_pixels
        or max(out) > limits.output_side
        or (overview and max(out) > limits.overview_side)
    ):
        raise Failure(
            422,
            "OUTPUT_LIMIT_EXCEEDED",
            suggested_scale_max=math.floor(maximum * 1_000_000) / 1_000_000,
        )
    return {
        "coordinate_space": "normalized_original_after_exif",
        "source_size": {"width": width, "height": height},
        "requested_region": region,
        "crop_pixels": pixels,
        "requested_scale": scale,
        "output_size": {"width": out[0], "height": out[1]},
        "effective_scale": {"x": out[0] / cw, "y": out[1] / ch},
    }


def crop(data: bytes, spec: dict[str, Any]) -> Image.Image:
    with Image.open(io.BytesIO(data)) as image:
        return image.crop(tuple(spec["crop_pixels"])).resize(
            tuple(spec["output_size"].values()), Image.Resampling.LANCZOS
        )


def response(
    image_id: str,
    page: int | None,
    spec: dict[str, Any],
    detected: list[dict[str, Any]],
    engine: dict[str, str],
    request_id: str,
    limits: Limits,
) -> dict[str, Any]:
    blocks: list[dict[str, Any]] = []
    warnings_out: list[str] = []
    left, top, _, _ = spec["crop_pixels"]
    sx, sy = spec["effective_scale"].values()
    width, height = spec["source_size"].values()
    ow, oh = spec["output_size"].values()
    result = {
        "schema_version": "1.0",
        "request_id": request_id,
        "status": "needs_review",
        "content_role": "untrusted_document_data",
        "image_id": image_id,
        "page_number": page,
        "geometry": spec,
        "text": "",
        "blocks": blocks,
        "truncated": True,
        "needs_review": True,
        "warnings": [
            "NO_TEXT_DETECTED",
            "TEXT_DETECTED_BUT_UNREADABLE",
            "LOW_OCR_CONFIDENCE",
            "RESPONSE_TRUNCATED",
        ],
        "engine": engine,
    }

    def encoded(value: Any) -> int:
        return len(
            json.dumps(
                value, ensure_ascii=False, separators=(",", ":")
            ).encode()
        )

    # Reserve the complete maximum status/warning envelope once. Add each block
    # and duplicated text once; never serialize an unbounded candidate response.
    byte_count = encoded(result)
    char_count = 0
    text_parts: list[str] = []
    truncated = False
    for index, item in enumerate(detected):
        if len(blocks) >= limits.response_blocks:
            truncated = True
            break
        text = item["text"]
        char_increment = 2 * len(text) + int(bool(text) and bool(text_parts))
        if char_count + char_increment > limits.response_chars:
            truncated = True
            break
        polygon = item["polygon"]
        if not polygon or any(
            len(p) != 2
            or not all(type(v) in (int, float) and math.isfinite(v) for v in p)
            for p in polygon
        ):
            raise Failure(502, "OCR_FAILED")
        if any(x < 0 or y < 0 or x > ow or y > oh for x, y in polygon):
            raise Failure(502, "OCR_FAILED")
        points = [
            ((left + x / sx) / width, (top + y / sy) / height)
            for x, y in polygon
        ]
        xs, ys = zip(*points)
        confidence = item.get("confidence")
        if confidence is not None and (
            type(confidence) not in (int, float)
            or not math.isfinite(confidence)
            or not 0 <= confidence <= 1
        ):
            confidence = None
        review = not text or confidence is None or confidence < 0.8
        block = {
            "block_id": f"b{index}",
            "text": text,
            "bbox": [min(xs), min(ys), max(xs), max(ys)],
            "confidence": confidence,
            "needs_review": review,
        }
        increment = encoded(block) + int(bool(blocks))
        if text:
            increment += encoded(text) - 2 + 2 * int(bool(text_parts))
        if byte_count + increment > limits.response_bytes:
            truncated = True
            break
        char_count += char_increment
        byte_count += increment
        blocks.append(block)
        if text:
            text_parts.append(text)
        if not text and "TEXT_DETECTED_BUT_UNREADABLE" not in warnings_out:
            warnings_out.append("TEXT_DETECTED_BUT_UNREADABLE")
        if review and text and "LOW_OCR_CONFIDENCE" not in warnings_out:
            warnings_out.append("LOW_OCR_CONFIDENCE")
    status = "ok"
    review = any(b["needs_review"] for b in blocks)
    if not detected:
        status, review = "no_text", True
        warnings_out.append("NO_TEXT_DETECTED")
    if truncated:
        warnings_out.append("RESPONSE_TRUNCATED")
        status, review = "needs_review", True
    elif review and status != "no_text":
        status = "needs_review"
    result.update(
        text="\n".join(text_parts),
        status=status,
        needs_review=review,
        truncated=truncated,
        warnings=warnings_out,
    )
    if encoded(result) > limits.response_bytes:
        raise Failure(500, "INTERNAL_ERROR")
    return result
