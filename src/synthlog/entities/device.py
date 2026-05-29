"""Synthetic device entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SyntheticDevice:
    id: str
    os: str
    os_version: str
    device_type: str  # Computer, Mobile, Tablet
    browser: str
    browser_version: str
    raw_user_agent: str
