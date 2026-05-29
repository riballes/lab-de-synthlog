"""Synthetic network/IP entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SyntheticIP:
    id: str
    ip_address: str
    city: str
    state: str
    country: str
    postal_code: str
    latitude: float
    longitude: float
    as_number: int
    as_org: str
    isp: str
    domain: str
    is_proxy: bool = False
