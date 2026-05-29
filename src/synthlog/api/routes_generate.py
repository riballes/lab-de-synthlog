"""Generation and job management routes."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from synthlog.api.auth import require_api_key
from synthlog.api.job_manager import Job, JobManager
from synthlog.api.models import GenerateRequest, JobListResponse, JobResponse

router = APIRouter(prefix="/api", tags=["generation"])

_background_tasks: set[asyncio.Task[None]] = set()


def _job_to_response(j: Job) -> JobResponse:
    return JobResponse(
        job_id=j.id,
        status=j.status,  # type: ignore[arg-type]
        mode=j.mode,  # type: ignore[arg-type]
        created_at=j.created_at,
        completed_at=j.completed_at,
        event_count=j.event_count,
        speed=j.speed,
        sim_time=j.sim_time,
        config=j.config,
        error=j.error,
    )


def _get_manager(request: Request) -> JobManager:
    return request.app.state.job_manager  # type: ignore[no-any-return]


@router.post("/generate", status_code=202, response_model=JobResponse)
async def create_generation_job(
    req: GenerateRequest,
    _api_key: str = Depends(require_api_key),
    manager: JobManager = Depends(_get_manager),
) -> JobResponse:
    job = manager.create(req.model_dump())
    task = asyncio.create_task(manager.run(job))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return _job_to_response(job)


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    _api_key: str = Depends(require_api_key),
    manager: JobManager = Depends(_get_manager),
) -> JobListResponse:
    jobs = manager.list_all()
    return JobListResponse(jobs=[_job_to_response(j) for j in jobs])


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    _api_key: str = Depends(require_api_key),
    manager: JobManager = Depends(_get_manager),
) -> JobResponse:
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)


@router.get("/jobs/{job_id}/events")
async def get_job_events(
    job_id: str,
    _api_key: str = Depends(require_api_key),
    manager: JobManager = Depends(_get_manager),
) -> Response:
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    lines = []
    for event in job.events:
        lines.append(event.model_dump_json(by_alias=True))

    content = "\n".join(lines) + "\n" if lines else ""
    return Response(content=content, media_type="application/x-ndjson")


@router.post("/jobs/{job_id}/stop", response_model=JobResponse)
async def stop_job(
    job_id: str,
    _api_key: str = Depends(require_api_key),
    manager: JobManager = Depends(_get_manager),
) -> JobResponse:
    job = manager.stop(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    # Give the async task a moment to finalize
    await asyncio.sleep(0.1)
    return _job_to_response(job)


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: str,
    _api_key: str = Depends(require_api_key),
    manager: JobManager = Depends(_get_manager),
) -> None:
    if not manager.delete(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
