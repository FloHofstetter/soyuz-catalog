"""Tests for ``POST /temporary-path-credentials``.

Mirrors the per-scheme routing pattern from
``tests/test_temporary_credentials.py`` but for the path-addressed
variant. Locks down the shared
:func:`soyuz_catalog.services.credentials_service._stub_credentials`
dispatch — same empty-cloud-object shapes, same expiration-only
fallback on ``file``, same ``UNKNOWN_*_OPERATION`` rejection policy.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

PATH_CREDS = "/api/2.1/unity-catalog/temporary-path-credentials"


@pytest.mark.parametrize(
    ("url", "cloud_key"),
    [
        ("s3://bucket/path", "aws_temp_credentials"),
        ("s3a://bucket/path", "aws_temp_credentials"),
        ("abfss://container@acct.dfs.core.windows.net/path", "azure_user_delegation_sas"),
        ("gs://bucket/path", "gcp_oauth_token"),
    ],
)
def test_path_credentials_routes_per_scheme(
    client: TestClient,
    url: str,
    cloud_key: str,
) -> None:
    r = client.post(PATH_CREDS, json={"url": url, "operation": "PATH_READ"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert cloud_key in body
    assert body[cloud_key] == {}
    for other in ("aws_temp_credentials", "azure_user_delegation_sas", "gcp_oauth_token"):
        if other != cloud_key:
            assert other not in body
    assert body["expiration_time"] > 0


def test_path_credentials_file_scheme_returns_expiration_only(
    client: TestClient,
) -> None:
    r = client.post(
        PATH_CREDS,
        json={"url": "file:///tmp/foo", "operation": "PATH_READ_WRITE"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == {"expiration_time"}
    assert body["expiration_time"] > 0


def test_path_credentials_accepts_path_create_table(client: TestClient) -> None:
    r = client.post(
        PATH_CREDS,
        json={"url": "s3://bucket/t", "operation": "PATH_CREATE_TABLE"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["aws_temp_credentials"] == {}


def test_path_credentials_rejects_unknown_operation_sentinel(
    client: TestClient,
) -> None:
    r = client.post(
        PATH_CREDS,
        json={"url": "s3://bucket/t", "operation": "UNKNOWN_PATH_OPERATION"},
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_path_credentials_rejects_unsupported_scheme(client: TestClient) -> None:
    r = client.post(
        PATH_CREDS,
        json={"url": "ftp://example.com/x", "operation": "PATH_READ"},
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_path_credentials_rejects_bare_path(client: TestClient) -> None:
    r = client.post(
        PATH_CREDS,
        json={"url": "/bare/path", "operation": "PATH_READ"},
    )
    assert r.status_code == 400


def test_path_credentials_rejects_garbage_operation(client: TestClient) -> None:
    r = client.post(
        PATH_CREDS,
        json={"url": "s3://bucket/x", "operation": "READ"},
    )
    assert r.status_code == 422


def test_path_credentials_rejects_extra_field(client: TestClient) -> None:
    r = client.post(
        PATH_CREDS,
        json={"url": "s3://bucket/x", "operation": "PATH_READ", "bogus": 1},
    )
    assert r.status_code == 422


def test_path_credentials_missing_url_is_422(client: TestClient) -> None:
    r = client.post(PATH_CREDS, json={"operation": "PATH_READ"})
    assert r.status_code == 422
