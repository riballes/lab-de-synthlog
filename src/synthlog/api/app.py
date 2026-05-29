"""FastAPI application assembly."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from synthlog.api.job_manager import JobManager
from synthlog.api.routes_generate import router as generate_router
from synthlog.api.routes_logs import router as logs_router
from synthlog.api.routes_meta import router as meta_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.job_manager = JobManager()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Synthlog API",
        description="Synthetic identity provider log event generator",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(meta_router)
    app.include_router(generate_router)
    app.include_router(logs_router)

    return app
