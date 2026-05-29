"""API key authentication dependency."""

from __future__ import annotations

import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key() -> str:
    key = os.environ.get("SYNTHLOG_API_KEY", "")
    if not key:
        msg = "SYNTHLOG_API_KEY environment variable is not set"
        raise RuntimeError(msg)
    return key


async def require_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str:
    expected = get_api_key()
    if api_key is None:
        raise HTTPException(status_code=401, detail="Missing API key")
    if api_key != expected:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key
