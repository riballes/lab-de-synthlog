![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Tests: 74 passing](https://img.shields.io/badge/tests-74%20passing-brightgreen)
![API: FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)
![Type Checked: mypy strict](https://img.shields.io/badge/type%20checked-mypy%20strict-blue)
![Linting: ruff](https://img.shields.io/badge/linting-ruff-orange)
![Container: Cloud Run](https://img.shields.io/badge/container-Cloud%20Run-4285F4?logo=googlecloud&logoColor=white)
![IaC: Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform&logoColor=white)
![CI/CD: GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)

# synthlog

A synthetic log event producer for **detection engineering**, SIEM rule testing, and security training data generation. Produces realistic, schema-correct identity provider system log events with configurable baseline traffic and injectable attack scenarios.

## Features

- **Realistic entity model** -- Synthetic users, groups, applications, devices, and networks with stable identifiers and correlated attributes
- **Baseline traffic** -- Time-of-day weighted workday patterns (login bursts at 9am, quiet at 3am, reduced weekends)
- **Attack scenario injection** -- YAML-defined attack patterns (credential stuffing, MFA fatigue) layered on top of baseline noise
- **Deterministic output** -- Seedable RNG produces byte-for-byte identical output for regression testing
- **REST API** -- FastAPI service with async job management, mock IdP log endpoint (`GET /api/v1/logs` with pagination), and API key auth
- **Streaming mode** -- Real-time event emission paced by clock speed multiplier; traffic patterns preserved for event hub integration (Kafka, etc.)
- **Plugin-based sinks** -- Built-in JSONL and console emitters; external sinks (Kafka, Splunk HEC, etc.) via Python entry points
- **Cloud Run ready** -- Dockerfile and Terraform for GCP Cloud Run deployment with optional Cloud Scheduler trigger

## Quickstart

```bash
# Install
uv pip install -e ".[dev]"

# Generate 8 hours of synthetic events for 5 users with a credential stuffing attack
uv run synthlog generate --seed 42 --users 5 --duration 8 --scenario credential_stuffing -o output/events.jsonl

# Pretty-print to console
uv run synthlog generate --emitter console --duration 1

# Create and persist an entity pool
uv run synthlog init-pool --seed 42 --users 10 -o pool.json

# List supported event types
uv run synthlog list-events

# Stream events in real-time (1 hour of sim time in 1 minute)
uv run synthlog stream --speed 60 --emitter console --duration 1

# Start the REST API server
SYNTHLOG_API_KEY=your-secret-key uv run synthlog serve --port 8080
```

## REST API

Start the server:

```bash
SYNTHLOG_API_KEY=your-secret-key uv run synthlog serve --port 8080
```

Interactive docs at `http://localhost:8080/docs`.

All `/api/*` endpoints require the `X-API-Key` header. `/health` is unauthenticated.

```bash
# Start a batch generation job
curl -X POST http://localhost:8080/api/generate \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"seed": 42, "num_users": 5, "duration_hours": 2, "mode": "batch"}'

# Start a streaming job (8h of traffic compressed into ~8 seconds)
curl -X POST http://localhost:8080/api/generate \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"seed": 42, "num_users": 5, "duration_hours": 8, "mode": "streaming", "speed": 3600}'

# Check job status
curl -H "X-API-Key: your-secret-key" http://localhost:8080/api/jobs/{job_id}

# Download events as JSONL
curl -H "X-API-Key: your-secret-key" http://localhost:8080/api/jobs/{job_id}/events

# Mock IdP endpoint with pagination (Link header with rel="next")
curl -H "X-API-Key: your-secret-key" "http://localhost:8080/api/v1/logs?limit=10"

# Stop a streaming job
curl -X POST -H "X-API-Key: your-secret-key" http://localhost:8080/api/jobs/{job_id}/stop

# List available scenarios
curl -H "X-API-Key: your-secret-key" http://localhost:8080/api/scenarios
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check (no auth) |
| POST | `/api/generate` | Start batch or streaming generation job |
| GET | `/api/jobs` | List all jobs |
| GET | `/api/jobs/{id}` | Job status (event_count updates live for streaming) |
| GET | `/api/jobs/{id}/events` | Download events as JSONL |
| POST | `/api/jobs/{id}/stop` | Stop a streaming job |
| DELETE | `/api/jobs/{id}` | Delete a job |
| GET | `/api/v1/logs` | Mock IdP log endpoint with cursor pagination |
| GET | `/api/scenarios` | List available attack scenarios |
| GET | `/api/event-types` | List supported event types |

## Streaming Mode

Stream events paced to match simulated timestamps. The `speed` parameter controls time compression:

| Speed | 8h workday takes | Use case |
|-------|-------------------|----------|
| `1.0` | 8 hours | Real-time simulation |
| `60.0` | 8 minutes | Demo / development |
| `3600.0` | 8 seconds | Testing |

Traffic patterns are preserved regardless of speed -- events cluster during business hours and thin out overnight.

```bash
# CLI: stream to console at 60x speed
uv run synthlog stream --speed 60 --emitter console --duration 8

# API: start streaming job that pushes to an external sink
curl -X POST http://localhost:8080/api/generate \
  -H "X-API-Key: key" -H "Content-Type: application/json" \
  -d '{"mode": "streaming", "speed": 60, "emitter": "kafka"}'
```

## Project Structure

```
lab-de-synthlog/
├── pyproject.toml                        # Package metadata, dependencies, tool config
├── Dockerfile                            # Multi-stage build for Cloud Run
├── .dockerignore
├── .gitignore
├── .python-version
│
├── src/synthlog/
│   ├── __init__.py                       # Package version
│   ├── cli.py                            # Typer CLI entry point
│   ├── config.py                         # pydantic-settings (SYNTHLOG_* env vars)
│   ├── clock.py                          # Virtual time model (real-time + accelerated)
│   │
│   ├── schema/                           # Pydantic models matching IdP log schema
│   │   ├── log_event.py                  #   Top-level LogEvent
│   │   ├── actor.py                      #   Actor (who performed the action)
│   │   ├── target.py                     #   Target (what was acted upon)
│   │   ├── client.py                     #   Client, UserAgent, GeographicalContext
│   │   ├── outcome.py                    #   Outcome (success/failure/deny)
│   │   ├── context.py                    #   Authentication, Security, Debug contexts
│   │   ├── transaction.py                #   Transaction grouping
│   │   ├── request.py                    #   Request and IP chain
│   │   └── enums.py                      #   Severity, OutcomeResult, CredentialType, etc.
│   │
│   ├── entities/                         # Layer 1: "The World"
│   │   ├── user.py                       #   SyntheticUser (frozen dataclass)
│   │   ├── group.py                      #   SyntheticGroup
│   │   ├── application.py                #   SyntheticApp
│   │   ├── device.py                     #   SyntheticDevice
│   │   ├── network.py                    #   SyntheticIP (geo, ASN, proxy)
│   │   ├── user_agent.py                 #   UserAgentProfile
│   │   ├── factory.py                    #   EntityFactory (Faker + seed)
│   │   └── pool.py                       #   EntityPool (registry + JSON persistence)
│   │
│   ├── api/                              # REST API (FastAPI)
│   │   ├── app.py                        #   App factory, lifespan, CORS
│   │   ├── auth.py                       #   API key auth dependency
│   │   ├── models.py                     #   Request/response Pydantic models
│   │   ├── job_manager.py                #   In-memory job store + batch/streaming runner
│   │   ├── routes_generate.py            #   POST /generate, GET/DELETE /jobs
│   │   ├── routes_logs.py                #   GET /api/v1/logs (mock IdP endpoint)
│   │   └── routes_meta.py               #   GET /health, /scenarios, /event-types
│   │
│   ├── engine/                           # Layer 2: "The Behavior"
│   │   ├── protocols.py                  #   Scenario and Emitter protocol definitions
│   │   ├── event_builder.py              #   Builds LogEvent from entities + event type
│   │   ├── baseline.py                   #   BaselineTraffic (workday patterns)
│   │   ├── scenario_loader.py            #   YAML DSL parser
│   │   ├── scheduler.py                  #   EventScheduler (batch, heapq.merge)
│   │   ├── streaming.py                  #   StreamingScheduler (real-time paced)
│   │   └── rng.py                        #   Seeded RNG manager
│   │
│   ├── scenarios/                        # Built-in attack scenario YAML files
│   │   ├── credential_stuffing.yaml      #   Password spray from single IP
│   │   └── mfa_fatigue.yaml              #   Repeated MFA push bombardment
│   │
│   └── emitter/                          # Layer 3: "The Sink"
│       ├── protocols.py                  #   Plugin loader (entry points discovery)
│       ├── jsonl.py                      #   JSONL file writer (orjson)
│       └── console.py                    #   Rich-formatted console output
│
├── infra/                                # Terraform for GCP
│   ├── main.tf                           #   Provider, backend config
│   ├── variables.tf                      #   Project ID, region, image tag, etc.
│   ├── outputs.tf                        #   Registry URI, job name, SA email
│   ├── artifact_registry.tf              #   Docker image repository
│   ├── cloud_run_job.tf                  #   Cloud Run Job definition
│   ├── service_account.tf                #   Minimal-permission SA
│   ├── scheduler.tf                      #   Optional Cloud Scheduler trigger
│   └── terraform.tfvars.example          #   Example variable values
│
├── tests/                                # 74 tests across all layers
│   ├── conftest.py
│   ├── test_schema/
│   │   └── test_log_event.py             #   Serialization, camelCase keys, roundtrip
│   ├── test_entities/
│   │   └── test_factory.py               #   Determinism, ID format, persistence
│   ├── test_engine/
│   │   ├── test_event_builder.py         #   Event construction, targets, determinism
│   │   ├── test_baseline.py              #   Traffic volume, ordering, weekday/weekend
│   │   ├── test_scenario_loader.py       #   YAML loading, failure sequences
│   │   └── test_streaming.py             #   Streaming pacing, stop signal, determinism
│   ├── test_emitter/
│   │   └── test_jsonl.py                 #   JSONL write/read, plugin loader
│   └── test_api/
│       └── test_api.py                   #   Auth, jobs, pagination, streaming, mock IdP
│
└── examples/
    └── config.yaml                       # Example run configuration
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Cloud Run Job / CLI (typer)                                  │
│  synthlog generate / serve / init-pool / list-events          │
├──────────────────────────────────────────────────────────────┤
│  Engine                                                       │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐              │
│  │ Baseline  │  │ YAML Scenario│  │ Scheduler │              │
│  │ Traffic   │  │ (attacks)    │  │ (merge)   │              │
│  └─────┬─────┘  └──────┬───────┘  └─────┬─────┘              │
│        └───────────┬────┘                │                    │
│              EventBuilder                │                    │
├──────────────┬───────────────────────────┤                    │
│  Schema      │  Entities                 │                    │
│  (Pydantic)  │  Pool / Factory / Faker   │                    │
├──────────────┴───────────────────────────┤                    │
│  Emitter Protocol                        ◄────────────────────┘
│  Built-in: JSONL | Console               │
│  External (separate packages via entry    │
│  points): Kafka | Splunk HEC | ...       │
└──────────────────────────────────────────────────────────────┘
```

**Three loosely coupled layers:**

1. **Entities ("the world")** -- A pool of synthetic users, groups, apps, devices, and networks with stable IDs. Generated once via Faker, persisted as JSON, reused across runs.

2. **Engine ("the behavior")** -- Baseline traffic generates realistic session flows (login, MFA, SSO, logout) shaped by time-of-day curves. Attack scenarios are YAML files that inject specific patterns (credential stuffing, MFA fatigue) into the timeline. The scheduler merges all sources by timestamp via `heapq.merge`.

3. **Emitters ("the sink")** -- Pluggable outputs. Built-in: JSONL files (via `orjson`) and Rich console. External sinks register via Python entry points (`synthlog.emitters` group) and are discovered at runtime.

## Creating an External Sink

External emitter packages implement the `Emitter` protocol and register via entry points:

```python
# In your package's emitter module
from synthlog.schema.log_event import LogEvent

class KafkaEmitter:
    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        ...

    def emit(self, event: LogEvent) -> None:
        ...

    def flush(self) -> None:
        ...

    def close(self) -> None:
        ...
```

```toml
# In your package's pyproject.toml
[project.entry-points."synthlog.emitters"]
kafka = "your_package.emitter:KafkaEmitter"
```

Then use it: `uv run synthlog generate --emitter kafka`

## Configuration

Settings can be provided via CLI flags, environment variables (`SYNTHLOG_` prefix), or YAML config:

| Setting | Env Var | CLI Flag | Default |
|---------|---------|----------|---------|
| Seed | `SYNTHLOG_SEED` | `--seed` | `42` |
| Users | `SYNTHLOG_NUM_USERS` | `--users` | `5` |
| Duration (hours) | `SYNTHLOG_DURATION_HOURS` | `--duration` | `8` |
| Emitter | `SYNTHLOG_EMITTER` | `--emitter` | `jsonl` |
| Output path | `SYNTHLOG_OUTPUT_PATH` | `--output` | `output/events.jsonl` |

## Cloud Run Deployment

Automated via CI/CD on tag push (see [CI/CD](#cicd) below). To deploy manually:

```bash
# Build and push
IMAGE=us-central1-docker.pkg.dev/PROJECT/synthlog/synthlog
docker build -t $IMAGE:latest .
docker push $IMAGE:latest

# Deploy to Cloud Run
gcloud run deploy synthlog \
  --image=$IMAGE:latest \
  --region=us-central1 \
  --platform=managed \
  --port=8080 \
  --set-env-vars="SYNTHLOG_API_KEY=your-secret-key"
```

## Development

```bash
# Install with dev + server dependencies
uv pip install -e ".[server,dev]"

# Run tests
uv run pytest -v

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/

# Run all checks
uv run ruff check src/ tests/ && uv run mypy src/ && uv run pytest
```

## CI/CD

GitHub Actions runs on every push and PR:

| Job | Tool | What it checks |
|-----|------|----------------|
| Lint | ruff | Code style and import ordering |
| Type Check | mypy (strict) | Static type safety |
| Test | pytest | 74 tests across all layers |
| Docker Build | docker | Dockerfile builds successfully |

**Deployment** is triggered by pushing a version tag. The pipeline builds the Docker image, pushes it to Artifact Registry, and deploys to Cloud Run via `gcloud run deploy`:

```bash
make release  # or: git tag v0.1.0 && git push origin v0.1.0
```

This runs all CI checks, builds and pushes the Docker image to Artifact Registry, then runs `terraform apply` to update the Cloud Run deployment.

### GCP Authentication (Workload Identity Federation)

The pipeline uses WIF -- no service account keys stored in GitHub. One-time setup:

```bash
# Set your project (replace with your actual project ID)
export PROJECT_ID=your-project-id
export PROJECT_NUM=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# 1. Create Workload Identity Pool
gcloud iam workload-identity-pools create "github" \
  --location="global" \
  --display-name="GitHub Actions"

# 2. Create OIDC Provider (replace YOUR_ORG/lab-de-synthlog with your GitHub org/repo)
gcloud iam workload-identity-pools providers create-oidc "github" \
  --location="global" \
  --workload-identity-pool="github" \
  --display-name="GitHub" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository == 'YOUR_ORG/lab-de-synthlog'" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# 3. Create Service Account (must specify --project to target the correct project)
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions" \
  --project=$PROJECT_ID

# 4. Grant roles to the Service Account
for role in roles/artifactregistry.writer roles/run.admin roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="$role"
done

# 5. Allow GitHub Actions to impersonate the SA (replace YOUR_ORG/lab-de-synthlog)
gcloud iam service-accounts add-iam-policy-binding \
  github-actions@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUM/locations/global/workloadIdentityPools/github/attribute.repository/YOUR_ORG/lab-de-synthlog"
```

### Required GitHub Repository Variables

Set in Settings > Secrets and Variables:

**Variables:**

| Variable | Description |
|----------|-------------|
| `GCP_PROJECT_ID` | GCP project ID |
| `GCP_REGION` | Region (e.g., `us-central1`) |
| `WIF_PROVIDER` | WIF provider resource name |
| `WIF_SERVICE_ACCOUNT` | Service account email |

**Secrets:**

| Secret | Description |
|--------|-------------|
| `SYNTHLOG_API_KEY` | API key passed to Cloud Run as env var |

### Release Commands

```bash
make version        # Show current and next versions
make release        # Bump patch: v0.1.0 -> v0.1.1
make release-minor  # Bump minor: v0.1.x -> v0.2.0
make release-major  # Bump major: v0.x.x -> v1.0.0
make retry          # Re-push latest tag to retrigger deploy
make check          # Run lint + typecheck + tests locally
```

## Supported Event Types

| Event Type | Severity | Description |
|------------|----------|-------------|
| `user.session.start` | INFO | User login |
| `user.session.end` | INFO | User logout |
| `user.authentication.sso` | INFO | Single sign-on to application |
| `user.authentication.auth_via_mfa` | INFO | MFA challenge |
| `user.mfa.factor.activate` | INFO | MFA factor activated |
| `policy.evaluate_sign_on` | INFO | Sign-on policy evaluation |
| `user.account.lock` | WARN | Account locked |
| `application.user_membership.add` | INFO | User assigned to application |
| `group.user_membership.add` | INFO | User added to group |
| `user.lifecycle.activate` | INFO | User account activated |

## License

MIT
