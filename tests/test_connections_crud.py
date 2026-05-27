"""Unit tests for the Connections resource (ADR-0013)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

CONNECTIONS = "/api/2.1/unity-catalog/connections"
CATALOGS = "/api/2.1/unity-catalog/catalogs"


def _minimal_body(
    name: str = "pg_prod",
    connection_type: str = "POSTGRESQL",
    options: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "connection_type": connection_type,
        "options": options if options is not None else {"host": "db.example.com", "port": "5432"},
    }


def _post(client: TestClient, name: str, **kwargs: Any) -> dict[str, Any]:
    r = client.post(CONNECTIONS, json=_minimal_body(name=name, **kwargs))
    assert r.status_code == 200, r.text
    return r.json()


def test_create_connection_minimal(client: TestClient) -> None:
    r = client.post(CONNECTIONS, json=_minimal_body())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "pg_prod"
    assert body["id"]
    assert body["connection_type"] == "POSTGRESQL"
    assert body["options"] == {"host": "db.example.com", "port": "5432"}
    assert body["created_at"] > 0


def test_create_connection_empty_options(client: TestClient) -> None:
    r = client.post(CONNECTIONS, json=_minimal_body(options={}))
    assert r.status_code == 200
    assert r.json()["options"] == {}


def test_create_connection_unknown_type_422(client: TestClient) -> None:
    body = _minimal_body()
    body["connection_type"] = "COCKROACHDB"
    r = client.post(CONNECTIONS, json=body)
    assert r.status_code == 422


def test_create_connection_extra_field_422(client: TestClient) -> None:
    body = _minimal_body()
    body["not_a_field"] = "boom"
    r = client.post(CONNECTIONS, json=body)
    assert r.status_code == 422


def test_create_connection_missing_type_422(client: TestClient) -> None:
    body = _minimal_body()
    body.pop("connection_type")
    r = client.post(CONNECTIONS, json=body)
    assert r.status_code == 422


def test_create_connection_conflict(client: TestClient) -> None:
    _post(client, "pg1")
    r = client.post(CONNECTIONS, json=_minimal_body(name="pg1"))
    assert r.status_code == 409


def test_get_connection(client: TestClient) -> None:
    _post(client, "pg1")
    r = client.get(f"{CONNECTIONS}/pg1")
    assert r.status_code == 200
    assert r.json()["name"] == "pg1"


def test_get_connection_not_found(client: TestClient) -> None:
    r = client.get(f"{CONNECTIONS}/missing")
    assert r.status_code == 404


def test_list_connections_order(client: TestClient) -> None:
    _post(client, "b")
    _post(client, "a")
    r = client.get(CONNECTIONS)
    assert r.status_code == 200
    body = r.json()
    assert [c["name"] for c in body["connections"]] == ["b", "a"]
    assert body.get("next_page_token") is None


def test_list_connections_empty(client: TestClient) -> None:
    r = client.get(CONNECTIONS)
    assert r.status_code == 200
    body = r.json()
    assert body["connections"] == []
    assert body.get("next_page_token") is None


def test_list_connections_pagination(client: TestClient) -> None:
    for n in ("c0", "c1", "c2", "c3"):
        _post(client, n)
    r1 = client.get(CONNECTIONS, params={"max_results": 2})
    body1 = r1.json()
    assert [c["name"] for c in body1["connections"]] == ["c0", "c1"]
    assert body1["next_page_token"]
    r2 = client.get(CONNECTIONS, params={"page_token": body1["next_page_token"]})
    body2 = r2.json()
    assert [c["name"] for c in body2["connections"]] == ["c2", "c3"]
    assert body2.get("next_page_token") is None


def test_patch_rename(client: TestClient) -> None:
    _post(client, "pg1")
    r = client.patch(f"{CONNECTIONS}/pg1", json={"new_name": "pg_primary"})
    assert r.status_code == 200
    assert r.json()["name"] == "pg_primary"
    assert client.get(f"{CONNECTIONS}/pg1").status_code == 404
    assert client.get(f"{CONNECTIONS}/pg_primary").status_code == 200


def test_patch_replace_options(client: TestClient) -> None:
    _post(client, "pg1")
    r = client.patch(f"{CONNECTIONS}/pg1", json={"options": {"host": "new.example.com"}})
    assert r.status_code == 200
    assert r.json()["options"] == {"host": "new.example.com"}


def test_patch_empty_options_clears(client: TestClient) -> None:
    _post(client, "pg1")
    r = client.patch(f"{CONNECTIONS}/pg1", json={"options": {}})
    assert r.status_code == 200
    assert r.json()["options"] == {}


def test_patch_empty_body_noop(client: TestClient) -> None:
    _post(client, "pg1")
    r = client.patch(f"{CONNECTIONS}/pg1", json={})
    assert r.status_code == 200
    assert r.json()["name"] == "pg1"


def test_patch_connection_type_forbidden_422(client: TestClient) -> None:
    _post(client, "pg1")
    r = client.patch(f"{CONNECTIONS}/pg1", json={"connection_type": "SNOWFLAKE"})
    assert r.status_code == 422


def test_patch_rename_conflict(client: TestClient) -> None:
    _post(client, "pg1")
    _post(client, "pg2")
    r = client.patch(f"{CONNECTIONS}/pg1", json={"new_name": "pg2"})
    assert r.status_code == 409


def test_patch_not_found(client: TestClient) -> None:
    r = client.patch(f"{CONNECTIONS}/missing", json={"new_name": "x"})
    assert r.status_code == 404


def test_delete_connection(client: TestClient) -> None:
    _post(client, "pg1")
    r = client.delete(f"{CONNECTIONS}/pg1")
    assert r.status_code == 200
    assert client.get(f"{CONNECTIONS}/pg1").status_code == 404


def test_delete_not_found(client: TestClient) -> None:
    r = client.delete(f"{CONNECTIONS}/missing")
    assert r.status_code == 404


def test_delete_connection_with_foreign_catalog_409(client: TestClient) -> None:
    _post(client, "pg1")
    r = client.post(
        CATALOGS,
        json={"name": "fc", "type": "FOREIGN", "connection_name": "pg1"},
    )
    assert r.status_code == 200, r.text
    r = client.delete(f"{CONNECTIONS}/pg1")
    assert r.status_code == 409


def test_delete_connection_force_cascades_foreign_catalog(client: TestClient) -> None:
    _post(client, "pg1")
    assert (
        client.post(
            CATALOGS,
            json={"name": "fc", "type": "FOREIGN", "connection_name": "pg1"},
        ).status_code
        == 200
    )
    r = client.delete(f"{CONNECTIONS}/pg1", params={"force": "true"})
    assert r.status_code == 200, r.text
    # Both the connection and the referencing foreign catalog are gone.
    assert client.get(f"{CONNECTIONS}/pg1").status_code == 404
    assert client.get(f"{CATALOGS}/fc").status_code == 404
