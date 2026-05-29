"""In-memory job store with batch and streaming runners."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from random import Random
from typing import Any

from synthlog.clock import VirtualClock
from synthlog.emitter.protocols import load_emitter
from synthlog.engine.baseline import BaselineTraffic
from synthlog.engine.protocols import Emitter, Scenario
from synthlog.engine.scenario_loader import ScenarioLoader
from synthlog.engine.scheduler import EventScheduler
from synthlog.engine.streaming import StreamingScheduler
from synthlog.entities import EntityFactory
from synthlog.schema.log_event import LogEvent


@dataclass
class Job:
    id: str
    status: str  # pending, running, completed, stopped, failed
    mode: str  # batch, streaming
    config: dict[str, Any]
    created_at: datetime
    completed_at: datetime | None = None
    events: list[LogEvent] = field(default_factory=list)
    event_count: int = 0
    speed: float = 1.0
    sim_time: datetime | None = None
    error: str | None = None
    _stop_event: asyncio.Event = field(default_factory=asyncio.Event)
    _streaming_scheduler: StreamingScheduler | None = field(
        default=None, repr=False
    )

    def stop(self) -> None:
        self._stop_event.set()
        if self._streaming_scheduler is not None:
            self._streaming_scheduler.stop()


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def create(self, config: dict[str, Any]) -> Job:
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        job = Job(
            id=job_id,
            status="pending",
            mode=config.get("mode", "batch"),
            config=config,
            created_at=datetime.now(UTC),
            speed=config.get("speed", 1.0),
        )
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def list_all(self) -> list[Job]:
        return list(self._jobs.values())

    def delete(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        if job.status == "running":
            job.stop()
        del self._jobs[job_id]
        return True

    def stop(self, job_id: str) -> Job | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        job.stop()
        return job

    async def run(self, job: Job) -> None:
        try:
            job.status = "running"
            config = job.config
            seed = config.get("seed", 42)
            num_users = config.get("num_users", 5)
            duration_hours = config.get("duration_hours", 8)
            scenario_names: list[str] = config.get("scenarios", [])
            rate = config.get("events_per_user_per_hour", 2.0)
            emitter_name = config.get("emitter")

            rng = Random(seed)
            pool = EntityFactory(seed=seed).create_pool(num_users=num_users)
            clock = VirtualClock.for_duration(
                duration_hours=duration_hours,
                speed=job.speed,
            )

            scenarios: list[Scenario] = [BaselineTraffic(events_per_user_per_hour=rate)]
            for name in scenario_names:
                path = Path(name)
                if path.exists() and path.suffix in (".yaml", ".yml"):
                    scenarios.append(ScenarioLoader.load(path))
                else:
                    scenarios.append(ScenarioLoader.load_builtin(name))

            emitter: Emitter | None = None
            if emitter_name:
                emitter = load_emitter(emitter_name)

            def on_event(event: LogEvent) -> None:
                job.events.append(event)
                job.event_count = len(job.events)
                job.sim_time = event.published

            if job.mode == "streaming":
                scheduler = StreamingScheduler(scenarios, pool, clock, rng)
                job._streaming_scheduler = scheduler
                await scheduler.run(emitter=emitter, on_event=on_event)
                job.status = "stopped" if scheduler.is_stopped else "completed"
            else:
                batch_scheduler = EventScheduler(scenarios, pool, clock, rng)
                for event in batch_scheduler._merged_events():
                    on_event(event)
                    if emitter is not None:
                        emitter.emit(event)
                if emitter is not None:
                    emitter.flush()
                job.status = "completed"

            if emitter is not None:
                emitter.close()

            job.completed_at = datetime.now(UTC)

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now(UTC)
