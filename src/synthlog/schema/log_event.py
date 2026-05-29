"""Top-level LogEvent model matching Okta's System Log schema."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from synthlog.schema.actor import LogActor
from synthlog.schema.client import LogClient
from synthlog.schema.context import (
    LogAuthenticationContext,
    LogDebugContext,
    LogSecurityContext,
)
from synthlog.schema.enums import LogSeverity
from synthlog.schema.outcome import LogOutcome
from synthlog.schema.request import LogRequest
from synthlog.schema.target import LogTarget
from synthlog.schema.transaction import LogTransaction


class LogEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uuid: str = Field(alias="uuid")
    published: datetime = Field(alias="published")
    event_type: str = Field(alias="eventType")
    version: str = Field(default="0", alias="version")
    severity: LogSeverity = Field(alias="severity")
    display_message: str = Field(alias="displayMessage")
    legacy_event_type: str | None = Field(default=None, alias="legacyEventType")
    actor: LogActor = Field(alias="actor")
    client: LogClient = Field(default_factory=LogClient, alias="client")
    request: LogRequest = Field(default_factory=LogRequest, alias="request")
    outcome: LogOutcome = Field(alias="outcome")
    target: list[LogTarget] = Field(default_factory=list, alias="target")
    transaction: LogTransaction = Field(
        default_factory=LogTransaction, alias="transaction"
    )
    debug_context: LogDebugContext = Field(
        default_factory=LogDebugContext, alias="debugContext"
    )
    authentication_context: LogAuthenticationContext = Field(
        default_factory=LogAuthenticationContext, alias="authenticationContext"
    )
    security_context: LogSecurityContext = Field(
        default_factory=LogSecurityContext, alias="securityContext"
    )
