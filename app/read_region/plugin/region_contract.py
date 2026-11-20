"""Shared strict service/Agent input contract; no SDK or OCR dependencies."""

import math
from typing import Any


class Failure(Exception):
    def __init__(self, status: int, code: str, **details: Any) -> None:
        self.status, self.code, self.details = status, code, details
        super().__init__(code)


def number(value: Any, lower: float, upper: float) -> float:
    if type(value) not in (int, float):
        raise Failure(422, "INVALID_REGION")
    # Check bounded integer magnitude before float conversion/math.isfinite.
    if (
        value < lower
        or value > upper
        or (type(value) is float and not math.isfinite(value))
    ):
        raise Failure(422, "INVALID_REGION")
    if not lower <= value <= upper:
        raise Failure(422, "INVALID_REGION")
    return float(value)


def validate_read(data: Any, *, flat: bool = False) -> dict[str, Any]:
    import re

    keys = (
        {"image_id", "x_min", "y_min", "x_max", "y_max", "scale"}
        if flat
        else {"image_id", "region", "scale"}
    )
    required = keys - {"scale"}
    if (
        not isinstance(data, dict)
        or set(data) - keys
        or not required <= set(data)
    ):
        raise Failure(422, "INVALID_REQUEST")
    if not isinstance(data["image_id"], str) or not re.fullmatch(
        r"img_[0-9a-f]{32}", data["image_id"]
    ):
        raise Failure(422, "INVALID_REQUEST")
    region = (
        [data[k] for k in ("x_min", "y_min", "x_max", "y_max")]
        if flat
        else data["region"]
    )
    if not isinstance(region, list) or len(region) != 4:
        raise Failure(422, "INVALID_REGION")
    coords = [number(v, 0, 1) for v in region]
    if coords[0] >= coords[2] or coords[1] >= coords[3]:
        raise Failure(422, "INVALID_REGION")
    return {
        "image_id": data["image_id"],
        "region": coords,
        "scale": number(data.get("scale", 2.0), 0.25, 4),
    }
