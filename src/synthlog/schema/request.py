"""LogRequest and LogIpAddress models."""

from pydantic import BaseModel, ConfigDict, Field

from synthlog.schema.client import LogGeographicalContext


class LogIpAddress(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ip: str | None = Field(default=None, alias="ip")
    geographical_context: LogGeographicalContext | None = Field(
        default=None, alias="geographicalContext"
    )
    version: str | None = Field(default=None, alias="version")
    source: str | None = Field(default=None, alias="source")


class LogRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ip_chain: list[LogIpAddress] = Field(default_factory=list, alias="ipChain")
