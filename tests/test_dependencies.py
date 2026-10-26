from app.config import Settings
from app.dependencies import get_app_settings


def test_dependency_composition_returns_resource_and_settings(client):
    response = client.get("/api/v1/debug/dependency")
    assert response.status_code == 200
    assert response.json()["connected"] is True
    assert response.json()["service"] == "LedgerLens Test"
    assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_dependency_override_is_isolated_and_cleaned_up(app, client):
    def overridden_settings() -> Settings:
        return Settings(app_name="Mocked Service", environment="testing", _env_file=None)

    app.dependency_overrides[get_app_settings] = overridden_settings
    try:
        response = client.get("/api/v1/health/live")
        assert response.json()["service"] == "Mocked Service"
    finally:
        app.dependency_overrides.clear()
    assert client.get("/api/v1/health/live").json()["service"] == "LedgerLens Test"
