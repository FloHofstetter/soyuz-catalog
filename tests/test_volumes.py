from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from soyuz_catalog.models import Volume

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
VOLUMES = "/api/2.1/unity-catalog/volumes"


def _make_catalog(client: TestClient, name: str = "main") -> None:
    r = client.post(CATALOGS, json={"name": name})
    assert r.status_code == 200, r.text


def _make_schema(client: TestClient, catalog_name: str = "main", name: str = "s") -> None:
    r = client.post(SCHEMAS, json={"name": name, "catalog_name": catalog_name})
    assert r.status_code == 200, r.text


def _post_volume(client: TestClient, name: str) -> None:
    body = _minimal_create_body(name=name, storage_location=f"s3://bucket/{name}")
    r = client.post(VOLUMES, json=body)
    assert r.status_code == 200, r.text


def _minimal_create_body(
    name: str = "v",
    catalog_name: str = "main",
    schema_name: str = "s",
    volume_type: str = "EXTERNAL",
    storage_location: str | None = "s3://bucket/v",
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "name": name,
        "catalog_name": catalog_name,
        "schema_name": schema_name,
        "volume_type": volume_type,
    }
    if storage_location is not None:
        body["storage_location"] = storage_location
    return body


def test_create_volume_happy_path(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.post(VOLUMES, json=_minimal_create_body())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "v"
    assert body["catalog_name"] == "main"
    assert body["schema_name"] == "s"
    assert body["full_name"] == "main.s.v"
    assert body["volume_type"] == "EXTERNAL"
    assert body["storage_location"] == "s3://bucket/v"
    assert body["volume_id"]
    assert body["created_at"] > 0


def test_create_volume_managed_without_storage_location(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = _minimal_create_body(volume_type="MANAGED", storage_location=None)
    r = client.post(VOLUMES, json=body)
    assert r.status_code == 200
    assert r.json()["volume_type"] == "MANAGED"
    assert r.json()["storage_location"] is None


def test_create_volume_requires_catalog_and_schema_name(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = _minimal_create_body()
    del body["catalog_name"]
    r = client.post(VOLUMES, json=body)
    assert r.status_code == 422


def test_create_volume_unknown_catalog_404(client: TestClient) -> None:
    r = client.post(VOLUMES, json=_minimal_create_body(catalog_name="nope"))
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


def test_create_volume_unknown_schema_404(client: TestClient) -> None:
    _make_catalog(client)
    r = client.post(VOLUMES, json=_minimal_create_body(schema_name="nope"))
    assert r.status_code == 404


def test_create_volume_duplicate_409(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    assert client.post(VOLUMES, json=_minimal_create_body()).status_code == 200
    r = client.post(VOLUMES, json=_minimal_create_body())
    assert r.status_code == 409
    assert r.json()["error_code"] == "ALREADY_EXISTS"


def test_create_volume_same_name_in_other_schema_allowed(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client, name="s1")
    _make_schema(client, name="s2")
    assert client.post(VOLUMES, json=_minimal_create_body(schema_name="s1")).status_code == 200
    assert client.post(VOLUMES, json=_minimal_create_body(schema_name="s2")).status_code == 200


def test_create_volume_unknown_field_rejected(client: TestClient) -> None:
    """UC OSS bug fix: unknown top-level fields are rejected, not silently ignored."""
    _make_catalog(client)
    _make_schema(client)
    body = _minimal_create_body()
    body["bogus"] = 1
    r = client.post(VOLUMES, json=body)
    assert r.status_code == 422


def test_create_volume_bad_type_422(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.post(VOLUMES, json=_minimal_create_body(volume_type="WEIRD"))
    assert r.status_code == 422


def test_get_volume_by_full_name(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(VOLUMES, json=_minimal_create_body())
    r = client.get(f"{VOLUMES}/main.s.v")
    assert r.status_code == 200
    assert r.json()["full_name"] == "main.s.v"


def test_get_volume_malformed_full_name_400(client: TestClient) -> None:
    r = client.get(f"{VOLUMES}/main.s")
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_get_volume_nonexistent_404(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.get(f"{VOLUMES}/main.s.nope")
    assert r.status_code == 404


def test_list_volumes_returns_created(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post_volume(client, "b")
    _post_volume(client, "a")
    r = client.get(VOLUMES, params={"catalog_name": "main", "schema_name": "s"})
    assert r.status_code == 200
    body = r.json()
    # List order is insertion order, not name-sorted.
    assert [v["name"] for v in body["volumes"]] == ["b", "a"]
    assert body["next_page_token"] is None


def test_list_volumes_empty(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = client.get(
        VOLUMES,
        params={"catalog_name": "main", "schema_name": "s"},
    ).json()
    assert body["volumes"] == []
    assert body["next_page_token"] is None


def test_list_volumes_multi_page_walk(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    for name in ("v0", "v1", "v2", "v3", "v4"):
        _post_volume(client, name)

    base = {"catalog_name": "main", "schema_name": "s", "max_results": 2}
    body1 = client.get(VOLUMES, params=base).json()
    assert [v["name"] for v in body1["volumes"]] == ["v0", "v1"]
    assert body1["next_page_token"] is not None

    body2 = client.get(
        VOLUMES,
        params={**base, "page_token": body1["next_page_token"]},
    ).json()
    assert [v["name"] for v in body2["volumes"]] == ["v2", "v3"]
    assert body2["next_page_token"] is not None

    body3 = client.get(
        VOLUMES,
        params={**base, "page_token": body2["next_page_token"]},
    ).json()
    assert [v["name"] for v in body3["volumes"]] == ["v4"]
    assert body3["next_page_token"] is None


def test_list_volumes_boundary_exact_page_size(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    for name in ("v0", "v1"):
        _post_volume(client, name)
    body = client.get(
        VOLUMES,
        params={"catalog_name": "main", "schema_name": "s", "max_results": 2},
    ).json()
    assert [v["name"] for v in body["volumes"]] == ["v0", "v1"]
    assert body["next_page_token"] is None


def test_list_volumes_rejects_tampered_page_token(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.get(
        VOLUMES,
        params={
            "catalog_name": "main",
            "schema_name": "s",
            "page_token": "tampered",
        },
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_list_volumes_rejects_out_of_range_max_results(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    # max_results=0 → 200 (JVM UC connector compat: sends 0 for default).
    assert (
        client.get(
            VOLUMES,
            params={"catalog_name": "main", "schema_name": "s", "max_results": 0},
        ).status_code
        == 200
    )
    assert (
        client.get(
            VOLUMES,
            params={"catalog_name": "main", "schema_name": "s", "max_results": -1},
        ).status_code
        == 422
    )
    assert (
        client.get(
            VOLUMES,
            params={"catalog_name": "main", "schema_name": "s", "max_results": 1001},
        ).status_code
        == 422
    )


def test_list_volumes_requires_both_parents(client: TestClient) -> None:
    r = client.get(VOLUMES, params={"catalog_name": "main"})
    assert r.status_code == 422


def test_list_volumes_unknown_parent_404(client: TestClient) -> None:
    r = client.get(VOLUMES, params={"catalog_name": "nope", "schema_name": "s"})
    assert r.status_code == 404


def test_patch_volume_comment(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    created = client.post(VOLUMES, json=_minimal_create_body()).json()
    r = client.patch(f"{VOLUMES}/main.s.v", json={"comment": "hi"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["comment"] == "hi"
    assert body["updated_at"] >= created["updated_at"]


def test_patch_volume_rename(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(VOLUMES, json=_minimal_create_body(name="old"))
    r = client.patch(f"{VOLUMES}/main.s.old", json={"new_name": "new"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "main.s.new"
    assert client.get(f"{VOLUMES}/main.s.old").status_code == 404
    assert client.get(f"{VOLUMES}/main.s.new").status_code == 200


def test_patch_volume_rename_conflict_409(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(VOLUMES, json=_minimal_create_body(name="a"))
    client.post(VOLUMES, json=_minimal_create_body(name="b"))
    r = client.patch(f"{VOLUMES}/main.s.a", json={"new_name": "b"})
    assert r.status_code == 409


def test_patch_volume_empty_body_is_noop(client: TestClient) -> None:
    """UC OSS bug fix: PATCH with empty body returns the unchanged volume, not 500."""
    _make_catalog(client)
    _make_schema(client)
    client.post(VOLUMES, json=_minimal_create_body())
    r = client.patch(f"{VOLUMES}/main.s.v", json={})
    assert r.status_code == 200
    assert r.json()["name"] == "v"


def test_patch_volume_unknown_field_422(client: TestClient) -> None:
    """UC OSS bug fix: unknown fields raise 422."""
    _make_catalog(client)
    _make_schema(client)
    client.post(VOLUMES, json=_minimal_create_body())
    r = client.patch(f"{VOLUMES}/main.s.v", json={"bogus": 1})
    assert r.status_code == 422


def test_patch_volume_storage_location_rejected_422(client: TestClient) -> None:
    """UC spec: storage_location is immutable; soyuz returns 422 instead of dropping."""
    _make_catalog(client)
    _make_schema(client)
    client.post(VOLUMES, json=_minimal_create_body())
    r = client.patch(f"{VOLUMES}/main.s.v", json={"storage_location": "s3://other/v"})
    assert r.status_code == 422


def test_patch_volume_type_rejected_422(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(VOLUMES, json=_minimal_create_body())
    r = client.patch(f"{VOLUMES}/main.s.v", json={"volume_type": "MANAGED"})
    assert r.status_code == 422


def test_patch_volume_missing_returns_404(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.patch(f"{VOLUMES}/main.s.nope", json={"comment": "x"})
    assert r.status_code == 404


def test_patch_volume_malformed_full_name_400(client: TestClient) -> None:
    r = client.patch(f"{VOLUMES}/main.s", json={"comment": "x"})
    assert r.status_code == 400


def test_delete_volume_then_get_404(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(VOLUMES, json=_minimal_create_body())
    r = client.delete(f"{VOLUMES}/main.s.v")
    assert r.status_code == 200
    assert r.json() == {}
    assert client.get(f"{VOLUMES}/main.s.v").status_code == 404


def test_delete_volume_missing_404(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.delete(f"{VOLUMES}/main.s.nope")
    assert r.status_code == 404


def test_delete_schema_with_volumes_conflict_409(client: TestClient) -> None:
    """DELETE /schemas refuses to drop a schema that still has volumes."""
    _make_catalog(client)
    _make_schema(client)
    client.post(VOLUMES, json=_minimal_create_body())
    r = client.delete(f"{SCHEMAS}/main.s")
    assert r.status_code == 409
    assert r.json()["error_code"] == "ALREADY_EXISTS"
    assert client.get(f"{VOLUMES}/main.s.v").status_code == 200


def test_delete_schema_with_volumes_force_cascades(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(VOLUMES, json=_minimal_create_body(name="v1"))
    client.post(VOLUMES, json=_minimal_create_body(name="v2"))

    r = client.delete(f"{SCHEMAS}/main.s", params={"force": "true"})
    assert r.status_code == 200

    with session_factory() as s:
        assert list(s.scalars(select(Volume))) == []


def test_delete_catalog_force_cascades_through_volumes(
    client: TestClient,
    session_factory: sessionmaker[Session],
) -> None:
    """force=true on catalog cascades through schemas → volumes via the ORM."""
    _make_catalog(client)
    _make_schema(client)
    client.post(VOLUMES, json=_minimal_create_body())
    r = client.delete(f"{CATALOGS}/main", params={"force": "true"})
    assert r.status_code == 200
    with session_factory() as s:
        assert list(s.scalars(select(Volume))) == []


def test_catalog_rename_propagates_to_volume_full_name(client: TestClient) -> None:
    """``full_name`` is computed, so renaming the parent catalog updates it for free."""
    _make_catalog(client, "old")
    _make_schema(client, catalog_name="old")
    client.post(VOLUMES, json=_minimal_create_body(catalog_name="old"))

    client.patch(f"{CATALOGS}/old", json={"new_name": "new"})

    assert client.get(f"{VOLUMES}/old.s.v").status_code == 404
    body = client.get(f"{VOLUMES}/new.s.v").json()
    assert body["full_name"] == "new.s.v"
    assert body["catalog_name"] == "new"


def test_schema_rename_propagates_to_volume_full_name(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client, name="old")
    client.post(VOLUMES, json=_minimal_create_body(schema_name="old"))

    client.patch(f"{SCHEMAS}/main.old", json={"new_name": "new"})

    assert client.get(f"{VOLUMES}/main.old.v").status_code == 404
    body = client.get(f"{VOLUMES}/main.new.v").json()
    assert body["full_name"] == "main.new.v"
    assert body["schema_name"] == "new"


def test_create_volume_rejects_unsupported_storage_scheme(client: TestClient) -> None:
    """Unsupported ``storage_location`` scheme is a 400."""
    _make_catalog(client)
    _make_schema(client)
    r = client.post(
        VOLUMES,
        json=_minimal_create_body(storage_location="hdfs://namenode/v"),
    )
    assert r.status_code == 400, r.text
    assert "unsupported storage URI scheme" in r.json()["message"]


def test_create_volume_managed_without_location_still_allowed(client: TestClient) -> None:
    """Guard: the scheme check only fires when the field is present."""
    _make_catalog(client)
    _make_schema(client)
    r = client.post(
        VOLUMES,
        json=_minimal_create_body(volume_type="MANAGED", storage_location=None),
    )
    assert r.status_code == 200, r.text
