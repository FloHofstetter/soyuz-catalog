"""Tests for POST /temporary-table-credentials and /temporary-volume-credentials.

Both endpoints are spec-conformant stubs: the response carries an
empty cloud-specific object keyed off the resolved row's
``storage_location`` scheme — ``s3``/``s3a`` →
``aws_temp_credentials: {}``, ``abfss`` → ``azure_user_delegation_sas: {}``,
``gs`` → ``gcp_oauth_token: {}``, ``file`` / legacy → expiration-only.
Real tokens are never vended (cloud credential vending is out of
scope; see README design principle 3).

These tests lock down the per-scheme routing plus the service-layer
validation rules: 404 on unknown id, 400 on the
``UNKNOWN_*_OPERATION`` sentinel, 422 on ``extra="forbid"``
violations.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from soyuz_catalog.services import credentials_service

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
TABLES = "/api/2.1/unity-catalog/tables"
VOLUMES = "/api/2.1/unity-catalog/volumes"
TABLE_CREDS = "/api/2.1/unity-catalog/temporary-table-credentials"
VOLUME_CREDS = "/api/2.1/unity-catalog/temporary-volume-credentials"


def _bootstrap_schema(client: TestClient) -> None:
    assert client.post(CATALOGS, json={"name": "main"}).status_code == 200
    assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).status_code == 200


def _create_table(
    client: TestClient,
    name: str = "t",
    storage_location: str | None = None,
) -> str:
    body: dict[str, Any] = {
        "name": name,
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
        "storage_location": storage_location or f"file:///tmp/{name}",
    }
    r = client.post(TABLES, json=body)
    assert r.status_code == 200, r.text
    return r.json()["table_id"]


def _create_volume(
    client: TestClient,
    name: str = "v",
    storage_location: str | None = None,
) -> str:
    body = {
        "name": name,
        "catalog_name": "main",
        "schema_name": "s",
        "volume_type": "EXTERNAL",
        "storage_location": storage_location or f"file:///tmp/{name}",
    }
    r = client.post(VOLUMES, json=body)
    assert r.status_code == 200, r.text
    return r.json()["volume_id"]


# ---------- tables ----------


def test_table_credentials_file_scheme_returns_expiration_only(
    client: TestClient,
) -> None:
    _bootstrap_schema(client)
    table_id = _create_table(client)
    r = client.post(TABLE_CREDS, json={"table_id": table_id, "operation": "READ"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == {"expiration_time"}
    assert body["expiration_time"] > 0


def test_table_credentials_accepts_read_write(client: TestClient) -> None:
    _bootstrap_schema(client)
    table_id = _create_table(client)
    r = client.post(
        TABLE_CREDS,
        json={"table_id": table_id, "operation": "READ_WRITE"},
    )
    assert r.status_code == 200, r.text
    assert "aws_temp_credentials" not in r.json()


@pytest.mark.parametrize(
    ("storage_location", "cloud_key"),
    [
        ("s3://bucket/t", "aws_temp_credentials"),
        ("s3a://bucket/t", "aws_temp_credentials"),
        ("abfss://container@acct.dfs.core.windows.net/t", "azure_user_delegation_sas"),
        ("gs://bucket/t", "gcp_oauth_token"),
    ],
)
def test_table_credentials_routes_per_storage_scheme(
    client: TestClient,
    storage_location: str,
    cloud_key: str,
) -> None:
    _bootstrap_schema(client)
    table_id = _create_table(client, name="t_cloud", storage_location=storage_location)
    r = client.post(TABLE_CREDS, json={"table_id": table_id, "operation": "READ"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert cloud_key in body
    assert body[cloud_key] == {}
    for other in ("aws_temp_credentials", "azure_user_delegation_sas", "gcp_oauth_token"):
        if other != cloud_key:
            assert other not in body
    assert body["expiration_time"] > 0


def test_table_credentials_404_on_unknown_id(client: TestClient) -> None:
    r = client.post(
        TABLE_CREDS,
        json={"table_id": "00000000000000000000000000000000", "operation": "READ"},
    )
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


def test_table_credentials_rejects_unknown_operation_sentinel(
    client: TestClient,
) -> None:
    _bootstrap_schema(client)
    table_id = _create_table(client)
    r = client.post(
        TABLE_CREDS,
        json={"table_id": table_id, "operation": "UNKNOWN_TABLE_OPERATION"},
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_table_credentials_rejects_garbage_operation(client: TestClient) -> None:
    _bootstrap_schema(client)
    table_id = _create_table(client)
    r = client.post(
        TABLE_CREDS,
        json={"table_id": table_id, "operation": "DELETE"},
    )
    assert r.status_code == 422


def test_table_credentials_rejects_extra_field(client: TestClient) -> None:
    _bootstrap_schema(client)
    table_id = _create_table(client)
    r = client.post(
        TABLE_CREDS,
        json={"table_id": table_id, "operation": "READ", "bogus": 1},
    )
    assert r.status_code == 422


STAGING = "/api/2.1/unity-catalog/staging-tables"


def test_table_credentials_resolves_staging_table_id(client: TestClient) -> None:
    """The JVM UC connector vends creds against a staging id.

    ``UCSingleCatalog.stageManagedDeltaTableAndGetProps`` in the upstream
    ``unitycatalog`` repo calls ``createStagingTable`` and then immediately
    hands the returned ``id`` to ``generateTemporaryTableCredentials``.
    The resolver therefore falls through to the staging service when no
    real table matches the id, otherwise the JVM connector would 404
    on every managed-Delta write. This test pins that fallthrough.
    """
    assert (
        client.post(CATALOGS, json={"name": "main", "storage_root": "s3://bucket/root"}).status_code
        == 200
    )
    assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).status_code == 200
    r = client.post(STAGING, json={"name": "t", "catalog_name": "main", "schema_name": "s"})
    assert r.status_code == 200, r.text
    staging_id = r.json()["id"]

    r = client.post(TABLE_CREDS, json={"table_id": staging_id, "operation": "READ_WRITE"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["aws_temp_credentials"] == {}
    assert body["expiration_time"] > 0


def test_table_credentials_staging_fallthrough_routes_file_scheme(
    client: TestClient,
) -> None:
    """``file://`` staging_location → expiration-only, same as a real table."""
    assert (
        client.post(
            CATALOGS, json={"name": "main", "storage_root": "file:///tmp/warehouse"}
        ).status_code
        == 200
    )
    assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).status_code == 200
    r = client.post(STAGING, json={"name": "t", "catalog_name": "main", "schema_name": "s"})
    assert r.status_code == 200, r.text
    staging_id = r.json()["id"]

    r = client.post(TABLE_CREDS, json={"table_id": staging_id, "operation": "READ_WRITE"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == {"expiration_time"}


# ---------- volumes ----------


def test_volume_credentials_file_scheme_returns_expiration_only(
    client: TestClient,
) -> None:
    _bootstrap_schema(client)
    volume_id = _create_volume(client)
    r = client.post(
        VOLUME_CREDS,
        json={"volume_id": volume_id, "operation": "READ_VOLUME"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == {"expiration_time"}
    assert body["expiration_time"] > 0


@pytest.mark.parametrize(
    ("storage_location", "cloud_key"),
    [
        ("s3://bucket/v", "aws_temp_credentials"),
        ("s3a://bucket/v", "aws_temp_credentials"),
        ("abfss://container@acct.dfs.core.windows.net/v", "azure_user_delegation_sas"),
        ("gs://bucket/v", "gcp_oauth_token"),
    ],
)
def test_volume_credentials_routes_per_storage_scheme(
    client: TestClient,
    storage_location: str,
    cloud_key: str,
) -> None:
    _bootstrap_schema(client)
    volume_id = _create_volume(client, name="v_cloud", storage_location=storage_location)
    r = client.post(
        VOLUME_CREDS,
        json={"volume_id": volume_id, "operation": "READ_VOLUME"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert cloud_key in body
    assert body[cloud_key] == {}
    for other in ("aws_temp_credentials", "azure_user_delegation_sas", "gcp_oauth_token"):
        if other != cloud_key:
            assert other not in body
    assert body["expiration_time"] > 0


def test_volume_credentials_accepts_write_volume(client: TestClient) -> None:
    _bootstrap_schema(client)
    volume_id = _create_volume(client)
    r = client.post(
        VOLUME_CREDS,
        json={"volume_id": volume_id, "operation": "WRITE_VOLUME"},
    )
    assert r.status_code == 200, r.text


def test_volume_credentials_404_on_unknown_id(client: TestClient) -> None:
    r = client.post(
        VOLUME_CREDS,
        json={
            "volume_id": "00000000000000000000000000000000",
            "operation": "READ_VOLUME",
        },
    )
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


def test_volume_credentials_rejects_unknown_operation_sentinel(
    client: TestClient,
) -> None:
    _bootstrap_schema(client)
    volume_id = _create_volume(client)
    r = client.post(
        VOLUME_CREDS,
        json={"volume_id": volume_id, "operation": "UNKNOWN_VOLUME_OPERATION"},
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_volume_credentials_rejects_garbage_operation(client: TestClient) -> None:
    _bootstrap_schema(client)
    volume_id = _create_volume(client)
    r = client.post(
        VOLUME_CREDS,
        json={"volume_id": volume_id, "operation": "READ"},
    )
    assert r.status_code == 422


def test_volume_credentials_rejects_extra_field(client: TestClient) -> None:
    _bootstrap_schema(client)
    volume_id = _create_volume(client)
    r = client.post(
        VOLUME_CREDS,
        json={"volume_id": volume_id, "operation": "READ_VOLUME", "bogus": 1},
    )
    assert r.status_code == 422


# ---------- model_version creds ----------

MODELS = "/api/2.1/unity-catalog/models"
MODEL_VERSIONS = "/api/2.1/unity-catalog/models/versions"
MODEL_VERSION_CREDS = "/api/2.1/unity-catalog/temporary-model-version-credentials"


def _create_model_version(
    client: TestClient,
    *,
    catalog: str = "main",
    schema: str = "s",
    model_name: str = "rf",
    source: str = "s3://artifacts/v1",
) -> dict[str, Any]:
    """Create catalog+schema+model+version, return the version body."""
    _bootstrap_schema(client)
    assert (
        client.post(
            MODELS,
            json={"name": model_name, "catalog_name": catalog, "schema_name": schema},
        ).status_code
        == 200
    )
    r = client.post(
        MODEL_VERSIONS,
        json={
            "model_name": model_name,
            "catalog_name": catalog,
            "schema_name": schema,
            "source": source,
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_model_version_credentials_local_returns_expiration_only(
    client: TestClient,
) -> None:
    """Local ``file://`` storage_location yields no cloud creds."""
    _create_model_version(client)
    r = client.post(
        MODEL_VERSION_CREDS,
        json={
            "catalog_name": "main",
            "schema_name": "s",
            "model_name": "rf",
            "version": 1,
            "operation": "READ_WRITE_MODEL_VERSION",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "expiration_time" in body
    assert "aws_temp_credentials" not in body
    assert "azure_user_delegation_sas" not in body
    assert "gcp_oauth_token" not in body


def test_model_version_credentials_unknown_operation_400(client: TestClient) -> None:
    _create_model_version(client)
    r = client.post(
        MODEL_VERSION_CREDS,
        json={
            "catalog_name": "main",
            "schema_name": "s",
            "model_name": "rf",
            "version": 1,
            "operation": "UNKNOWN_MODEL_VERSION_OPERATION",
        },
    )
    assert r.status_code == 400


def test_model_version_credentials_404_for_unknown_version(client: TestClient) -> None:
    _create_model_version(client)
    r = client.post(
        MODEL_VERSION_CREDS,
        json={
            "catalog_name": "main",
            "schema_name": "s",
            "model_name": "rf",
            "version": 99,
            "operation": "READ_MODEL_VERSION",
        },
    )
    assert r.status_code == 404


def test_model_version_credentials_extra_field_422(client: TestClient) -> None:
    _create_model_version(client)
    r = client.post(
        MODEL_VERSION_CREDS,
        json={
            "catalog_name": "main",
            "schema_name": "s",
            "model_name": "rf",
            "version": 1,
            "operation": "READ_MODEL_VERSION",
            "bogus": 1,
        },
    )
    assert r.status_code == 422


# ---------- unit: scheme resolver fallback ----------


def test_resolve_scheme_falls_back_for_missing_and_legacy_locations() -> None:
    """The read path must stay lax for legacy / unparseable locations.

    The write-path validator refuses to create a row with ``None`` or a
    bare path today, but legacy rows from earlier versions may still
    carry such values. ``_resolve_scheme`` must swallow both cases
    and return ``None`` — which routes to the expiration-only
    response, matching DIVERGENCES.md "Storage URIs".
    """
    assert credentials_service._resolve_scheme("table", "id", None) is None
    assert credentials_service._resolve_scheme("volume", "id", "/bare/path") is None
    assert credentials_service._resolve_scheme("table", "id", "") is None
