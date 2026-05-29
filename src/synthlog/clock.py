"""Virtual time model for simulation."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass
class VirtualClock:
    start: datetime
    end: datetime
    speed: float = 1.0
    _current: datetime = field(init=False)

    def __post_init__(self) -> None:
        self._current = self.start

    @property
    def now(self) -> datetime:
        return self._current

    def advance(self, delta: timedelta) -> None:
        self._current = min(self._current + delta, self.end)

    def is_finished(self) -> bool:
        return self._current >= self.end

    def is_business_hours(self, hour: int | None = None) -> bool:
        h = hour if hour is not None else self._current.hour
        return 8 <= h < 18

    def is_peak_hours(self, hour: int | None = None) -> bool:
        h = hour if hour is not None else self._current.hour
        return (9 <= h < 11) or (14 <= h < 16)

    def is_weekend(self) -> bool:
        return self._current.weekday() >= 5

    def tick_range(self, interval: timedelta) -> Iterator[datetime]:
        t = self.start
        while t < self.end:
            yield t
            t += interval

    @classmethod
    def for_duration(
        cls,
        start: datetime | None = None,
        duration_hours: int = 8,
        speed: float = 1.0,
    ) -> VirtualClock:
        if start is None:
            start = datetime(2025, 1, 6, 8, 0, tzinfo=UTC)
        end = start + timedelta(hours=duration_hours)
        return cls(start=start, end=end, speed=speed)
