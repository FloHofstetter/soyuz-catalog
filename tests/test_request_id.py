"""Tests for the Request-ID middleware and the error envelope it feeds."""

from __future__ import annotations

import re
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from soyuz_catalog.api.main import create_app
from soyuz_catalog.api.middleware import RequestIDMiddleware

_HEX_RE = re.compile(r"^[0-9a-f]{32}$")

CATALOGS = "/api/2.1/unity-catalog/catalogs"


def _is_uuid_hex(value: str) -> bool:
    try:
        return uuid.UUID(value).hex == value
    except ValueError:
        return False


def test_mints_uuid_when_header_absent(client: TestClient) -> None:
    r = client.get("/healthz")
    rid = r.headers.get("X-Request-ID")
    assert rid is not None
    assert _HEX_RE.match(rid), rid
    assert _is_uuid_hex(rid)


def test_honours_valid_inbound_request_id(client: TestClient) -> None:
    rid = uuid.uuid4().hex
    r = client.get("/healthz", headers={"X-Request-ID": rid})
    assert r.headers["X-Request-ID"] == rid


def test_rejects_malformed_inbound_request_id(client: TestClient) -> None:
    r = client.get("/healthz", headers={"X-Request-ID": "; DROP TABLE --"})
    out = r.headers["X-Request-ID"]
    assert out != "; DROP TABLE --"
    assert _is_uuid_hex(out)


def test_request_id_differs_across_requests(client: TestClient) -> None:
    a = client.get("/healthz").headers["X-Request-ID"]
    b = client.get("/healthz").headers["X-Request-ID"]
    assert a != b


def test_error_body_contains_request_id(client: TestClient) -> None:
    r = client.get(f"{CATALOGS}/does-not-exist")
    assert r.status_code == 404
    body = r.json()
    assert body["error_code"] == "NOT_FOUND"
    assert body["request_id"] == r.headers["X-Request-ID"]


def test_500_has_envelope_and_request_id() -> None:
    """A route raising RuntimeError hits the fallback handler, not Starlette."""
    app = create_app()

    @app.get("/__boom__")
    def _boom() -> None:
        raise RuntimeError("kaboom")

    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/__boom__")
    assert r.status_code == 500
    body = r.json()
    assert body["error_code"] == "INTERNAL"
    assert body["message"] == "Internal server error."
    assert body["request_id"] == r.headers["X-Request-ID"]
    assert _is_uuid_hex(body["request_id"])


def test_middleware_is_registered() -> None:
    """Smoke test: create_app() wires RequestIDMiddleware at least once."""
    app: FastAPI = create_app()
    assert any(m.cls is RequestIDMiddleware for m in app.user_middleware)
