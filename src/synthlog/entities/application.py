"""Synthetic application entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SyntheticApp:
    id: str
    name: str
    label: str
    sign_on_mode: str = "SAML_2_0"
    status: str = "ACTIVE"
