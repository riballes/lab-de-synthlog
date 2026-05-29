"""Tests for StreamingScheduler."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from random import Random

import pytest

from synthlog.clock import VirtualClock
from synthlog.engine.baseline import BaselineTraffic
from synthlog.engine.streaming import StreamingScheduler
from synthlog.entities import EntityFactory
from synthlog.schema.log_event import LogEvent


class TestStreamingScheduler:
    @pytest.mark.asyncio
    async def test_produces_events(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=3)
        clock = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 9, 0, tzinfo=UTC),
            duration_hours=1,
            speed=99999.0,  # very fast for testing
        )
        scheduler = StreamingScheduler([BaselineTraffic()], pool, clock, Random(42))

        events: list[LogEvent] = []
        count = await scheduler.run(on_event=lambda e: events.append(e))
        assert count > 0
        assert len(events) == count

    @pytest.mark.asyncio
    async def test_stop_signal(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5)
        clock = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=8,
            speed=100.0,
        )
        scheduler = StreamingScheduler(
            [BaselineTraffic()], pool, clock, Random(42)
        )

        events: list[LogEvent] = []

        async def stop_after_delay() -> None:
            await asyncio.sleep(0.3)
            scheduler.stop()

        task = asyncio.create_task(stop_after_delay())
        count = await scheduler.run(on_event=lambda e: events.append(e))
        await task

        assert scheduler.is_stopped
        assert count >= 1  # should have emitted at least some events

    @pytest.mark.asyncio
    async def test_deterministic(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=3)

        events1: list[LogEvent] = []
        events2: list[LogEvent] = []

        for events in [events1, events2]:
            clock = VirtualClock.for_duration(
                start=datetime(2025, 1, 6, 9, 0, tzinfo=UTC),
                duration_hours=1,
                speed=99999.0,
            )
            scheduler = StreamingScheduler(
                [BaselineTraffic()], pool, clock, Random(42)
            )
            await scheduler.run(on_event=lambda e: events.append(e))

        assert len(events1) == len(events2)
        for e1, e2 in zip(events1, events2):
            assert e1.uuid == e2.uuid

    def test_sync_produces_events(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=3)
        clock = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 9, 0, tzinfo=UTC),
            duration_hours=1,
            speed=99999.0,
        )
        scheduler = StreamingScheduler(
            [BaselineTraffic()], pool, clock, Random(42)
        )

        events: list[LogEvent] = []
        count = scheduler.run_sync(on_event=lambda e: events.append(e))
        assert count > 0
        assert len(events) == count
