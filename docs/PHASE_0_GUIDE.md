# LedgerLens: Phase 0 — FastAPI Foundation

**Learn by building | Lessons 0.1–0.13 | Starter architecture, observability, testing, interview readiness**

> **Purpose.** Build a small but production-shaped FastAPI foundation that will later support transaction APIs, auth, Redis, Kafka/RabbitMQ workers, search and RAG. We postpone those systems until we can explain the web framework itself. This guide pairs with the runnable code in `app/` and tests in `tests/`. It is written for practical backend interviews as much as for implementation.

## How to use this guide

1. Read the scenario and explain your approach **before** opening a Python file.
2. Implement the checkpoint yourself. Then compare with the supplied solution.
3. Run the indicated command; inspect the returned status, body, and headers.
4. Read the failure scenario and predict what breaks under concurrency, restarts, or worker processes.
5. Run the tests and deliberately break something; learn to trace the failure rather than merely memorize definitions.
6. Complete lesson 0.13 without looking at its answer key. An interview expects reasoning, not syntax recitation.

A foundation is complete when you can trace a request end-to-end, explain the ownership of every resource, inspect logs, reproduce failures, and test these behaviors without manually starting a server.

## Environment and setup

Requires Python 3.11+; tested with FastAPI 0.128.x, Starlette 0.50.x, Pydantic 2.13.x and pytest 9.x (version ranges are intentionally broader in the project file). Commands assume you are in the `ledgerlens` folder.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
python -m uvicorn app.main:app --reload
```

Windows activation: `.venv\Scripts\Activate.ps1`; file copy: `copy .env.example .env`. Visit `http://127.0.0.1:8000/docs` for Swagger UI and `http://127.0.0.1:8000/openapi.json` for the machine-readable contract. Test with `python -m pytest -q`.

---

# 0.1 — What FastAPI is (and is not)

**Scenario.** A junior engineer says, "FastAPI is the web server and Pydantic is the database model." How would you correct that?

FastAPI is an ASGI web framework. **Uvicorn** is an ASGI server: it listens for network requests and invokes the Python ASGI application. **Starlette** provides underlying ASGI, routing, request/response, middleware and lifespan utilities. **Pydantic** validates/parses typed data and helps serialize API data. **FastAPI** brings these together with type-driven request handling, dependency injection, OpenAPI generation and security helpers.

```text
Client --HTTP--> Uvicorn --ASGI--> FastAPI/Starlette --route--> endpoint
                                                  |
                                        Pydantic validation
```

- FastAPI does not itself listen on a TCP port when you merely instantiate `FastAPI()`.
- Uvicorn does not define your business endpoints; it hosts the ASGI app.
- Pydantic models describe data shapes; SQLAlchemy later maps Python classes to database tables. These are distinct roles.
- Automatic docs come from the OpenAPI schema FastAPI generates from routes and type information.

**Try it.** Open `app/main.py`. Locate the `FastAPI(...)` object, then find the `uvicorn app.main:app` command. Explain each segment: module path `app.main` and object `app`.

**Interview answer.** "FastAPI is a Python ASGI framework built on Starlette with Pydantic-powered validation. An ASGI server such as Uvicorn hosts it. Its strength is typed request/response contracts, dependency injection and automatic OpenAPI documentation."

**Misconception to reject.** "Async means every task executes in parallel." ASGI permits concurrent I/O; CPU-bound Python code can still block the event loop.

# 0.2 — HTTP request lifecycle and ASGI

**Scenario.** A client calls `GET /api/v1/health/live`. Where does validation happen, and why might your endpoint's first `print()` never execute?

Typical flow:

```text
network -> Uvicorn -> ASGI -> middleware (request side) -> router
        -> path/query/header/body validation -> dependency graph -> endpoint
        -> response validation/serialization -> middleware (response side)
        -> Uvicorn -> client
```

The exact ordering of dependency resolution, validation and exception handling can depend on their relationships; treat this as a high-level mental model, not a literal fixed execution schedule for every route. Invalid query/body data can produce a 422 response before the endpoint body runs. A dependency can reject the request before business logic runs, for example an auth dependency that returns 401/403.

**ASGI vs WSGI.** WSGI's classic request-response application interface is synchronous. ASGI is designed for async application interaction, including HTTP and WebSockets. The key performance idea is *cooperative I/O concurrency*: a coroutine awaiting network I/O allows other tasks to run. `async def` with CPU-heavy synchronous work still blocks the event loop unless offloaded.

**Try it.** Hit `/api/v1/debug/pagination?limit=200`. Predict whether its endpoint returns a dict. It does not: FastAPI rejects `limit > 100` and the exception handler generates a 422 response.

**Interview follow-up.** "Why is my async route slow?" Investigate blocking calls, CPU work, queries, serialization, connection pools and thread/process boundaries rather than repeating "because Python has the GIL."

# 0.3 — Project structure: separation without architecture theater

**Scenario.** A company has 100 endpoints in one `main.py` file; adding a test breaks unrelated routes. Where should responsibilities go?

The supplied structure is intentionally small:

```text
app/main.py               app composition root
app/config.py             typed configuration
app/api/router.py         API router composition
app/api/v1/health.py      health endpoints
app/api/v1/debug.py       training-only routes
app/dependencies.py       request-facing dependency functions
app/lifespan.py           long-lived resource ownership
app/resources.py          FakeResource
app/middleware.py         request-wide cross-cutting logic
app/logging_config.py     JSON logging and context
app/exceptions.py         business/domain error types
app/exception_handlers.py HTTP mapping
```

The composition root knows which parts to assemble. The feature routers know HTTP endpoints; domain error types do not know FastAPI. Later, **services** will own business workflows, **repositories** will manage persistence operations, **models** will describe persistence, and **schemas** will describe API contracts. Do not add them to Phase 0 just to imitate a directory diagram.

**Checkpoint.** In `app/main.py`, find `create_app`. Trace how configuration, logging, lifespan, middleware, exception handlers and routers are assembled. Why does the app factory make it easier to create isolated test applications?

**Design smell.** An endpoint imports a concrete Redis client, configures the logger, starts a Kafka producer and queries PostgreSQL. It is mixing HTTP behavior, infrastructure ownership, business rules and configuration.

# 0.4 — Configuration and environments

**Scenario.** Your laptop, CI server and production all run the same Python code but need different app names, logging levels, database URLs and secrets.

Use environment variables as the deployment-facing source of configuration. `app/config.py` defines a typed `Settings(BaseSettings)` model. `.env.example` documents expected names; real `.env` values are excluded from version control. Pydantic Settings converts e.g. `DEBUG=true` to a Python boolean and validates constrained values like the environment name.

```python
class Settings(BaseSettings):
    app_name: str = "LedgerLens API"
    environment: Literal["development", "testing", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
```

`get_settings()` is cached with `@lru_cache`, so the configuration is normally constructed once per Python process. The app factory stores the chosen settings in `app.state`; the `get_app_settings` dependency exposes those settings to endpoints, allowing the factory to supply test-specific configuration. These are two different patterns working together: a cached factory default, and per-application state.

**Security rule.** Never commit production credentials. Do not store private keys inside the docs or error messages. A real deployment injects secrets using its secret-management/runtime system. Treat `DEBUG=true` cautiously in public deployments.

**Checkpoint.** Set `APP_NAME=LedgerLens Workshop` in `.env`, restart and call `/api/v1/health/live`. Why is restarting needed when settings are cached?

**Interview follow-up.** Two app instances in one process can receive different `Settings` through `create_app(settings=...)`, even though the `get_settings()` default is cached.

# 0.5 — APIRouter and API versioning

**Scenario.** Health endpoints should live together; transactions, auth and search will eventually be separate packages. How do we assemble them without changing their business code?

`APIRouter` collects related routes. `app/api/v1/health.py` declares `router = APIRouter(prefix="/health", tags=["health"])`. `app/api/router.py` includes it and `app/main.py` adds the root prefix `/api/v1`. The final liveness route is `/api/v1/health/live`.

```text
FastAPI app
└── /api/v1
    ├── /health/live
    ├── /health/ready
    └── /debug/* [development/testing only]
```

Routers aren't new server processes. `include_router` composes routes and lets common prefixes, tags and dependencies be applied at a grouping level. Versioning helps you evolve *breaking public API contracts* deliberately; it does not mean automatically making a v2 for every internal code change.

**Try it.** Find all paths in `/openapi.json`. Change the prefix locally and predict which calls break. Why might a mobile client need the old contract for months after a backend deployment?

# 0.6 — Dependency injection (DI)

**Scenario.** The same endpoint needs settings, the current request ID and a Redis client. How can each concern be independently mocked in tests?

A dependency is a callable FastAPI knows how to resolve, including its own sub-dependencies. The `Annotated` idiom keeps the Python type visible and adds the injection instruction.

```python
def get_request_id(request: Request) -> str:
    return request.state.request_id

RequestIdDep = Annotated[str, Depends(get_request_id)]

@router.get("/request")
async def debug_request(request_id: RequestIdDep):
    return {"request_id": request_id}
```

When a request is handled, FastAPI calls `get_request_id` and injects the resulting string. `SettingsDep` and `ResourceDep` work the same way. A dependency can depend on other dependencies (for example `require_admin` -> `get_current_user` -> `decode_token` -> settings). By default, resolved dependencies are cached *within a request* so a shared dependency generally isn't recomputed multiple times. This is unlike `@lru_cache` which persists across requests within a Python process.

**Don't overuse DI.** A calculator function that multiplies two values does not need to become a dependency. Shared infrastructure, security, reusable validation, pagination and request context usually do.

**Testable design.** The test suite demonstrates `app.dependency_overrides[get_app_settings] = overridden_settings`. Clear overrides in a `finally` block (or fixture teardown) so one test cannot contaminate the next.

**Checkpoint.** Add an endpoint that injects both `SettingsDep` and `RequestIdDep`. Explain how neither value is read directly from globals in the endpoint.

# 0.7 — Lifespan and resource scope

**Scenario.** A worker receives 1,000 HTTP requests. Should each request create a new Redis client/DB engine/HTTP connection pool? Who closes those resources during shutdown?

Use application lifespan for expensive shared resources. In `app/lifespan.py`:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    resource = FakeResource()
    await resource.connect()
    app.state.resource = resource
    try:
        yield  # App serves requests while the context remains open.
    finally:
        await resource.close()
```

*Before `yield`* is startup. *After `yield`* is shutdown. `try/finally` makes cleanup deterministic if the app exits after a successful startup. The resource instance is process-local, not a distributed singleton. Four Uvicorn worker processes do not share Python object memory.

**Critical scope distinction:**

- Application-scoped: DB engine/connection pool, Redis client/pool, Kafka producer, long-lived HTTP client, model loaded in memory.
- Request-/operation-scoped: DB session or transaction, current user, tenant context, request ID.

The `ResourceDep` dependency retrieves `app.state.resource` but the endpoint knows only the returned typed resource. It is *not* correct to share one mutable SQLAlchemy session between unrelated concurrent requests. Later we will create a session per unit of work while reusing the app-level engine/pool.

**Checkpoint.** Run `test_lifespan_connects_once_and_cleans_up`. Predict the values of `connect_count`, `close_count`, and `connected` before, inside and after `with TestClient(app):`.

# 0.8 — Middleware and the request ID

**Scenario.** Hundreds of requests interleave in logs. An incident report gives you one failed response. How do you correlate all events about that request?

Middleware surrounds HTTP request processing. In `app/middleware.py`, `request_context_middleware` generates a server-side UUID, stores it on `request.state.request_id`, binds it to logging context, times `call_next(request)` and adds `X-Request-ID` plus `X-Process-Time` response headers. `request.state` is per request, whereas `app.state` is per app instance. A middleware sees all HTTP requests, even invalid paths; dependencies are typically scoped to matching endpoints or router operations.

```python
request_id = str(uuid4())
request.state.request_id = request_id
start = time.perf_counter()
response = await call_next(request)
duration = time.perf_counter() - start
response.headers["X-Request-ID"] = request_id
```

Our real middleware also logs failures and builds a safe generic 500 response for unhandled exceptions. This ensures correlation headers appear on expected and unexpected failures. It logs the **route template**, when available, instead of arbitrary path parameters, and never logs raw query strings, HTTP request bodies, cookies or authorization tokens. A request ID is a correlation hint, **not** proof of trusted identity or a distributed trace.

**Limitations worth knowing.** This teaching example uses FastAPI/Starlette's convenient `call_next` middleware. Large streaming responses, request-body interception and advanced instrumentation justify learning pure ASGI middleware later. Duration here measures middleware-level request handling, not necessarily the entire time to stream a response body to the client.

**Checkpoint.** Send two requests. Confirm two different `X-Request-ID` values. Call `/debug/request` and verify that the JSON body matches the header. Why is a new UUID better than a mutable module-level `CURRENT_REQUEST_ID` global?

# 0.9 — Exceptions and a stable API error contract

**Scenario.** A transaction ID does not exist. A client submits `limit=200` when the maximum is 100. An endpoint crashes unexpectedly. Should all three return HTTP 200 and an `error` field?

No. Use HTTP semantics and stable machine-readable error codes:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Transaction 'abc123' not found",
    "request_id": "<uuid>"
  }
}
```

- **404**: resource absent; convert `ResourceNotFoundError` in an HTTP exception handler.
- **422**: invalid request data; FastAPI produces `RequestValidationError`, which our handler converts into a sanitized response with the location/type/message of each problem.
- **503**: a critical resource for this service is unavailable; `ServiceUnavailableError`.
- **500**: unhandled application failure; clients get a generic explanation, while trusted logs contain a traceback.
- **405**: the path exists but not for the submitted HTTP method.

Keep domain exceptions HTTP-agnostic so future Kafka consumers, CLI processes, and workers can reuse services without importing FastAPI exceptions. Our handlers live in `app/exception_handlers.py`; the domain exceptions are in `app/exceptions.py`.

**Security lesson.** Never expose SQL statements, internal file paths, stack traces, secrets or private input in an error response. Do not echo rejected Pydantic input values. A user-facing request ID makes support triage much easier.

**Checkpoint.** Call `/debug/not-found`, `/debug/boom`, and `/debug/pagination?limit=200`. Predict their status codes, response `error.code`, and presence of correlation headers before calling them.

# 0.10 — Liveness vs readiness

**Scenario.** The HTTP process is alive but PostgreSQL is unreachable. Should an orchestrator send transaction traffic to it? Should it restart the process every time an optional cache fails?

**Liveness** asks whether the process is alive and responsive. It should normally be a cheap signal, not a dependency sweep. **Readiness** asks whether this instance can currently serve the type of traffic it advertises. If critical database access is impossible, readiness may return `503`. If optional cache is down but the database fallback works, readiness may remain `200`.

This module provides:

```text
GET /api/v1/health/live  -> 200 if the web process responds
GET /api/v1/health/ready -> 200 if FakeResource.connected else 503
```

Do not implement readiness as "ping every external system and fail if anything is down." A RAG endpoint failing to reach an optional LLM provider should not necessarily remove a healthy transaction API instance from service; service-level readiness needs careful scoping. Readiness is not a replacement for detailed operational monitoring.

**Checkpoint.** In a test, set `app.state.resource.connected = False`. Confirm liveness is still `200` and readiness is `503`. Explain why these two statuses are intentionally different.

---

# 0.11 — Structured logging and practical observability

**Scenario.** A customer reports that a request was slow and produced a 500. An application has 8 workers, thousands of concurrent requests and several internal services. How do you find *one request's* path through the system?

## 0.11.1 Logs, metrics and traces have different jobs

- **Logs** are events with useful context: `request_completed`, `resource_closed`, `transaction_import_failed`.
- **Metrics** summarize numbers over time: error rates, requests/second, latency distribution, consumer lag, connection pool pressure.
- **Traces** show causal operations across components: incoming HTTP span -> database query span -> Kafka publish span. A request ID alone is not a trace ID or a full tracing system.

We start with structured logs because they teach consistent event schemas and correlation without requiring external infrastructure.

## 0.11.2 Why `print()` breaks down

A line `Error` does not contain a timestamp, level, service, status code or request ID. Unstructured free-form text is hard to search consistently. JSON logs are objects the runtime/log collector can index:

```json
{
  "timestamp": "2026-10-26T12:00:00+00:00",
  "level": "INFO",
  "logger": "ledgerlens.requests",
  "message": "request_completed",
  "request_id": "7e01...",
  "event": "request_completed",
  "method": "GET",
  "path": "/api/v1/health/live",
  "status_code": 200,
  "duration_ms": 1.42
}
```

The exact numbers/IDs above are illustrative, not an application snapshot. `path` should generally be a normalized **route template**, not a path carrying sensitive identifiers. Never indiscriminately log headers, access tokens, cookies, passwords, request bodies or query strings.

## 0.11.3 Python logging vocabulary

`logging.getLogger("ledgerlens.requests")` identifies a logger. A **LogRecord** carries a message, severity and optional `extra` fields. A **Handler** chooses a destination (we use stdout). A **Formatter** turns each record into text (our `JsonFormatter` uses JSON). **Levels** are generally DEBUG < INFO < WARNING < ERROR < CRITICAL. Use INFO for business/process state, WARNING for recoverable abnormal conditions, ERROR/exception for failures, DEBUG for developer diagnostics. Logging a recovered/expected 404 as ERROR would pollute alerts.

In `app/logging_config.py` we configure just the `ledgerlens` logger namespace, rather than rewriting every library's logger. The formatter allowlists event metadata. Each request gets a `ContextVar` binding for its correlation ID; the middleware resets it in `finally` so a later request does not inherit it.

## 0.11.4 Why `ContextVar`, not a module-level global?

```python
CURRENT_REQUEST_ID = "xyz"  # Bad for concurrent requests
```

Concurrent coroutines could overwrite the global and mix users' logs. `ContextVar` supplies context-local state to async tasks and threads in the intended execution context (see the [Python logging cookbook](https://docs.python.org/3/howto/logging-cookbook.html#use-of-contextvars)). Important qualification: context is not automatically transported across processes or a Kafka/RabbitMQ message; explicitly include correlation metadata in the message when we reach messaging phases. Context propagation also requires attention at thread and task boundaries.

## 0.11.5 Trace one request

1. Run `python -m uvicorn app.main:app --reload`.
2. Request `/api/v1/debug/request` with `curl -i`.
3. Copy the `X-Request-ID` header.
4. Inspect the JSON logs. Find `request_started`, `debug_request_seen` and `request_completed` sharing the same `request_id`.
5. Send `/api/v1/debug/boom`; note `request_failed` logs a traceback, while the HTTP 500 body contains only `INTERNAL_SERVER_ERROR` and a request ID.
6. Send `?token=MY_SECRET_VALUE` to the pagination endpoint and confirm the logs never contain that query value.

## 0.11.6 What to improve in a real system

Use central log collection and retention/access policies; define a standard event schema, a service/version field and trace/span IDs; instrument metrics/histograms, connect OpenTelemetry spans and propagate tracing headers with an explicitly chosen trust boundary. Add sampling where traffic volume demands it, and a redaction policy reviewed against actual data. A logging statement is not a substitute for proper privacy controls.

**Acceptance criteria.** Every request has a correlation header; completed logs include status and duration; no query value/credential is emitted by access logging; expected errors remain controlled; surprising errors have a traceback in internal logs but no traceback in client JSON.

---

# 0.12 — Testing: unit, integration and failure scenarios

**Scenario.** An endpoint returns 200 locally. Can you prove startup/shutdown works, validation rejects bad data, dependency overrides isolate services, and production doesn't expose debug routes?

## 0.12.1 Test pyramid for the foundation

- **Unit:** test the JSON formatter or pure settings parsing without an HTTP request.
- **API/integration:** call the actual ASGI app with FastAPI `TestClient` (HTTPX-based) and verify headers, status codes and bodies.
- **Lifecycle:** enter and exit `with TestClient(app):` and assert shared resources connect exactly once and close once.
- **Fault injection:** make FakeResource unavailable; force a domain exception; trigger a simulated unhandled runtime error.
- **Configuration/security:** verify debug endpoints are absent from a production-configured app and raw queries aren't written to access logs.

The suite currently contains **19 tests**, organized in `tests/test_health.py`, `test_middleware.py`, `test_errors.py`, `test_dependencies.py` and `test_misc.py`.

## 0.12.2 Why `with TestClient(app)` matters

```python
with TestClient(app) as client:
    response = client.get("/api/v1/health/ready")
```

Using the client as a context manager enters and exits the application's ASGI lifespan, triggering startup/shutdown. Merely constructing a `TestClient` object is not the reliable way to test lifespan execution. Our fixture also passes `raise_server_exceptions=False` so tests can inspect HTTP 500 error responses rather than having the client re-raise server exceptions.

## 0.12.3 Fixtures and isolation

`tests/conftest.py` exposes `app` and `client` pytest fixtures. A test application gets explicitly constructed settings with `_env_file=None` so the developer's local `.env` does not alter test results. This example isolates FastAPI state, not an external real DB (one does not exist in Phase 0).

```python
@pytest.fixture
def app():
    return create_app(Settings(environment="testing", _env_file=None))

@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
```

The actual fixture also sets a test-specific app name.

## 0.12.4 Dependency overrides

Suppose a dependency would otherwise call a paid auth provider or external database. `app.dependency_overrides[original_callable] = replacement_callable` allows deterministic testing. **Always clean overrides after the test**, ideally with a fixture or `try/finally`. Overriding a dependency does not automatically test the real dependency; test important real integrations separately when we reach those phases.

## 0.12.5 Test the contract, not just the implementation

For `/debug/not-found`, verify *404*, machine error code, request ID and correlation header. Do not only verify that the response contains the word "not found". For `/health/ready`, simulate failed connectivity and verify *503*, then confirm `/health/live` remains *200*. For `/debug/boom`, verify *500* and prove the internal exception text is absent from the response.

Good failure-driven tests target properties, not internal implementation details:

```python
def test_request_id_is_propagated_to_endpoint_and_headers(client):
    response = client.get("/api/v1/debug/request")
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
```

## 0.12.6 Testing logs reliably

This is a common subtlety: your app may configure its logging handler during fixture setup, outside the current test capture context. Instead of assuming `capsys` always sees the records, the sample test attaches its own `logging.StreamHandler(io.StringIO())` with the JSON formatter, executes a request, then detaches it. This is deterministic and validates the actual log schema. It also tests that raw query string secrets are absent.

## 0.12.7 Run and extend

```bash
python -m pytest -q
python -m pytest --cov=app --cov-report=term-missing
```

Deliberate break/fix lab:

1. Remove middleware's request-ID header assignment. Identify which tests fail.
2. Remove `finally: await resource.close()` from lifespan. Identify the leaked-resource test failure.
3. Remove the `le=100` validation. Identify the 422 test failure.
4. Change production configuration to include debug routes. Identify the security regression.
5. Replace request-local `ContextVar` with a global variable and reason about interleaved concurrent requests.

**Interview distinction.** A passing unit test on `FakeResource` proves its small behavior, but does not prove the real network connection will recover from Redis/Kafka outages. We'll need contract and integration tests against actual infrastructure later.

---

# 0.13 — Phase 0 interview and debugging drills

**How to perform the drill.** Spend 2–3 minutes answering aloud before reading the model answer. You should be able to describe the sequence, point to the corresponding source file and discuss failure cases. A strong interview answer has: (a) a precise mechanism, (b) a concrete LedgerLens example, (c) a tradeoff/limitation, and (d) how you would test it.

## Round A — 12 core interview questions

1. Explain the responsibility split between Uvicorn, ASGI, Starlette, FastAPI and Pydantic.
2. Walk through an HTTP request that fails validation before the endpoint body runs.
3. Why split routers out of `main.py`? What belongs in the composition root?
4. How do you inject environment-specific settings safely, and how does `@lru_cache` differ from the FastAPI dependency cache?
5. What problem does `Depends` solve? Can a dependency depend on another dependency?
6. Which resources are long-lived and which are request-scoped? Why not share one DB session across all requests?
7. In a lifespan context manager, when do code paths before and after `yield` run? What about multiple worker processes?
8. Middleware vs dependency vs service: where should request IDs, authorization, logging and business rules live?
9. What's the difference between `app.state`, `request.state` and a `ContextVar`?
10. Describe a stable 404/422/500/503 HTTP error contract and why HTTP-agnostic domain exceptions help.
11. What is the difference between liveness and readiness? Should Redis outage always fail readiness?
12. How would you test middleware, lifespan, error handling, security of debug routes and log correlation without running a remote server?

## Round B — 5 debugging incidents

**Incident 1 — Request IDs mix across users.** Code uses `CURRENT_REQUEST_ID = uuid4()` as a module global overwritten in each request. At 200 concurrent requests, logs for user A include user B's ID. Identify the race and fix the ownership/context model. Then define how you would test it.

**Incident 2 — Readiness is green even though the API can't serve transactions.** It only returns `{"ok": true}`. Define a realistic readiness contract, distinguish optional cache failure from required database failure, and decide what status a load balancer should see.

**Incident 3 — The first request works; later requests fail after restart.** A Redis-like resource was created at import time and never closed. Explain why lifespan ownership, startup errors, worker processes and cleanup matter. Suggest an integration test.

**Incident 4 — Tests mysteriously pass alone and fail together.** One test overrides `get_app_settings` but never clears `app.dependency_overrides`. Diagnose contamination and propose a safe fixture lifecycle.

**Incident 5 — A 500 error exposes an internal exception and a bearer token appears in logs.** Determine how response construction, logging metadata allowlists and error handlers should differ. Explain what a compliant production log should and should not capture.

## Round C — 3 hands-on coding prompts

**Coding 1 (20 min).** Add a `X-Service-Name` header to every HTTP response using a dependency-compatible settings provider, while preserving request ID and timing behavior. Explain why it might be better to keep the service name in configuration rather than hardcode it.

**Coding 2 (25 min).** Add `GET /api/v1/debug/echo-query?limit=N`, accept `1 <= limit <= 100`, return a stable 422 error for invalid input, and test valid, missing/invalid and boundary cases. Keep the handler out of production.

**Coding 3 (30 min).** Add a simulated `SearchClient` in lifespan, expose it through a dependency, add a readiness rule for an endpoint that requires it, and write a test proving startup occurs once and shutdown cleanup occurs once. Explain why an optional search failure might degrade only search routes rather than the whole app.

## Scoring rubric

| Score | Signal |
|---|---|
| 0 | Cannot explain mechanism or gives incorrect claims |
| 1 | Recites a definition but no real example |
| 2 | Mechanism + source reference + concrete example |
| 3 | Adds failure mode, tradeoff, test and security implications |

A strong Phase 0 exit: at least **28/36** across Round A (12 × 3), solve 4/5 incidents coherently, and independently implement two coding prompts with tests.

## Model answer notes (consult after practice)

1. **Framework stack:** Uvicorn hosts ASGI; Starlette supplies web primitives; FastAPI adds DI/typing/OpenAPI integration; Pydantic validates/parses typed data.
2. **422 path:** request matched a route, Pydantic/FastAPI validated query/body, `RequestValidationError` mapped to a controlled response; endpoint body may never execute.
3. **Router boundaries:** keep feature HTTP routes grouped; `main.py` assembles app-wide concerns. Do not add abstractions without behavior to isolate.
4. **Settings:** external env + typed parsing; Python `lru_cache` is per-process/persistent, while FastAPI's default dependency reuse is per-request.
5. **DI:** endpoint declares a resource/requirement, FastAPI resolves callable and nested dependencies; can override in tests.
6. **Resource lifetime:** share engine/client/pool, not mutable transaction/session state between unrelated concurrent requests. Close at correct lifetime boundary.
7. **Lifespan:** startup before `yield`, shutdown after; once per running app lifespan/worker, not shared memory across worker processes.
8. **Placement:** middleware for request-wide metadata, dependency for auth/permissions/tenant, service for business workflow, lifespan for pooled resources.
9. **State:** `app.state` is app instance storage; `request.state` is request storage; `ContextVar` exposes task-local context to log calls. Cross-process propagation must be explicit.
10. **Errors:** domain exceptions map to client codes, validation stays 422, unexpected 500 stays generic, 503 represents unavailable critical capability. No stack traces in client JSON.
11. **Checks:** liveness asks alive; readiness asks able to serve required traffic. Optional cache failure can degrade gracefully without an unready response.
12. **Testing:** app factory + isolated Settings + `with TestClient` + dependency overrides + failure injection + JSON log capture + route-absence checks.

**Incident solutions:**

- I1: remove global mutable request ID, use per-request state plus bound/reset `ContextVar`, concurrency tests verifying each request's header/body/log correlation.
- I2: readiness should check service-critical dependencies with bounded/time-limited probes, and avoid treating an optional cache as universally fatal; 503 for genuinely unready traffic.
- I3: app-scoped resources belong in lifespan, with cleanup in `finally`; each worker constructs its own; test lifecycle with context-managed client.
- I4: clear `dependency_overrides` reliably using `try/finally` or fixture teardown, create independent app per test.
- I5: catch unexpected failures and send generic 500 with request ID; log diagnostic tracebacks only to secured logs; redact/sanitize, never log auth secrets/raw queries/bodies.

**Coding review:**

- C1: the header matches configured service name across app instances; middleware still stamps headers on 4xx/5xx; tests cover the contract.
- C2: uses `Query(ge=1, le=100)` or equivalently validated dependency, 422 contract applies, no production debug endpoint.
- C3: pool/client initialized/cleaned by lifespan, dependency returns it, test checks `connect_count/close_count`, avoid conflating optional search outages with core transaction readiness.

---

# Phase 0 exit checklist and bridge to Phase 1

- [ ] I can explain the web server/framework/validation roles.
- [ ] I can trace request, middleware, routing, DI, exception mapping and response.
- [ ] I can assemble routers and explain API prefixes.
- [ ] I can configure separate testing/development/production apps safely.
- [ ] I can explain `lru_cache` vs request dependency cache.
- [ ] I can explain request/application scope and lifespan.
- [ ] Every response has a correlation ID and timing header.
- [ ] Logs are structured, useful, and avoid credentials and raw inputs.
- [ ] Domain, HTTP, validation and unexpected failures map to correct statuses.
- [ ] I understand liveness vs readiness under partial dependency outages.
- [ ] I have run all tests; I have broken and repaired at least three.
- [ ] I can complete the interview round with examples and tradeoffs.

**Phase 1 follows next.** Build the transaction CRUD API in memory, introduce request/response Pydantic schemas, `Decimal` for money, validation rules, HTTP status semantics, filtering, pagination and service boundary. We introduce persistence and real SQL transactions only after those HTTP and domain contracts are sound.

## Useful official references

FastAPI official docs: [Bigger apps](https://fastapi.tiangolo.com/tutorial/bigger-applications/) · [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/) · [Lifespan](https://fastapi.tiangolo.com/advanced/events/) · [Middleware](https://fastapi.tiangolo.com/tutorial/middleware/) · [Error handling](https://fastapi.tiangolo.com/tutorial/handling-errors/) · [Testing](https://fastapi.tiangolo.com/tutorial/testing/) · [Dependency overrides](https://fastapi.tiangolo.com/advanced/testing-dependencies/).
