def test_domain_exception_returns_stable_404(client):
    response = client.get("/api/v1/debug/not-found")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "RESOURCE_NOT_FOUND"
    assert error["message"] == "Transaction 'abc123' not found"
    assert error["request_id"] == response.headers["X-Request-ID"]


def test_validation_error_returns_sanitized_422(client):
    response = client.get("/api/v1/debug/pagination?limit=200")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"][0]["location"] == ["query", "limit"]


def test_unexpected_error_becomes_generic_500_with_headers(client):
    response = client.get("/api/v1/debug/boom")
    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "INTERNAL_SERVER_ERROR"
    assert error["request_id"] == response.headers["X-Request-ID"]
    assert "Intentional training" not in str(response.json())
    assert "X-Process-Time" in response.headers


def test_method_not_allowed_becomes_405(client):
    response = client.post("/api/v1/health/live")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "HTTP_ERROR"
