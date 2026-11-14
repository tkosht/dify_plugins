"""Run with one Uvicorn worker and access/error trace logging disabled."""

import json
import os
from pathlib import Path

from service.api import create_app


def app_factory():
    path = Path(os.environ["READ_REGION_CREDENTIALS_FILE"])
    tokens = json.loads(path.read_text())
    return create_app(
        Path(os.environ.get("READ_REGION_STATE_DIR", "/state")),
        Path(os.environ.get("READ_REGION_MODEL_DIR", "/models")),
        Path(__file__).resolve().parents[1] / "models.lock.json",
        tokens,
    )
