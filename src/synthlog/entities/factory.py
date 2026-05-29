"""Faker-based entity generation with seedable determinism."""

from __future__ import annotations

import string
from random import Random

from faker import Faker

from synthlog.entities.application import SyntheticApp
from synthlog.entities.device import SyntheticDevice
from synthlog.entities.group import SyntheticGroup
from synthlog.entities.network import SyntheticIP
from synthlog.entities.pool import EntityPool
from synthlog.entities.user import SyntheticUser
from synthlog.entities.user_agent import UserAgentProfile

_DEPARTMENTS = [
    "Engineering", "Sales", "Marketing", "Finance", "HR",
    "Legal", "Operations", "Product", "Support", "Security",
]

_APPS = [
    ("Salesforce", "SAML_2_0"),
    ("Slack", "OPENID_CONNECT"),
    ("GitHub", "SAML_2_0"),
    ("Jira", "SAML_2_0"),
    ("Google Workspace", "SAML_2_0"),
    ("AWS Console", "SAML_2_0"),
    ("Zoom", "OPENID_CONNECT"),
    ("Office 365", "WS_FEDERATION"),
]

_DEVICES = [
    ("Mac OS X", "14.2", "Computer", "Chrome", "120.0",
     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0"),
    ("Windows", "11", "Computer", "Edge", "120.0",
     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/120.0"),
    ("Mac OS X", "14.2", "Computer", "Safari", "17.2",
     "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 Safari/17.2"),
    ("iOS", "17.2", "Mobile", "Safari", "17.2",
     "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15"),
    ("Android", "14", "Mobile", "Chrome", "120.0",
     "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/120.0"),
    ("Windows", "11", "Computer", "Chrome", "120.0",
     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"),
]

_MFA_FACTOR_SETS: list[tuple[str, ...]] = [
    ("OKTA_VERIFY",),
    ("OKTA_VERIFY", "SMS"),
    ("OKTA_VERIFY", "EMAIL"),
    ("SMS",),
    ("OKTA_VERIFY", "SMS", "EMAIL"),
]

_US_OFFICES = [
    ("San Francisco", "California", "US", "94105", 37.7749, -122.4194,
     15169, "Google LLC", "Google Fiber", "google.com"),
    ("New York", "New York", "US", "10001", 40.7128, -74.0060,
     7922, "Comcast", "Comcast Cable", "comcast.net"),
    ("Austin", "Texas", "US", "73301", 30.2672, -97.7431,
     7018, "AT&T", "AT&T Services", "att.net"),
    ("Seattle", "Washington", "US", "98101", 47.6062, -122.3321,
     16509, "Amazon.com", "Amazon Technologies", "amazon.com"),
    ("Chicago", "Illinois", "US", "60601", 41.8781, -87.6298,
     20115, "Charter Communications", "Charter", "charter.com"),
]


class EntityFactory:
    def __init__(self, seed: int = 42) -> None:
        self.rng = Random(seed)
        self.faker = Faker()
        Faker.seed(seed)
        self._id_counter = 0

    def _okta_id(self, prefix: str = "00u") -> str:
        self._id_counter += 1
        chars = string.ascii_lowercase + string.digits
        suffix = "".join(self.rng.choices(chars, k=20))
        return f"{prefix}{suffix}"

    def create_pool(
        self,
        num_users: int = 5,
        num_apps: int = 3,
        num_groups: int = 2,
    ) -> EntityPool:
        networks = [self._make_network(i) for i in range(len(_US_OFFICES))]
        devices = [self._make_device(i) for i in range(min(len(_DEVICES), 6))]
        apps = [self._make_app(i) for i in range(num_apps)]
        users = [
            self._make_user(networks, devices) for _ in range(num_users)
        ]
        groups = [self._make_group(users, i) for i in range(num_groups)]
        user_agents = [self._make_user_agent(d) for d in devices]

        return EntityPool(
            users=users,
            groups=groups,
            apps=apps,
            devices=devices,
            networks=networks,
            user_agents=user_agents,
        )

    def _make_user(
        self,
        networks: list[SyntheticIP],
        devices: list[SyntheticDevice],
    ) -> SyntheticUser:
        first = self.faker.first_name()
        last = self.faker.last_name()
        domain = "example.com"
        login = f"{first.lower()}.{last.lower()}@{domain}"
        net = self.rng.choice(networks)
        dev = self.rng.choice(devices)
        dept = self.rng.choice(_DEPARTMENTS)

        return SyntheticUser(
            id=self._okta_id("00u"),
            login=login,
            display_name=f"{first} {last}",
            email=login,
            department=dept,
            title=self.faker.job(),
            manager_id=None,
            primary_device_id=dev.id,
            primary_network_id=net.id,
            mfa_factors=self.rng.choice(_MFA_FACTOR_SETS),
            risk_score=round(self.rng.uniform(0.0, 0.3), 2),
            timezone="America/Los_Angeles",
            is_admin=(dept == "Security" and self.rng.random() < 0.5),
        )

    def _make_app(self, index: int) -> SyntheticApp:
        name, sso = _APPS[index % len(_APPS)]
        return SyntheticApp(
            id=self._okta_id("0oa"),
            name=name.lower().replace(" ", "_"),
            label=name,
            sign_on_mode=sso,
        )

    def _make_group(self, users: list[SyntheticUser], index: int) -> SyntheticGroup:
        group_names = ["Engineering Team", "All Employees", "Security Team", "Sales Team"]
        name = group_names[index % len(group_names)]
        if index == 0:
            member_ids = tuple(u.id for u in users)
        else:
            count = max(1, len(users) // 2)
            member_ids = tuple(u.id for u in self.rng.sample(users, count))

        return SyntheticGroup(
            id=self._okta_id("00g"),
            name=name,
            description=f"Auto-generated group: {name}",
            member_ids=member_ids,
        )

    def _make_device(self, index: int) -> SyntheticDevice:
        os_, os_ver, dev_type, browser, brow_ver, ua = _DEVICES[index % len(_DEVICES)]
        return SyntheticDevice(
            id=self._okta_id("oud"),
            os=os_,
            os_version=os_ver,
            device_type=dev_type,
            browser=browser,
            browser_version=brow_ver,
            raw_user_agent=ua,
        )

    def _make_network(self, index: int) -> SyntheticIP:
        city, state, country, postal, lat, lon, asn, as_org, isp, domain = (
            _US_OFFICES[index % len(_US_OFFICES)]
        )
        octets = [self.rng.randint(10, 200) for _ in range(4)]
        ip = ".".join(str(o) for o in octets)

        return SyntheticIP(
            id=self._okta_id("net"),
            ip_address=ip,
            city=city,
            state=state,
            country=country,
            postal_code=postal,
            latitude=lat,
            longitude=lon,
            as_number=asn,
            as_org=as_org,
            isp=isp,
            domain=domain,
        )

    def _make_user_agent(self, device: SyntheticDevice) -> UserAgentProfile:
        return UserAgentProfile(
            id=self._okta_id("uap"),
            raw_user_agent=device.raw_user_agent,
            os=device.os,
            browser=device.browser,
            device_type=device.device_type,
        )
