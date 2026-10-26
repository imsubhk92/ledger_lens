"""Translate domain/validation errors into stable HTTP response contracts."""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import ResourceNotFoundError, ServiceUnavailableError


def error_response(request: Request, *, status_code: int, code: str, message: str,
                   details: list[dict] | None = None) -> JSONResponse:
    error = {
        "code": code,
        "message": message,
        "request_id": getattr(request.state, "request_id", None),
    }
    if details is not None:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"error": error})


async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError) -> JSONResponse:
    return error_response(request, status_code=404, code="RESOURCE_NOT_FOUND", message=str(exc))


async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError) -> JSONResponse:
    return error_response(request, status_code=503, code="SERVICE_UNAVAILABLE", message=str(exc))


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Do not echo rejected input: credentials or private data may be present.
    details = [{"location": list(e["loc"]), "message": e["msg"], "type": e["type"]}
               for e in exc.errors()]
    return error_response(request, status_code=422, code="VALIDATION_ERROR",
                          message="Request validation failed", details=details)


async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Handles FastAPI HTTPException AND framework-generated 404/405 errors.
    return error_response(request, status_code=exc.status_code, code="HTTP_ERROR",
                          message=str(exc.detail))


def internal_error_response(request: Request) -> JSONResponse:
    # Called from the request-context middleware so even unexpected errors receive headers.
    return error_response(request, status_code=500, code="INTERNAL_SERVER_ERROR",
                          message="An unexpected server error occurred")
