![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Tests: 53 passing](https://img.shields.io/badge/tests-53%20passing-brightgreen)
![Type Checked: mypy strict](https://img.shields.io/badge/type%20checked-mypy%20strict-blue)
![Linting: ruff](https://img.shields.io/badge/linting-ruff-orange)
![Container: Cloud Run](https://img.shields.io/badge/container-Cloud%20Run-4285F4?logo=googlecloud&logoColor=white)
![IaC: Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform&logoColor=white)

# synthlog

A synthetic log event producer for **detection engineering**, SIEM rule testing, and security training data generation. Produces realistic, schema-correct identity provider system log events with configurable baseline traffic and injectable attack scenarios.

## Features

- **Realistic entity model** -- Synthetic users, groups, applications, devices, and networks with stable identifiers and correlated attributes
- **Baseline traffic** -- Time-of-day weighted workday patterns (login bursts at 9am, quiet at 3am, reduced weekends)
- **Attack scenario injection** -- YAML-defined attack patterns (credential stuffing, MFA fatigue) layered on top of baseline noise
- **Deterministic output** -- Seedable RNG produces byte-for-byte identical output for regression testing
- **Plugin-based sinks** -- Built-in JSONL and console emitters; external sinks (Kafka, Splunk HEC, etc.) via Python entry points
- **Cloud Run ready** -- Dockerfile and Terraform for GCP Cloud Run Job deployment with optional Cloud Scheduler trigger

## Quickstart

```bash
# Install
pip install -e ".[dev]"

# Generate 8 hours of synthetic events for 5 users with a credential stuffing attack
synthlog generate --seed 42 --users 5 --duration 8 --scenario credential_stuffing -o output/events.jsonl

# Pretty-print to console
synthlog generate --emitter console --duration 1

# Create and persist an entity pool
synthlog init-pool --seed 42 --users 10 -o pool.json

# List supported event types
synthlog list-events
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
│   ├── engine/                           # Layer 2: "The Behavior"
│   │   ├── protocols.py                  #   Scenario and Emitter protocol definitions
│   │   ├── event_builder.py              #   Builds LogEvent from entities + event type
│   │   ├── baseline.py                   #   BaselineTraffic (workday patterns)
│   │   ├── scenario_loader.py            #   YAML DSL parser
│   │   ├── scheduler.py                  #   EventScheduler (heapq.merge by timestamp)
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
├── tests/                                # 53 tests across all layers
│   ├── conftest.py
│   ├── test_schema/
│   │   └── test_log_event.py             #   Serialization, camelCase keys, roundtrip
│   ├── test_entities/
│   │   └── test_factory.py               #   Determinism, ID format, persistence
│   ├── test_engine/
│   │   ├── test_event_builder.py         #   Event construction, targets, determinism
│   │   ├── test_baseline.py              #   Traffic volume, ordering, weekday/weekend
│   │   └── test_scenario_loader.py       #   YAML loading, failure sequences
│   └── test_emitter/
│       └── test_jsonl.py                 #   JSONL write/read, plugin loader
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

Then use it: `synthlog generate --emitter kafka`

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

```bash
# Build and push
docker build -t us-central1-docker.pkg.dev/PROJECT/synthlog/synthlog:latest .
docker push us-central1-docker.pkg.dev/PROJECT/synthlog/synthlog:latest

# Deploy with Terraform
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your project ID
terraform init
terraform apply

# Trigger manually
gcloud run jobs execute synthlog-generator --region us-central1
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run all checks
ruff check src/ tests/ && mypy src/ && pytest
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
