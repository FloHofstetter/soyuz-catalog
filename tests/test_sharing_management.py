"""Unit tests for the Delta Sharing management surface (ADR-0015).

Covers shares / share objects / recipients / grants CRUD plus the
token-handling invariants (plaintext exactly once, hash never on the
wire). The recipient-facing protocol surface has its own suite in
``tests/test_sharing_protocol.py``.
"""

from __future__ import annotations

import hashlib
from typing import Any

from fastapi.testclient import TestClient

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
TABLES = "/api/2.1/unity-catalog/tables"
SHARES = "/api/2.1/unity-catalog/shares"
RECIPIENTS = "/api/2.1/unity-catalog/recipients"
AUDIT_LOG = "/audit-log"


def _make_table(client: TestClient, name: str = "orders") -> None:
    if client.get(f"{CATALOGS}/main").status_code == 404:
        assert client.post(CATALOGS, json={"name": "main"}).status_code == 200
        assert client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"}).status_code == 200
    body: dict[str, Any] = {
        "name": name,
        "catalog_name": "main",
        "schema_name": "s",
        "table_type": "EXTERNAL",
        "data_source_format": "DELTA",
        "storage_location": f"file:///tmp/{name}",
        "columns": [
            {"name": "id", "type_name": "LONG", "type_text": "bigint", "type_json": "{}"},
        ],
    }
    assert client.post(TABLES, json=body).status_code == 200


def _make_share(client: TestClient, name: str = "sh") -> dict[str, Any]:
    r = client.post(SHARES, json={"name": name})
    assert r.status_code == 200, r.text
    return r.json()


def _make_recipient(client: TestClient, name: str = "r1") -> dict[str, Any]:
    r = client.post(RECIPIENTS, json={"name": name})
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Shares CRUD
# ---------------------------------------------------------------------------


def test_create_share(client: TestClient) -> None:
    r = client.post(SHARES, json={"name": "sh", "comment": "quarterly data"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "sh"
    assert body["comment"] == "quarterly data"
    assert body["id"]
    assert body["objects"] == []
    assert body["created_at"] > 0


def test_create_share_conflict(client: TestClient) -> None:
    _make_share(client)
    r = client.post(SHARES, json={"name": "sh"})
    assert r.status_code == 409


def test_create_share_extra_field_422(client: TestClient) -> None:
    r = client.post(SHARES, json={"name": "sh", "objects": []})
    assert r.status_code == 422


def test_get_share_not_found(client: TestClient) -> None:
    assert client.get(f"{SHARES}/missing").status_code == 404


def test_list_shares_pagination(client: TestClient) -> None:
    for n in ("s0", "s1", "s2"):
        _make_share(client, n)
    r1 = client.get(SHARES, params={"max_results": 2})
    body1 = r1.json()
    assert [s["name"] for s in body1["shares"]] == ["s0", "s1"]
    assert body1["next_page_token"]
    r2 = client.get(SHARES, params={"page_token": body1["next_page_token"]})
    assert [s["name"] for s in r2.json()["shares"]] == ["s2"]


def test_patch_share_rename_and_comment(client: TestClient) -> None:
    _make_share(client)
    r = client.patch(f"{SHARES}/sh", json={"new_name": "sh2", "comment": "x"})
    assert r.status_code == 200
    assert r.json()["name"] == "sh2"
    assert client.get(f"{SHARES}/sh").status_code == 404
    assert client.get(f"{SHARES}/sh2").status_code == 200


def test_patch_share_rename_collision_409(client: TestClient) -> None:
    _make_share(client, "a")
    _make_share(client, "b")
    assert client.patch(f"{SHARES}/a", json={"new_name": "b"}).status_code == 409


def test_delete_share_cascades_objects_and_grants(client: TestClient) -> None:
    _make_table(client)
    _make_share(client)
    _make_recipient(client)
    assert (
        client.post(f"{SHARES}/sh/objects", json={"table_full_name": "main.s.orders"}).status_code
        == 200
    )
    assert client.put(f"{SHARES}/sh/recipients/r1").status_code == 200
    assert client.delete(f"{SHARES}/sh").status_code == 200
    assert client.get(f"{SHARES}/sh").status_code == 404
    # Recreating the name yields a fresh, empty share — no orphan
    # objects or grants resurface.
    body = _make_share(client)
    assert body["objects"] == []


# ---------------------------------------------------------------------------
# Share objects
# ---------------------------------------------------------------------------


def test_add_share_object(client: TestClient) -> None:
    _make_table(client)
    _make_share(client)
    r = client.post(f"{SHARES}/sh/objects", json={"table_full_name": "main.s.orders"})
    assert r.status_code == 200, r.text
    objects = r.json()["objects"]
    assert len(objects) == 1
    assert objects[0]["table_full_name"] == "main.s.orders"
    assert objects[0].get("shared_as") is None
    assert objects[0]["added_at"] > 0


def test_add_share_object_with_shared_as(client: TestClient) -> None:
    _make_table(client)
    _make_share(client)
    r = client.post(
        f"{SHARES}/sh/objects",
        json={"table_full_name": "main.s.orders", "shared_as": "public.orders_v1"},
    )
    assert r.status_code == 200
    assert r.json()["objects"][0]["shared_as"] == "public.orders_v1"


def test_add_share_object_missing_table_404(client: TestClient) -> None:
    _make_share(client)
    r = client.post(f"{SHARES}/sh/objects", json={"table_full_name": "main.s.missing"})
    assert r.status_code == 404


def test_add_share_object_malformed_name_400(client: TestClient) -> None:
    _make_share(client)
    r = client.post(f"{SHARES}/sh/objects", json={"table_full_name": "two.parts"})
    assert r.status_code == 400


def test_add_share_object_malformed_shared_as_400(client: TestClient) -> None:
    _make_table(client)
    _make_share(client)
    r = client.post(
        f"{SHARES}/sh/objects",
        json={"table_full_name": "main.s.orders", "shared_as": "three.part.alias"},
    )
    assert r.status_code == 400


def test_add_share_object_duplicate_409(client: TestClient) -> None:
    _make_table(client)
    _make_share(client)
    body = {"table_full_name": "main.s.orders", "shared_as": "public.orders"}
    assert client.post(f"{SHARES}/sh/objects", json=body).status_code == 200
    assert client.post(f"{SHARES}/sh/objects", json=body).status_code == 409


def test_add_share_object_placement_collision_409(client: TestClient) -> None:
    """Two objects must never answer to the same protocol address."""
    _make_table(client, "orders")
    _make_table(client, "orders_v2")
    _make_share(client)
    assert (
        client.post(f"{SHARES}/sh/objects", json={"table_full_name": "main.s.orders"}).status_code
        == 200
    )
    r = client.post(
        f"{SHARES}/sh/objects",
        json={"table_full_name": "main.s.orders_v2", "shared_as": "s.orders"},
    )
    assert r.status_code == 409


def test_remove_share_object(client: TestClient) -> None:
    _make_table(client)
    _make_share(client)
    assert (
        client.post(f"{SHARES}/sh/objects", json={"table_full_name": "main.s.orders"}).status_code
        == 200
    )
    r = client.delete(f"{SHARES}/sh/objects", params={"table_full_name": "main.s.orders"})
    assert r.status_code == 200
    assert r.json()["objects"] == []


def test_remove_share_object_not_in_share_404(client: TestClient) -> None:
    _make_share(client)
    r = client.delete(f"{SHARES}/sh/objects", params={"table_full_name": "main.s.orders"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Recipients + tokens
# ---------------------------------------------------------------------------


def test_create_recipient_returns_token_once(client: TestClient) -> None:
    body = _make_recipient(client)
    assert body["name"] == "r1"
    assert body["token"]
    # Subsequent reads never carry the token (or any hash).
    fetched = client.get(f"{RECIPIENTS}/r1").json()
    assert "token" not in fetched
    assert "bearer_token_hash" not in fetched
    listed = client.get(RECIPIENTS).json()["recipients"][0]
    assert "token" not in listed


def test_recipient_token_stored_as_sha256_hash(
    client: TestClient,
    session_factory: Any,
) -> None:
    """Only the SHA-256 of the token may touch the database."""
    from soyuz_catalog.models import Recipient

    token = _make_recipient(client)["token"]
    with session_factory() as session:
        row = session.query(Recipient).one()
        assert row.bearer_token_hash == hashlib.sha256(token.encode()).hexdigest()
        assert token not in (row.bearer_token_hash or "")


def test_create_recipient_conflict(client: TestClient) -> None:
    _make_recipient(client)
    assert client.post(RECIPIENTS, json={"name": "r1"}).status_code == 409


def test_recipient_crud(client: TestClient) -> None:
    _make_recipient(client)
    r = client.patch(f"{RECIPIENTS}/r1", json={"new_name": "r2", "comment": "edited"})
    assert r.status_code == 200
    assert r.json()["name"] == "r2"
    assert client.get(f"{RECIPIENTS}/r1").status_code == 404
    assert client.delete(f"{RECIPIENTS}/r2").status_code == 200
    assert client.get(f"{RECIPIENTS}/r2").status_code == 404


def test_rotate_token_returns_fresh_plaintext(client: TestClient) -> None:
    first = _make_recipient(client)["token"]
    r = client.post(f"{RECIPIENTS}/r1/rotate-token")
    assert r.status_code == 200
    second = r.json()["token"]
    assert second and second != first


def test_rotate_token_not_found(client: TestClient) -> None:
    assert client.post(f"{RECIPIENTS}/missing/rotate-token").status_code == 404


# ---------------------------------------------------------------------------
# Grants
# ---------------------------------------------------------------------------


def test_grant_and_revoke(client: TestClient) -> None:
    _make_share(client)
    _make_recipient(client)
    assert client.put(f"{SHARES}/sh/recipients/r1").status_code == 200
    # Idempotent PUT — re-granting is success, not 409.
    assert client.put(f"{SHARES}/sh/recipients/r1").status_code == 200
    assert client.delete(f"{SHARES}/sh/recipients/r1").status_code == 200
    # Revoking a grant that is no longer there is a 404.
    assert client.delete(f"{SHARES}/sh/recipients/r1").status_code == 404


def test_grant_missing_share_or_recipient_404(client: TestClient) -> None:
    _make_share(client)
    assert client.put(f"{SHARES}/sh/recipients/missing").status_code == 404
    assert client.put(f"{SHARES}/missing/recipients/r1").status_code == 404


def test_delete_recipient_cascades_grants(client: TestClient) -> None:
    _make_share(client)
    _make_recipient(client)
    assert client.put(f"{SHARES}/sh/recipients/r1").status_code == 200
    assert client.delete(f"{RECIPIENTS}/r1").status_code == 200
    # Recreating the recipient name does not resurrect the grant: the
    # fresh recipient's token sees no shares on the protocol surface.
    token = _make_recipient(client)["token"]
    r = client.get("/delta-sharing/shares", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["items"] == []


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def test_sharing_mutations_are_audited_without_token_material(client: TestClient) -> None:
    run_id = "99999999-8888-7777-6666-555555555555"
    headers = {"X-Agent-Run-Id": run_id}
    _make_table(client)
    assert client.post(SHARES, json={"name": "sh"}, headers=headers).status_code == 200
    assert (
        client.post(
            f"{SHARES}/sh/objects",
            json={"table_full_name": "main.s.orders"},
            headers=headers,
        ).status_code
        == 200
    )
    token = client.post(RECIPIENTS, json={"name": "r1"}, headers=headers).json()["token"]
    rotated = client.post(f"{RECIPIENTS}/r1/rotate-token", headers=headers).json()["token"]
    assert client.put(f"{SHARES}/sh/recipients/r1", headers=headers).status_code == 200
    assert client.delete(f"{SHARES}/sh/recipients/r1", headers=headers).status_code == 200

    rows = client.get(AUDIT_LOG, params={"agent_run_id": run_id}).json()
    actions = [row["action"] for row in rows]
    assert actions == [
        "share.created",
        "share.object_added",
        "recipient.created",
        "recipient.token_rotated",
        "share.granted",
        "share.revoked",
    ]
    # Token material must never reach the audit trail.
    serialized = str(rows)
    assert token not in serialized
    assert rotated not in serialized
