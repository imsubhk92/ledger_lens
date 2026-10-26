"""Root API composition. Feature routers remain independent."""
from fastapi import APIRouter

from app.api.v1 import health


def make_api_router(*, include_training_routes: bool) -> APIRouter:
    router = APIRouter()
    router.include_router(health.router)
    if include_training_routes:
        from app.api.v1 import debug
        router.include_router(debug.router)
    return router
