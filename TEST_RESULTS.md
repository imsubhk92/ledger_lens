# Phase 0 validation snapshot

Ran locally (2026-10-26) using `python -m pytest --cov=app --cov-report=term-missing -q`.

**19 tests passed. 211/211 counted application statements covered (100% statement coverage).**

Coverage is a useful signal that the teaching code paths are exercised. It **does not prove absence of bugs, concurrency safety under load, production security, or integration reliability with Kafka/Postgres/Redis** (those technologies are intentionally not present yet).

Verified checks include:
- typed environment parsing, application factory, debug endpoint absent in production
- lifespan startup/shutdown and resource connection counts
- liveness vs readiness under simulated critical-resource failure
- request-scoped UUID and `X-Request-ID` header
- `X-Process-Time` header, correlation into JSON logs, no query-string logging
- dependency composition and test override cleanup
- domain 404, framework 405, validation 422 and sanitized unexpected 500
- OpenAPI health paths

Reproduce:

```bash
python -m pip install -e '.[dev]'
python -m pytest --cov=app --cov-report=term-missing -q
```
