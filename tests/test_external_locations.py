from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

CREDENTIALS = "/api/2.1/unity-catalog/credentials"
EXTERNAL_LOCATIONS = "/api/2.1/unity-catalog/external-locations"

_ROLE_ARN = "arn:aws:iam::123456789012:role/soyuz-test"


def _make_credential(client: TestClient, name: str = "cred1") -> dict[str, Any]:
    r = client.post(
        CREDENTIALS,
        json={"name": name, "aws_iam_role": {"role_arn": _ROLE_ARN}},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _minimal_body(
    name: str = "loc1",
    url: str = "s3://bucket/loc1",
    credential_name: str = "cred1",
) -> dict[str, Any]:
    return {"name": name, "url": url, "credential_name": credential_name}


def _post(client: TestClient, name: str, credential_name: str = "cred1") -> dict[str, Any]:
    r = client.post(
        EXTERNAL_LOCATIONS,
        json=_minimal_body(name=name, url=f"s3://bucket/{name}", credential_name=credential_name),
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_create_external_location_happy_path(client: TestClient) -> None:
    cred = _make_credential(client)
    r = client.post(EXTERNAL_LOCATIONS, json=_minimal_body())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "loc1"
    assert body["url"] == "s3://bucket/loc1"
    assert body["credential_name"] == "cred1"
    assert body["credential_id"] == cred["id"]
    assert body["id"]
    assert body["created_at"] > 0


def test_create_external_location_missing_credential_404(client: TestClient) -> None:
    r = client.post(EXTERNAL_LOCATIONS, json=_minimal_body(credential_name="nope"))
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


def test_create_external_location_rejects_unknown_field(client: TestClient) -> None:
    _make_credential(client)
    body = _minimal_body()
    body["made_up"] = "value"
    r = client.post(EXTERNAL_LOCATIONS, json=body)
    assert r.status_code == 422


def test_create_external_location_rejects_credential_id(client: TestClient) -> None:
    _make_credential(client)
    body = _minimal_body()
    body["credential_id"] = "forged-id"
    r = client.post(EXTERNAL_LOCATIONS, json=body)
    assert r.status_code == 422


def test_create_external_location_unsupported_scheme_400(client: TestClient) -> None:
    _make_credential(client)
    r = client.post(
        EXTERNAL_LOCATIONS,
        json=_minimal_body(url="ftp://bucket/loc1"),
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_create_external_location_duplicate_name_409(client: TestClient) -> None:
    _make_credential(client)
    _post(client, "loc1")
    r = client.post(EXTERNAL_LOCATIONS, json=_minimal_body(name="loc1"))
    assert r.status_code == 409


def test_get_external_location_not_found_404(client: TestClient) -> None:
    r = client.get(f"{EXTERNAL_LOCATIONS}/missing")
    assert r.status_code == 404


def test_list_external_locations_empty(client: TestClient) -> None:
    r = client.get(EXTERNAL_LOCATIONS)
    assert r.status_code == 200
    assert r.json() == {"external_locations": [], "next_page_token": None}


def test_list_external_locations_multi_page(client: TestClient) -> None:
    _make_credential(client)
    for i in range(5):
        _post(client, f"loc{i}")
    r = client.get(f"{EXTERNAL_LOCATIONS}?max_results=2")
    body = r.json()
    assert len(body["external_locations"]) == 2
    assert body["next_page_token"]
    r2 = client.get(
        f"{EXTERNAL_LOCATIONS}?max_results=2&page_token={body['next_page_token']}",
    )
    assert len(r2.json()["external_locations"]) == 2


def test_update_external_location_rename(client: TestClient) -> None:
    _make_credential(client)
    _post(client, "loc1")
    r = client.patch(
        f"{EXTERNAL_LOCATIONS}/loc1",
        json={"new_name": "loc1-renamed"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "loc1-renamed"
    assert client.get(f"{EXTERNAL_LOCATIONS}/loc1").status_code == 404


def test_update_external_location_rename_collision_409(client: TestClient) -> None:
    _make_credential(client)
    _post(client, "loc1")
    _post(client, "loc2")
    r = client.patch(f"{EXTERNAL_LOCATIONS}/loc1", json={"new_name": "loc2"})
    assert r.status_code == 409


def test_update_external_location_rebind_credential(client: TestClient) -> None:
    cred1 = _make_credential(client, "cred1")
    cred2 = _make_credential(client, "cred2")
    _post(client, "loc1")
    r = client.patch(
        f"{EXTERNAL_LOCATIONS}/loc1",
        json={"credential_name": "cred2"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["credential_name"] == "cred2"
    assert body["credential_id"] == cred2["id"]
    assert body["credential_id"] != cred1["id"]


def test_update_external_location_rebind_missing_credential_404(
    client: TestClient,
) -> None:
    _make_credential(client)
    _post(client, "loc1")
    r = client.patch(
        f"{EXTERNAL_LOCATIONS}/loc1",
        json={"credential_name": "nope"},
    )
    assert r.status_code == 404


def test_update_external_location_url_scheme_gated(client: TestClient) -> None:
    _make_credential(client)
    _post(client, "loc1")
    r = client.patch(
        f"{EXTERNAL_LOCATIONS}/loc1",
        json={"url": "ftp://bucket/loc1"},
    )
    assert r.status_code == 400


def test_update_external_location_empty_body_is_noop(client: TestClient) -> None:
    _make_credential(client)
    _post(client, "loc1")
    r = client.patch(f"{EXTERNAL_LOCATIONS}/loc1", json={})
    assert r.status_code == 200
    assert r.json()["name"] == "loc1"


def test_update_external_location_forbids_read_only_fields(client: TestClient) -> None:
    _make_credential(client)
    _post(client, "loc1")
    r = client.patch(f"{EXTERNAL_LOCATIONS}/loc1", json={"id": "forged"})
    assert r.status_code == 422


def test_credential_rename_propagates_to_external_location_read(
    client: TestClient,
) -> None:
    """Critical rename-invariance test.

    Renaming a credential must surface the new name on every bound
    external location on the next read, without any fan-out UPDATE on
    the external_locations table. This is the whole point of storing
    only credential_id on the row and reconstructing credential_name
    at response time.
    """
    _make_credential(client, "cred1")
    _post(client, "loc1")

    r = client.patch(f"{CREDENTIALS}/cred1", json={"new_name": "cred1-renamed"})
    assert r.status_code == 200

    r = client.get(f"{EXTERNAL_LOCATIONS}/loc1")
    assert r.status_code == 200
    assert r.json()["credential_name"] == "cred1-renamed"


def test_delete_credential_with_external_location_409_without_force(
    client: TestClient,
) -> None:
    _make_credential(client)
    _post(client, "loc1")
    r = client.delete(f"{CREDENTIALS}/cred1")
    assert r.status_code == 409
    assert r.json()["error_code"] == "ALREADY_EXISTS"


def test_delete_credential_with_external_location_force_cascades(
    client: TestClient,
) -> None:
    _make_credential(client)
    _post(client, "loc1")
    r = client.delete(f"{CREDENTIALS}/cred1?force=true")
    assert r.status_code == 200
    # Credential and the referencing external location are both gone.
    assert client.get(f"{CREDENTIALS}/cred1").status_code == 404
    assert client.get(f"{EXTERNAL_LOCATIONS}/loc1").status_code == 404


def test_delete_external_location_happy_path(client: TestClient) -> None:
    _make_credential(client)
    _post(client, "loc1")
    r = client.delete(f"{EXTERNAL_LOCATIONS}/loc1")
    assert r.status_code == 200
    assert client.get(f"{EXTERNAL_LOCATIONS}/loc1").status_code == 404


def test_delete_external_location_not_found_404(client: TestClient) -> None:
    r = client.delete(f"{EXTERNAL_LOCATIONS}/missing")
    assert r.status_code == 404
