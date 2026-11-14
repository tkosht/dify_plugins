"""Synthetic-only local OCR comparison; no Dify or Agent success is implied."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

from service.core import Failure, Limits, response
from service.ocr import check_models, run


def distance(a: str, b: str) -> int:
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        next_row = [i]
        for j, y in enumerate(b, 1):
            next_row.append(
                min(next_row[-1] + 1, row[j] + 1, row[j - 1] + (x != y))
            )
        row = next_row
    return row[-1]


def main() -> None:
    data = Path(sys.argv[1]).read_bytes()
    truth = json.loads(Path(sys.argv[2]).read_text())
    limits = Limits()
    engine = check_models(Path("/models"), Path("/app/models.lock.json"))
    results = {}
    original = data
    for name, operation, region, scale in [
        ("B1_local_overview", "register", [0, 0, 1, 1], 1),
        ("region_manual_proxy", "read", truth["region"], 2),
    ]:
        start = time.monotonic()
        raw = run(
            operation,
            original,
            "image/png",
            region,
            scale,
            limits,
            Path("/models"),
            start + limits.request_seconds,
        )
        if operation == "register":
            original = raw["original"]
        result = response(
            "img_" + "a" * 32,
            1,
            raw["geometry"],
            raw["blocks"],
            engine,
            "req_" + "b" * 32,
            limits,
        )
        # Strict text comparison; do not erase punctuation, signs, units or spaces.
        predicted = result["text"]
        expected = truth["text"]
        results[name] = {
            "seconds": time.monotonic() - start,
            "ocr_calls": 1,
            "text": predicted,
            "expected": expected,
            "edit_distance": distance(expected, predicted),
            "cer_strict": distance(expected, predicted) / len(expected),
            "important_numeric_exact": truth["numeric"] in predicted,
            "status": result["status"],
            "geometry": result["geometry"],
        }
    missing = False
    try:
        check_models(Path("/missing-models"), Path("/app/models.lock.json"))
    except Failure as exc:
        missing = exc.code == "OCR_UNAVAILABLE"
    print(
        json.dumps(
            {
                "scope": "one synthetic input, manually selected region; no Agent/Dify; B0 and full T not performed",
                "fixture_sha256": hashlib.sha256(data).hexdigest(),
                "engine": engine,
                "network": "Docker --network none; kernel isolated; native connection attempts not traced",
                "missing_models_fail_closed": missing,
                "results": results,
                "representative_quality_accepted": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
