"""Tests for the Model Versions CRUD sub-resource."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
MODELS = "/api/2.1/unity-catalog/models"
MODEL_VERSIONS = "/api/2.1/unity-catalog/models/versions"


def _setup(client: TestClient) -> None:
    assert client.post(CATALOGS, json={"name": "main"}).status_code == 200
    assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).status_code == 200
    assert (
        client.post(
            MODELS,
            json={"name": "rf", "catalog_name": "main", "schema_name": "s"},
        ).status_code
        == 200
    )


def _create_version_body(
    model_name: str = "rf",
    source: str = "s3://artifacts/v1",
    **overrides: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "model_name": model_name,
        "catalog_name": "main",
        "schema_name": "s",
        "source": source,
    }
    body.update(overrides)
    return body


def test_create_version_happy_path(client: TestClient) -> None:
    _setup(client)
    r = client.post(MODEL_VERSIONS, json=_create_version_body())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["version"] == 1
    # Create writes PENDING_REGISTRATION; client uploads artifacts then
    # calls finalize to flip status to READY.
    assert body["status"] == "PENDING_REGISTRATION"
    assert body["source"] == "s3://artifacts/v1"
    assert body["model_name"] == "rf"
    assert body["catalog_name"] == "main"
    assert body["schema_name"] == "s"
    # Server populates storage_location so the MLflow client has a target
    # URL for artifact upload before finalize.
    assert body["storage_location"].startswith("file://")
    assert body["storage_location"].endswith("/1")


def test_create_version_auto_increments(client: TestClient) -> None:
    _setup(client)
    v1 = client.post(MODEL_VERSIONS, json=_create_version_body(source="s3://a")).json()
    v2 = client.post(MODEL_VERSIONS, json=_create_version_body(source="s3://b")).json()
    v3 = client.post(MODEL_VERSIONS, json=_create_version_body(source="s3://c")).json()
    assert v1["version"] == 1
    assert v2["version"] == 2
    assert v3["version"] == 3


def test_create_version_missing_source_422(client: TestClient) -> None:
    _setup(client)
    body = _create_version_body()
    del body["source"]
    r = client.post(MODEL_VERSIONS, json=body)
    assert r.status_code == 422


def test_create_version_unknown_field_422(client: TestClient) -> None:
    _setup(client)
    body = _create_version_body()
    body["status"] = "READY"  # server-controlled, not accepted on create
    r = client.post(MODEL_VERSIONS, json=body)
    assert r.status_code == 422


def test_create_version_parent_model_404(client: TestClient) -> None:
    _setup(client)
    r = client.post(MODEL_VERSIONS, json=_create_version_body(model_name="nope"))
    assert r.status_code == 404


def test_create_version_parent_schema_404(client: TestClient) -> None:
    assert client.post(CATALOGS, json={"name": "main"}).status_code == 200
    r = client.post(MODEL_VERSIONS, json=_create_version_body())
    assert r.status_code == 404


def test_get_version_happy_path(client: TestClient) -> None:
    _setup(client)
    client.post(MODEL_VERSIONS, json=_create_version_body())
    r = client.get(f"{MODELS}/main.s.rf/versions/1")
    assert r.status_code == 200
    assert r.json()["version"] == 1


def test_get_version_404(client: TestClient) -> None:
    _setup(client)
    r = client.get(f"{MODELS}/main.s.rf/versions/1")
    assert r.status_code == 404


def test_get_version_parent_404(client: TestClient) -> None:
    r = client.get(f"{MODELS}/main.s.rf/versions/1")
    assert r.status_code == 404


def test_get_version_malformed_full_name_400(client: TestClient) -> None:
    r = client.get(f"{MODELS}/main.s/versions/1")
    # FastAPI path matching: "main.s" then "versions/1" → /models/main.s/versions/1 is a
    # different route. But the 3-part guard fires inside get_model_version.
    assert r.status_code in (400, 404)


def test_list_versions_empty(client: TestClient) -> None:
    _setup(client)
    body = client.get(f"{MODELS}/main.s.rf/versions").json()
    assert body["model_versions"] == []
    assert body["next_page_token"] is None


def test_list_versions_order_and_pagination(client: TestClient) -> None:
    _setup(client)
    for src in ("a", "b", "c", "d"):
        client.post(MODEL_VERSIONS, json=_create_version_body(source=f"s3://{src}"))
    base = {"max_results": 2}
    p1 = client.get(f"{MODELS}/main.s.rf/versions", params=base).json()
    assert [v["version"] for v in p1["model_versions"]] == [1, 2]
    assert p1["next_page_token"]
    p2 = client.get(
        f"{MODELS}/main.s.rf/versions",
        params={**base, "page_token": p1["next_page_token"]},
    ).json()
    assert [v["version"] for v in p2["model_versions"]] == [3, 4]


def test_list_versions_parent_404(client: TestClient) -> None:
    r = client.get(f"{MODELS}/main.s.rf/versions")
    assert r.status_code == 404


def test_patch_version_comment(client: TestClient) -> None:
    _setup(client)
    client.post(MODEL_VERSIONS, json=_create_version_body())
    r = client.patch(f"{MODELS}/main.s.rf/versions/1", json={"comment": "tested"})
    assert r.status_code == 200
    assert r.json()["comment"] == "tested"


def test_patch_version_empty_body_noop(client: TestClient) -> None:
    _setup(client)
    client.post(MODEL_VERSIONS, json=_create_version_body())
    r = client.patch(f"{MODELS}/main.s.rf/versions/1", json={})
    assert r.status_code == 200


def test_patch_version_source_rejected_422(client: TestClient) -> None:
    _setup(client)
    client.post(MODEL_VERSIONS, json=_create_version_body())
    r = client.patch(f"{MODELS}/main.s.rf/versions/1", json={"source": "s3://new"})
    assert r.status_code == 422


def test_patch_version_status_rejected_422(client: TestClient) -> None:
    _setup(client)
    client.post(MODEL_VERSIONS, json=_create_version_body())
    r = client.patch(
        f"{MODELS}/main.s.rf/versions/1",
        json={"status": "PENDING_REGISTRATION"},
    )
    assert r.status_code == 422


def test_patch_version_404(client: TestClient) -> None:
    _setup(client)
    r = client.patch(f"{MODELS}/main.s.rf/versions/1", json={"comment": "x"})
    assert r.status_code == 404


def test_delete_version_happy_path(client: TestClient) -> None:
    _setup(client)
    client.post(MODEL_VERSIONS, json=_create_version_body())
    r = client.delete(f"{MODELS}/main.s.rf/versions/1")
    assert r.status_code == 200
    assert client.get(f"{MODELS}/main.s.rf/versions/1").status_code == 404


def test_delete_version_404(client: TestClient) -> None:
    _setup(client)
    r = client.delete(f"{MODELS}/main.s.rf/versions/1")
    assert r.status_code == 404


def test_finalize_transitions_pending_to_ready(client: TestClient) -> None:
    """Finalize moves PENDING_REGISTRATION → READY."""
    _setup(client)
    create = client.post(MODEL_VERSIONS, json=_create_version_body()).json()
    assert create["status"] == "PENDING_REGISTRATION"
    r = client.patch(f"{MODELS}/main.s.rf/versions/1/finalize")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "READY"
    assert body["version"] == 1
    # Re-read returns READY.
    after = client.get(f"{MODELS}/main.s.rf/versions/1").json()
    assert after["status"] == "READY"


def test_finalize_idempotent_on_ready(client: TestClient) -> None:
    """Re-finalizing a READY version is a no-op (200)."""
    _setup(client)
    client.post(MODEL_VERSIONS, json=_create_version_body())
    assert client.patch(f"{MODELS}/main.s.rf/versions/1/finalize").status_code == 200
    r = client.patch(f"{MODELS}/main.s.rf/versions/1/finalize")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "READY"


def test_finalize_404_for_unknown_version(client: TestClient) -> None:
    _setup(client)
    r = client.patch(f"{MODELS}/main.s.rf/versions/99/finalize")
    assert r.status_code == 404


def test_parent_rename_propagates_to_version(client: TestClient) -> None:
    _setup(client)
    client.post(MODEL_VERSIONS, json=_create_version_body())
    client.patch(f"{MODELS}/main.s.rf", json={"new_name": "rf2"})
    r = client.get(f"{MODELS}/main.s.rf2/versions/1")
    assert r.status_code == 200
    assert r.json()["model_name"] == "rf2"


def test_catalog_rename_propagates_to_version(client: TestClient) -> None:
    _setup(client)
    client.post(MODEL_VERSIONS, json=_create_version_body())
    client.patch(f"{CATALOGS}/main", json={"new_name": "prod"})
    r = client.get(f"{MODELS}/prod.s.rf/versions/1")
    assert r.status_code == 200
    assert r.json()["catalog_name"] == "prod"
