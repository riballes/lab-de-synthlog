"""Baseline traffic generator — realistic workday login/app patterns."""

from __future__ import annotations

import math
from collections.abc import Iterator
from datetime import timedelta
from random import Random

from synthlog.clock import VirtualClock
from synthlog.engine.event_builder import EventBuilder
from synthlog.entities.pool import EntityPool
from synthlog.schema import LogSeverity, OutcomeResult
from synthlog.schema.log_event import LogEvent


def _hour_weight(hour: int) -> float:
    """Gaussian mixture for time-of-day activity: peaks at 9-11 and 14-16."""
    morning = math.exp(-0.5 * ((hour - 10) / 1.5) ** 2)
    afternoon = math.exp(-0.5 * ((hour - 15) / 1.5) ** 2)
    return morning + 0.8 * afternoon


class BaselineTraffic:
    name: str = "baseline"

    def __init__(self, events_per_user_per_hour: float = 2.0) -> None:
        self._rate = events_per_user_per_hour

    def generate(
        self, pool: EntityPool, clock: VirtualClock, rng: Random
    ) -> Iterator[LogEvent]:
        builder = EventBuilder(rng)
        tick = timedelta(minutes=5)
        active_sessions: dict[str, str] = {}  # user_id -> session_id

        for t in clock.tick_range(tick):
            hour = t.hour
            if t.weekday() >= 5:
                weight = 0.05
            else:
                weight = _hour_weight(hour)

            tick_prob = (self._rate / 12.0) * weight

            for user in pool.users:
                if rng.random() > tick_prob:
                    continue

                net = pool.get_network(user.primary_network_id)
                dev = pool.get_device(user.primary_device_id)
                jitter = timedelta(seconds=rng.randint(0, 290))
                event_time = t + jitter

                if user.id not in active_sessions:
                    # Occasional failed login attempt (~5%)
                    if rng.random() < 0.05:
                        yield builder.build(
                            "user.session.start",
                            event_time,
                            user,
                            network=net,
                            device=dev,
                            targets=[user],
                            outcome_result=OutcomeResult.FAILURE,
                            outcome_reason="INVALID_CREDENTIALS",
                            severity_override=LogSeverity.WARN,
                        )
                        event_time += timedelta(seconds=rng.randint(3, 15))

                    # Session start
                    session_id = f"idx{rng.getrandbits(64):016x}"
                    yield builder.build(
                        "user.session.start",
                        event_time,
                        user,
                        network=net,
                        device=dev,
                        targets=[user],
                        session_id=session_id,
                    )
                    active_sessions[user.id] = session_id
                    event_time += timedelta(seconds=rng.randint(1, 5))

                    # MFA challenge
                    yield builder.build(
                        "user.authentication.auth_via_mfa",
                        event_time,
                        user,
                        network=net,
                        device=dev,
                        targets=[user],
                        session_id=session_id,
                    )
                    event_time += timedelta(seconds=rng.randint(1, 3))

                    # Policy evaluation
                    yield builder.build(
                        "policy.evaluate_sign_on",
                        event_time,
                        user,
                        network=net,
                        device=dev,
                        session_id=session_id,
                    )
                    event_time += timedelta(seconds=rng.randint(1, 3))

                # SSO to a random app
                session_id = active_sessions.get(user.id, f"idx{rng.getrandbits(64):016x}")
                app = pool.random_app(rng)
                event_time += timedelta(seconds=rng.randint(5, 120))
                yield builder.build(
                    "user.authentication.sso",
                    event_time,
                    user,
                    network=net,
                    device=dev,
                    targets=[app],
                    session_id=session_id,
                )

                # Occasionally end session (~20% per tick)
                if rng.random() < 0.20 and user.id in active_sessions:
                    event_time += timedelta(seconds=rng.randint(60, 600))
                    yield builder.build(
                        "user.session.end",
                        event_time,
                        user,
                        network=net,
                        device=dev,
                        targets=[user],
                        session_id=active_sessions.pop(user.id),
                    )
