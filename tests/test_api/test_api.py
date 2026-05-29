"""Tests for the REST API."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from synthlog.api.app import create_app

API_KEY = "test-key-12345"


@pytest.fixture(autouse=True)
def _set_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYNTHLOG_API_KEY", API_KEY)


@pytest.fixture()
def client() -> Iterator[TestClient]:
    app = create_app()
    with TestClient(app) as c:
        yield c


HEADERS = {"X-API-Key": API_KEY}


class TestHealth:
    def test_health_no_auth(self, client: TestClient) -> None:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


class TestAuth:
    def test_missing_key(self, client: TestClient) -> None:
        r = client.post("/api/generate", json={"seed": 42})
        assert r.status_code == 401

    def test_wrong_key(self, client: TestClient) -> None:
        r = client.post(
            "/api/generate",
            json={"seed": 42},
            headers={"X-API-Key": "wrong"},
        )
        assert r.status_code == 403

    def test_valid_key(self, client: TestClient) -> None:
        r = client.post(
            "/api/generate",
            json={"seed": 42, "duration_hours": 1},
            headers=HEADERS,
        )
        assert r.status_code == 202


class TestBatchGeneration:
    def test_create_batch_job(self, client: TestClient) -> None:
        r = client.post(
            "/api/generate",
            json={"seed": 42, "num_users": 3, "duration_hours": 1, "mode": "batch"},
            headers=HEADERS,
        )
        assert r.status_code == 202
        data = r.json()
        assert data["status"] in ("pending", "running", "completed")
        assert data["mode"] == "batch"
        assert "job_id" in data

    def test_poll_job_until_complete(self, client: TestClient) -> None:
        r = client.post(
            "/api/generate",
            json={"seed": 42, "num_users": 3, "duration_hours": 1, "mode": "batch"},
            headers=HEADERS,
        )
        job_id = r.json()["job_id"]

        # Poll until complete (batch should be fast)
        for _ in range(20):
            r = client.get(f"/api/jobs/{job_id}", headers=HEADERS)
            if r.json()["status"] == "completed":
                break
            time.sleep(0.1)

        data = r.json()
        assert data["status"] == "completed"
        assert data["event_count"] > 0

    def test_get_job_events(self, client: TestClient) -> None:
        r = client.post(
            "/api/generate",
            json={"seed": 42, "num_users": 3, "duration_hours": 1, "mode": "batch"},
            headers=HEADERS,
        )
        job_id = r.json()["job_id"]

        for _ in range(20):
            r = client.get(f"/api/jobs/{job_id}", headers=HEADERS)
            if r.json()["status"] == "completed":
                break
            time.sleep(0.1)

        r = client.get(f"/api/jobs/{job_id}/events", headers=HEADERS)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/x-ndjson"

        lines = r.text.strip().split("\n")
        assert len(lines) > 0
        first = json.loads(lines[0])
        assert "eventType" in first

    def test_delete_job(self, client: TestClient) -> None:
        r = client.post(
            "/api/generate",
            json={"seed": 42, "num_users": 3, "duration_hours": 1},
            headers=HEADERS,
        )
        job_id = r.json()["job_id"]

        for _ in range(20):
            r = client.get(f"/api/jobs/{job_id}", headers=HEADERS)
            if r.json()["status"] == "completed":
                break
            time.sleep(0.1)

        r = client.delete(f"/api/jobs/{job_id}", headers=HEADERS)
        assert r.status_code == 204

        r = client.get(f"/api/jobs/{job_id}", headers=HEADERS)
        assert r.status_code == 404


class TestStreamingGeneration:
    def test_create_streaming_job(self, client: TestClient) -> None:
        r = client.post(
            "/api/generate",
            json={
                "seed": 42,
                "num_users": 3,
                "duration_hours": 1,
                "mode": "streaming",
                "speed": 3600.0,
            },
            headers=HEADERS,
        )
        assert r.status_code == 202
        data = r.json()
        assert data["mode"] == "streaming"
        job_id = data["job_id"]

        # Let it run briefly then stop
        time.sleep(0.5)

        r = client.post(f"/api/jobs/{job_id}/stop", headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] in ("stopped", "completed")


class TestListJobs:
    def test_list_jobs(self, client: TestClient) -> None:
        # Create two jobs
        client.post(
            "/api/generate",
            json={"seed": 1, "duration_hours": 1},
            headers=HEADERS,
        )
        client.post(
            "/api/generate",
            json={"seed": 2, "duration_hours": 1},
            headers=HEADERS,
        )

        r = client.get("/api/jobs", headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert len(data["jobs"]) >= 2


class TestMockIdPEndpoint:
    def test_get_logs_pagination(self, client: TestClient) -> None:
        r = client.post(
            "/api/generate",
            json={"seed": 42, "num_users": 5, "duration_hours": 2, "mode": "batch"},
            headers=HEADERS,
        )
        job_id = r.json()["job_id"]

        for _ in range(20):
            r = client.get(f"/api/jobs/{job_id}", headers=HEADERS)
            if r.json()["status"] == "completed":
                break
            time.sleep(0.1)

        # First page
        r = client.get(
            f"/api/v1/logs?limit=5&job_id={job_id}",
            headers=HEADERS,
        )
        assert r.status_code == 200
        events = r.json()
        assert len(events) == 5
        assert "Link" in r.headers

        # Check Link header has rel="next"
        link = r.headers["Link"]
        assert 'rel="next"' in link
        assert 'rel="self"' in link

    def test_get_logs_no_jobs(self, client: TestClient) -> None:
        r = client.get("/api/v1/logs?limit=5", headers=HEADERS)
        assert r.status_code == 404

    def test_get_logs_with_sort_order(self, client: TestClient) -> None:
        r = client.post(
            "/api/generate",
            json={"seed": 42, "num_users": 3, "duration_hours": 1, "mode": "batch"},
            headers=HEADERS,
        )
        job_id = r.json()["job_id"]

        for _ in range(20):
            r = client.get(f"/api/jobs/{job_id}", headers=HEADERS)
            if r.json()["status"] == "completed":
                break
            time.sleep(0.1)

        r = client.get(
            f"/api/v1/logs?limit=10&sort_order=DESCENDING&job_id={job_id}",
            headers=HEADERS,
        )
        assert r.status_code == 200
        events = r.json()
        assert len(events) > 0


class TestMetaRoutes:
    def test_list_scenarios(self, client: TestClient) -> None:
        r = client.get("/api/scenarios", headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        names = [s["name"] for s in data]
        assert "credential_stuffing" in names
        assert "mfa_fatigue" in names

    def test_list_event_types(self, client: TestClient) -> None:
        r = client.get("/api/event-types", headers=HEADERS)
        assert r.status_code == 200
        data = r.json()
        types = [e["event_type"] for e in data]
        assert "user.session.start" in types
        assert len(data) >= 10

    def test_scenarios_require_auth(self, client: TestClient) -> None:
        r = client.get("/api/scenarios")
        assert r.status_code == 401

    def test_event_types_require_auth(self, client: TestClient) -> None:
        r = client.get("/api/event-types")
        assert r.status_code == 401
