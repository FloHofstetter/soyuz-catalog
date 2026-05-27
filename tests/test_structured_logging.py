"""Unit tests for the JSON / text logging configuration."""

from __future__ import annotations

import json
import logging

from soyuz_catalog.api.request_context import request_id_var
from soyuz_catalog.logging_config import (
    JsonFormatter,
    RequestIDLogFilter,
    configure_logging,
)


def _make_record(msg: str = "hello") -> logging.LogRecord:
    return logging.LogRecord(
        name="soyuz_catalog.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )


def test_filter_attaches_request_id_from_contextvar() -> None:
    record = _make_record()
    token = request_id_var.set("abc123")
    try:
        assert RequestIDLogFilter().filter(record) is True
    finally:
        request_id_var.reset(token)
    assert record.request_id == "abc123"  # type: ignore[attr-defined]


def test_filter_falls_back_when_no_request_scope() -> None:
    record = _make_record()
    assert RequestIDLogFilter().filter(record) is True
    assert record.request_id == "-"  # type: ignore[attr-defined]


def test_json_formatter_emits_expected_keys() -> None:
    record = _make_record("a message")
    RequestIDLogFilter().filter(record)
    out = JsonFormatter().format(record)
    payload = json.loads(out)
    assert payload["level"] == "INFO"
    assert payload["logger"] == "soyuz_catalog.test"
    assert payload["message"] == "a message"
    assert payload["request_id"] == "-"
    assert "timestamp" in payload


def test_json_formatter_includes_exc_info() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="t",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="oops",
            args=(),
            exc_info=sys.exc_info(),
        )
    RequestIDLogFilter().filter(record)
    payload = json.loads(JsonFormatter().format(record))
    assert "ValueError: boom" in payload["exc_info"]


def test_configure_logging_text_mode_installs_single_handler() -> None:
    configure_logging("INFO", structured=False)
    root = logging.getLogger()
    assert len(root.handlers) == 1
    formatter = root.handlers[0].formatter
    assert formatter is not None
    assert not isinstance(formatter, JsonFormatter)


def test_configure_logging_json_mode_installs_json_formatter() -> None:
    configure_logging("DEBUG", structured=True)
    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)
    assert root.level == logging.DEBUG
    # Reset so we don't leak JSON formatting into other tests' log capture.
    configure_logging("INFO", structured=False)
