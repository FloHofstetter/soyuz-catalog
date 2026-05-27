"""Regression tests for the normalised 422 error envelope."""

from __future__ import annotations

from fastapi.testclient import TestClient

CATALOGS = "/api/2.1/unity-catalog/catalogs"


def test_422_uses_envelope_on_missing_field(client: TestClient) -> None:
    r = client.post(CATALOGS, json={})
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "INVALID_ARGUMENT"
    assert body["message"]
    assert body["request_id"] == r.headers["X-Request-ID"]
    assert isinstance(body["details"], list)
    assert body["details"]


def test_422_uses_envelope_on_extra_forbidden_field(client: TestClient) -> None:
    # extra="forbid" fires via FastAPI's RequestValidationError path, so
    # this covers the normalisation of pydantic's "extra_forbidden" case.
    r = client.post(CATALOGS, json={"name": "c", "nope": 1})
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "INVALID_ARGUMENT"
    assert "nope" in body["message"]
    assert body["request_id"] is not None


def test_422_preserves_pagination_out_of_range(client: TestClient) -> None:
    r = client.get(CATALOGS, params={"max_results": -1})
    assert r.status_code == 422
    body = r.json()
    assert body["error_code"] == "INVALID_ARGUMENT"
    assert body["request_id"] is not None

    r = client.get(CATALOGS, params={"max_results": 1001})
    assert r.status_code == 422
    assert r.json()["error_code"] == "INVALID_ARGUMENT"
