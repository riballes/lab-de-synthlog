"""LogClient and related models."""

from pydantic import BaseModel, ConfigDict, Field


class LogGeolocation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lat: float | None = Field(default=None, alias="lat")
    lon: float | None = Field(default=None, alias="lon")


class LogGeographicalContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    city: str | None = Field(default=None, alias="city")
    state: str | None = Field(default=None, alias="state")
    country: str | None = Field(default=None, alias="country")
    postal_code: str | None = Field(default=None, alias="postalCode")
    geolocation: LogGeolocation | None = Field(default=None, alias="geolocation")


class LogUserAgent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    raw_user_agent: str | None = Field(default=None, alias="rawUserAgent")
    os: str | None = Field(default=None, alias="os")
    browser: str | None = Field(default=None, alias="browser")


class LogClient(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = Field(default=None, alias="id")
    ip_address: str | None = Field(default=None, alias="ipAddress")
    user_agent: LogUserAgent | None = Field(default=None, alias="userAgent")
    zone: str | None = Field(default=None, alias="zone")
    device: str | None = Field(default=None, alias="device")
    geographical_context: LogGeographicalContext | None = Field(
        default=None, alias="geographicalContext"
    )
