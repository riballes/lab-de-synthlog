"""Mock IdP log endpoint with cursor-based pagination."""

from __future__ import annotations

import base64
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from synthlog.api.auth import require_api_key
from synthlog.api.job_manager import JobManager

router = APIRouter(tags=["logs"])


def _get_manager(request: Request) -> JobManager:
    return request.app.state.job_manager  # type: ignore[no-any-return]


def _encode_cursor(index: int) -> str:
    return base64.urlsafe_b64encode(str(index).encode()).decode()


def _decode_cursor(cursor: str) -> int:
    try:
        return int(base64.urlsafe_b64decode(cursor).decode())
    except (ValueError, Exception):
        return 0


@router.get("/api/v1/logs")
async def get_logs(
    request: Request,
    since: datetime | None = None,
    until: datetime | None = None,
    after: str | None = None,
    limit: int = 100,
    sort_order: str = "ASCENDING",
    job_id: str | None = None,
    _api_key: str = Depends(require_api_key),
    manager: JobManager = Depends(_get_manager),
) -> Response:
    limit = min(max(1, limit), 1000)

    # Find the job to serve events from
    if job_id:
        job = manager.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
    else:
        # Use most recent job with events
        jobs = sorted(manager.list_all(), key=lambda j: j.created_at, reverse=True)
        job = next((j for j in jobs if j.events), None)
        if job is None:
            raise HTTPException(
                status_code=404, detail="No jobs with events found"
            )

    events = job.events

    # Apply time filters
    if since:
        events = [e for e in events if e.published >= since]
    if until:
        events = [e for e in events if e.published <= until]

    # Sort
    if sort_order.upper() == "DESCENDING":
        events = list(reversed(events))

    # Cursor-based pagination
    start_index = 0
    if after:
        start_index = _decode_cursor(after)

    page = events[start_index : start_index + limit]
    next_index = start_index + limit

    # Serialize events
    import orjson

    event_dicts = [e.model_dump(by_alias=True, mode="json") for e in page]
    body = orjson.dumps(event_dicts)

    headers: dict[str, str] = {}
    base_url = str(request.url).split("?")[0]

    links = [f'<{base_url}?after={_encode_cursor(start_index)}&limit={limit}>; rel="self"']
    if next_index < len(events):
        cursor = _encode_cursor(next_index)
        links.append(f'<{base_url}?after={cursor}&limit={limit}>; rel="next"')
    headers["Link"] = ", ".join(links)

    return Response(
        content=body,
        media_type="application/json",
        headers=headers,
    )
