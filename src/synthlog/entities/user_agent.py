"""User agent profile entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UserAgentProfile:
    id: str
    raw_user_agent: str
    os: str
    browser: str
    device_type: str  # Computer, Mobile, Tablet
