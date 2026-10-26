"""Request-facing access to application resources and request-specific state."""
from typing import Annotated

from fastapi import Depends, Request

from app.config import Settings
from app.resources import FakeResource


def get_app_settings(request: Request) -> Settings:
    # The factory picks the actual settings; tests can override this dependency.
    return request.app.state.settings


def get_resource(request: Request) -> FakeResource:
    return request.app.state.resource


def get_request_id(request: Request) -> str:
    return request.state.request_id


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
ResourceDep = Annotated[FakeResource, Depends(get_resource)]
RequestIdDep = Annotated[str, Depends(get_request_id)]
