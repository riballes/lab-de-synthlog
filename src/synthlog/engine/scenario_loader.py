"""YAML scenario loader — parses scenario definitions into event generators."""

from __future__ import annotations

import importlib.resources
from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path
from random import Random

import yaml

from synthlog.clock import VirtualClock
from synthlog.engine.event_builder import EventBuilder
from synthlog.entities.network import SyntheticIP
from synthlog.entities.pool import EntityPool
from synthlog.schema import LogSeverity, OutcomeResult
from synthlog.schema.log_event import LogEvent


def _parse_duration(iso: str) -> timedelta:
    """Parse a subset of ISO 8601 durations: PT2H, PT15M, PT30S, PT2H15M."""
    s = iso.upper()
    if not s.startswith("PT"):
        msg = f"Only PT durations supported, got: {iso}"
        raise ValueError(msg)
    s = s[2:]
    hours = minutes = seconds = 0
    for unit, label in [("H", "hours"), ("M", "minutes"), ("S", "seconds")]:
        if unit in s:
            val, s = s.split(unit, 1)
            if label == "hours":
                hours = int(val)
            elif label == "minutes":
                minutes = int(val)
            else:
                seconds = int(val)
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


class YAMLScenario:
    def __init__(self, definition: dict) -> None:  # type: ignore[type-arg]
        self._def = definition
        self._name: str = definition["name"]

    @property
    def name(self) -> str:
        return self._name

    def generate(
        self, pool: EntityPool, clock: VirtualClock, rng: Random
    ) -> Iterator[LogEvent]:
        builder = EventBuilder(rng)
        params = self._def.get("parameters", {})
        schedule = self._def.get("schedule", {})
        steps = self._def.get("steps", [])

        start_offset = _parse_duration(schedule.get("start_offset", "PT0S"))
        start_time = clock.start + start_offset
        interval = timedelta(
            seconds=params.get("attempt_interval_seconds", 10)
        )

        # Build attacker network
        attacker_net = self._build_attacker_network(params, rng)

        # Determine target users
        target_count = min(params.get("target_count", 1), len(pool.users))
        target_users = rng.sample(pool.users, target_count)

        current_time = start_time

        for step in steps:
            event_type = step["event_type"]
            outcome = OutcomeResult(step.get("outcome", "SUCCESS"))
            outcome_reason = step.get("outcome_reason")
            severity = (
                LogSeverity(step["severity"]) if "severity" in step else None
            )

            if step.get("repeat_per_target"):
                for user in target_users:
                    jitter = timedelta(seconds=rng.randint(0, 3))
                    yield builder.build(
                        event_type,
                        current_time + jitter,
                        user,
                        targets=[user],
                        outcome_result=outcome,
                        outcome_reason=outcome_reason,
                        severity_override=severity,
                        network=attacker_net,
                    )
                    current_time += interval
            elif "repeat_count" in step:
                count_raw = step["repeat_count"]
                if isinstance(count_raw, str) and count_raw.startswith("$"):
                    count = params.get(count_raw[1:], 1)
                else:
                    count = int(count_raw)
                # Use first target user for repeated steps
                user = target_users[0] if target_users else pool.users[0]
                for _ in range(count):
                    jitter = timedelta(seconds=rng.randint(0, 3))
                    push_interval = timedelta(
                        seconds=params.get("push_interval_seconds", interval.total_seconds())
                    )
                    yield builder.build(
                        event_type,
                        current_time + jitter,
                        user,
                        targets=[user],
                        outcome_result=outcome,
                        outcome_reason=outcome_reason,
                        severity_override=severity,
                        network=attacker_net,
                    )
                    current_time += push_interval
            else:
                target_idx = step.get("target_index", 0)
                user = target_users[target_idx] if target_users else pool.users[0]
                targets: list = [user]  # type: ignore[type-arg]

                if "target_app_index" in step:
                    app_idx = step["target_app_index"]
                    if app_idx < len(pool.apps):
                        targets = [pool.apps[app_idx]]

                jitter = timedelta(seconds=rng.randint(0, 5))
                yield builder.build(
                    event_type,
                    current_time + jitter,
                    user,
                    targets=targets,
                    outcome_result=outcome,
                    outcome_reason=outcome_reason,
                    severity_override=severity,
                    network=attacker_net,
                )
                current_time += timedelta(seconds=rng.randint(1, 10))

    def _build_attacker_network(self, params: dict, rng: Random) -> SyntheticIP:  # type: ignore[type-arg]
        geo = params.get("attacker_geo", {})
        octets = [rng.randint(100, 250) for _ in range(4)]
        ip = ".".join(str(o) for o in octets)

        return SyntheticIP(
            id=f"net_attacker_{rng.getrandbits(32):08x}",
            ip_address=ip,
            city=geo.get("city", "Unknown"),
            state=geo.get("state", "Unknown"),
            country=geo.get("country", "Unknown"),
            postal_code=geo.get("postal_code", "00000"),
            latitude=geo.get("latitude", 0.0),
            longitude=geo.get("longitude", 0.0),
            as_number=geo.get("as_number", 0),
            as_org=geo.get("as_org", "Unknown"),
            isp=geo.get("isp", "Unknown"),
            domain=geo.get("domain", "unknown"),
            is_proxy=True,
        )


class ScenarioLoader:
    @staticmethod
    def load(path: Path) -> YAMLScenario:
        with open(path) as f:
            definition = yaml.safe_load(f)
        return YAMLScenario(definition)

    @staticmethod
    def load_builtin(name: str) -> YAMLScenario:
        scenarios_pkg = importlib.resources.files("synthlog.scenarios")
        yaml_file = scenarios_pkg / f"{name}.yaml"
        content = yaml_file.read_text(encoding="utf-8")
        definition = yaml.safe_load(content)
        return YAMLScenario(definition)

    @staticmethod
    def list_builtin() -> list[str]:
        scenarios_pkg = importlib.resources.files("synthlog.scenarios")
        names = []
        for item in scenarios_pkg.iterdir():
            if hasattr(item, "name") and item.name.endswith(".yaml"):
                names.append(item.name.removesuffix(".yaml"))
        return sorted(names)
