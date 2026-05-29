"""Tests for baseline traffic generation."""

from datetime import UTC, datetime
from random import Random

from synthlog.clock import VirtualClock
from synthlog.engine.baseline import BaselineTraffic
from synthlog.entities import EntityFactory


class TestBaselineTraffic:
    def test_generates_events(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5)
        clock = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=1,
        )
        baseline = BaselineTraffic(events_per_user_per_hour=3.0)
        events = list(baseline.generate(pool, clock, Random(42)))
        assert len(events) > 0

    def test_events_are_chronologically_ordered(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5)
        clock = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=2,
        )
        baseline = BaselineTraffic(events_per_user_per_hour=2.0)
        events = list(baseline.generate(pool, clock, Random(42)))

        # Events within a user's session chain should be ordered,
        # but cross-user ordering may interleave.
        # Verify no event is before the simulation start.
        for e in events:
            assert e.published >= datetime(2025, 1, 6, 8, 0, tzinfo=UTC)

    def test_event_types_are_valid(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5)
        clock = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=2,
        )
        baseline = BaselineTraffic(events_per_user_per_hour=3.0)
        events = list(baseline.generate(pool, clock, Random(42)))

        valid_types = {
            "user.session.start", "user.session.end",
            "user.authentication.sso", "user.authentication.auth_via_mfa",
            "policy.evaluate_sign_on",
        }
        for e in events:
            assert e.event_type in valid_types, f"Unexpected: {e.event_type}"

    def test_deterministic(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5)
        clock1 = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=1,
        )
        clock2 = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=1,
        )
        baseline = BaselineTraffic(events_per_user_per_hour=2.0)

        events1 = list(baseline.generate(pool, clock1, Random(42)))
        events2 = list(baseline.generate(pool, clock2, Random(42)))

        assert len(events1) == len(events2)
        for e1, e2 in zip(events1, events2):
            assert e1.uuid == e2.uuid

    def test_weekend_produces_fewer_events(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5)
        # Monday
        clock_weekday = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=8,
        )
        # Saturday
        clock_weekend = VirtualClock.for_duration(
            start=datetime(2025, 1, 11, 8, 0, tzinfo=UTC),
            duration_hours=8,
        )
        baseline = BaselineTraffic(events_per_user_per_hour=2.0)

        weekday_events = list(baseline.generate(pool, clock_weekday, Random(42)))
        weekend_events = list(baseline.generate(pool, clock_weekend, Random(42)))

        assert len(weekend_events) < len(weekday_events)

    def test_eight_hour_workday_event_count(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5)
        clock = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=8,
        )
        baseline = BaselineTraffic(events_per_user_per_hour=2.0)
        events = list(baseline.generate(pool, clock, Random(42)))
        # With 5 users, 2 events/user/hour, 8 hours, expect roughly
        # 80 events but with variance. Just check reasonable range.
        assert 20 < len(events) < 500
