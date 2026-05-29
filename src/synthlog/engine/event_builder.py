"""Builds LogEvent instances from entity references and event type metadata."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from random import Random

from synthlog.entities.application import SyntheticApp
from synthlog.entities.device import SyntheticDevice
from synthlog.entities.group import SyntheticGroup
from synthlog.entities.network import SyntheticIP
from synthlog.entities.user import SyntheticUser
from synthlog.schema import (
    LogActor,
    LogAuthenticationContext,
    LogClient,
    LogDebugContext,
    LogEvent,
    LogGeographicalContext,
    LogGeolocation,
    LogOutcome,
    LogRequest,
    LogSecurityContext,
    LogSeverity,
    LogTarget,
    LogTransaction,
    LogUserAgent,
    OutcomeResult,
    TransactionType,
)


@dataclass(frozen=True)
class EventTypeMeta:
    event_type: str
    display_message: str
    severity: LogSeverity
    target_type: str | None = None


EVENT_TYPE_REGISTRY: dict[str, EventTypeMeta] = {
    "user.session.start": EventTypeMeta(
        event_type="user.session.start",
        display_message="User login to Okta",
        severity=LogSeverity.INFO,
        target_type="User",
    ),
    "user.session.end": EventTypeMeta(
        event_type="user.session.end",
        display_message="User logout from Okta",
        severity=LogSeverity.INFO,
        target_type="User",
    ),
    "user.authentication.sso": EventTypeMeta(
        event_type="user.authentication.sso",
        display_message="User single sign on to app",
        severity=LogSeverity.INFO,
        target_type="AppInstance",
    ),
    "user.authentication.auth_via_mfa": EventTypeMeta(
        event_type="user.authentication.auth_via_mfa",
        display_message="Authentication of user via MFA",
        severity=LogSeverity.INFO,
        target_type="User",
    ),
    "user.mfa.factor.activate": EventTypeMeta(
        event_type="user.mfa.factor.activate",
        display_message="User MFA factor activated",
        severity=LogSeverity.INFO,
        target_type="User",
    ),
    "policy.evaluate_sign_on": EventTypeMeta(
        event_type="policy.evaluate_sign_on",
        display_message="Evaluation of sign-on policy",
        severity=LogSeverity.INFO,
    ),
    "user.account.lock": EventTypeMeta(
        event_type="user.account.lock",
        display_message="User account locked",
        severity=LogSeverity.WARN,
        target_type="User",
    ),
    "application.user_membership.add": EventTypeMeta(
        event_type="application.user_membership.add",
        display_message="Add user to application membership",
        severity=LogSeverity.INFO,
        target_type="AppInstance",
    ),
    "group.user_membership.add": EventTypeMeta(
        event_type="group.user_membership.add",
        display_message="Add user to group membership",
        severity=LogSeverity.INFO,
        target_type="UserGroup",
    ),
    "user.lifecycle.activate": EventTypeMeta(
        event_type="user.lifecycle.activate",
        display_message="Activate Okta user",
        severity=LogSeverity.INFO,
        target_type="User",
    ),
}


class EventBuilder:
    def __init__(self, rng: Random) -> None:
        self._rng = rng

    def build(
        self,
        event_type: str,
        timestamp: datetime,
        actor: SyntheticUser,
        *,
        targets: list[SyntheticUser | SyntheticApp | SyntheticGroup] | None = None,
        outcome_result: OutcomeResult = OutcomeResult.SUCCESS,
        outcome_reason: str | None = None,
        network: SyntheticIP | None = None,
        device: SyntheticDevice | None = None,
        session_id: str | None = None,
        severity_override: LogSeverity | None = None,
        display_message_override: str | None = None,
    ) -> LogEvent:
        meta = EVENT_TYPE_REGISTRY.get(event_type)
        severity = severity_override or (meta.severity if meta else LogSeverity.INFO)
        display_message = display_message_override or (
            meta.display_message if meta else event_type
        )

        log_actor = LogActor(
            id=actor.id,
            type="User",
            alternate_id=actor.login,
            display_name=actor.display_name,
        )

        log_targets = []
        if targets:
            for t in targets:
                log_targets.append(self._build_target(t))

        log_client = self._build_client(network, device)
        log_security = self._build_security_context(network)
        log_request = self._build_request(network)

        txn_id = f"txn{uuid.UUID(int=self._rng.getrandbits(128)).hex[:16]}"
        sess_id = session_id or f"idx{uuid.UUID(int=self._rng.getrandbits(128)).hex[:20]}"

        return LogEvent(
            uuid=str(uuid.UUID(int=self._rng.getrandbits(128))),
            published=timestamp,
            event_type=event_type,
            version="0",
            severity=severity,
            display_message=display_message,
            actor=log_actor,
            client=log_client,
            request=log_request,
            outcome=LogOutcome(result=outcome_result, reason=outcome_reason),
            target=log_targets,
            transaction=LogTransaction(id=txn_id, type=TransactionType.WEB),
            authentication_context=LogAuthenticationContext(
                external_session_id=sess_id,
            ),
            security_context=log_security,
            debug_context=LogDebugContext(
                debug_data={"requestUri": "/api/v1/authn"},
            ),
        )

    def _build_target(
        self, entity: SyntheticUser | SyntheticApp | SyntheticGroup
    ) -> LogTarget:
        if isinstance(entity, SyntheticUser):
            return LogTarget(
                id=entity.id,
                type="User",
                alternate_id=entity.login,
                display_name=entity.display_name,
            )
        elif isinstance(entity, SyntheticApp):
            return LogTarget(
                id=entity.id,
                type="AppInstance",
                alternate_id=entity.name,
                display_name=entity.label,
            )
        else:
            return LogTarget(
                id=entity.id,
                type="UserGroup",
                alternate_id=entity.name,
                display_name=entity.name,
            )

    def _build_client(
        self,
        network: SyntheticIP | None,
        device: SyntheticDevice | None,
    ) -> LogClient:
        geo = None
        if network:
            geo = LogGeographicalContext(
                city=network.city,
                state=network.state,
                country=network.country,
                postal_code=network.postal_code,
                geolocation=LogGeolocation(
                    lat=network.latitude, lon=network.longitude
                ),
            )

        ua = None
        if device:
            ua = LogUserAgent(
                raw_user_agent=device.raw_user_agent,
                os=device.os,
                browser=device.browser,
            )

        return LogClient(
            ip_address=network.ip_address if network else None,
            user_agent=ua,
            zone="null",
            device=device.device_type if device else None,
            geographical_context=geo,
        )

    def _build_security_context(self, network: SyntheticIP | None) -> LogSecurityContext:
        if not network:
            return LogSecurityContext()
        return LogSecurityContext(
            as_number=network.as_number,
            as_org=network.as_org,
            isp=network.isp,
            domain=network.domain,
            is_proxy=network.is_proxy,
        )

    def _build_request(self, network: SyntheticIP | None) -> LogRequest:
        if not network:
            return LogRequest()
        from synthlog.schema.request import LogIpAddress

        return LogRequest(
            ip_chain=[
                LogIpAddress(
                    ip=network.ip_address,
                    geographical_context=LogGeographicalContext(
                        city=network.city,
                        state=network.state,
                        country=network.country,
                        postal_code=network.postal_code,
                        geolocation=LogGeolocation(
                            lat=network.latitude, lon=network.longitude
                        ),
                    ),
                    version="V4",
                )
            ]
        )
