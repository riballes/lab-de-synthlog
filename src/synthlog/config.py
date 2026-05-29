"""Configuration via pydantic-settings.

Supports env vars (SYNTHLOG_ prefix), YAML, and CLI overrides.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class SynthlogSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SYNTHLOG_")

    # Determinism
    seed: int = 42

    # Entity pool
    num_users: int = 5
    num_apps: int = 3
    num_groups: int = 2

    # Time
    start_time: datetime = datetime(2025, 1, 6, 8, 0, tzinfo=UTC)  # Monday 8 AM
    duration_hours: int = 8
    clock_speed: float = 1.0

    # Baseline
    events_per_user_per_hour: float = 2.0

    # Scenarios
    scenario_files: list[Path] = []
    builtin_scenarios: list[str] = []

    # Output
    emitter: Literal["jsonl", "http", "console"] | str = "jsonl"
    output_path: Path = Path("output/events.jsonl")
    http_port: int = 8080

    # Entity pool persistence
    pool_path: Path | None = None
