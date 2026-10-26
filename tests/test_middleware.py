import io
import json
import logging
import re

from app.logging_config import JsonFormatter


def test_request_id_is_propagated_to_endpoint_and_headers(client):
    response = client.get("/api/v1/debug/request")
    assert response.status_code == 200
    assert response.json()["request_id"] == response.headers["X-Request-ID"]
    assert re.fullmatch(r"[0-9a-f-]{36}", response.headers["X-Request-ID"])


def test_request_ids_are_distinct_per_request(client):
    first = client.get("/api/v1/health/live")
    second = client.get("/api/v1/health/live")
    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]


def test_elapsed_header_is_nonnegative_number(client):
    response = client.get("/api/v1/health/live")
    assert float(response.headers["X-Process-Time"]) >= 0


def test_even_404_responses_get_request_id(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == response.json()["error"]["request_id"]


def test_access_logging_emits_json_without_query_string(client):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("ledgerlens")
    logger.addHandler(handler)
    try:
        client.get("/api/v1/debug/pagination?limit=7&offset=1&token=NEVER_LOG_THIS")
    finally:
        logger.removeHandler(handler)
    text = stream.getvalue()
    events = [json.loads(line) for line in text.splitlines() if line.startswith("{")]
    completed = [e for e in events if e.get("event") == "request_completed"]
    assert any(e["status_code"] == 200 and e["path"] == "/api/v1/debug/pagination" for e in completed)
    assert all(e.get("request_id") for e in completed)
    assert "NEVER_LOG_THIS" not in text
