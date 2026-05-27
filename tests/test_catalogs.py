from fastapi.testclient import TestClient

PREFIX = "/api/2.1/unity-catalog/catalogs"


def _post_catalog(client: TestClient, name: str) -> None:
    assert client.post(PREFIX, json={"name": name}).status_code == 200


def test_create_and_get(client: TestClient) -> None:
    r = client.post(PREFIX, json={"name": "main"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "main"
    assert body["id"]
    assert body["created_at"] > 0
    assert body["properties"] == {}

    r = client.get(f"{PREFIX}/main")
    assert r.status_code == 200
    assert r.json()["name"] == "main"


def test_list_returns_created(client: TestClient) -> None:
    # Canonical list order is ``(created_at ASC, id ASC)`` — insertion
    # order, not name-sorted.
    _post_catalog(client, "b")
    _post_catalog(client, "a")
    r = client.get(PREFIX)
    assert r.status_code == 200
    body = r.json()
    names = [c["name"] for c in body["catalogs"]]
    assert names == ["b", "a"]
    assert body["next_page_token"] is None


def test_list_empty(client: TestClient) -> None:
    r = client.get(PREFIX)
    assert r.status_code == 200
    body = r.json()
    assert body["catalogs"] == []
    assert body["next_page_token"] is None


def test_list_multi_page_walk(client: TestClient) -> None:
    for name in ("c0", "c1", "c2", "c3", "c4"):
        _post_catalog(client, name)

    r1 = client.get(PREFIX, params={"max_results": 2})
    body1 = r1.json()
    assert [c["name"] for c in body1["catalogs"]] == ["c0", "c1"]
    assert body1["next_page_token"] is not None

    r2 = client.get(
        PREFIX,
        params={"max_results": 2, "page_token": body1["next_page_token"]},
    )
    body2 = r2.json()
    assert [c["name"] for c in body2["catalogs"]] == ["c2", "c3"]
    assert body2["next_page_token"] is not None

    r3 = client.get(
        PREFIX,
        params={"max_results": 2, "page_token": body2["next_page_token"]},
    )
    body3 = r3.json()
    assert [c["name"] for c in body3["catalogs"]] == ["c4"]
    assert body3["next_page_token"] is None


def test_list_boundary_exact_page_size(client: TestClient) -> None:
    """Last page has exactly ``max_results`` rows — no phantom next page."""
    for name in ("c0", "c1"):
        _post_catalog(client, name)
    r = client.get(PREFIX, params={"max_results": 2})
    body = r.json()
    assert [c["name"] for c in body["catalogs"]] == ["c0", "c1"]
    assert body["next_page_token"] is None


def test_list_rejects_tampered_page_token(client: TestClient) -> None:
    r = client.get(PREFIX, params={"page_token": "definitely-not-a-real-token"})
    assert r.status_code == 400
    body = r.json()
    assert body["error_code"] == "INVALID_ARGUMENT"


def test_list_rejects_out_of_range_max_results(client: TestClient) -> None:
    # FastAPI's Query(ge=0, le=1000) intercepts before the service layer.
    # max_results=0 is accepted as "use server default" because the
    # upstream JVM UCSingleCatalog connector sends 0 for the default;
    # rejecting 0 with 422 would break every listTables call from it.
    assert client.get(PREFIX, params={"max_results": 0}).status_code == 200
    assert client.get(PREFIX, params={"max_results": -1}).status_code == 422
    assert client.get(PREFIX, params={"max_results": 1001}).status_code == 422


def test_patch_comment_updates_timestamp(client: TestClient) -> None:
    created = client.post(PREFIX, json={"name": "c"}).json()
    r = client.patch(f"{PREFIX}/c", json={"comment": "hi"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["comment"] == "hi"
    assert body["updated_at"] >= created["updated_at"]


def test_patch_empty_properties_clears(client: TestClient) -> None:
    """UC OSS bug fix: PATCH {"properties": {}} clears all properties."""
    client.post(PREFIX, json={"name": "c", "properties": {"a": "1", "b": "2"}})
    r = client.patch(f"{PREFIX}/c", json={"properties": {}})
    assert r.status_code == 200, r.text
    assert r.json()["properties"] == {}

    r = client.get(f"{PREFIX}/c")
    assert r.json()["properties"] == {}


def test_patch_replaces_properties(client: TestClient) -> None:
    client.post(PREFIX, json={"name": "c", "properties": {"a": "1"}})
    r = client.patch(f"{PREFIX}/c", json={"properties": {"b": "2"}})
    assert r.status_code == 200
    assert r.json()["properties"] == {"b": "2"}


def test_patch_owner_rejected(client: TestClient) -> None:
    """UC OSS bug fix: unknown/read-only fields raise 422 instead of being dropped."""
    client.post(PREFIX, json={"name": "c"})
    r = client.patch(f"{PREFIX}/c", json={"owner": "bob"})
    assert r.status_code == 422

    # Owner unchanged.
    body = client.get(f"{PREFIX}/c").json()
    assert body["owner"] is None


def test_patch_rename(client: TestClient) -> None:
    client.post(PREFIX, json={"name": "old"})
    r = client.patch(f"{PREFIX}/old", json={"new_name": "new"})
    assert r.status_code == 200
    assert r.json()["name"] == "new"

    assert client.get(f"{PREFIX}/old").status_code == 404
    assert client.get(f"{PREFIX}/new").status_code == 200


def test_patch_missing_returns_404(client: TestClient) -> None:
    r = client.patch(f"{PREFIX}/nope", json={"comment": "x"})
    assert r.status_code == 404


def test_patch_empty_body_is_noop(client: TestClient) -> None:
    created = client.post(PREFIX, json={"name": "c"}).json()
    r = client.patch(f"{PREFIX}/c", json={})
    assert r.status_code == 200
    assert r.json()["name"] == created["name"]


def test_create_duplicate_returns_409(client: TestClient) -> None:
    assert client.post(PREFIX, json={"name": "c"}).status_code == 200
    r = client.post(PREFIX, json={"name": "c"})
    assert r.status_code == 409
    assert r.json()["error_code"] == "ALREADY_EXISTS"


def test_create_missing_name_returns_422(client: TestClient) -> None:
    r = client.post(PREFIX, json={})
    assert r.status_code == 422


def test_create_unknown_field_rejected(client: TestClient) -> None:
    r = client.post(PREFIX, json={"name": "c", "bogus": 1})
    assert r.status_code == 422


def test_delete_then_get_returns_404(client: TestClient) -> None:
    client.post(PREFIX, json={"name": "c"})
    r = client.delete(f"{PREFIX}/c")
    assert r.status_code == 200
    assert r.json() == {}
    assert client.get(f"{PREFIX}/c").status_code == 404


def test_delete_missing_returns_404(client: TestClient) -> None:
    r = client.delete(f"{PREFIX}/nope")
    assert r.status_code == 404


def test_create_catalog_with_supported_storage_root(client: TestClient) -> None:
    """``storage_root`` with a supported scheme is accepted."""
    r = client.post(PREFIX, json={"name": "c", "storage_root": "s3://bucket/root"})
    assert r.status_code == 200, r.text
    assert r.json()["storage_root"] == "s3://bucket/root"


def test_create_catalog_rejects_unsupported_storage_root_scheme(client: TestClient) -> None:
    r = client.post(PREFIX, json={"name": "c", "storage_root": "hdfs://nn/root"})
    assert r.status_code == 400, r.text
    assert "unsupported storage URI scheme" in r.json()["message"]


def test_create_catalog_derives_storage_location_from_root(client: TestClient) -> None:
    """``storage_location`` is derived under ``__unitystorage/catalogs/{id}``."""
    r = client.post(PREFIX, json={"name": "c", "storage_root": "s3://bucket/root"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["storage_location"] == f"s3://bucket/root/__unitystorage/catalogs/{body['id']}"


def test_create_catalog_strips_trailing_slash_from_root(client: TestClient) -> None:
    r = client.post(PREFIX, json={"name": "c", "storage_root": "s3://bucket/root/"})
    body = r.json()
    assert body["storage_location"] == f"s3://bucket/root/__unitystorage/catalogs/{body['id']}"


def test_create_catalog_without_storage_root_has_null_location(client: TestClient) -> None:
    r = client.post(PREFIX, json={"name": "c"})
    assert r.status_code == 200, r.text
    assert r.json()["storage_location"] is None


def test_rename_catalog_preserves_storage_location(client: TestClient) -> None:
    """Rename-invariant: the derived path keys on ``id``, not ``name``.

    Regression guard against a naive refactor that recomputes
    ``storage_location`` from the current name — which would
    silently break any child resource whose physical layout
    references the old path.
    """
    created = client.post(PREFIX, json={"name": "old", "storage_root": "s3://bucket/root"}).json()
    location_before = created["storage_location"]
    assert location_before is not None

    patched = client.patch(f"{PREFIX}/old", json={"new_name": "new"})
    assert patched.status_code == 200, patched.text
    assert patched.json()["storage_location"] == location_before

    fetched = client.get(f"{PREFIX}/new").json()
    assert fetched["storage_location"] == location_before
    assert fetched["id"] == created["id"]
