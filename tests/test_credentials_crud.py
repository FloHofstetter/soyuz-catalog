from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

CREDENTIALS = "/api/2.1/unity-catalog/credentials"
EXTERNAL_LOCATIONS = "/api/2.1/unity-catalog/external-locations"

_ROLE_ARN = "arn:aws:iam::123456789012:role/soyuz-test"


def _minimal_body(name: str = "cred1", with_role: bool = True) -> dict[str, Any]:
    body: dict[str, Any] = {"name": name}
    if with_role:
        body["aws_iam_role"] = {"role_arn": _ROLE_ARN}
    return body


def _post(client: TestClient, name: str) -> dict[str, Any]:
    r = client.post(CREDENTIALS, json=_minimal_body(name=name))
    assert r.status_code == 200, r.text
    return r.json()


def test_create_credential_minimal(client: TestClient) -> None:
    r = client.post(CREDENTIALS, json=_minimal_body())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "cred1"
    assert body["id"]
    assert body["purpose"] == "STORAGE"
    assert body["aws_iam_role"]["role_arn"] == _ROLE_ARN
    assert body["aws_iam_role"]["external_id"]
    # unity_catalog_iam_arn must not appear on the wire — we never populate
    # it and the route uses exclude_none.
    assert "unity_catalog_iam_arn" not in body["aws_iam_role"]
    assert body["created_at"] > 0


def test_create_credential_without_aws_iam_role(client: TestClient) -> None:
    r = client.post(CREDENTIALS, json=_minimal_body(with_role=False))
    assert r.status_code == 200
    body = r.json()
    # No aws_iam_role at all — exclude_none kicks in because we only build the
    # nested model when role_arn is set.
    assert "aws_iam_role" not in body


def test_create_credential_explicit_purpose(client: TestClient) -> None:
    body = _minimal_body()
    body["purpose"] = "STORAGE"
    r = client.post(CREDENTIALS, json=body)
    assert r.status_code == 200
    assert r.json()["purpose"] == "STORAGE"


def test_create_credential_invalid_purpose_422(client: TestClient) -> None:
    body = _minimal_body()
    body["purpose"] = "LINEAGE"
    r = client.post(CREDENTIALS, json=body)
    assert r.status_code == 422


def test_create_credential_rejects_unknown_field(client: TestClient) -> None:
    body = _minimal_body()
    body["made_up"] = "value"
    r = client.post(CREDENTIALS, json=body)
    assert r.status_code == 422


def test_create_credential_rejects_unknown_field_in_aws_iam_role(
    client: TestClient,
) -> None:
    body = _minimal_body()
    body["aws_iam_role"] = {"role_arn": _ROLE_ARN, "rolearn_typo": "oops"}
    r = client.post(CREDENTIALS, json=body)
    assert r.status_code == 422


def test_create_credential_duplicate_name_409(client: TestClient) -> None:
    _post(client, "cred1")
    r = client.post(CREDENTIALS, json=_minimal_body(name="cred1"))
    assert r.status_code == 409
    assert r.json()["error_code"] == "ALREADY_EXISTS"


def test_get_credential_happy_path(client: TestClient) -> None:
    _post(client, "cred1")
    r = client.get(f"{CREDENTIALS}/cred1")
    assert r.status_code == 200
    assert r.json()["name"] == "cred1"


def test_get_credential_not_found_404(client: TestClient) -> None:
    r = client.get(f"{CREDENTIALS}/missing")
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


def test_list_credentials_empty(client: TestClient) -> None:
    r = client.get(CREDENTIALS)
    assert r.status_code == 200
    assert r.json() == {"credentials": []}


def test_list_credentials_multi_page(client: TestClient) -> None:
    for i in range(5):
        _post(client, f"cred{i}")
    r = client.get(f"{CREDENTIALS}?max_results=2")
    body = r.json()
    assert len(body["credentials"]) == 2
    assert body["next_page_token"]
    r2 = client.get(f"{CREDENTIALS}?max_results=2&page_token={body['next_page_token']}")
    body2 = r2.json()
    assert len(body2["credentials"]) == 2
    assert body2["next_page_token"]
    r3 = client.get(f"{CREDENTIALS}?max_results=2&page_token={body2['next_page_token']}")
    body3 = r3.json()
    assert len(body3["credentials"]) == 1
    assert body3.get("next_page_token") is None


def test_list_credentials_bad_token_400(client: TestClient) -> None:
    r = client.get(f"{CREDENTIALS}?page_token=not-a-real-token")
    assert r.status_code == 400


def test_list_credentials_purpose_filter(client: TestClient) -> None:
    _post(client, "cred1")
    r = client.get(f"{CREDENTIALS}?purpose=STORAGE")
    assert r.status_code == 200
    assert len(r.json()["credentials"]) == 1


def test_list_credentials_invalid_purpose_filter_422(client: TestClient) -> None:
    r = client.get(f"{CREDENTIALS}?purpose=BOGUS")
    assert r.status_code == 422


def test_update_credential_rename(client: TestClient) -> None:
    _post(client, "cred1")
    r = client.patch(f"{CREDENTIALS}/cred1", json={"new_name": "cred1-renamed"})
    assert r.status_code == 200
    assert r.json()["name"] == "cred1-renamed"
    assert client.get(f"{CREDENTIALS}/cred1").status_code == 404
    assert client.get(f"{CREDENTIALS}/cred1-renamed").status_code == 200


def test_update_credential_rename_collision_409(client: TestClient) -> None:
    _post(client, "cred1")
    _post(client, "cred2")
    r = client.patch(f"{CREDENTIALS}/cred1", json={"new_name": "cred2"})
    assert r.status_code == 409


def test_update_credential_replaces_role_arn(client: TestClient) -> None:
    _post(client, "cred1")
    new_arn = "arn:aws:iam::999999999999:role/other"
    r = client.patch(
        f"{CREDENTIALS}/cred1",
        json={"aws_iam_role": {"role_arn": new_arn}},
    )
    assert r.status_code == 200
    assert r.json()["aws_iam_role"]["role_arn"] == new_arn


def test_update_credential_preserves_external_id_on_role_replace(
    client: TestClient,
) -> None:
    before = _post(client, "cred1")
    external_id_before = before["aws_iam_role"]["external_id"]
    r = client.patch(
        f"{CREDENTIALS}/cred1",
        json={"aws_iam_role": {"role_arn": "arn:aws:iam::1:role/x"}},
    )
    assert r.status_code == 200
    # external_id is server-owned and must NOT rotate on PATCH — doing so
    # would defeat its purpose as the confused-deputy mitigation.
    assert r.json()["aws_iam_role"]["external_id"] == external_id_before


def test_update_credential_empty_body_is_noop(client: TestClient) -> None:
    _post(client, "cred1")
    r = client.patch(f"{CREDENTIALS}/cred1", json={})
    assert r.status_code == 200
    assert r.json()["name"] == "cred1"


def test_update_credential_forbids_read_only_fields(client: TestClient) -> None:
    _post(client, "cred1")
    r = client.patch(f"{CREDENTIALS}/cred1", json={"id": "deadbeef"})
    assert r.status_code == 422


def test_delete_credential_happy_path(client: TestClient) -> None:
    _post(client, "cred1")
    r = client.delete(f"{CREDENTIALS}/cred1")
    assert r.status_code == 200
    assert client.get(f"{CREDENTIALS}/cred1").status_code == 404


def test_delete_credential_not_found_404(client: TestClient) -> None:
    r = client.delete(f"{CREDENTIALS}/missing")
    assert r.status_code == 404
