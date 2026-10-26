import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def app():
    # Controlled settings: isolated from any developer's local .env values.
    return create_app(Settings(environment="testing", app_name="LedgerLens Test", _env_file=None))


@pytest.fixture
def client(app):
    # Context manager is mandatory for triggering lifespan startup/shutdown.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
