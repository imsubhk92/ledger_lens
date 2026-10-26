# LedgerLens — Phase 0: Production FastAPI Foundations

**Learning project**, not a payment/transaction production application. This module contains the working application corresponding to **lessons 0.1–0.13**. It intentionally has **no database, JWT, Kafka, RabbitMQ, Redis, Elasticsearch, or vector store yet**: those arrive in later phases when they solve real requirements.

## Prerequisites
- Python 3.11+
- A terminal and an editor

## Setup

```bash
cd ledgerlens
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
cp .env.example .env         # Windows: copy .env.example .env
```

Run (from the folder containing `pyproject.toml`):

```bash
python -m uvicorn app.main:app --reload
```

Try:

```bash
curl -i http://127.0.0.1:8000/api/v1/health/live
curl -i http://127.0.0.1:8000/api/v1/health/ready
curl -i http://127.0.0.1:8000/api/v1/debug/request
curl -i http://127.0.0.1:8000/api/v1/debug/not-found
curl -i 'http://127.0.0.1:8000/api/v1/debug/pagination?limit=200'
curl -i http://127.0.0.1:8000/api/v1/debug/boom
```

Docs: <http://127.0.0.1:8000/docs> and <http://127.0.0.1:8000/openapi.json>.

## Run tests

```bash
python -m pytest -q
python -m pytest --cov=app --cov-report=term-missing
```

`TestClient` runs the FastAPI lifespan correctly **when used as a context manager**. The fixtures use a new application factory instance with controlled `Settings` for each test.

## Current API

| HTTP endpoint | Purpose | Expected |
|---|---|---|
| `GET /api/v1/health/live` | Cheap liveness check | `200` |
| `GET /api/v1/health/ready` | Fake critical resource readiness | `200` / `503` |
| `GET /api/v1/debug/request` | Current correlation ID | `200` |
| `GET /api/v1/debug/dependency` | Settings + resource + request ID injection | `200` |
| `GET /api/v1/debug/not-found` | Domain exception mapping | `404` |
| `GET /api/v1/debug/pagination` | Parameter validation | `200` / `422` |
| `GET /api/v1/debug/boom` | Controlled unexpected failure | `500` |

All routes have `X-Request-ID` and `X-Process-Time` response headers. Every request emits structured JSON logs. **Training-only `/debug` routes are mounted only for `development` and `testing` environments**, not staging/production.

## Folder navigation

```text
ledgerlens/
├── app/
│   ├── api/
│   │   ├── router.py          # Assembles versioned routers
│   │   └── v1/
│   │       ├── health.py      # Liveness and readiness
│   │       └── debug.py       # Demonstration endpoints, non-prod only
│   ├── config.py              # Pydantic Settings
│   ├── dependencies.py        # App settings, fake resource, request context
│   ├── exception_handlers.py  # Stable HTTP error contracts
│   ├── exceptions.py          # HTTP-agnostic domain exceptions
│   ├── lifespan.py            # Resource initialization and cleanup
│   ├── logging_config.py      # JSON formatter + contextvars
│   ├── main.py                # Application factory/composition root
│   ├── middleware.py          # Correlation and timing
│   └── resources.py           # FakeResource lifecycle simulator
├── tests/                     # 19 test cases
├── docs/
│   ├── PHASE_0_GUIDE.md       # Full lessons 0.1–0.13
│   ├── INTERVIEW_DRILLS.md    # Problems, hints, and answer rubric
│   └── CHEATSHEET.md          # Compact reminders
└── pyproject.toml
```

## Request lifecycle

```text
client -> Uvicorn -> FastAPI middleware -> router -> dependencies -> endpoint
       -> exception mapping and response -> middleware headers/logs -> client
```

## What this example deliberately does NOT claim

- `FakeResource` simulates a long-lived resource; it is not a Redis client.
- A simple `request_id` is *correlation*, not a distributed tracing system; OpenTelemetry comes later.
- Middleware timing is HTTP handling latency, not database timing or full streaming duration.
- `ContextVar` request IDs are scoped to this process/context. Worker messages must explicitly propagate correlation metadata.
- The current middleware is an educational, straightforward approach; for extremely large streaming bodies/responses or ASGI-level instrumentation we will study pure ASGI middleware later.
- The application is *training-safe*, but not hardened for untrusted public internet traffic; it lacks authentication, external resource readiness, rate limits and deployments.

## Recommended order

Read `docs/PHASE_0_GUIDE.md`, implement each checkpoint without looking at the supplied files, compare your code, run tests, and then use `docs/INTERVIEW_DRILLS.md` as a closed-book interview.

## Official references

- <https://fastapi.tiangolo.com/tutorial/bigger-applications/>
- <https://fastapi.tiangolo.com/tutorial/dependencies/>
- <https://fastapi.tiangolo.com/advanced/events/>
- <https://fastapi.tiangolo.com/tutorial/middleware/>
- <https://fastapi.tiangolo.com/tutorial/handling-errors/>
- <https://fastapi.tiangolo.com/tutorial/testing/>
- <https://fastapi.tiangolo.com/advanced/testing-dependencies/>
- <https://docs.python.org/3/howto/logging-cookbook.html#use-of-contextvars>
