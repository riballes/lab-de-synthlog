"""EventScheduler — merges multiple scenario outputs by timestamp."""

from __future__ import annotations

import heapq
from collections.abc import Iterator
from random import Random

from synthlog.clock import VirtualClock
from synthlog.engine.protocols import Emitter, Scenario
from synthlog.entities.pool import EntityPool
from synthlog.schema.log_event import LogEvent


class EventScheduler:
    def __init__(
        self,
        scenarios: list[Scenario],
        pool: EntityPool,
        clock: VirtualClock,
        rng: Random,
    ) -> None:
        self._scenarios = scenarios
        self._pool = pool
        self._clock = clock
        self._rng = rng

    def _merged_events(self) -> Iterator[LogEvent]:
        iterators: list[Iterator[LogEvent]] = []
        for scenario in self._scenarios:
            child_rng = Random(self._rng.randint(0, 2**63))
            iterators.append(scenario.generate(self._pool, self._clock, child_rng))

        yield from heapq.merge(
            *iterators,
            key=lambda e: e.published,
        )

    def run(self, emitter: Emitter) -> int:
        count = 0
        for event in self._merged_events():
            emitter.emit(event)
            count += 1
        emitter.flush()
        return count
