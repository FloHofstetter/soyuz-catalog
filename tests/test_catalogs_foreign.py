"""Tests for the foreign-catalog (Lakehouse-Federation) variant (ADR-0013)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

CATALOGS = "/api/2.1/unity-catalog/catalogs"
CONNECTIONS = "/api/2.1/unity-catalog/connections"


def _connection(client: TestClient, name: str = "pg1") -> dict[str, Any]:
    r = client.post(
        CONNECTIONS,
        json={
            "name": name,
            "connection_type": "POSTGRESQL",
            "options": {"host": "db.example.com"},
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def _foreign_catalog(
    client: TestClient,
    name: str = "fc",
    connection_name: str = "pg1",
    options: dict[str, str] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "name": name,
        "type": "FOREIGN",
        "connection_name": connection_name,
    }
    if options is not None:
        body["options"] = options
    r = client.post(CATALOGS, json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_create_managed_catalog_default_type(client: TestClient) -> None:
    r = client.post(CATALOGS, json={"name": "main"})
    body = r.json()
    assert r.status_code == 200
    assert body["type"] == "MANAGED"
    # connection_name must serialise null for managed catalogs because
    # a managed catalog has no connection binding.
    assert body.get("connection_name") is None


def test_create_foreign_catalog(client: TestClient) -> None:
    _connection(client, "pg1")
    body = _foreign_catalog(client, "fc", "pg1", options={"schema_filter": "public"})
    assert body["type"] == "FOREIGN"
    assert body["connection_name"] == "pg1"
    assert body["options"] == {"schema_filter": "public"}
    assert body.get("storage_root") is None
    assert body.get("storage_location") is None


def test_create_foreign_catalog_missing_connection_400(client: TestClient) -> None:
    r = client.post(CATALOGS, json={"name": "fc", "type": "FOREIGN"})
    assert r.status_code == 400


def test_create_foreign_catalog_unknown_connection_404(client: TestClient) -> None:
    r = client.post(
        CATALOGS,
        json={"name": "fc", "type": "FOREIGN", "connection_name": "nope"},
    )
    assert r.status_code == 404


def test_create_foreign_catalog_with_storage_root_400(client: TestClient) -> None:
    _connection(client, "pg1")
    r = client.post(
        CATALOGS,
        json={
            "name": "fc",
            "type": "FOREIGN",
            "connection_name": "pg1",
            "storage_root": "s3://bucket/root",
        },
    )
    assert r.status_code == 400


def test_create_managed_with_connection_name_400(client: TestClient) -> None:
    _connection(client, "pg1")
    r = client.post(
        CATALOGS,
        json={"name": "main", "type": "MANAGED", "connection_name": "pg1"},
    )
    assert r.status_code == 400


def test_create_managed_with_connection_name_default_type_400(client: TestClient) -> None:
    _connection(client, "pg1")
    r = client.post(CATALOGS, json={"name": "main", "connection_name": "pg1"})
    assert r.status_code == 400


def test_invalid_type_literal_422(client: TestClient) -> None:
    r = client.post(CATALOGS, json={"name": "main", "type": "VIRTUAL"})
    assert r.status_code == 422


def test_patch_type_forbidden_422(client: TestClient) -> None:
    client.post(CATALOGS, json={"name": "main"}).raise_for_status()
    r = client.patch(f"{CATALOGS}/main", json={"type": "FOREIGN"})
    assert r.status_code == 422


def test_patch_connection_name_on_managed_catalog_400(client: TestClient) -> None:
    _connection(client, "pg1")
    client.post(CATALOGS, json={"name": "main"}).raise_for_status()
    r = client.patch(f"{CATALOGS}/main", json={"connection_name": "pg1"})
    assert r.status_code == 400


def test_patch_rebind_foreign_catalog(client: TestClient) -> None:
    _connection(client, "pg1")
    _connection(client, "pg2")
    _foreign_catalog(client, "fc", "pg1")
    r = client.patch(f"{CATALOGS}/fc", json={"connection_name": "pg2"})
    assert r.status_code == 200, r.text
    assert r.json()["connection_name"] == "pg2"


def test_patch_foreign_catalog_connection_not_found_404(client: TestClient) -> None:
    _connection(client, "pg1")
    _foreign_catalog(client, "fc", "pg1")
    r = client.patch(f"{CATALOGS}/fc", json={"connection_name": "missing"})
    assert r.status_code == 404


def test_patch_options_replace(client: TestClient) -> None:
    _connection(client, "pg1")
    _foreign_catalog(client, "fc", "pg1", options={"schema_filter": "public"})
    r = client.patch(f"{CATALOGS}/fc", json={"options": {"schema_filter": "reporting"}})
    assert r.status_code == 200
    assert r.json()["options"] == {"schema_filter": "reporting"}


def test_foreign_catalog_rename_of_connection_propagates(client: TestClient) -> None:
    _connection(client, "pg1")
    _foreign_catalog(client, "fc", "pg1")
    r = client.patch(f"{CONNECTIONS}/pg1", json={"new_name": "pg_prod"})
    assert r.status_code == 200
    r = client.get(f"{CATALOGS}/fc")
    assert r.status_code == 200
    assert r.json()["connection_name"] == "pg_prod"
