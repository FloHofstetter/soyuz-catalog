"""Unit tests for the Permissions CRUD endpoints (ADR-0005).

Covers address resolution for every securable type, the per-type
privilege allow-set, add/remove idempotency, GET filtering, the
rename-invariance property of the opaque ``securable_id`` column,
and the cascade-on-parent-delete cleanup path.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

API = "/api/2.1/unity-catalog"
PERMS = f"{API}/permissions"
CATALOGS = f"{API}/catalogs"
SCHEMAS = f"{API}/schemas"
TABLES = f"{API}/tables"
VOLUMES = f"{API}/volumes"
CREDENTIALS = f"{API}/credentials"
EXTERNAL_LOCATIONS = f"{API}/external-locations"
FUNCTIONS = f"{API}/functions"
MODELS = f"{API}/models"
METASTORE_SUMMARY = f"{API}/metastore_summary"

_ALICE = "alice@example.com"
_BOB = "bob@example.com"


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------


def _make_catalog(client: TestClient, name: str = "cat1") -> dict[str, Any]:
    r = client.post(CATALOGS, json={"name": name})
    assert r.status_code == 200, r.text
    return r.json()


def _make_schema(client: TestClient, catalog: str = "cat1", name: str = "sch1") -> dict[str, Any]:
    _make_catalog(client, catalog)
    r = client.post(SCHEMAS, json={"name": name, "catalog_name": catalog})
    assert r.status_code == 200, r.text
    return r.json()


def _make_table(
    client: TestClient,
    catalog: str = "cat1",
    schema: str = "sch1",
    name: str = "tbl1",
) -> dict[str, Any]:
    _make_schema(client, catalog, schema)
    r = client.post(
        TABLES,
        json={
            "name": name,
            "catalog_name": catalog,
            "schema_name": schema,
            "table_type": "MANAGED",
            "data_source_format": "DELTA",
            "storage_location": f"s3://bucket/{name}",
            "columns": [
                {
                    "name": "id",
                    "type_text": "long",
                    "type_json": "{}",
                    "type_name": "LONG",
                    "position": 0,
                },
            ],
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def _make_volume(
    client: TestClient,
    catalog: str = "cat1",
    schema: str = "sch1",
    name: str = "vol1",
) -> dict[str, Any]:
    _make_schema(client, catalog, schema)
    r = client.post(
        VOLUMES,
        json={
            "name": name,
            "catalog_name": catalog,
            "schema_name": schema,
            "volume_type": "MANAGED",
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def _make_function(
    client: TestClient,
    catalog: str = "cat1",
    schema: str = "sch1",
    name: str = "fn1",
) -> dict[str, Any]:
    _make_schema(client, catalog, schema)
    r = client.post(
        FUNCTIONS,
        json={
            "function_info": {
                "name": name,
                "catalog_name": catalog,
                "schema_name": schema,
                "input_params": {"parameters": []},
                "return_params": {"parameters": []},
                "data_type": "INT",
                "full_data_type": "INT",
                "routine_body": "SQL",
                "routine_definition": "SELECT 1",
                "parameter_style": "S",
                "is_deterministic": True,
                "sql_data_access": "CONTAINS_SQL",
                "is_null_call": False,
                "security_type": "DEFINER",
                "specific_name": name,
            },
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def _make_model(
    client: TestClient,
    catalog: str = "cat1",
    schema: str = "sch1",
    name: str = "m1",
) -> dict[str, Any]:
    _make_schema(client, catalog, schema)
    r = client.post(
        MODELS,
        json={"name": name, "catalog_name": catalog, "schema_name": schema},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _make_credential(client: TestClient, name: str = "cred1") -> dict[str, Any]:
    r = client.post(
        CREDENTIALS,
        json={
            "name": name,
            "aws_iam_role": {"role_arn": "arn:aws:iam::123456789012:role/x"},
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def _make_external_location(
    client: TestClient,
    name: str = "loc1",
    cred_name: str = "cred1",
) -> dict[str, Any]:
    _make_credential(client, cred_name)
    r = client.post(
        EXTERNAL_LOCATIONS,
        json={
            "name": name,
            "url": f"s3://bucket/{name}",
            "credential_name": cred_name,
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def _patch(
    client: TestClient,
    securable_type: str,
    full_name: str,
    changes: list[dict[str, Any]],
) -> dict[str, Any]:
    r = client.patch(
        f"{PERMS}/{securable_type}/{full_name}",
        json={"changes": changes},
    )
    assert r.status_code == 200, r.text
    return r.json()


def _get(
    client: TestClient,
    securable_type: str,
    full_name: str,
    principal: str | None = None,
) -> dict[str, Any]:
    url = f"{PERMS}/{securable_type}/{full_name}"
    if principal is not None:
        url = f"{url}?principal={principal}"
    r = client.get(url)
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Empty-state and basic add/remove
# ---------------------------------------------------------------------------


def test_get_empty_state(client: TestClient) -> None:
    _make_catalog(client)
    assert _get(client, "catalog", "cat1") == {"privilege_assignments": []}


def test_patch_add_then_get(client: TestClient) -> None:
    _make_catalog(client)
    body = _patch(
        client,
        "catalog",
        "cat1",
        [{"principal": _ALICE, "add": ["USE CATALOG"], "remove": []}],
    )
    assert body["privilege_assignments"] == [
        {"principal": _ALICE, "privileges": ["USE CATALOG"]},
    ]
    assert _get(client, "catalog", "cat1") == body


def test_patch_add_then_remove(client: TestClient) -> None:
    _make_catalog(client)
    _patch(
        client,
        "catalog",
        "cat1",
        [{"principal": _ALICE, "add": ["USE CATALOG"], "remove": []}],
    )
    after = _patch(
        client,
        "catalog",
        "cat1",
        [{"principal": _ALICE, "add": [], "remove": ["USE CATALOG"]}],
    )
    assert after == {"privilege_assignments": []}


def test_patch_idempotent_add(client: TestClient) -> None:
    _make_catalog(client)
    body = {"principal": _ALICE, "add": ["USE CATALOG"], "remove": []}
    _patch(client, "catalog", "cat1", [body])
    _patch(client, "catalog", "cat1", [body])
    state = _get(client, "catalog", "cat1")
    assert state["privilege_assignments"][0]["privileges"] == ["USE CATALOG"]


def test_patch_remove_nonexistent_is_noop(client: TestClient) -> None:
    _make_catalog(client)
    body = _patch(
        client,
        "catalog",
        "cat1",
        [{"principal": _ALICE, "add": [], "remove": ["USE CATALOG"]}],
    )
    assert body == {"privilege_assignments": []}


def test_patch_empty_changes_is_noop(client: TestClient) -> None:
    _make_catalog(client)
    _patch(
        client,
        "catalog",
        "cat1",
        [{"principal": _ALICE, "add": ["USE CATALOG"], "remove": []}],
    )
    body = _patch(client, "catalog", "cat1", [])
    assert body["privilege_assignments"][0]["principal"] == _ALICE


def test_patch_add_wins_on_overlap(client: TestClient) -> None:
    _make_catalog(client)
    body = _patch(
        client,
        "catalog",
        "cat1",
        [
            {
                "principal": _ALICE,
                "add": ["USE CATALOG"],
                "remove": ["USE CATALOG"],
            },
        ],
    )
    assert body["privilege_assignments"] == [
        {"principal": _ALICE, "privileges": ["USE CATALOG"]},
    ]


def test_get_principal_filter(client: TestClient) -> None:
    _make_catalog(client)
    _patch(
        client,
        "catalog",
        "cat1",
        [
            {"principal": _ALICE, "add": ["USE CATALOG"], "remove": []},
            {"principal": _BOB, "add": ["CREATE SCHEMA"], "remove": []},
        ],
    )
    only_alice = _get(client, "catalog", "cat1", principal=_ALICE)
    assert only_alice == {
        "privilege_assignments": [
            {"principal": _ALICE, "privileges": ["USE CATALOG"]},
        ],
    }


def test_response_sorted_by_principal(client: TestClient) -> None:
    _make_catalog(client)
    _patch(
        client,
        "catalog",
        "cat1",
        [
            {"principal": _BOB, "add": ["USE CATALOG"], "remove": []},
            {"principal": _ALICE, "add": ["USE CATALOG"], "remove": []},
        ],
    )
    body = _get(client, "catalog", "cat1")
    principals = [a["principal"] for a in body["privilege_assignments"]]
    assert principals == sorted(principals)


# ---------------------------------------------------------------------------
# Per-type resolution
# ---------------------------------------------------------------------------


def test_schema_two_part_resolution(client: TestClient) -> None:
    _make_schema(client)
    body = _patch(
        client,
        "schema",
        "cat1.sch1",
        [{"principal": _ALICE, "add": ["USE SCHEMA"], "remove": []}],
    )
    assert body["privilege_assignments"][0]["privileges"] == ["USE SCHEMA"]


def test_table_three_part_resolution(client: TestClient) -> None:
    _make_table(client)
    body = _patch(
        client,
        "table",
        "cat1.sch1.tbl1",
        [{"principal": _ALICE, "add": ["SELECT"], "remove": []}],
    )
    assert body["privilege_assignments"][0]["privileges"] == ["SELECT"]


def test_volume_three_part_resolution(client: TestClient) -> None:
    _make_volume(client)
    _patch(
        client,
        "volume",
        "cat1.sch1.vol1",
        [{"principal": _ALICE, "add": ["READ VOLUME"], "remove": []}],
    )


def test_function_three_part_resolution(client: TestClient) -> None:
    _make_function(client)
    _patch(
        client,
        "function",
        "cat1.sch1.fn1",
        [{"principal": _ALICE, "add": ["EXECUTE"], "remove": []}],
    )


def test_registered_model_three_part_resolution(client: TestClient) -> None:
    _make_model(client)
    _patch(
        client,
        "registered_model",
        "cat1.sch1.m1",
        [{"principal": _ALICE, "add": ["EXECUTE"], "remove": []}],
    )


def test_credential_one_part_resolution(client: TestClient) -> None:
    _make_credential(client)
    _patch(
        client,
        "credential",
        "cred1",
        [{"principal": _ALICE, "add": ["CREATE EXTERNAL LOCATION"], "remove": []}],
    )


def test_external_location_one_part_resolution(client: TestClient) -> None:
    _make_external_location(client)
    _patch(
        client,
        "external_location",
        "loc1",
        [{"principal": _ALICE, "add": ["READ FILES"], "remove": []}],
    )


def test_metastore_full_name_is_metastore_id(client: TestClient) -> None:
    r = client.get(METASTORE_SUMMARY)
    assert r.status_code == 200
    mid = r.json()["metastore_id"]
    _patch(
        client,
        "metastore",
        mid,
        [{"principal": _ALICE, "add": ["CREATE CATALOG"], "remove": []}],
    )
    state = _get(client, "metastore", mid)
    assert state["privilege_assignments"][0]["privileges"] == ["CREATE CATALOG"]


def test_metastore_wrong_id_404(client: TestClient) -> None:
    r = client.get(f"{PERMS}/metastore/not-the-real-id")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_unknown_securable_type_422(client: TestClient) -> None:
    r = client.get(f"{PERMS}/galaxy/foo")
    assert r.status_code == 422


def test_unknown_full_name_404(client: TestClient) -> None:
    r = client.get(f"{PERMS}/catalog/missing")
    assert r.status_code == 404


def test_wrong_segment_count_400(client: TestClient) -> None:
    r = client.get(f"{PERMS}/schema/just-one")
    assert r.status_code == 400


def test_typo_in_privilege_422(client: TestClient) -> None:
    _make_catalog(client)
    r = client.patch(
        f"{PERMS}/catalog/cat1",
        json={
            "changes": [
                {"principal": _ALICE, "add": ["USE-CATALOG"], "remove": []},
            ],
        },
    )
    assert r.status_code == 422


def test_disallowed_privilege_for_type_400(client: TestClient) -> None:
    _make_catalog(client)
    r = client.patch(
        f"{PERMS}/catalog/cat1",
        json={
            "changes": [
                {"principal": _ALICE, "add": ["SELECT"], "remove": []},
            ],
        },
    )
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"
    # The batch must be rejected atomically — no row should have been written.
    assert _get(client, "catalog", "cat1") == {"privilege_assignments": []}


def test_update_body_forbids_unknown_field(client: TestClient) -> None:
    _make_catalog(client)
    r = client.patch(
        f"{PERMS}/catalog/cat1",
        json={
            "changes": [
                {
                    "principal": _ALICE,
                    "add": ["USE CATALOG"],
                    "remove": [],
                    "made_up": 1,
                },
            ],
        },
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Rename-invariance and cascade
# ---------------------------------------------------------------------------


def test_rename_parent_catalog_preserves_table_grants(client: TestClient) -> None:
    _make_table(client)
    _patch(
        client,
        "table",
        "cat1.sch1.tbl1",
        [{"principal": _ALICE, "add": ["SELECT"], "remove": []}],
    )
    r = client.patch(f"{CATALOGS}/cat1", json={"new_name": "cat1_renamed"})
    assert r.status_code == 200
    body = _get(client, "table", "cat1_renamed.sch1.tbl1")
    assert body["privilege_assignments"][0]["privileges"] == ["SELECT"]


def test_delete_catalog_cascades_permissions(client: TestClient) -> None:
    from sqlalchemy import select

    from soyuz_catalog.models import Permission

    _make_table(client)
    _patch(
        client,
        "table",
        "cat1.sch1.tbl1",
        [{"principal": _ALICE, "add": ["SELECT"], "remove": []}],
    )
    _patch(
        client,
        "catalog",
        "cat1",
        [{"principal": _ALICE, "add": ["USE CATALOG"], "remove": []}],
    )
    r = client.delete(f"{CATALOGS}/cat1?force=true")
    assert r.status_code == 200

    # Peek directly at the DB via the override: no rows should remain.
    factory = client.app.dependency_overrides[  # type: ignore[attr-defined]
        __import__("soyuz_catalog.api.deps", fromlist=["get_db"]).get_db
    ]
    gen = factory()
    db = next(gen)
    try:
        remaining = list(db.scalars(select(Permission)))
    finally:
        gen.close()
    assert remaining == []


def test_delete_credential_force_cascades_location_grants(client: TestClient) -> None:
    from sqlalchemy import select

    from soyuz_catalog.models import Permission

    _make_external_location(client)
    _patch(
        client,
        "external_location",
        "loc1",
        [{"principal": _ALICE, "add": ["READ FILES"], "remove": []}],
    )
    _patch(
        client,
        "credential",
        "cred1",
        [{"principal": _ALICE, "add": ["CREATE EXTERNAL LOCATION"], "remove": []}],
    )
    r = client.delete(f"{CREDENTIALS}/cred1?force=true")
    assert r.status_code == 200

    factory = client.app.dependency_overrides[  # type: ignore[attr-defined]
        __import__("soyuz_catalog.api.deps", fromlist=["get_db"]).get_db
    ]
    gen = factory()
    db = next(gen)
    try:
        remaining = list(db.scalars(select(Permission)))
    finally:
        gen.close()
    assert remaining == []
