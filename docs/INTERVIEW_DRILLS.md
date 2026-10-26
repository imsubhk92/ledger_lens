# LedgerLens Phase 0 — Interview Drills (Print-Friendly)

**Instructions:** Do not open `PHASE_0_GUIDE.md` until you finish the first round. 2–3 minutes per spoken answer; 20–30 minutes per coding prompt. Score each verbal answer 0–3 for mechanism, real example, failure case and testability. Answers and a rubric appear near the end of the full guide.

## Round A: Architecture + request lifecycle

1. A request gets `422` but the first line in the endpoint is never reached. Walk me through why.
2. FastAPI, Starlette, Uvicorn, Pydantic and ASGI: who owns what?
3. An API has auth, transactions and search. How do you lay out modules and API versioning without giant files?
4. Why use type-checked settings instead of accessing `os.getenv` in every route?
5. What's the practical difference between `@lru_cache` and FastAPI dependency caching?
6. What can a dependency depend on? How does a test replace a dependency?
7. You created one SQLAlchemy session globally and concurrent requests corrupt state. Why?
8. Why does a connection pool belong in lifespan, but a database session usually doesn't?
9. `app.state` vs `request.state` vs `ContextVar`—what goes where?
10. What does `call_next` do? Why can middleware alter both requests and responses?
11. Why are exception handlers sometimes better than raising `HTTPException` inside a domain service?
12. How do you decide whether Redis outage should fail readiness?

## Round B: Failure diagnosis

1. **Crossed log IDs.** Each request writes its ID to a process-global variable. Under load, IDs mismatch. Root cause, correction and test?
2. **Memory leak.** Creating one new client per request; request volume grows memory and socket count. What redesign?
3. **Wrong statuses.** A missing transaction returns `200` with `{error: ...}`; a server bug returns a Python traceback. Which contracts are wrong?
4. **Unreliable tests.** A test passes alone but fails after another test overrides a dependency. How to isolate?
5. **Health paradox.** All health probes return `200` while the database required for all requests is down. What changes to the probes?

## Round C: Implementation prompts

1. Add a process-safe request correlation ID mechanism using middleware + `ContextVar`; ensure headers appear on 404/422/500 and tests demonstrate distinct IDs on two requests.
2. Use a `FakeResource` that records startup/shutdown call counts. Add a dependency wrapper, readiness check and lifecycle test. Show 200/503 behavior under a simulated outage.
3. Add typed pagination validation and a custom sanitized 422 contract. Add parametrized pytest cases at 0, 1, 100 and 101.
4. Add a JSON log field `event` and `duration_ms`. Assert that the logs do **not** contain an injected secret-like query parameter.
5. Create a production-configured app using the factory and prove training-only routes are not registered.

## What a strong interview answer includes

- **Mechanism:** exact control flow or scope rather than a vague definition.
- **Code anchor:** point to one LedgerLens module/function.
- **Tradeoff:** a real reason this approach can fail and when to choose something else.
- **Test:** a deterministic assertion demonstrating the expected behavior.

## Score sheet

| Area | Questions/activities | Target |
|---|---|---|
| Round A | 12 oral | 28/36 points |
| Round B | 5 incidents | 4 correct investigations |
| Round C | 5 coding prompts | Finish any 2 with passing tests |

The complete model answers and commentary for these themes are in `PHASE_0_GUIDE.md`, lesson 0.13. Don't read them until after attempting the interview.
