"""Tests for ``POST /staging-tables``.

Staging tables are allocation-only in soyuz — see
:mod:`soyuz_catalog.services.staging_table_service` for the rationale.
These tests cover the happy path, parent resolution, the derived
``staging_location`` URL, the no-uniqueness semantics, and the
``extra="forbid"`` + 404 / 400 regression set.
"""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
STAGING = "/api/2.1/unity-catalog/staging-tables"

_HEX32 = re.compile(r"^[0-9a-f]{32}$")


def _bootstrap(client: TestClient, storage_root: str = "s3://bucket/root") -> None:
    assert (
        client.post(CATALOGS, json={"name": "main", "storage_root": storage_root}).status_code
        == 200
    )
    assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).status_code == 200


def test_staging_table_happy_path(client: TestClient) -> None:
    _bootstrap(client)
    r = client.post(
        STAGING,
        json={"name": "t", "catalog_name": "main", "schema_name": "s"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "t"
    assert body["catalog_name"] == "main"
    assert body["schema_name"] == "s"
    assert _HEX32.match(body["id"]), body["id"]
    assert body["staging_location"].startswith("s3://bucket/root/")
    assert "__staging__" in body["staging_location"]
    assert body["staging_location"].endswith("/t")


def test_staging_table_location_prefers_schema_storage(client: TestClient) -> None:
    assert (
        client.post(
            CATALOGS,
            json={"name": "main", "storage_root": "s3://catalog-root/x"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            SCHEMAS,
            json={
                "name": "s",
                "catalog_name": "main",
                "storage_root": "s3://schema-root/y",
            },
        ).status_code
        == 200
    )
    r = client.post(
        STAGING,
        json={"name": "t", "catalog_name": "main", "schema_name": "s"},
    )
    assert r.status_code == 200, r.text
    # Schema has its own storage_location derived from schema-root.
    assert r.json()["staging_location"].startswith("s3://schema-root/y/")


def test_staging_table_two_allocations_under_same_name_succeed(
    client: TestClient,
) -> None:
    _bootstrap(client)
    a = client.post(
        STAGING,
        json={"name": "t", "catalog_name": "main", "schema_name": "s"},
    ).json()
    b = client.post(
        STAGING,
        json={"name": "t", "catalog_name": "main", "schema_name": "s"},
    ).json()
    assert a["id"] != b["id"]
    assert a["staging_location"] != b["staging_location"]


def test_staging_table_unknown_catalog_returns_404(client: TestClient) -> None:
    r = client.post(
        STAGING,
        json={"name": "t", "catalog_name": "nope", "schema_name": "s"},
    )
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


def test_staging_table_unknown_schema_returns_404(client: TestClient) -> None:
    assert (
        client.post(
            CATALOGS,
            json={"name": "main", "storage_root": "s3://bucket/root"},
        ).status_code
        == 200
    )
    r = client.post(
        STAGING,
        json={"name": "t", "catalog_name": "main", "schema_name": "nope"},
    )
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


def test_staging_table_requires_storage_root_on_parent(client: TestClient) -> None:
    assert client.post(CATALOGS, json={"name": "main"}).status_code == 200
    assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).status_code == 200
    r = client.post(
        STAGING,
        json={"name": "t", "catalog_name": "main", "schema_name": "s"},
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_staging_table_rejects_extra_field(client: TestClient) -> None:
    _bootstrap(client)
    r = client.post(
        STAGING,
        json={
            "name": "t",
            "catalog_name": "main",
            "schema_name": "s",
            "storage_location": "s3://evil/",
        },
    )
    assert r.status_code == 422


def test_staging_table_missing_required_field_is_422(client: TestClient) -> None:
    _bootstrap(client)
    r = client.post(STAGING, json={"catalog_name": "main", "schema_name": "s"})
    assert r.status_code == 422


def test_staging_table_file_scheme_works(client: TestClient) -> None:
    assert (
        client.post(
            CATALOGS,
            json={"name": "main", "storage_root": "file:///tmp/uc"},
        ).status_code
        == 200
    )
    assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).status_code == 200
    r = client.post(
        STAGING,
        json={"name": "t", "catalog_name": "main", "schema_name": "s"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["staging_location"].startswith("file:///tmp/uc/")


def test_staging_table_parent_rename_propagates_to_response(client: TestClient) -> None:
    _bootstrap(client)
    first = client.post(
        STAGING,
        json={"name": "t", "catalog_name": "main", "schema_name": "s"},
    ).json()
    # rename catalog
    assert (
        client.patch(
            f"{CATALOGS}/main",
            json={"new_name": "main2"},
        ).status_code
        == 200
    )
    # New allocations see the new catalog name, even though the stored
    # row's staging_location was frozen at creation time.
    r = client.post(
        STAGING,
        json={"name": "t2", "catalog_name": "main2", "schema_name": "s"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["catalog_name"] == "main2"
    # The original allocation's staging_location stays byte-stable —
    # rename-invariance is what the __staging__/{uuid} layout is for.
    assert first["staging_location"].startswith("s3://bucket/root/")
