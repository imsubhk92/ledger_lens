# Phase 0 Quick Reference

| Question | Choose | Why |
|---|---|---|
| Who listens on TCP? | Uvicorn | ASGI web server |
| Who provides routing + middleware plumbing? | Starlette / FastAPI | Web application layer |
| Who validates typed data? | Pydantic via FastAPI | Schema contract |
| Group related routes? | APIRouter | Feature boundaries |
| Read env/config? | BaseSettings | Typed, validated configuration |
| Construct DB engine/client at startup? | Lifespan | Shared resource ownership and cleanup |
| Obtain DB session per request? | Yield dependency | Request/operation isolation |
| Get current user/permissions? | Dependencies | Reusable per-route security |
| Add request ID/timing to each HTTP request? | Middleware | Cross-cutting behavior |
| Store per-request ID for endpoints? | request.state | Isolated to request |
| Share resource for app worker? | app.state | Process/app-local state |
| Propagate request ID to logging calls? | ContextVar | Async-safe context binding |
| Convert domain 404 into JSON contract? | Exception handler | HTTP boundary |
| Process alive? | Liveness | Cheap process probe |
| Able to serve intended traffic? | Readiness | Critical dependencies |
| Test startup/shutdown? | with TestClient(app) | Enters lifespan context |
| Replace external dependencies in a unit/API test? | dependency_overrides | Deterministic isolation |

## Commands

```bash
python -m pip install -e '.[dev]'
python -m uvicorn app.main:app --reload
python -m pytest -q
python -m pytest --cov=app --cov-report=term-missing
```

## Response status quick guide

`200` success; `404` missing resource; `405` method not allowed; `422` validation failed; `500` unexpected error (generic client response); `503` service not ready. All are subject to your API's explicit contract.

## Essential failure cases

- Four workers -> four process-local app resources and separate Python globals.
- One mutable global request ID -> corrupt correlation under concurrent requests.
- One shared DB session -> cross-request transaction/state interference.
- Import-time clients -> unclear ownership and shutdown semantics.
- `raise HTTPException` everywhere -> domain becomes tied to HTTP.
- Logging raw headers/queries/bodies -> privacy and credential disclosure risks.
- No TestClient context manager -> lifespan tests may not run startup/teardown.
