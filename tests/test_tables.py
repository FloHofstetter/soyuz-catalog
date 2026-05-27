from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from soyuz_catalog.models import Column

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
TABLES = "/api/2.1/unity-catalog/tables"


def _make_catalog(client: TestClient, name: str = "main") -> None:
    r = client.post(CATALOGS, json={"name": name})
    assert r.status_code == 200, r.text


def _make_schema(client: TestClient, catalog_name: str = "main", name: str = "s") -> None:
    r = client.post(SCHEMAS, json={"name": name, "catalog_name": catalog_name})
    assert r.status_code == 200, r.text


def _minimal_column(name: str = "c0", position: int = 0) -> dict[str, Any]:
    return {
        "name": name,
        "type_text": "int",
        "type_json": '{"type":"integer"}',
        "type_name": "INT",
        "position": position,
    }


def _post_table(client: TestClient, name: str) -> None:
    body = _minimal_create_body(name=name, columns=[_minimal_column(name=f"c_{name}")])
    body["storage_location"] = f"s3://bucket/{name}"
    r = client.post(TABLES, json=body)
    assert r.status_code == 200, r.text


def _minimal_create_body(
    name: str = "t",
    catalog_name: str = "main",
    schema_name: str = "s",
    columns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "catalog_name": catalog_name,
        "schema_name": schema_name,
        "table_type": "MANAGED",
        "data_source_format": "DELTA",
        "columns": columns if columns is not None else [_minimal_column()],
        "storage_location": "s3://bucket/t",
    }


def test_create_table_happy_path(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.post(TABLES, json=_minimal_create_body())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "t"
    assert body["catalog_name"] == "main"
    assert body["schema_name"] == "s"
    assert body["full_name"] == "main.s.t"
    assert body["table_type"] == "MANAGED"
    assert body["data_source_format"] == "DELTA"
    assert body["storage_location"] == "s3://bucket/t"
    assert body["table_id"]
    assert body["created_at"] > 0
    assert body["properties"] == {}
    assert len(body["columns"]) == 1
    assert body["columns"][0]["name"] == "c0"
    assert body["columns"][0]["position"] == 0
    assert body["columns"][0]["nullable"] is True


def test_create_table_with_multiple_columns_preserves_position(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    cols = [_minimal_column("a", 0), _minimal_column("b", 1), _minimal_column("c", 2)]
    r = client.post(TABLES, json=_minimal_create_body(columns=cols))
    assert r.status_code == 200, r.text
    body = r.json()
    assert [c["name"] for c in body["columns"]] == ["a", "b", "c"]
    assert [c["position"] for c in body["columns"]] == [0, 1, 2]


def test_create_table_requires_catalog_and_schema_name(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = _minimal_create_body()
    del body["catalog_name"]
    r = client.post(TABLES, json=body)
    assert r.status_code == 422


def test_create_table_unknown_catalog_404(client: TestClient) -> None:
    r = client.post(TABLES, json=_minimal_create_body(catalog_name="nope"))
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


def test_create_table_unknown_schema_404(client: TestClient) -> None:
    _make_catalog(client)
    r = client.post(TABLES, json=_minimal_create_body(schema_name="nope"))
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


def test_create_table_duplicate_409(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    assert client.post(TABLES, json=_minimal_create_body()).status_code == 200
    r = client.post(TABLES, json=_minimal_create_body())
    assert r.status_code == 409
    assert r.json()["error_code"] == "ALREADY_EXISTS"


def test_create_table_same_name_in_other_schema_allowed(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client, name="s1")
    _make_schema(client, name="s2")
    assert client.post(TABLES, json=_minimal_create_body(schema_name="s1")).status_code == 200
    assert client.post(TABLES, json=_minimal_create_body(schema_name="s2")).status_code == 200


def test_create_table_unknown_field_rejected(client: TestClient) -> None:
    """UC OSS bug fix: unknown top-level fields are rejected, not silently ignored."""
    _make_catalog(client)
    _make_schema(client)
    body = _minimal_create_body()
    body["bogus"] = 1
    r = client.post(TABLES, json=body)
    assert r.status_code == 422


def test_create_table_unknown_column_field_rejected(client: TestClient) -> None:
    """UC OSS bug fix: unknown fields inside a column entry are also rejected."""
    _make_catalog(client)
    _make_schema(client)
    col = _minimal_column()
    col["type_neme"] = "INT"  # typo, should 422
    body = _minimal_create_body(columns=[col])
    r = client.post(TABLES, json=body)
    assert r.status_code == 422


def test_get_table_by_full_name(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(TABLES, json=_minimal_create_body())
    r = client.get(f"{TABLES}/main.s.t")
    assert r.status_code == 200
    assert r.json()["full_name"] == "main.s.t"


def test_get_table_malformed_full_name_400(client: TestClient) -> None:
    r = client.get(f"{TABLES}/main.s")
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_get_table_nonexistent_404(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.get(f"{TABLES}/main.s.nope")
    assert r.status_code == 404


def test_list_tables_returns_created(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post_table(client, "b")
    _post_table(client, "a")
    r = client.get(TABLES, params={"catalog_name": "main", "schema_name": "s"})
    assert r.status_code == 200
    body = r.json()
    # List order is insertion order, not name-sorted.
    assert [t["name"] for t in body["tables"]] == ["b", "a"]
    assert body["next_page_token"] is None


def test_list_tables_empty(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = client.get(
        TABLES,
        params={"catalog_name": "main", "schema_name": "s"},
    ).json()
    assert body["tables"] == []
    assert body["next_page_token"] is None


def test_list_tables_multi_page_walk(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    for name in ("t0", "t1", "t2", "t3", "t4"):
        _post_table(client, name)

    base = {"catalog_name": "main", "schema_name": "s", "max_results": 2}
    body1 = client.get(TABLES, params=base).json()
    assert [t["name"] for t in body1["tables"]] == ["t0", "t1"]
    assert body1["next_page_token"] is not None

    body2 = client.get(
        TABLES,
        params={**base, "page_token": body1["next_page_token"]},
    ).json()
    assert [t["name"] for t in body2["tables"]] == ["t2", "t3"]
    assert body2["next_page_token"] is not None

    body3 = client.get(
        TABLES,
        params={**base, "page_token": body2["next_page_token"]},
    ).json()
    assert [t["name"] for t in body3["tables"]] == ["t4"]
    assert body3["next_page_token"] is None


def test_list_tables_boundary_exact_page_size(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    for name in ("t0", "t1"):
        _post_table(client, name)
    body = client.get(
        TABLES,
        params={"catalog_name": "main", "schema_name": "s", "max_results": 2},
    ).json()
    assert [t["name"] for t in body["tables"]] == ["t0", "t1"]
    assert body["next_page_token"] is None


def test_list_tables_rejects_tampered_page_token(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.get(
        TABLES,
        params={
            "catalog_name": "main",
            "schema_name": "s",
            "page_token": "tampered",
        },
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_list_tables_rejects_out_of_range_max_results(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    # max_results=0 → 200 (JVM UC connector compat: sends 0 for default).
    assert (
        client.get(
            TABLES,
            params={"catalog_name": "main", "schema_name": "s", "max_results": 0},
        ).status_code
        == 200
    )
    assert (
        client.get(
            TABLES,
            params={"catalog_name": "main", "schema_name": "s", "max_results": -1},
        ).status_code
        == 422
    )
    assert (
        client.get(
            TABLES,
            params={"catalog_name": "main", "schema_name": "s", "max_results": 1001},
        ).status_code
        == 422
    )


def test_list_tables_requires_both_catalog_and_schema_name(client: TestClient) -> None:
    r = client.get(TABLES, params={"catalog_name": "main"})
    assert r.status_code == 422


def test_list_tables_unknown_parent_404(client: TestClient) -> None:
    r = client.get(TABLES, params={"catalog_name": "nope", "schema_name": "s"})
    assert r.status_code == 404


def test_patch_table_returns_405(client: TestClient) -> None:
    """Spec-faithful divergence: UC defines no UpdateTable, soyuz returns 405."""
    _make_catalog(client)
    _make_schema(client)
    client.post(TABLES, json=_minimal_create_body())
    r = client.patch(f"{TABLES}/main.s.t", json={"comment": "nope"})
    assert r.status_code == 405


def test_delete_table_then_get_404(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(TABLES, json=_minimal_create_body())
    r = client.delete(f"{TABLES}/main.s.t")
    assert r.status_code == 200
    assert r.json() == {}
    assert client.get(f"{TABLES}/main.s.t").status_code == 404


def test_delete_table_cascades_columns(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    _make_catalog(client)
    _make_schema(client)
    cols = [_minimal_column("a", 0), _minimal_column("b", 1)]
    client.post(TABLES, json=_minimal_create_body(columns=cols))
    with session_factory() as s:
        assert s.scalar(select(Column).where(Column.name == "a")) is not None

    r = client.delete(f"{TABLES}/main.s.t")
    assert r.status_code == 200

    with session_factory() as s:
        remaining = list(s.scalars(select(Column)))
        assert remaining == []


def test_delete_table_missing_404(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.delete(f"{TABLES}/main.s.nope")
    assert r.status_code == 404


def test_delete_table_accepts_force_noop(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(TABLES, json=_minimal_create_body())
    r = client.delete(f"{TABLES}/main.s.t", params={"force": "true"})
    assert r.status_code == 200


def test_delete_schema_with_tables_conflict_409(client: TestClient) -> None:
    """DELETE /schemas refuses to drop a schema that still has tables."""
    _make_catalog(client)
    _make_schema(client)
    client.post(TABLES, json=_minimal_create_body())
    r = client.delete(f"{SCHEMAS}/main.s")
    assert r.status_code == 409
    assert r.json()["error_code"] == "ALREADY_EXISTS"
    assert client.get(f"{TABLES}/main.s.t").status_code == 200


def test_delete_schema_with_tables_force_cascades(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    from soyuz_catalog.models import Table

    _make_catalog(client)
    _make_schema(client)
    client.post(TABLES, json=_minimal_create_body(name="t1"))
    client.post(TABLES, json=_minimal_create_body(name="t2"))

    r = client.delete(f"{SCHEMAS}/main.s", params={"force": "true"})
    assert r.status_code == 200

    with session_factory() as s:
        assert list(s.scalars(select(Table))) == []
        assert list(s.scalars(select(Column))) == []


def test_delete_catalog_force_cascades_through_tables_and_columns(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    """force=true on catalog cascades through schemas → tables → columns via the ORM."""
    from soyuz_catalog.models import Table

    _make_catalog(client)
    _make_schema(client)
    cols = [_minimal_column("a", 0), _minimal_column("b", 1)]
    client.post(TABLES, json=_minimal_create_body(columns=cols))

    r = client.delete(f"{CATALOGS}/main", params={"force": "true"})
    assert r.status_code == 200

    with session_factory() as s:
        assert list(s.scalars(select(Table))) == []
        assert list(s.scalars(select(Column))) == []


def test_catalog_rename_propagates_to_table_full_name(client: TestClient) -> None:
    """``full_name`` is computed, so renaming the parent catalog updates it for free."""
    _make_catalog(client, "old")
    _make_schema(client, catalog_name="old")
    client.post(TABLES, json=_minimal_create_body(catalog_name="old"))

    client.patch(f"{CATALOGS}/old", json={"new_name": "new"})

    assert client.get(f"{TABLES}/old.s.t").status_code == 404
    body = client.get(f"{TABLES}/new.s.t").json()
    assert body["full_name"] == "new.s.t"
    assert body["catalog_name"] == "new"


def test_create_table_rejects_unsupported_storage_scheme(client: TestClient) -> None:
    """Unsupported storage URI scheme → 400 INVALID_ARGUMENT.

    UC OSS Java would silently accept this and push the failure down to
    the engine. soyuz-catalog fails at write time — see DIVERGENCES.md.
    """
    _make_catalog(client)
    _make_schema(client)
    body = _minimal_create_body()
    body["storage_location"] = "hdfs://namenode/path"
    r = client.post(TABLES, json=body)
    assert r.status_code == 400, r.text
    assert "unsupported storage URI scheme" in r.json()["message"]


def test_create_table_rejects_bare_path_storage_location(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = _minimal_create_body()
    body["storage_location"] = "/tmp/foo"
    r = client.post(TABLES, json=body)
    assert r.status_code == 400, r.text
    assert "missing a URI scheme" in r.json()["message"]


def test_create_table_accepts_file_scheme(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = _minimal_create_body()
    body["storage_location"] = "file:///tmp/t"
    r = client.post(TABLES, json=body)
    assert r.status_code == 200, r.text
    assert r.json()["storage_location"] == "file:///tmp/t"


def test_schema_rename_propagates_to_table_full_name(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client, name="old")
    client.post(TABLES, json=_minimal_create_body(schema_name="old"))

    client.patch(f"{SCHEMAS}/main.old", json={"new_name": "new"})

    assert client.get(f"{TABLES}/main.old.t").status_code == 404
    body = client.get(f"{TABLES}/main.new.t").json()
    assert body["full_name"] == "main.new.t"
    assert body["schema_name"] == "new"
