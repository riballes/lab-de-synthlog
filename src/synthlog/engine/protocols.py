"""Protocol definitions for the engine layer."""

from __future__ import annotations

from collections.abc import Iterator
from random import Random
from typing import Protocol

from synthlog.clock import VirtualClock
from synthlog.entities.pool import EntityPool
from synthlog.schema.log_event import LogEvent


class Scenario(Protocol):
    @property
    def name(self) -> str: ...

    def generate(
        self, pool: EntityPool, clock: VirtualClock, rng: Random
    ) -> Iterator[LogEvent]: ...


class Emitter(Protocol):
    def emit(self, event: LogEvent) -> None: ...
    def flush(self) -> None: ...
    def close(self) -> None: ...
