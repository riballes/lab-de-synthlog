"""Authentication, Security, and Debug context models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from synthlog.schema.enums import (
    AuthenticationProvider,
    CredentialProvider,
    CredentialType,
)


class LogIssuer(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = Field(default=None, alias="id")
    type: str | None = Field(default=None, alias="type")


class LogAuthenticationContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    authentication_provider: AuthenticationProvider | None = Field(
        default=None, alias="authenticationProvider"
    )
    authentication_step: int | None = Field(default=None, alias="authenticationStep")
    credential_provider: CredentialProvider | None = Field(
        default=None, alias="credentialProvider"
    )
    credential_type: CredentialType | None = Field(
        default=None, alias="credentialType"
    )
    issuer: LogIssuer | None = Field(default=None, alias="issuer")
    interface: str | None = Field(default=None, alias="interface")
    external_session_id: str | None = Field(
        default=None, alias="externalSessionId"
    )
    root_session_id: str | None = Field(default=None, alias="rootSessionId")


class LogSecurityContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    as_number: int | None = Field(default=None, alias="asNumber")
    as_org: str | None = Field(default=None, alias="asOrg")
    isp: str | None = Field(default=None, alias="isp")
    domain: str | None = Field(default=None, alias="domain")
    is_proxy: bool | None = Field(default=None, alias="isProxy")


class LogDebugContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    debug_data: dict[str, Any] | None = Field(default=None, alias="debugData")
