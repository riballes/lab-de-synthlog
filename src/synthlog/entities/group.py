"""Synthetic group entity."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SyntheticGroup:
    id: str
    name: str
    description: str
    member_ids: tuple[str, ...]
