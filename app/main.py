"""Application composition root. Run with: uvicorn app.main:app --reload"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import make_api_router
from app.config import Settings, get_settings
from app.exception_handlers import (
    http_error_handler,
    resource_not_found_handler,
    service_unavailable_handler,
    validation_error_handler,
)
from app.exceptions import ResourceNotFoundError, ServiceUnavailableError
from app.lifespan import lifespan
from app.logging_config import configure_logging
from app.middleware import request_context_middleware


def create_app(settings: Settings | None = None) -> FastAPI:
    actual = settings if settings is not None else get_settings()
    configure_logging(actual.log_level)
    app = FastAPI(
        title=actual.app_name, debug=actual.debug, lifespan=lifespan, version="0.1.0"
    )
    app.state.settings = actual
    app.middleware("http")(request_context_middleware)

    app.add_exception_handler(ResourceNotFoundError, resource_not_found_handler)
    app.add_exception_handler(ServiceUnavailableError, service_unavailable_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)

    app.include_router(
        make_api_router(
            include_training_routes=actual.environment in ("development", "testing")
        ),
        prefix=actual.api_v1_prefix,
    )
    return app


app = create_app()
