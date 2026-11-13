"""Local Tesseract adapter, run with decoding in a killable process group."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import multiprocessing
import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from PIL import Image

from service.core import Failure, Limits, crop, geometry, normalize


def check_models(directory: Path, manifest: Path) -> dict[str, str]:
    try:
        spec = json.loads(manifest.read_text())
        if set(spec["sha256"]) != {
            "jpn.traineddata",
            "eng.traineddata",
        } or any(
            not isinstance(v, str)
            or len(v) != 64
            or any(c not in "0123456789abcdef" for c in v)
            for v in spec["sha256"].values()
        ):
            raise ValueError("model manifest")
        actual = (
            subprocess.run(
                ["tesseract", "--version"],
                capture_output=True,
                timeout=2,
                check=True,
                env={"PATH": os.defpath},
            )
            .stdout.decode()
            .splitlines()[0]
        )
        if actual != "tesseract 5.3.0":
            raise ValueError("engine version mismatch")
        for name, expected in spec["sha256"].items():
            if (
                hashlib.sha256((directory / name).read_bytes()).hexdigest()
                != expected
            ):
                raise ValueError("model mismatch")
        return {
            "name": "tesseract",
            "version": "5.3.0",
            "model_id": "tessdata_fast/4.1.0:jpn+eng",
            "confidence_kind": "engine_score_not_probability",
            "reading_order": "engine_order",
        }
    except Exception:
        raise Failure(503, "OCR_UNAVAILABLE") from None


def tesseract(
    image: Image.Image, work: Path, model_dir: Path, timeout: float
) -> list[dict[str, Any]]:
    source, target = work / "input.png", work / "result.tsv"
    image.save(source, format="PNG")
    # No shell, stdin, URL, orientation detection, external OCR or model fetching.
    with target.open("wb") as output:
        try:
            done = subprocess.run(
                [
                    "tesseract",
                    str(source),
                    "stdout",
                    "--tessdata-dir",
                    str(model_dir),
                    "-l",
                    "jpn+eng",
                    "--oem",
                    "1",
                    "--psm",
                    "6",
                    "-c",
                    "tessedit_create_tsv=1",
                ],
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.DEVNULL,
                timeout=timeout,
                check=False,
                env={
                    "PATH": os.defpath,
                    "OMP_THREAD_LIMIT": "1",
                    "HOME": str(work),
                },
            )
        except subprocess.TimeoutExpired:
            raise Failure(504, "OCR_TIMEOUT") from None
        except FileNotFoundError:
            raise Failure(503, "OCR_UNAVAILABLE") from None
    if done.returncode != 0:
        raise Failure(502, "OCR_FAILED")
    if target.stat().st_size > 8 * 1024**2:
        raise Failure(502, "OCR_FAILED")
    return parse_tsv(target)


def parse_tsv(target: Path) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    try:
        with target.open(encoding="utf-8") as output:
            reader = csv.DictReader(
                output, delimiter="\t", quoting=csv.QUOTE_NONE
            )
            if reader.fieldnames != [
                "level",
                "page_num",
                "block_num",
                "par_num",
                "line_num",
                "word_num",
                "left",
                "top",
                "width",
                "height",
                "conf",
                "text",
            ]:
                raise ValueError("TSV header")
            for row in reader:
                if set(row) != set(reader.fieldnames) or any(
                    v is None for v in row.values()
                ):
                    raise ValueError("TSV row")
                level = int(row["level"])
                if not 1 <= level <= 5:
                    raise ValueError("TSV level")
                if level != 5:
                    continue
                x, y, w, h = (
                    int(row[key]) for key in ("left", "top", "width", "height")
                )
                confidence = float(row["conf"])
                if (
                    x < 0
                    or y < 0
                    or w <= 0
                    or h <= 0
                    or not math.isfinite(confidence)
                    or not -1 <= confidence <= 100
                ):
                    raise ValueError("TSV geometry or score")
                blocks.append(
                    {
                        "text": row["text"],
                        "polygon": [
                            (x, y),
                            (x + w, y),
                            (x + w, y + h),
                            (x, y + h),
                        ],
                        "confidence": (
                            confidence / 100 if confidence >= 0 else None
                        ),
                    }
                )
        return blocks
    except Exception:
        raise Failure(502, "OCR_FAILED") from None


def worker(
    connection: Any,
    work: str,
    operation: str,
    data: bytes,
    mime: str,
    region: list[float],
    scale: float,
    limits: Limits,
    models: str,
) -> None:
    try:
        import resource

        os.setsid()
        resource.setrlimit(
            resource.RLIMIT_AS, (1536 * 1024**2, 1536 * 1024**2)
        )
        fsize = max(limits.source_pixels, limits.output_pixels) * 4 + 1024**2
        resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (int(limits.request_seconds) + 1, int(limits.request_seconds) + 1),
        )
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
        blocks = tesseract(
            crop(original, spec), Path(work), Path(models), limits.ocr_seconds
        )
        # Only a small completed-file receipt crosses the Pipe. Waiting on a
        # partially written large Pipe frame must never bypass the deadline.
        if operation == "register":
            (Path(work) / "original.png").write_bytes(original)
        metadata = json.dumps(
            {
                "geometry": spec,
                "blocks": blocks,
                "original_sha256": (
                    hashlib.sha256(original).hexdigest()
                    if operation == "register"
                    else None
                ),
            },
            ensure_ascii=False,
        ).encode()
        if len(metadata) > 16 * 1024**2:
            raise Failure(502, "OCR_FAILED")
        (Path(work) / "result.json").write_bytes(metadata)
        connection.send((True, None))

    except Failure as exc:
        connection.send((False, (exc.status, exc.code, exc.details)))
    except Exception:
        connection.send((False, (502, "OCR_FAILED", {})))
    finally:
        connection.close()


def run(
    operation: str,
    data: bytes,
    mime: str,
    region: list[float],
    scale: float,
    limits: Limits,
    models: Path,
    deadline: float,
    *,
    target: Any = worker,
) -> dict[str, Any]:
    context = multiprocessing.get_context("spawn")
    parent, child = context.Pipe(duplex=False)
    with tempfile.TemporaryDirectory(prefix="read-region-") as temporary:
        process = context.Process(
            target=target,
            args=(
                child,
                temporary,
                operation,
                data,
                mime,
                region,
                scale,
                limits,
                str(models),
            ),
            daemon=False,
        )
        process.start()
        child.close()
        try:
            if not parent.poll(max(0, deadline - time.monotonic())):
                raise Failure(504, "OCR_TIMEOUT")
            try:
                success, value = parent.recv()
            except EOFError:
                raise Failure(502, "OCR_FAILED") from None
            if not success:
                raise Failure(*value[:2], **value[2])
            try:
                metadata_file = Path(temporary) / "result.json"
                if metadata_file.stat().st_size > 16 * 1024**2:
                    raise Failure(502, "OCR_FAILED")
                value = json.loads(metadata_file.read_bytes())
                if (
                    not isinstance(value, dict)
                    or set(value) != {"geometry", "blocks", "original_sha256"}
                    or not isinstance(value["geometry"], dict)
                    or not isinstance(value["blocks"], list)
                ):
                    raise Failure(502, "OCR_FAILED")
                expected_digest = value.pop("original_sha256")
                value["original"] = None
                if operation == "register":
                    source = Path(temporary) / "original.png"
                    if (
                        source.stat().st_size
                        > limits.source_pixels * 4 + 1024**2
                    ):
                        raise Failure(413, "INPUT_TOO_LARGE")
                    value["original"] = source.read_bytes()
                    if (
                        hashlib.sha256(value["original"]).hexdigest()
                        != expected_digest
                    ):
                        raise Failure(502, "OCR_FAILED")
            except (OSError, ValueError, KeyError, TypeError):
                raise Failure(502, "OCR_FAILED") from None
            if time.monotonic() >= deadline:
                raise Failure(504, "OCR_TIMEOUT")
            return value
        finally:
            # Kill the complete process group, including native OCR descendants.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                if process.is_alive():
                    process.kill()
            process.join(timeout=2)
            parent.close()
