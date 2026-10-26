"""Structured, correlation-aware logging using Python's standard library.

Only an allowlist of safe request metadata is logged. Never log request bodies,
authorization headers, cookies, JWTs, passwords, or sensitive query strings.
"""
import json
import logging
import sys
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

_SAFE_LOG_FIELDS = ("event", "method", "path", "status_code", "duration_ms", "environment")


def bind_request_id(value: str) -> Token:
    return _request_id.set(value)


def reset_request_id(token: Token) -> None:
    _request_id.reset(token)


def current_request_id() -> str | None:
    return _request_id.get()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": current_request_id(),
        }
        for field in _SAFE_LOG_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            # Tracebacks belong in trusted logs, never in HTTP responses.
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure the application namespace, not unrelated third-party loggers."""
    logger = logging.getLogger("ledgerlens")
    logger.setLevel(level.upper())
    logger.propagate = False
    # Idempotent when create_app is called repeatedly in test suites.
    for old_handler in logger.handlers[:]:
        logger.removeHandler(old_handler)
        old_handler.close()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger
