import json
import logging

from app.config import Settings
from app.logging_config import JsonFormatter, bind_request_id, reset_request_id
from app.main import create_app


def test_log_formatter_attaches_context_and_allowed_fields():
    formatter = JsonFormatter()
    token = bind_request_id("request-123")
    try:
        record = logging.LogRecord("ledgerlens.test", logging.INFO, __file__, 1,
                                   "example_event", (), None)
        record.event = "unit_test"
        record.status_code = 201
        data = json.loads(formatter.format(record))
    finally:
        reset_request_id(token)
    assert data["request_id"] == "request-123"
    assert data["event"] == "unit_test"
    assert data["status_code"] == 201
    assert data["level"] == "INFO"


def test_prod_does_not_register_training_routes():
    from fastapi.testclient import TestClient
    app = create_app(Settings(environment="production", debug=False, _env_file=None))
    with TestClient(app) as client:
        assert client.get("/api/v1/debug/boom").status_code == 404
        assert client.get("/api/v1/health/live").status_code == 200


def test_typed_configuration_parses_environment(monkeypatch):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("APP_NAME", "Environment Name")
    settings = Settings(_env_file=None)
    assert settings.debug is True
    assert settings.app_name == "Environment Name"


def test_openapi_contains_health_routes(client):
    data = client.get("/openapi.json").json()
    assert "/api/v1/health/live" in data["paths"]
    assert "/api/v1/health/ready" in data["paths"]
