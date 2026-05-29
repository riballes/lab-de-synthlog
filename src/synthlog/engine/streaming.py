"""StreamingScheduler — emits events paced to match simulated timestamps."""

from __future__ import annotations

import asyncio
import heapq
from collections.abc import Callable, Iterator
from random import Random

from synthlog.clock import VirtualClock
from synthlog.engine.protocols import Emitter, Scenario
from synthlog.entities.pool import EntityPool
from synthlog.schema.log_event import LogEvent


class StreamingScheduler:
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
        self._stop_event = asyncio.Event()

    def stop(self) -> None:
        self._stop_event.set()

    @property
    def is_stopped(self) -> bool:
        return self._stop_event.is_set()

    def _merged_events(self) -> Iterator[LogEvent]:
        iterators: list[Iterator[LogEvent]] = []
        for scenario in self._scenarios:
            child_rng = Random(self._rng.randint(0, 2**63))
            iterators.append(
                scenario.generate(self._pool, self._clock, child_rng)
            )
        yield from heapq.merge(*iterators, key=lambda e: e.published)

    async def run(
        self,
        emitter: Emitter | None = None,
        on_event: Callable[[LogEvent], None] | None = None,
    ) -> int:
        count = 0
        prev_published = None

        for event in self._merged_events():
            if self._stop_event.is_set():
                break

            if prev_published is not None:
                delta = (event.published - prev_published).total_seconds()
                wall_delay = delta / self._clock.speed if self._clock.speed > 0 else 0
                if wall_delay > 0:
                    try:
                        await asyncio.wait_for(
                            self._stop_event.wait(), timeout=wall_delay
                        )
                        break  # stop was signaled during sleep
                    except TimeoutError:
                        pass  # normal: sleep completed without stop

            if emitter is not None:
                emitter.emit(event)
            if on_event is not None:
                on_event(event)
            count += 1
            prev_published = event.published

        if emitter is not None:
            emitter.flush()
        return count

    def run_sync(
        self,
        emitter: Emitter | None = None,
        on_event: Callable[[LogEvent], None] | None = None,
    ) -> int:
        """Blocking synchronous version for CLI use."""
        import time

        count = 0
        prev_published = None

        for event in self._merged_events():
            if prev_published is not None:
                delta = (event.published - prev_published).total_seconds()
                wall_delay = delta / self._clock.speed if self._clock.speed > 0 else 0
                if wall_delay > 0:
                    time.sleep(wall_delay)

            if emitter is not None:
                emitter.emit(event)
            if on_event is not None:
                on_event(event)
            count += 1
            prev_published = event.published

        if emitter is not None:
            emitter.flush()
        return count
