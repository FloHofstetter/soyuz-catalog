"""Contract: every 4xx/5xx carries the soyuz envelope + request_id.

Walks a curated list of known-error endpoints covering each status code
the API can emit. Lighter than a middleware audit and easy to extend
whenever a new error path appears.
"""

from __future__ import annotations

from collections.abc import Callable

import httpx
from fastapi.testclient import TestClient

from soyuz_catalog.api.main import create_app

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"


def _assert_envelope(r: httpx.Response) -> None:
    assert 400 <= r.status_code < 600, f"unexpected status {r.status_code}"
    body = r.json()
    assert body.get("error_code"), body
    assert body.get("message"), body
    assert body.get("request_id"), body
    assert body["request_id"] == r.headers.get("X-Request-ID")


def _case_404(c: TestClient) -> httpx.Response:
    return c.get(f"{CATALOGS}/does-not-exist")


def _case_409(c: TestClient) -> httpx.Response:
    assert c.post(CATALOGS, json={"name": "dup"}).status_code == 200
    return c.post(CATALOGS, json={"name": "dup"})


def _case_400_bad_token(c: TestClient) -> httpx.Response:
    return c.get(CATALOGS, params={"page_token": "garbage"})


def _case_400_bad_storage(c: TestClient) -> httpx.Response:
    assert c.post(CATALOGS, json={"name": "c"}).status_code == 200
    return c.post(
        SCHEMAS,
        json={
            "name": "s",
            "catalog_name": "c",
            "storage_root": "hdfs://namenode/schema",
        },
    )


def _case_422_missing(c: TestClient) -> httpx.Response:
    return c.post(CATALOGS, json={})


def _case_422_pagination(c: TestClient) -> httpx.Response:
    return c.get(CATALOGS, params={"max_results": -1})


CASES: list[tuple[str, Callable[[TestClient], httpx.Response], int]] = [
    ("404", _case_404, 404),
    ("409", _case_409, 409),
    ("400_bad_token", _case_400_bad_token, 400),
    ("400_bad_storage", _case_400_bad_storage, 400),
    ("422_missing", _case_422_missing, 422),
    ("422_pagination", _case_422_pagination, 422),
]


def test_every_known_error_has_envelope(client: TestClient) -> None:
    for label, case, expected in CASES:
        r = case(client)
        assert r.status_code == expected, f"{label}: got {r.status_code} {r.text}"
        _assert_envelope(r)


def test_500_fallback_has_envelope() -> None:
    app = create_app()

    @app.get("/__boom__")
    def _boom() -> None:
        raise RuntimeError("kaboom")

    c = TestClient(app, raise_server_exceptions=False)
    r = c.get("/__boom__")
    assert r.status_code == 500
    _assert_envelope(r)
