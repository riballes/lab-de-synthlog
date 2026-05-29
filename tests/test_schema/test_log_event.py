"""Tests for LogEvent schema serialization and field names."""

from datetime import UTC, datetime

from synthlog.schema import (
    LogActor,
    LogAuthenticationContext,
    LogClient,
    LogDebugContext,
    LogEvent,
    LogGeographicalContext,
    LogGeolocation,
    LogOutcome,
    LogSecurityContext,
    LogSeverity,
    LogTarget,
    LogTransaction,
    LogUserAgent,
    OutcomeResult,
    TransactionType,
)


def _make_full_event() -> LogEvent:
    return LogEvent(
        uuid="evt-test-001",
        published=datetime(2025, 1, 6, 9, 15, 30, tzinfo=UTC),
        event_type="user.session.start",
        version="0",
        severity=LogSeverity.INFO,
        display_message="User login to Okta",
        actor=LogActor(
            id="00u1234567890ABCDEF",
            type="User",
            alternate_id="alice@example.com",
            display_name="Alice Johnson",
        ),
        client=LogClient(
            ip_address="203.0.113.42",
            user_agent=LogUserAgent(
                raw_user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                os="Mac OS X",
                browser="Chrome",
            ),
            zone="null",
            device="Computer",
            geographical_context=LogGeographicalContext(
                city="San Francisco",
                state="California",
                country="United States",
                postal_code="94105",
                geolocation=LogGeolocation(lat=37.7749, lon=-122.4194),
            ),
        ),
        outcome=LogOutcome(result=OutcomeResult.SUCCESS),
        target=[
            LogTarget(
                id="00u1234567890ABCDEF",
                type="User",
                alternate_id="alice@example.com",
                display_name="Alice Johnson",
            ),
        ],
        transaction=LogTransaction(id="txn-abc-123", type=TransactionType.WEB),
        authentication_context=LogAuthenticationContext(
            external_session_id="idx-session-001",
        ),
        security_context=LogSecurityContext(
            as_number=15169,
            as_org="Google LLC",
            isp="Google",
            domain="google.com",
            is_proxy=False,
        ),
        debug_context=LogDebugContext(
            debug_data={"requestUri": "/api/v1/authn"},
        ),
    )


class TestLogEventSerialization:
    def test_camel_case_top_level_keys(self) -> None:
        event = _make_full_event()
        data = event.model_dump(by_alias=True)

        expected_keys = {
            "uuid", "published", "eventType", "version", "severity",
            "displayMessage", "legacyEventType", "actor", "client",
            "request", "outcome", "target", "transaction",
            "debugContext", "authenticationContext", "securityContext",
        }
        assert set(data.keys()) == expected_keys

    def test_actor_camel_case(self) -> None:
        event = _make_full_event()
        data = event.model_dump(by_alias=True)
        actor = data["actor"]
        assert "alternateId" in actor
        assert "displayName" in actor
        assert actor["alternateId"] == "alice@example.com"

    def test_client_camel_case(self) -> None:
        event = _make_full_event()
        data = event.model_dump(by_alias=True)
        client = data["client"]
        assert "ipAddress" in client
        assert "userAgent" in client
        assert "geographicalContext" in client
        ua = client["userAgent"]
        assert "rawUserAgent" in ua
        geo = client["geographicalContext"]
        assert "postalCode" in geo

    def test_outcome_values(self) -> None:
        event = _make_full_event()
        data = event.model_dump(by_alias=True)
        assert data["outcome"]["result"] == "SUCCESS"

    def test_authentication_context_camel_case(self) -> None:
        event = _make_full_event()
        data = event.model_dump(by_alias=True)
        auth = data["authenticationContext"]
        assert "externalSessionId" in auth
        assert "authenticationProvider" in auth
        assert "credentialType" in auth

    def test_security_context_camel_case(self) -> None:
        event = _make_full_event()
        data = event.model_dump(by_alias=True)
        sec = data["securityContext"]
        assert "asNumber" in sec
        assert "asOrg" in sec
        assert "isProxy" in sec
        assert sec["asNumber"] == 15169

    def test_debug_context_camel_case(self) -> None:
        event = _make_full_event()
        data = event.model_dump(by_alias=True)
        assert "debugData" in data["debugContext"]

    def test_transaction_camel_case(self) -> None:
        event = _make_full_event()
        data = event.model_dump(by_alias=True)
        assert data["transaction"]["type"] == "WEB"

    def test_target_is_list(self) -> None:
        event = _make_full_event()
        data = event.model_dump(by_alias=True)
        assert isinstance(data["target"], list)
        assert len(data["target"]) == 1
        assert data["target"][0]["alternateId"] == "alice@example.com"

    def test_request_ip_chain(self) -> None:
        event = _make_full_event()
        data = event.model_dump(by_alias=True)
        assert "ipChain" in data["request"]
        assert isinstance(data["request"]["ipChain"], list)

    def test_roundtrip_json(self) -> None:
        event = _make_full_event()
        json_str = event.model_dump_json(by_alias=True)
        restored = LogEvent.model_validate_json(json_str)
        assert restored.uuid == event.uuid
        assert restored.event_type == event.event_type
        assert restored.actor.alternate_id == event.actor.alternate_id

    def test_event_type_string(self) -> None:
        event = _make_full_event()
        data = event.model_dump(by_alias=True)
        assert data["eventType"] == "user.session.start"

    def test_severity_string(self) -> None:
        event = _make_full_event()
        data = event.model_dump(by_alias=True)
        assert data["severity"] == "INFO"
