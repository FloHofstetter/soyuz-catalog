"""Tests for the effective-permissions endpoint.

``GET /api/2.1/unity-catalog/effective-permissions/{securable_type}/{full_name}``
returns the inherited grant set for a securable — the union of every
privilege granted to each principal at any level of the ownership chain
(``leaf → schema → catalog → metastore``). This is a soyuz-specific
over-the-spec extension; upstream ``all.yaml`` defines only the
direct-grant sibling under ``/permissions``.

The test matrix exercises:

1. Inheritance flows leaf-ward: catalog grants show up on tables,
   schema grants show up on tables, metastore grants show up everywhere.
2. Inheritance does **not** leak root-ward: a table-level grant does
   not appear when querying effective permissions on its parent schema
   (the chain is walked from leaf to root, not bidirectionally).
3. Sibling isolation: a schema grant shows on tables under that schema
   but not under a different schema in the same catalog.
4. Per-principal union: multiple grants for the same principal at
   different levels merge into a single sorted privilege list.
5. ``?principal=`` filter trims the response to one assignment.
6. 404 on unresolved leaves, 422 on unknown types, 200 empty on
   chains with no grants anywhere.
7. One test per securable type that has a non-trivial chain
   (volume / function / registered_model) to lock in that
   ``_ancestor_chain`` exercises every branch.

Builder helpers are imported verbatim from
:mod:`tests.test_permissions` to stay in lock-step with the direct-
permissions contract — if the builders evolve, both test files move
together.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from tests.test_permissions import (
    _ALICE,
    _BOB,
    _make_catalog,
    _make_function,
    _make_model,
    _make_schema,
    _make_table,
    _make_volume,
    _patch,
)

API = "/api/2.1/unity-catalog"
EFFECTIVE = f"{API}/effective-permissions"
METASTORE_SUMMARY = f"{API}/metastore_summary"

_CAROL = "carol@example.com"


def _effective(
    client: TestClient,
    securable_type: str,
    full_name: str,
    principal: str | None = None,
) -> dict[str, Any]:
    """Call the effective-permissions endpoint and return the parsed body.

    Asserts 200 so a test that only cares about content does not have
    to duplicate the success check. Tests that expect a non-200 use
    ``client.get(...)`` directly.
    """
    url = f"{EFFECTIVE}/{securable_type}/{full_name}"
    if principal is not None:
        url = f"{url}?principal={principal}"
    r = client.get(url)
    assert r.status_code == 200, r.text
    return r.json()


def _assignment_for(body: dict[str, Any], principal: str) -> dict[str, Any] | None:
    """Pick one principal's assignment out of a PermissionsList body.

    Returns ``None`` when the principal has no grants at all in the
    response — keeps the "is this privilege present" assertions
    readable.
    """
    for a in body["privilege_assignments"]:
        if a["principal"] == principal:
            return a
    return None


def _metastore_id(client: TestClient) -> str:
    """Return the live metastore id the conformance routes need.

    The permissions service treats ``metastore`` as a singleton keyed
    on the current metastore id; granting at the metastore level
    requires knowing that exact id.
    """
    r = client.get(METASTORE_SUMMARY)
    assert r.status_code == 200, r.text
    return r.json()["metastore_id"]


def test_catalog_grant_inherits_to_table(client: TestClient) -> None:
    _make_table(client, catalog="cat1", schema="sch1", name="tbl1")
    _patch(
        client,
        "catalog",
        "cat1",
        [{"principal": _ALICE, "add": ["USE CATALOG"], "remove": []}],
    )

    body = _effective(client, "table", "cat1.sch1.tbl1")
    alice = _assignment_for(body, _ALICE)
    assert alice is not None
    assert "USE CATALOG" in alice["privileges"]


def test_schema_grant_flows_to_table_under_schema(client: TestClient) -> None:
    _make_table(client, catalog="cat1", schema="sch1", name="tbl1")
    _patch(
        client,
        "schema",
        "cat1.sch1",
        [{"principal": _BOB, "add": ["USE SCHEMA"], "remove": []}],
    )

    body = _effective(client, "table", "cat1.sch1.tbl1")
    bob = _assignment_for(body, _BOB)
    assert bob is not None
    assert bob["privileges"] == ["USE SCHEMA"]


def test_schema_grant_does_not_flow_to_sibling_schema(client: TestClient) -> None:
    # First table under sch1 (creates cat1 + sch1 transitively).
    _make_table(client, catalog="cat1", schema="sch1", name="tbl1")
    # Second schema and table under the same catalog without re-creating cat1
    # (the builder helper is not idempotent on the catalog create).
    r = client.post(f"{API}/schemas", json={"name": "sch2", "catalog_name": "cat1"})
    assert r.status_code == 200, r.text
    r = client.post(
        f"{API}/tables",
        json={
            "name": "tbl2",
            "catalog_name": "cat1",
            "schema_name": "sch2",
            "table_type": "MANAGED",
            "data_source_format": "DELTA",
            "storage_location": "s3://bucket/tbl2",
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
    _patch(
        client,
        "schema",
        "cat1.sch1",
        [{"principal": _BOB, "add": ["USE SCHEMA"], "remove": []}],
    )

    body = _effective(client, "table", "cat1.sch2.tbl2")
    assert _assignment_for(body, _BOB) is None


def test_table_grant_does_not_leak_upward_to_schema(client: TestClient) -> None:
    _make_table(client, catalog="cat1", schema="sch1", name="tbl1")
    _patch(
        client,
        "table",
        "cat1.sch1.tbl1",
        [{"principal": _CAROL, "add": ["SELECT"], "remove": []}],
    )

    body = _effective(client, "schema", "cat1.sch1")
    assert _assignment_for(body, _CAROL) is None


def test_union_across_three_levels_for_single_principal(client: TestClient) -> None:
    _make_table(client, catalog="cat1", schema="sch1", name="tbl1")
    _patch(
        client,
        "catalog",
        "cat1",
        [{"principal": _ALICE, "add": ["USE CATALOG"], "remove": []}],
    )
    _patch(
        client,
        "schema",
        "cat1.sch1",
        [{"principal": _ALICE, "add": ["USE SCHEMA"], "remove": []}],
    )
    _patch(
        client,
        "table",
        "cat1.sch1.tbl1",
        [{"principal": _ALICE, "add": ["SELECT"], "remove": []}],
    )

    body = _effective(client, "table", "cat1.sch1.tbl1")
    alice = _assignment_for(body, _ALICE)
    assert alice is not None
    assert alice["privileges"] == ["SELECT", "USE CATALOG", "USE SCHEMA"]


def test_principal_filter_narrows_response(client: TestClient) -> None:
    _make_table(client, catalog="cat1", schema="sch1", name="tbl1")
    _patch(
        client,
        "catalog",
        "cat1",
        [{"principal": _ALICE, "add": ["USE CATALOG"], "remove": []}],
    )
    _patch(
        client,
        "schema",
        "cat1.sch1",
        [{"principal": _BOB, "add": ["USE SCHEMA"], "remove": []}],
    )
    _patch(
        client,
        "table",
        "cat1.sch1.tbl1",
        [{"principal": _CAROL, "add": ["SELECT"], "remove": []}],
    )

    filtered = _effective(client, "table", "cat1.sch1.tbl1", principal=_BOB)
    principals = [a["principal"] for a in filtered["privilege_assignments"]]
    assert principals == [_BOB]
    assert filtered["privilege_assignments"][0]["privileges"] == ["USE SCHEMA"]


def test_metastore_grant_inherits_to_everything(client: TestClient) -> None:
    _make_table(client, catalog="cat1", schema="sch1", name="tbl1")
    mid = _metastore_id(client)
    _patch(
        client,
        "metastore",
        mid,
        [{"principal": _ALICE, "add": ["CREATE CATALOG"], "remove": []}],
    )

    body = _effective(client, "table", "cat1.sch1.tbl1")
    alice = _assignment_for(body, _ALICE)
    assert alice is not None
    assert "CREATE CATALOG" in alice["privileges"]


def test_empty_chain_returns_empty_list(client: TestClient) -> None:
    _make_table(client, catalog="cat1", schema="sch1", name="tbl1")

    body = _effective(client, "table", "cat1.sch1.tbl1")
    assert body == {"privilege_assignments": []}


def test_404_on_unknown_table(client: TestClient) -> None:
    _make_schema(client, catalog="cat1", name="sch1")
    r = client.get(f"{EFFECTIVE}/table/cat1.sch1.does_not_exist")
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


def test_422_on_unknown_securable_type(client: TestClient) -> None:
    r = client.get(f"{EFFECTIVE}/not_a_type/some.name")
    assert r.status_code == 422


def test_400_on_wrong_segment_count(client: TestClient) -> None:
    _make_catalog(client)
    r = client.get(f"{EFFECTIVE}/schema/cat1")  # schema expects 2 segments
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_volume_inherits_schema_and_catalog_grants(client: TestClient) -> None:
    _make_volume(client, catalog="cat1", schema="sch1", name="vol1")
    _patch(
        client,
        "catalog",
        "cat1",
        [{"principal": _ALICE, "add": ["USE CATALOG"], "remove": []}],
    )
    _patch(
        client,
        "schema",
        "cat1.sch1",
        [{"principal": _ALICE, "add": ["USE SCHEMA"], "remove": []}],
    )
    _patch(
        client,
        "volume",
        "cat1.sch1.vol1",
        [{"principal": _ALICE, "add": ["READ VOLUME"], "remove": []}],
    )

    body = _effective(client, "volume", "cat1.sch1.vol1")
    alice = _assignment_for(body, _ALICE)
    assert alice is not None
    assert alice["privileges"] == ["READ VOLUME", "USE CATALOG", "USE SCHEMA"]


def test_function_inherits_catalog_grant(client: TestClient) -> None:
    _make_function(client, catalog="cat1", schema="sch1", name="fn1")
    _patch(
        client,
        "catalog",
        "cat1",
        [{"principal": _ALICE, "add": ["USE CATALOG"], "remove": []}],
    )

    body = _effective(client, "function", "cat1.sch1.fn1")
    alice = _assignment_for(body, _ALICE)
    assert alice is not None
    assert "USE CATALOG" in alice["privileges"]


def test_registered_model_inherits_schema_grant(client: TestClient) -> None:
    _make_model(client, catalog="cat1", schema="sch1", name="m1")
    _patch(
        client,
        "schema",
        "cat1.sch1",
        [{"principal": _ALICE, "add": ["USE SCHEMA"], "remove": []}],
    )

    body = _effective(client, "registered_model", "cat1.sch1.m1")
    alice = _assignment_for(body, _ALICE)
    assert alice is not None
    assert alice["privileges"] == ["USE SCHEMA"]


def test_direct_grant_on_leaf_also_returned(client: TestClient) -> None:
    """Leaf-level grants flow through the same union as ancestor grants."""
    _make_table(client, catalog="cat1", schema="sch1", name="tbl1")
    _patch(
        client,
        "table",
        "cat1.sch1.tbl1",
        [{"principal": _ALICE, "add": ["SELECT", "MODIFY"], "remove": []}],
    )

    body = _effective(client, "table", "cat1.sch1.tbl1")
    alice = _assignment_for(body, _ALICE)
    assert alice is not None
    assert alice["privileges"] == ["MODIFY", "SELECT"]
