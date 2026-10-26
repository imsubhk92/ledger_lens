"""Resource ownership is centralized; startup/shutdown each happen once per app lifespan."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.resources import FakeResource

logger = logging.getLogger("ledgerlens.lifecycle")


@asynccontextmanager
async def lifespan(app: FastAPI):
    resource = FakeResource()
    await resource.connect()
    app.state.resource = resource
    logger.info("resource_connected", extra={"event": "resource_connected"})
    try:
        yield
    finally:
        await resource.close()
        logger.info("resource_closed", extra={"event": "resource_closed"})
