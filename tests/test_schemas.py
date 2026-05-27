from fastapi.testclient import TestClient

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"


def _make_catalog(client: TestClient, name: str = "main") -> None:
    r = client.post(CATALOGS, json={"name": name})
    assert r.status_code == 200, r.text


def _post_schema(client: TestClient, name: str, catalog_name: str = "main") -> None:
    r = client.post(SCHEMAS, json={"name": name, "catalog_name": catalog_name})
    assert r.status_code == 200, r.text


def test_create_schema_happy_path(client: TestClient) -> None:
    _make_catalog(client)
    r = client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "s"
    assert body["catalog_name"] == "main"
    assert body["full_name"] == "main.s"
    assert body["schema_id"]
    assert body["created_at"] > 0
    assert body["properties"] == {}


def test_create_schema_requires_catalog_name(client: TestClient) -> None:
    r = client.post(SCHEMAS, json={"name": "s"})
    assert r.status_code == 422


def test_create_schema_unknown_catalog_404(client: TestClient) -> None:
    r = client.post(SCHEMAS, json={"name": "s", "catalog_name": "nope"})
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


def test_create_schema_duplicate_409(client: TestClient) -> None:
    _make_catalog(client)
    assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).status_code == 200
    r = client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    assert r.status_code == 409
    assert r.json()["error_code"] == "ALREADY_EXISTS"


def test_create_schema_same_name_in_other_catalog_allowed(client: TestClient) -> None:
    _make_catalog(client, "a")
    _make_catalog(client, "b")
    assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "a"}).status_code == 200
    assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "b"}).status_code == 200


def test_create_schema_unknown_field_rejected(client: TestClient) -> None:
    _make_catalog(client)
    r = client.post(SCHEMAS, json={"name": "s", "catalog_name": "main", "bogus": 1})
    assert r.status_code == 422


def test_get_schema_by_full_name(client: TestClient) -> None:
    _make_catalog(client)
    client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    r = client.get(f"{SCHEMAS}/main.s")
    assert r.status_code == 200
    assert r.json()["full_name"] == "main.s"


def test_get_schema_malformed_full_name_400(client: TestClient) -> None:
    r = client.get(f"{SCHEMAS}/nodot")
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_get_schema_not_found_404(client: TestClient) -> None:
    _make_catalog(client)
    r = client.get(f"{SCHEMAS}/main.nope")
    assert r.status_code == 404


def test_list_schemas_by_catalog(client: TestClient) -> None:
    _make_catalog(client)
    _post_schema(client, "b")
    _post_schema(client, "a")
    r = client.get(SCHEMAS, params={"catalog_name": "main"})
    assert r.status_code == 200
    body = r.json()
    # List order is insertion order, not name-sorted.
    assert [s["name"] for s in body["schemas"]] == ["b", "a"]
    assert body["next_page_token"] is None


def test_list_schemas_empty(client: TestClient) -> None:
    _make_catalog(client)
    r = client.get(SCHEMAS, params={"catalog_name": "main"})
    body = r.json()
    assert body["schemas"] == []
    assert body["next_page_token"] is None


def test_list_schemas_multi_page_walk(client: TestClient) -> None:
    _make_catalog(client)
    for name in ("s0", "s1", "s2", "s3", "s4"):
        _post_schema(client, name)

    r1 = client.get(SCHEMAS, params={"catalog_name": "main", "max_results": 2})
    body1 = r1.json()
    assert [s["name"] for s in body1["schemas"]] == ["s0", "s1"]
    assert body1["next_page_token"] is not None

    r2 = client.get(
        SCHEMAS,
        params={
            "catalog_name": "main",
            "max_results": 2,
            "page_token": body1["next_page_token"],
        },
    )
    body2 = r2.json()
    assert [s["name"] for s in body2["schemas"]] == ["s2", "s3"]
    assert body2["next_page_token"] is not None

    r3 = client.get(
        SCHEMAS,
        params={
            "catalog_name": "main",
            "max_results": 2,
            "page_token": body2["next_page_token"],
        },
    )
    body3 = r3.json()
    assert [s["name"] for s in body3["schemas"]] == ["s4"]
    assert body3["next_page_token"] is None


def test_list_schemas_boundary_exact_page_size(client: TestClient) -> None:
    _make_catalog(client)
    for name in ("s0", "s1"):
        _post_schema(client, name)
    body = client.get(
        SCHEMAS,
        params={"catalog_name": "main", "max_results": 2},
    ).json()
    assert [s["name"] for s in body["schemas"]] == ["s0", "s1"]
    assert body["next_page_token"] is None


def test_list_schemas_rejects_tampered_page_token(client: TestClient) -> None:
    _make_catalog(client)
    r = client.get(
        SCHEMAS,
        params={"catalog_name": "main", "page_token": "tampered"},
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_list_schemas_rejects_out_of_range_max_results(client: TestClient) -> None:
    _make_catalog(client)
    # max_results=0 → 200 (JVM UC connector compat: it sends 0 for default).
    assert client.get(SCHEMAS, params={"catalog_name": "main", "max_results": 0}).status_code == 200
    assert (
        client.get(SCHEMAS, params={"catalog_name": "main", "max_results": -1}).status_code == 422
    )
    assert (
        client.get(
            SCHEMAS,
            params={"catalog_name": "main", "max_results": 1001},
        ).status_code
        == 422
    )


def test_list_schemas_requires_catalog_name(client: TestClient) -> None:
    r = client.get(SCHEMAS)
    assert r.status_code == 422


def test_list_schemas_unknown_catalog_404(client: TestClient) -> None:
    r = client.get(SCHEMAS, params={"catalog_name": "nope"})
    assert r.status_code == 404


def test_patch_schema_comment(client: TestClient) -> None:
    _make_catalog(client)
    created = client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).json()
    r = client.patch(f"{SCHEMAS}/main.s", json={"comment": "hi"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["comment"] == "hi"
    assert body["updated_at"] >= created["updated_at"]


def test_patch_schema_rename(client: TestClient) -> None:
    _make_catalog(client)
    client.post(SCHEMAS, json={"name": "old", "catalog_name": "main"})
    r = client.patch(f"{SCHEMAS}/main.old", json={"new_name": "new"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "main.new"
    assert client.get(f"{SCHEMAS}/main.old").status_code == 404
    assert client.get(f"{SCHEMAS}/main.new").status_code == 200


def test_patch_schema_rename_conflict_409(client: TestClient) -> None:
    _make_catalog(client)
    client.post(SCHEMAS, json={"name": "a", "catalog_name": "main"})
    client.post(SCHEMAS, json={"name": "b", "catalog_name": "main"})
    r = client.patch(f"{SCHEMAS}/main.a", json={"new_name": "b"})
    assert r.status_code == 409


def test_patch_empty_properties_clears(client: TestClient) -> None:
    """UC OSS bug fix: PATCH {"properties": {}} clears all properties."""
    _make_catalog(client)
    client.post(
        SCHEMAS,
        json={"name": "s", "catalog_name": "main", "properties": {"a": "1"}},
    )
    r = client.patch(f"{SCHEMAS}/main.s", json={"properties": {}})
    assert r.status_code == 200
    assert r.json()["properties"] == {}
    assert client.get(f"{SCHEMAS}/main.s").json()["properties"] == {}


def test_patch_schema_unknown_field_422(client: TestClient) -> None:
    """UC OSS bug fix: unknown fields raise 422."""
    _make_catalog(client)
    client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    r = client.patch(f"{SCHEMAS}/main.s", json={"bogus": 1})
    assert r.status_code == 422


def test_patch_schema_owner_rejected_422(client: TestClient) -> None:
    """UC OSS bug fix: read-only ``owner`` is rejected, not silently ignored."""
    _make_catalog(client)
    client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    r = client.patch(f"{SCHEMAS}/main.s", json={"owner": "bob"})
    assert r.status_code == 422


def test_patch_schema_empty_body_is_noop(client: TestClient) -> None:
    _make_catalog(client)
    client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    r = client.patch(f"{SCHEMAS}/main.s", json={})
    assert r.status_code == 200
    assert r.json()["name"] == "s"


def test_patch_schema_missing_returns_404(client: TestClient) -> None:
    _make_catalog(client)
    r = client.patch(f"{SCHEMAS}/main.nope", json={"comment": "x"})
    assert r.status_code == 404


def test_delete_schema(client: TestClient) -> None:
    _make_catalog(client)
    client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    r = client.delete(f"{SCHEMAS}/main.s")
    assert r.status_code == 200
    assert r.json() == {}
    assert client.get(f"{SCHEMAS}/main.s").status_code == 404


def test_delete_schema_accepts_force_noop(client: TestClient) -> None:
    _make_catalog(client)
    client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    r = client.delete(f"{SCHEMAS}/main.s", params={"force": "true"})
    assert r.status_code == 200


def test_delete_schema_missing_returns_404(client: TestClient) -> None:
    _make_catalog(client)
    r = client.delete(f"{SCHEMAS}/main.nope")
    assert r.status_code == 404


def test_delete_catalog_with_schemas_conflict_409(client: TestClient) -> None:
    """DELETE /catalogs refuses to drop a catalog that still has schemas."""
    _make_catalog(client)
    client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    r = client.delete(f"{CATALOGS}/main")
    assert r.status_code == 409
    assert r.json()["error_code"] == "ALREADY_EXISTS"
    # Catalog and schema both still exist.
    assert client.get(f"{CATALOGS}/main").status_code == 200
    assert client.get(f"{SCHEMAS}/main.s").status_code == 200


def test_delete_catalog_with_schemas_force_cascades(client: TestClient) -> None:
    """``force=true`` cascades the catalog delete through to child schemas."""
    _make_catalog(client)
    client.post(SCHEMAS, json={"name": "s1", "catalog_name": "main"})
    client.post(SCHEMAS, json={"name": "s2", "catalog_name": "main"})
    r = client.delete(f"{CATALOGS}/main", params={"force": "true"})
    assert r.status_code == 200
    assert client.get(f"{CATALOGS}/main").status_code == 404


def test_catalog_rename_propagates_to_schema_full_name(client: TestClient) -> None:
    """``full_name`` is computed, so renaming the parent catalog updates it for free."""
    _make_catalog(client, "old")
    client.post(SCHEMAS, json={"name": "s", "catalog_name": "old"})
    client.patch(f"{CATALOGS}/old", json={"new_name": "new"})

    # Old full_name no longer resolves.
    assert client.get(f"{SCHEMAS}/old.s").status_code == 404

    body = client.get(f"{SCHEMAS}/new.s").json()
    assert body["full_name"] == "new.s"
    assert body["catalog_name"] == "new"


def test_create_schema_with_supported_storage_root(client: TestClient) -> None:
    """``storage_root`` with a supported scheme is accepted."""
    _make_catalog(client)
    r = client.post(
        SCHEMAS,
        json={
            "name": "s",
            "catalog_name": "main",
            "storage_root": "s3://bucket/schema",
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["storage_root"] == "s3://bucket/schema"


def test_create_schema_rejects_unsupported_storage_root_scheme(
    client: TestClient,
) -> None:
    _make_catalog(client)
    r = client.post(
        SCHEMAS,
        json={
            "name": "s",
            "catalog_name": "main",
            "storage_root": "hdfs://namenode/schema",
        },
    )
    assert r.status_code == 400, r.text
    assert "unsupported storage URI scheme" in r.json()["message"]


def test_create_schema_without_storage_root_still_allowed(client: TestClient) -> None:
    """Guard: the scheme check only fires when ``storage_root`` is present."""
    _make_catalog(client)
    r = client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    assert r.status_code == 200, r.text


def test_create_schema_derives_storage_location_from_own_root(client: TestClient) -> None:
    """Schema's own ``storage_root`` feeds the derivation when set."""
    _make_catalog(client)
    r = client.post(
        SCHEMAS,
        json={"name": "s", "catalog_name": "main", "storage_root": "s3://bucket/schema"},
    )
    body = r.json()
    assert body["storage_location"] == (
        f"s3://bucket/schema/__unitystorage/schemas/{body['schema_id']}"
    )


def test_create_schema_falls_back_to_parent_catalog_root(client: TestClient) -> None:
    """Schemas inherit the parent catalog's root when they have none.

    Without this inheritance ``SchemaInfo.storage_location`` would
    always come back ``None`` whenever the schema itself had no
    ``storage_root``, even when the parent catalog had a perfectly
    good one — that silent-NULL is the gap this test pins shut.
    """
    client.post(CATALOGS, json={"name": "main", "storage_root": "s3://bucket/root"})
    r = client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    body = r.json()
    assert body["storage_location"] == (
        f"s3://bucket/root/__unitystorage/schemas/{body['schema_id']}"
    )


def test_create_schema_without_any_root_has_null_location(client: TestClient) -> None:
    _make_catalog(client)
    r = client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    assert r.json()["storage_location"] is None


def test_rename_schema_preserves_storage_location(client: TestClient) -> None:
    """Rename-invariant regression: id-keyed derivation survives PATCH."""
    client.post(CATALOGS, json={"name": "main", "storage_root": "s3://bucket/root"})
    created = client.post(SCHEMAS, json={"name": "old", "catalog_name": "main"}).json()
    location_before = created["storage_location"]
    assert location_before is not None

    patched = client.patch(f"{SCHEMAS}/main.old", json={"new_name": "new"})
    assert patched.status_code == 200, patched.text
    assert patched.json()["storage_location"] == location_before

    fetched = client.get(f"{SCHEMAS}/main.new").json()
    assert fetched["storage_location"] == location_before
