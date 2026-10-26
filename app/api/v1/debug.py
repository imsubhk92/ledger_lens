"""Training-only routes; intentionally NOT mounted in production or staging."""
import logging
from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import RequestIdDep, ResourceDep, SettingsDep
from app.exceptions import ResourceNotFoundError

router = APIRouter(prefix="/debug", tags=["training only"])
logger = logging.getLogger("ledgerlens.debug")


@router.get("/request")
async def debug_request(request_id: RequestIdDep):
    logger.info("debug_request_seen", extra={"event": "debug_request_seen"})
    return {"request_id": request_id}


@router.get("/not-found")
async def debug_not_found():
    raise ResourceNotFoundError("Transaction", "abc123")


@router.get("/boom")
async def debug_boom():
    raise RuntimeError("Intentional training failure; must not reach clients")


@router.get("/pagination")
async def debug_pagination(limit: Annotated[int, Query(ge=1, le=100)] = 20,
                           offset: Annotated[int, Query(ge=0)] = 0):
    return {"limit": limit, "offset": offset}


@router.get("/dependency")
async def debug_dependency(settings: SettingsDep, resource: ResourceDep, request_id: RequestIdDep):
    return {"service": settings.app_name, "connected": resource.connected,
            "request_id": request_id}
