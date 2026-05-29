"""Tests for EventBuilder."""

from datetime import UTC, datetime
from random import Random

from synthlog.engine.event_builder import EventBuilder
from synthlog.entities import EntityFactory
from synthlog.schema import LogSeverity, OutcomeResult


def _setup():  # type: ignore[no-untyped-def]
    pool = EntityFactory(seed=42).create_pool(num_users=5, num_apps=3)
    rng = Random(42)
    builder = EventBuilder(rng)
    return pool, builder


class TestEventBuilder:
    def test_basic_session_start(self) -> None:
        pool, builder = _setup()
        user = pool.users[0]
        net = pool.get_network(user.primary_network_id)
        dev = pool.get_device(user.primary_device_id)
        ts = datetime(2025, 1, 6, 9, 0, 0, tzinfo=UTC)

        event = builder.build(
            "user.session.start", ts, user,
            network=net, device=dev,
        )

        assert event.event_type == "user.session.start"
        assert event.actor.id == user.id
        assert event.actor.alternate_id == user.login
        assert event.published == ts
        assert event.severity == LogSeverity.INFO
        assert event.display_message == "User login to Okta"
        assert event.outcome.result == OutcomeResult.SUCCESS

    def test_failed_session_start(self) -> None:
        pool, builder = _setup()
        user = pool.users[0]
        ts = datetime(2025, 1, 6, 9, 5, 0, tzinfo=UTC)

        event = builder.build(
            "user.session.start", ts, user,
            outcome_result=OutcomeResult.FAILURE,
            outcome_reason="INVALID_CREDENTIALS",
        )

        assert event.outcome.result == OutcomeResult.FAILURE
        assert event.outcome.reason == "INVALID_CREDENTIALS"

    def test_sso_with_app_target(self) -> None:
        pool, builder = _setup()
        user = pool.users[0]
        app = pool.apps[0]
        ts = datetime(2025, 1, 6, 9, 10, 0, tzinfo=UTC)

        event = builder.build(
            "user.authentication.sso", ts, user,
            targets=[app],
        )

        assert event.event_type == "user.authentication.sso"
        assert len(event.target) == 1
        assert event.target[0].id == app.id
        assert event.target[0].type == "AppInstance"

    def test_client_has_geo_when_network_provided(self) -> None:
        pool, builder = _setup()
        user = pool.users[0]
        net = pool.get_network(user.primary_network_id)
        ts = datetime(2025, 1, 6, 9, 0, 0, tzinfo=UTC)

        event = builder.build("user.session.start", ts, user, network=net)

        assert event.client.ip_address == net.ip_address
        geo = event.client.geographical_context
        assert geo is not None
        assert geo.city == net.city

    def test_security_context_from_network(self) -> None:
        pool, builder = _setup()
        user = pool.users[0]
        net = pool.get_network(user.primary_network_id)
        ts = datetime(2025, 1, 6, 9, 0, 0, tzinfo=UTC)

        event = builder.build("user.session.start", ts, user, network=net)

        assert event.security_context.as_number == net.as_number
        assert event.security_context.isp == net.isp

    def test_uuid_is_generated(self) -> None:
        pool, builder = _setup()
        user = pool.users[0]
        ts = datetime(2025, 1, 6, 9, 0, 0, tzinfo=UTC)

        event1 = builder.build("user.session.start", ts, user)
        event2 = builder.build("user.session.start", ts, user)
        assert event1.uuid != event2.uuid

    def test_deterministic_with_same_seed(self) -> None:
        pool = EntityFactory(seed=42).create_pool(num_users=5)
        user = pool.users[0]
        ts = datetime(2025, 1, 6, 9, 0, 0, tzinfo=UTC)

        b1 = EventBuilder(Random(99))
        b2 = EventBuilder(Random(99))

        e1 = b1.build("user.session.start", ts, user)
        e2 = b2.build("user.session.start", ts, user)
        assert e1.uuid == e2.uuid
        assert e1.transaction.id == e2.transaction.id

    def test_account_lock_severity(self) -> None:
        pool, builder = _setup()
        user = pool.users[0]
        ts = datetime(2025, 1, 6, 9, 0, 0, tzinfo=UTC)

        event = builder.build("user.account.lock", ts, user, targets=[user])

        assert event.severity == LogSeverity.WARN

    def test_serializes_to_valid_json(self) -> None:
        pool, builder = _setup()
        user = pool.users[0]
        net = pool.get_network(user.primary_network_id)
        dev = pool.get_device(user.primary_device_id)
        ts = datetime(2025, 1, 6, 9, 0, 0, tzinfo=UTC)

        event = builder.build(
            "user.session.start", ts, user,
            network=net, device=dev, targets=[user],
        )

        data = event.model_dump(by_alias=True)
        assert data["eventType"] == "user.session.start"
        assert data["actor"]["id"] == user.id
        assert data["securityContext"]["asNumber"] == net.as_number
        assert len(data["request"]["ipChain"]) == 1
