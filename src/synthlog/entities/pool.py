"""EntityPool — central registry of synthetic entities."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from random import Random

from synthlog.entities.application import SyntheticApp
from synthlog.entities.device import SyntheticDevice
from synthlog.entities.group import SyntheticGroup
from synthlog.entities.network import SyntheticIP
from synthlog.entities.user import SyntheticUser
from synthlog.entities.user_agent import UserAgentProfile


@dataclass
class EntityPool:
    users: list[SyntheticUser] = field(default_factory=list)
    groups: list[SyntheticGroup] = field(default_factory=list)
    apps: list[SyntheticApp] = field(default_factory=list)
    devices: list[SyntheticDevice] = field(default_factory=list)
    networks: list[SyntheticIP] = field(default_factory=list)
    user_agents: list[UserAgentProfile] = field(default_factory=list)

    def get_user(self, user_id: str) -> SyntheticUser:
        for u in self.users:
            if u.id == user_id:
                return u
        raise KeyError(f"User not found: {user_id}")

    def get_network(self, network_id: str) -> SyntheticIP:
        for n in self.networks:
            if n.id == network_id:
                return n
        raise KeyError(f"Network not found: {network_id}")

    def get_device(self, device_id: str) -> SyntheticDevice:
        for d in self.devices:
            if d.id == device_id:
                return d
        raise KeyError(f"Device not found: {device_id}")

    def random_user(self, rng: Random) -> SyntheticUser:
        return rng.choice(self.users)

    def random_app(self, rng: Random) -> SyntheticApp:
        return rng.choice(self.apps)

    def random_network(self, rng: Random) -> SyntheticIP:
        return rng.choice(self.networks)

    def to_json(self) -> str:
        data = {
            "users": [asdict(u) for u in self.users],
            "groups": [asdict(g) for g in self.groups],
            "apps": [asdict(a) for a in self.apps],
            "devices": [asdict(d) for d in self.devices],
            "networks": [asdict(n) for n in self.networks],
            "user_agents": [asdict(ua) for ua in self.user_agents],
        }
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, data: str) -> EntityPool:
        raw = json.loads(data)
        return cls(
            users=[
                SyntheticUser(**{**u, "mfa_factors": tuple(u["mfa_factors"])})
                for u in raw["users"]
            ],
            groups=[
                SyntheticGroup(**{**g, "member_ids": tuple(g["member_ids"])})
                for g in raw["groups"]
            ],
            apps=[SyntheticApp(**a) for a in raw["apps"]],
            devices=[SyntheticDevice(**d) for d in raw["devices"]],
            networks=[SyntheticIP(**n) for n in raw["networks"]],
            user_agents=[UserAgentProfile(**ua) for ua in raw["user_agents"]],
        )
