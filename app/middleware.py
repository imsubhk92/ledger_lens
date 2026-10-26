"""Request context, safe structured access logs, and reliable error headers."""
import logging
import time
from uuid import uuid4

from fastapi import Request, Response

from app.exception_handlers import internal_error_response
from app.logging_config import bind_request_id, reset_request_id

logger = logging.getLogger("ledgerlens.requests")


async def request_context_middleware(request: Request, call_next) -> Response:
    # Server-generated request IDs avoid spoofed/unbounded inbound identifiers.
    request_id = str(uuid4())
    request.state.request_id = request_id
    token = bind_request_id(request_id)
    started = time.perf_counter()
    # Route template is not yet resolved. Do not log raw paths/queries: they may contain PII.
    safe_metadata = {"method": request.method}
    logger.info("request_started", extra={"event": "request_started", **safe_metadata})

    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request_failed", extra={"event": "request_failed", **safe_metadata})
            # Catch unexpected crashes here to ensure correlation headers on HTTP 500.
            # Expected/domain/validation errors are already handled inside FastAPI.
            response = internal_error_response(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        route = request.scope.get("route")
        # E.g. /transactions/{id}, rather than logging sensitive path IDs.
        safe_metadata["path"] = getattr(route, "path", "<unmatched>")
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{duration_ms / 1000:.6f}"
        logger.info("request_completed", extra={
            "event": "request_completed", **safe_metadata,
            "status_code": response.status_code, "duration_ms": duration_ms,
        })
        return response
    finally:
        reset_request_id(token)
