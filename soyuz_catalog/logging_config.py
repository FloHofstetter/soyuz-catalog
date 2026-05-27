"""Logging configuration for soyuz-catalog.

Replaces the one-line ``logging.basicConfig`` call in the FastAPI lifespan
with a configurable setup that can emit either plain text (default, no
behaviour change for existing users) or JSON lines suitable for log
aggregators. The ``request_id`` from the Request-ID middleware is
injected into every record via a ``logging.Filter`` reading the
module-level ``ContextVar``, so both formatters can reference it
uniformly.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from soyuz_catalog.api.request_context import get_request_id

_TEXT_FORMAT = "%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"

_JSON_FIELDS = ("timestamp", "level", "logger", "message", "request_id")


class RequestIDLogFilter(logging.Filter):
    """Attach the current request ID to every log record.

    Runs before formatting so both text and JSON formatters can reference
    ``%(request_id)s``. Outside a request scope (startup, tests that
    bypass the middleware) the value falls back to ``"-"`` — using a
    sentinel instead of an empty string keeps text log lines aligned.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D102
        record.request_id = get_request_id() or "-"
        return True


class JsonFormatter(logging.Formatter):
    """Minimal JSON-lines formatter.

    One ``json.dumps`` per record with a fixed key set. Deliberately
    hand-rolled — adding ``python-json-logger`` for twenty lines of code
    is not worth the extra dependency, and the key set is small enough
    that future additions (trace IDs, user IDs) stay a local edit.
    """

    def format(self, record: logging.LogRecord) -> str:  # noqa: D102
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str, structured: bool) -> None:
    """Install soyuz-catalog's root logging configuration.

    Idempotent: clears existing handlers on the root logger before
    installing a fresh one. This matters because ``create_app()`` may
    run multiple times in the same process (tests build a new app per
    fixture) and we do not want duplicated handlers stacking up.

    Args:
        level: Logging level name passed through to ``setLevel``
            (``"INFO"``, ``"DEBUG"``, ...).
        structured: If true, emit one JSON object per line. Otherwise,
            emit the conventional soyuz text format with the
            ``[request_id]`` prefix.
    """
    handler = logging.StreamHandler()
    handler.addFilter(RequestIDLogFilter())
    if structured:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(_TEXT_FORMAT))

    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)


__all__ = [
    "JsonFormatter",
    "RequestIDLogFilter",
    "configure_logging",
]
