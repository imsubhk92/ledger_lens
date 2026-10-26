def test_liveness_reports_config(client):
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive", "service": "LedgerLens Test", "environment": "testing"}


def test_readiness_is_200_with_connected_resource(client):
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_is_503_without_critical_resource(app, client):
    app.state.resource.connected = False
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert client.get("/api/v1/health/live").status_code == 200


def test_lifespan_connects_once_and_cleans_up(app):
    from fastapi.testclient import TestClient
    assert not hasattr(app.state, "resource")
    with TestClient(app) as local_client:
        assert local_client.get("/api/v1/health/ready").status_code == 200
        resource = app.state.resource
        assert resource.connect_count == 1
        assert resource.close_count == 0
    assert resource.connected is False
    assert resource.close_count == 1
