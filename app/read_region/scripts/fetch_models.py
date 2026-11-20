"""Build-time only: fetch reviewed, hash-locked upstream OCR data."""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
lock = json.loads((root / "models.lock.json").read_text())
target = Path(sys.argv[1])
target.mkdir(parents=True, exist_ok=True)
for name, expected in lock["sha256"].items():
    data = urllib.request.urlopen(
        f'{lock["source"]}/{lock["commit"]}/{name}', timeout=60
    ).read()
    if hashlib.sha256(data).hexdigest() != expected:
        raise SystemExit("OCR model integrity failure")
    (target / name).write_bytes(data)
print("Verified local OCR models:", ", ".join(lock["sha256"]))
