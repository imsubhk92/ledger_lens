"""Liveness is cheap. Readiness checks only this lesson's critical fake resource."""
from fastapi import APIRouter

from app.dependencies import ResourceDep, SettingsDep
from app.exceptions import ServiceUnavailableError

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness(settings: SettingsDep):
    return {"status": "alive", "service": settings.app_name, "environment": settings.environment}


@router.get("/ready")
async def readiness(resource: ResourceDep):
    if not resource.connected:
        raise ServiceUnavailableError()
    return {"status": "ready"}
