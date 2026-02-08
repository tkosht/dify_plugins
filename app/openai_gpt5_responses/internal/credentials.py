from __future__ import annotations


def normalize_api_base(value: object) -> str:
    raw = str(value or "").strip().rstrip("/")
    if not raw:
        return ""

    if raw.endswith("/v1"):
        return raw

    return f"{raw}/v1"
