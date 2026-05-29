"""Meta routes — health check, scenarios, event types."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from synthlog.api.auth import require_api_key
from synthlog.api.models import EventTypeInfo, ScenarioInfo
from synthlog.engine.event_builder import EVENT_TYPE_REGISTRY
from synthlog.engine.scenario_loader import ScenarioLoader

router = APIRouter(tags=["meta"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/scenarios", response_model=list[ScenarioInfo])
async def list_scenarios(
    _api_key: str = Depends(require_api_key),
) -> list[ScenarioInfo]:
    names = ScenarioLoader.list_builtin()
    return [ScenarioInfo(name=n) for n in names]


@router.get("/api/event-types", response_model=list[EventTypeInfo])
async def list_event_types(
    _api_key: str = Depends(require_api_key),
) -> list[EventTypeInfo]:
    return [
        EventTypeInfo(
            event_type=meta.event_type,
            severity=meta.severity,
            display_message=meta.display_message,
        )
        for meta in sorted(EVENT_TYPE_REGISTRY.values(), key=lambda m: m.event_type)
    ]
