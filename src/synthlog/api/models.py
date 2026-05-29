"""Pydantic request/response models for the API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    seed: int = Field(default=42, description="Random seed for deterministic output")
    num_users: int = Field(default=5, ge=1, le=1000, description="Number of synthetic users")
    duration_hours: int = Field(default=8, ge=1, le=168, description="Hours of simulated time")
    scenarios: list[str] = Field(default_factory=list, description="Scenario names")
    events_per_user_per_hour: float = Field(default=2.0, gt=0, description="Baseline event rate")
    mode: Literal["batch", "streaming"] = Field(
        default="batch", description="batch (all at once) or streaming (real-time paced)"
    )
    speed: float = Field(
        default=1.0, gt=0, description="Clock speed multiplier (streaming mode only)"
    )
    emitter: str | None = Field(
        default=None, description="Optional emitter plugin name (e.g., kafka)"
    )


class JobResponse(BaseModel):
    job_id: str
    status: Literal["pending", "running", "completed", "stopped", "failed"]
    mode: Literal["batch", "streaming"]
    created_at: datetime
    completed_at: datetime | None = None
    event_count: int = 0
    speed: float = 1.0
    sim_time: datetime | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class JobListResponse(BaseModel):
    jobs: list[JobResponse]


class ScenarioInfo(BaseModel):
    name: str


class EventTypeInfo(BaseModel):
    event_type: str
    severity: str
    display_message: str
