"""Tests for opt-in real AWS STS credential vending.

By default the temporary-credentials endpoints stay metadata-only: an S3
table gets an empty ``aws_temp_credentials``. With
``SOYUZ_ENABLE_STS_VENDING`` set and the path governed by an external
location bound to an IAM-role credential, soyuz assumes the role via STS
(mocked here with moto) and returns the short-lived keys.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from soyuz_catalog.models import Credential, ExternalLocation
from soyuz_catalog.services.external_location_service import (
    resolve_external_location_for_path,
)
from soyuz_catalog.settings import reset_settings_cache

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
TABLES = "/api/2.1/unity-catalog/tables"
CREDENTIALS = "/api/2.1/unity-catalog/credentials"
EXTERNAL_LOCATIONS = "/api/2.1/unity-catalog/external-locations"
TABLE_CREDS = "/api/2.1/unity-catalog/temporary-table-credentials"
PATH_CREDS = "/api/2.1/unity-catalog/temporary-path-credentials"

_ROLE = "arn:aws:iam::123456789012:role/soyuz-test"


def _bootstrap(client: TestClient) -> None:
    assert client.post(CATALOGS, json={"name": "main"}).status_code == 200
    assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).status_code == 200


def _create_table(client: TestClient, storage_location: str) -> str:
    body: dict[str, Any] = {
        "name": "t",
        "catalog_name": "main",
        "schema_name": "s",
        "table_type": "EXTERNAL",
        "data_source_format": "DELTA",
        "columns": [
            {
                "name": "id",
                "type_text": "bigint",
                "type_json": '{"type":"long"}',
                "type_name": "LONG",
                "position": 0,
            }
        ],
        "storage_location": storage_location,
    }
    r = client.post(TABLES, json=body)
    assert r.status_code == 200, r.text
    return r.json()["table_id"]


def _register_location(client: TestClient, url: str, name: str = "loc") -> None:
    assert (
        client.post(
            CREDENTIALS,
            json={"name": f"cred-{name}", "aws_iam_role": {"role_arn": _ROLE}},
        ).status_code
        == 200
    )
    assert (
        client.post(
            EXTERNAL_LOCATIONS,
            json={"name": name, "url": url, "credential_name": f"cred-{name}"},
        ).status_code
        == 200
    )


@pytest.fixture
def vending_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Turn STS vending on and supply dummy AWS creds for moto to sign."""
    monkeypatch.setenv("SOYUZ_ENABLE_STS_VENDING", "1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")  # pragma: allowlist secret
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    reset_settings_cache()


def test_s3_table_is_empty_stub_when_vending_disabled(client: TestClient) -> None:
    """Default (vending off): an S3 table still gets an empty stub."""
    _bootstrap(client)
    table_id = _create_table(client, "s3://bucket/main/s/t")
    r = client.post(TABLE_CREDS, json={"table_id": table_id, "operation": "READ"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["aws_temp_credentials"] == {}
    assert "expiration_time" in body


def test_s3_table_vends_real_credentials(client: TestClient, vending_enabled: None) -> None:
    """Vending on + a governing IAM-role location yields real STS keys."""
    _bootstrap(client)
    _register_location(client, "s3://bucket")
    table_id = _create_table(client, "s3://bucket/main/s/t")
    with mock_aws():
        r = client.post(TABLE_CREDS, json={"table_id": table_id, "operation": "READ_WRITE"})
    assert r.status_code == 200, r.text
    creds = r.json()["aws_temp_credentials"]
    assert creds["access_key_id"]
    assert creds["secret_access_key"]
    assert creds["session_token"]


def test_no_matching_external_location_returns_stub(
    client: TestClient, vending_enabled: None
) -> None:
    """Vending on but no location governs the path → empty stub."""
    _bootstrap(client)
    _register_location(client, "s3://other-bucket")
    table_id = _create_table(client, "s3://bucket/main/s/t")
    with mock_aws():
        r = client.post(TABLE_CREDS, json={"table_id": table_id, "operation": "READ"})
    assert r.status_code == 200, r.text
    assert r.json()["aws_temp_credentials"] == {}


def test_path_credentials_vend_real(client: TestClient, vending_enabled: None) -> None:
    """The url-keyed path endpoint vends real keys for a governed path."""
    _register_location(client, "s3://bucket")
    with mock_aws():
        r = client.post(
            PATH_CREDS,
            json={"url": "s3://bucket/x/y", "operation": "PATH_READ_WRITE"},
        )
    assert r.status_code == 200, r.text
    assert r.json()["aws_temp_credentials"]["access_key_id"]


def test_sts_failure_degrades_to_stub(
    client: TestClient, vending_enabled: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An STS error is downgraded to an empty stub, not surfaced as 500."""
    _bootstrap(client)
    _register_location(client, "s3://bucket")
    table_id = _create_table(client, "s3://bucket/main/s/t")

    from soyuz_catalog.services import aws_sts

    def _boom(**_: Any) -> Any:
        raise RuntimeError("sts unreachable")

    monkeypatch.setattr(aws_sts, "assume_role_credentials", _boom)
    r = client.post(TABLE_CREDS, json={"table_id": table_id, "operation": "READ"})
    assert r.status_code == 200, r.text
    assert r.json()["aws_temp_credentials"] == {}


def test_resolve_external_location_longest_prefix_and_boundary(
    session_factory: Any,
) -> None:
    """Longest URL prefix wins and prefixes respect the path boundary."""
    session = session_factory()
    try:
        cred = Credential(name="c", aws_iam_role_arn=_ROLE)
        session.add(cred)
        session.flush()
        session.add_all(
            [
                ExternalLocation(name="broad", url="s3://bucket", credential_id=cred.id),
                ExternalLocation(name="narrow", url="s3://bucket/main", credential_id=cred.id),
                ExternalLocation(name="other", url="s3://bucket2", credential_id=cred.id),
            ]
        )
        session.commit()

        narrow = resolve_external_location_for_path(session, "s3://bucket/main/s/t")
        assert narrow is not None and narrow.name == "narrow"
        # "s3://bucket" must NOT match "s3://bucket2/..." (boundary).
        other = resolve_external_location_for_path(session, "s3://bucket2/x")
        assert other is not None and other.name == "other"
        assert resolve_external_location_for_path(session, "s3://nope/x") is None
    finally:
        session.close()
