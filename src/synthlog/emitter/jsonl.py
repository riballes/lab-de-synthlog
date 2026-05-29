"""JSONL file emitter — one JSON object per line, using orjson for speed."""

from __future__ import annotations

from pathlib import Path
from typing import IO

import orjson

from synthlog.schema.log_event import LogEvent


class JSONLEmitter:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._file: IO[bytes] = open(self._path, "wb")

    def emit(self, event: LogEvent) -> None:
        data = event.model_dump(by_alias=True, mode="json")
        self._file.write(orjson.dumps(data))
        self._file.write(b"\n")

    def flush(self) -> None:
        self._file.flush()

    def close(self) -> None:
        self._file.flush()
        self._file.close()
