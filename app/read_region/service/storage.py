"""Single-owner, bounded image RAM + durable content-free execution tombstones."""

from __future__ import annotations

import fcntl
import hashlib
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from service.core import Failure, Limits


class Store:
    def __init__(
        self,
        directory: Path,
        limits: Limits,
        clock: Callable[[], float] = time.time,
    ) -> None:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.lock_file = (directory / "owner.lock").open("a+")
        try:
            fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock_file.close()
            raise RuntimeError(
                "exactly one service owner is required"
            ) from None
        self.db = sqlite3.connect(
            directory / "executions.sqlite", check_same_thread=False
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS runs (key TEXT PRIMARY KEY, expires REAL NOT NULL, revoked INTEGER NOT NULL, calls INTEGER NOT NULL, images INTEGER NOT NULL, pixels INTEGER NOT NULL)"
        )
        # Restart never reopens a previous context or resets its budget/TTL.
        self.db.execute("UPDATE runs SET revoked=1")
        self.db.commit()
        self.limits, self.clock = limits, clock
        self.lock = threading.RLock()
        self.images: dict[tuple[str, str], dict[str, Any]] = {}

    @staticmethod
    def key(scope: str, execution: str) -> str:
        return hashlib.sha256(
            (scope + "\x00" + execution).encode()
        ).hexdigest()

    def _row(self, key: str) -> tuple[Any, ...] | None:
        return self.db.execute(
            "SELECT expires,revoked,calls,images,pixels FROM runs WHERE key=?",
            (key,),
        ).fetchone()

    def _active(self, key: str) -> tuple[Any, ...]:
        row = self._row(key)
        if row is None or row[1] or row[0] <= self.clock():
            raise Failure(404, "IMAGE_NOT_AVAILABLE")
        return row

    def begin(self, key: str) -> float:
        with self.lock:
            self.sweep()
            if self._row(key) is None:
                if (
                    self.db.execute("SELECT count(*) FROM runs").fetchone()[0]
                    >= self.limits.ledger_entries
                ):
                    raise Failure(429, "BUSY")
                self.db.execute(
                    "INSERT INTO runs VALUES(?,?,0,0,0,0)",
                    (key, self.clock() + self.limits.ttl_seconds),
                )
                self.db.commit()
            row = self._active(key)
            if row[3] >= self.limits.execution_images:
                raise Failure(429, "BUDGET_EXCEEDED")
            return row[0]

    def put(
        self, key: str, data: bytes, spec: dict[str, Any], page: int | None
    ) -> str:
        with self.lock:
            row = self._active(key)
            size = spec["source_size"]
            pixels = size["width"] * size["height"]
            global_pixels = sum(i["pixels"] for i in self.images.values())
            if (
                row[3] >= self.limits.execution_images
                or row[4] + pixels > self.limits.execution_pixels
                or global_pixels + pixels > self.limits.global_pixels
            ):
                raise Failure(429, "BUDGET_EXCEEDED")
            image_id = "img_" + uuid.uuid4().hex
            self.images[key, image_id] = {
                "original": data,
                "page": page,
                "pixels": pixels,
            }
            self.db.execute(
                "UPDATE runs SET images=images+1,pixels=pixels+? WHERE key=?",
                (pixels, key),
            )
            self.db.commit()
            return image_id

    def read(self, key: str, image_id: str) -> dict[str, Any]:
        with self.lock:
            row = self._active(key)
            image = self.images.get((key, image_id))
            if image is None:
                raise Failure(404, "IMAGE_NOT_AVAILABLE")
            if row[2] >= self.limits.calls:
                raise Failure(429, "BUDGET_EXCEEDED")
            self.db.execute(
                "UPDATE runs SET calls=calls+1 WHERE key=?", (key,)
            )
            self.db.commit()
            return image.copy()

    def authorize(self, key: str, image_id: str) -> None:
        with self.lock:
            self._active(key)
            if (key, image_id) not in self.images:
                raise Failure(404, "IMAGE_NOT_AVAILABLE")

    def delete(self, key: str) -> int:
        with self.lock:
            if self._row(key) is None:
                self.begin(key)
            self.db.execute("UPDATE runs SET revoked=1 WHERE key=?", (key,))
            self.db.commit()
            selected = [pair for pair in self.images if pair[0] == key]
            for pair in selected:
                del self.images[pair]
            return len(selected)

    def sweep(self) -> None:
        with self.lock:
            expired = [
                r[0]
                for r in self.db.execute(
                    "SELECT key FROM runs WHERE revoked=0 AND expires<=?",
                    (self.clock(),),
                )
            ]
            for key in expired:
                self.delete(key)

    def close(self) -> None:
        with self.lock:
            self.images.clear()
            self.db.close()
            self.lock_file.close()
