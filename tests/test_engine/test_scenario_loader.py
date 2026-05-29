"""Tests for scenario loader and credential stuffing scenario."""

from datetime import UTC, datetime
from random import Random

from synthlog.clock import VirtualClock
from synthlog.engine.scenario_loader import ScenarioLoader
from synthlog.entities import EntityFactory
from synthlog.schema import OutcomeResult


class TestScenarioLoader:
    def test_load_builtin_credential_stuffing(self) -> None:
        scenario = ScenarioLoader.load_builtin("credential_stuffing")
        assert scenario.name == "credential_stuffing"

    def test_load_builtin_mfa_fatigue(self) -> None:
        scenario = ScenarioLoader.load_builtin("mfa_fatigue")
        assert scenario.name == "mfa_fatigue"

    def test_list_builtin(self) -> None:
        names = ScenarioLoader.list_builtin()
        assert "credential_stuffing" in names
        assert "mfa_fatigue" in names

    def test_credential_stuffing_generates_events(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5, num_apps=3)
        clock = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=8,
        )
        scenario = ScenarioLoader.load_builtin("credential_stuffing")
        events = list(scenario.generate(pool, clock, Random(42)))
        assert len(events) > 0

    def test_credential_stuffing_has_failures_then_success(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5, num_apps=3)
        clock = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=8,
        )
        scenario = ScenarioLoader.load_builtin("credential_stuffing")
        events = list(scenario.generate(pool, clock, Random(42)))

        outcomes = [e.outcome.result for e in events]
        # Should have failures followed by successes
        failure_count = sum(1 for o in outcomes if o == OutcomeResult.FAILURE)
        success_count = sum(1 for o in outcomes if o == OutcomeResult.SUCCESS)
        assert failure_count >= 3  # at least some failures
        assert success_count >= 1  # attacker eventually succeeds

    def test_credential_stuffing_uses_single_attacker_ip(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5, num_apps=3)
        clock = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=8,
        )
        scenario = ScenarioLoader.load_builtin("credential_stuffing")
        events = list(scenario.generate(pool, clock, Random(42)))

        ips = {e.client.ip_address for e in events}
        assert len(ips) == 1  # all from one attacker IP

    def test_credential_stuffing_deterministic(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5, num_apps=3)
        clock1 = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=8,
        )
        clock2 = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=8,
        )
        scenario = ScenarioLoader.load_builtin("credential_stuffing")

        events1 = list(scenario.generate(pool, clock1, Random(42)))
        events2 = list(scenario.generate(pool, clock2, Random(42)))

        assert len(events1) == len(events2)
        for e1, e2 in zip(events1, events2):
            assert e1.uuid == e2.uuid

    def test_mfa_fatigue_has_many_failures(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5, num_apps=3)
        clock = VirtualClock.for_duration(
            start=datetime(2025, 1, 6, 8, 0, tzinfo=UTC),
            duration_hours=8,
        )
        scenario = ScenarioLoader.load_builtin("mfa_fatigue")
        events = list(scenario.generate(pool, clock, Random(42)))

        mfa_failures = [
            e for e in events
            if e.event_type == "user.authentication.auth_via_mfa"
            and e.outcome.result == OutcomeResult.FAILURE
        ]
        assert len(mfa_failures) >= 10  # push_count is 15 in the YAML
