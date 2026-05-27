"""Tests for the Registered Models CRUD resource."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
MODELS = "/api/2.1/unity-catalog/models"
MODEL_VERSIONS = "/api/2.1/unity-catalog/models/versions"


def _make_catalog(client: TestClient, name: str = "main") -> None:
    assert client.post(CATALOGS, json={"name": name}).status_code == 200


def _make_schema(
    client: TestClient,
    catalog_name: str = "main",
    name: str = "s",
) -> None:
    assert (
        client.post(SCHEMAS, json={"name": name, "catalog_name": catalog_name}).status_code == 200
    )


def _minimal_body(
    name: str = "rf",
    catalog_name: str = "main",
    schema_name: str = "s",
) -> dict[str, Any]:
    return {"name": name, "catalog_name": catalog_name, "schema_name": schema_name}


def _post_model(client: TestClient, name: str) -> None:
    assert client.post(MODELS, json=_minimal_body(name=name)).status_code == 200


def _post_version(client: TestClient, model_name: str = "rf", source: str = "s3://a") -> int:
    r = client.post(
        MODEL_VERSIONS,
        json={
            "model_name": model_name,
            "catalog_name": "main",
            "schema_name": "s",
            "source": source,
        },
    )
    assert r.status_code == 200, r.text
    return int(r.json()["version"])


def test_create_registered_model_happy_path(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.post(MODELS, json=_minimal_body())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["full_name"] == "main.s.rf"
    assert body["name"] == "rf"
    assert body["catalog_name"] == "main"
    assert body["schema_name"] == "s"
    assert body["id"]


def test_create_registered_model_unknown_parent_404(client: TestClient) -> None:
    r = client.post(MODELS, json=_minimal_body(catalog_name="nope"))
    assert r.status_code == 404


def test_create_registered_model_duplicate_409(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body())
    r = client.post(MODELS, json=_minimal_body())
    assert r.status_code == 409


def test_create_registered_model_unknown_field_422(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = _minimal_body()
    body["storage_location"] = "s3://nope"  # read-only, not on Create
    r = client.post(MODELS, json=body)
    assert r.status_code == 422


def test_same_model_name_in_two_schemas(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client, name="s1")
    _make_schema(client, name="s2")
    assert client.post(MODELS, json=_minimal_body(schema_name="s1")).status_code == 200
    assert client.post(MODELS, json=_minimal_body(schema_name="s2")).status_code == 200


def test_get_registered_model_happy_path(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body())
    r = client.get(f"{MODELS}/main.s.rf")
    assert r.status_code == 200
    assert r.json()["full_name"] == "main.s.rf"


def test_get_registered_model_malformed_full_name_400(client: TestClient) -> None:
    r = client.get(f"{MODELS}/main.s")
    assert r.status_code == 400


def test_get_registered_model_404(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.get(f"{MODELS}/main.s.nope")
    assert r.status_code == 404


def test_list_registered_models_empty(client: TestClient) -> None:
    body = client.get(MODELS).json()
    assert body["registered_models"] == []
    assert body["next_page_token"] is None


def test_list_registered_models_metastore_wide(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client, name="s1")
    _make_schema(client, name="s2")
    client.post(MODELS, json=_minimal_body(name="a", schema_name="s1"))
    client.post(MODELS, json=_minimal_body(name="b", schema_name="s2"))
    body = client.get(MODELS).json()
    assert {m["name"] for m in body["registered_models"]} == {"a", "b"}


def test_list_registered_models_schema_name_without_catalog_400(client: TestClient) -> None:
    r = client.get(MODELS, params={"schema_name": "s"})
    assert r.status_code == 400


def test_list_registered_models_catalog_filter(client: TestClient) -> None:
    _make_catalog(client, name="one")
    _make_catalog(client, name="two")
    _make_schema(client, catalog_name="one", name="s")
    _make_schema(client, catalog_name="two", name="s")
    client.post(MODELS, json=_minimal_body(catalog_name="one"))
    client.post(MODELS, json=_minimal_body(catalog_name="two"))
    body = client.get(MODELS, params={"catalog_name": "one"}).json()
    assert len(body["registered_models"]) == 1
    assert body["registered_models"][0]["catalog_name"] == "one"


def test_list_registered_models_pagination(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    for name in ("m0", "m1", "m2", "m3"):
        _post_model(client, name)
    base = {"max_results": 2}
    p1 = client.get(MODELS, params=base).json()
    assert [m["name"] for m in p1["registered_models"]] == ["m0", "m1"]
    assert p1["next_page_token"]
    p2 = client.get(MODELS, params={**base, "page_token": p1["next_page_token"]}).json()
    assert [m["name"] for m in p2["registered_models"]] == ["m2", "m3"]


def test_patch_registered_model_rename(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body())
    r = client.patch(f"{MODELS}/main.s.rf", json={"new_name": "rf2"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "main.s.rf2"


def test_patch_registered_model_comment(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body())
    r = client.patch(f"{MODELS}/main.s.rf", json={"comment": "cool"})
    assert r.status_code == 200
    assert r.json()["comment"] == "cool"


def test_patch_registered_model_empty_body_is_noop(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body())
    r = client.patch(f"{MODELS}/main.s.rf", json={})
    assert r.status_code == 200


def test_patch_registered_model_unknown_field_422(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body())
    r = client.patch(f"{MODELS}/main.s.rf", json={"storage_location": "s3://x"})
    assert r.status_code == 422


def test_patch_registered_model_rename_collision_409(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body(name="a"))
    client.post(MODELS, json=_minimal_body(name="b"))
    r = client.patch(f"{MODELS}/main.s.a", json={"new_name": "b"})
    assert r.status_code == 409


def test_delete_registered_model_happy_path(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body())
    assert client.delete(f"{MODELS}/main.s.rf").status_code == 200
    assert client.get(f"{MODELS}/main.s.rf").status_code == 404


def test_delete_registered_model_404(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.delete(f"{MODELS}/main.s.nope")
    assert r.status_code == 404


def test_delete_registered_model_refused_when_versions_exist(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body())
    _post_version(client)
    r = client.delete(f"{MODELS}/main.s.rf")
    assert r.status_code == 409


def test_delete_registered_model_force_cascades_versions(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body())
    _post_version(client)
    _post_version(client)
    r = client.delete(f"{MODELS}/main.s.rf", params={"force": "true"})
    assert r.status_code == 200
    # Versions are gone too.
    assert client.get(f"{MODELS}/main.s.rf/versions/1").status_code == 404


def test_schema_delete_refuses_when_registered_models_exist(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body())
    r = client.delete(f"{SCHEMAS}/main.s")
    assert r.status_code == 409
    assert "registered models" in r.json()["message"]


def test_schema_delete_force_cascades_registered_models(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body())
    _post_version(client)
    r = client.delete(f"{SCHEMAS}/main.s", params={"force": "true"})
    assert r.status_code == 200


def test_catalog_rename_propagates_to_model_full_name(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    client.post(MODELS, json=_minimal_body())
    client.patch(f"{CATALOGS}/main", json={"new_name": "prod"})
    r = client.get(f"{MODELS}/prod.s.rf")
    assert r.status_code == 200
    assert r.json()["catalog_name"] == "prod"
