"""Synthetic user entity."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SyntheticUser:
    id: str
    login: str
    display_name: str
    email: str
    department: str
    title: str
    manager_id: str | None
    primary_device_id: str
    primary_network_id: str
    mfa_factors: tuple[str, ...] = field(default=("OKTA_VERIFY",))
    risk_score: float = 0.1
    timezone: str = "America/Los_Angeles"
    is_admin: bool = False
