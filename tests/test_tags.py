"""Tests for the tags endpoints (ADR-0010).

Covers the additive ``set``/``remove`` PATCH shape, GET/PATCH round-trip
on every MVP securable type (catalog / schema / table / column),
rename-invariance of opaque securable ids, the ``set wins`` tiebreaker
when the same key is removed and set in one batch, and the append-only
delete posture where dropping the parent resource leaves orphan rows.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

API = "/api/2.1/unity-catalog"
CATALOGS = f"{API}/catalogs"
SCHEMAS = f"{API}/schemas"
TABLES = f"{API}/tables"

TAGS = "/tags"


def _make_catalog(client: TestClient, name: str = "cat1") -> None:
    r = client.post(CATALOGS, json={"name": name})
    assert r.status_code == 200, r.text


def _make_schema(client: TestClient, catalog: str = "cat1", name: str = "sch1") -> None:
    r = client.post(SCHEMAS, json={"name": name, "catalog_name": catalog})
    assert r.status_code == 200, r.text


def _make_table(
    client: TestClient,
    name: str = "tbl1",
    catalog: str = "cat1",
    schema: str = "sch1",
) -> dict[str, Any]:
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
                {
                    "name": "email",
                    "type_text": "string",
                    "type_json": "{}",
                    "type_name": "STRING",
                    "position": 1,
                },
            ],
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def _seed(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _make_table(client)


def _set(key: str, value: str | None = None) -> dict[str, Any]:
    return {"op": "set", "key": key, "value": value}


def _remove(key: str) -> dict[str, Any]:
    return {"op": "remove", "key": key}


# ---------------------------------------------------------------------------
# GET empty
# ---------------------------------------------------------------------------


def test_get_tags_empty(client: TestClient) -> None:
    _seed(client)
    r = client.get(f"{TAGS}/table/cat1.sch1.tbl1")
    assert r.status_code == 200, r.text
    assert r.json() == {"tags": []}


def test_get_tags_unknown_securable_404(client: TestClient) -> None:
    _make_catalog(client)
    r = client.get(f"{TAGS}/schema/cat1.nope")
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# PATCH: set / remove / upsert on every MVP type
# ---------------------------------------------------------------------------


def test_patch_tags_catalog(client: TestClient) -> None:
    _make_catalog(client)
    r = client.patch(
        f"{TAGS}/catalog/cat1",
        json={"changes": [_set("owner", "alice"), _set("pii", "true")]},
    )
    assert r.status_code == 200, r.text
    tags = r.json()["tags"]
    assert [(t["key"], t["value"]) for t in tags] == [
        ("owner", "alice"),
        ("pii", "true"),
    ]
    # GET mirrors PATCH response
    r2 = client.get(f"{TAGS}/catalog/cat1")
    assert r2.json() == r.json()


def test_patch_tags_schema(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.patch(
        f"{TAGS}/schema/cat1.sch1",
        json={"changes": [_set("domain", "sales")]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["tags"] == [
        {
            "key": "domain",
            "value": "sales",
            "created_at": r.json()["tags"][0]["created_at"],
            "updated_at": r.json()["tags"][0]["updated_at"],
        },
    ]


def test_patch_tags_table_and_column(client: TestClient) -> None:
    _seed(client)
    r = client.patch(
        f"{TAGS}/table/cat1.sch1.tbl1",
        json={"changes": [_set("layer", "bronze")]},
    )
    assert r.status_code == 200, r.text

    r2 = client.patch(
        f"{TAGS}/column/cat1.sch1.tbl1.email",
        json={"changes": [_set("pii"), _set("mask", "sha256")]},
    )
    assert r2.status_code == 200, r2.text
    col_tags = r2.json()["tags"]
    assert [t["key"] for t in col_tags] == ["mask", "pii"]  # sorted by key
    assert [t["value"] for t in col_tags] == ["sha256", None]

    # Tags on different securables are independent.
    assert client.get(f"{TAGS}/table/cat1.sch1.tbl1").json()["tags"][0]["key"] == "layer"
    assert {t["key"] for t in client.get(f"{TAGS}/column/cat1.sch1.tbl1.email").json()["tags"]} == {
        "mask",
        "pii",
    }


def test_patch_upsert_updates_value(client: TestClient) -> None:
    _make_catalog(client)
    r1 = client.patch(
        f"{TAGS}/catalog/cat1",
        json={"changes": [_set("owner", "alice")]},
    )
    assert r1.status_code == 200
    r2 = client.patch(
        f"{TAGS}/catalog/cat1",
        json={"changes": [_set("owner", "bob")]},
    )
    assert r2.status_code == 200
    tags = r2.json()["tags"]
    assert len(tags) == 1
    assert tags[0] == {
        "key": "owner",
        "value": "bob",
        "created_at": tags[0]["created_at"],
        "updated_at": tags[0]["updated_at"],
    }
    # Still exactly one row for the key.
    assert len(client.get(f"{TAGS}/catalog/cat1").json()["tags"]) == 1


def test_patch_remove_nonexistent_is_noop(client: TestClient) -> None:
    _make_catalog(client)
    r = client.patch(
        f"{TAGS}/catalog/cat1",
        json={"changes": [_remove("ghost")]},
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"tags": []}


def test_patch_set_and_remove_mix(client: TestClient) -> None:
    _make_catalog(client)
    client.patch(
        f"{TAGS}/catalog/cat1",
        json={"changes": [_set("a", "1"), _set("b", "2"), _set("c", "3")]},
    )
    r = client.patch(
        f"{TAGS}/catalog/cat1",
        json={"changes": [_remove("b"), _set("d", "4")]},
    )
    assert r.status_code == 200
    assert [t["key"] for t in r.json()["tags"]] == ["a", "c", "d"]


def test_patch_set_wins_over_remove_in_same_batch(client: TestClient) -> None:
    _make_catalog(client)
    client.patch(
        f"{TAGS}/catalog/cat1",
        json={"changes": [_set("owner", "alice")]},
    )
    r = client.patch(
        f"{TAGS}/catalog/cat1",
        json={"changes": [_remove("owner"), _set("owner", "bob")]},
    )
    assert r.status_code == 200
    tags = r.json()["tags"]
    assert len(tags) == 1
    assert tags[0]["key"] == "owner"
    assert tags[0]["value"] == "bob"


def test_patch_empty_changes_is_noop(client: TestClient) -> None:
    _make_catalog(client)
    client.patch(
        f"{TAGS}/catalog/cat1",
        json={"changes": [_set("owner", "alice")]},
    )
    r = client.patch(f"{TAGS}/catalog/cat1", json={"changes": []})
    assert r.status_code == 200
    assert len(r.json()["tags"]) == 1


# ---------------------------------------------------------------------------
# Validation: forbid extra fields, wrong segment count, unknown type
# ---------------------------------------------------------------------------


def test_patch_rejects_unknown_fields(client: TestClient) -> None:
    _make_catalog(client)
    r = client.patch(
        f"{TAGS}/catalog/cat1",
        json={"changes": [{"op": "set", "key": "x", "value": "y", "extra": True}]},
    )
    assert r.status_code == 422, r.text


def test_patch_rejects_unknown_op(client: TestClient) -> None:
    _make_catalog(client)
    r = client.patch(
        f"{TAGS}/catalog/cat1",
        json={"changes": [{"op": "replace", "key": "x"}]},
    )
    assert r.status_code == 422, r.text


def test_unknown_securable_type_422(client: TestClient) -> None:
    _make_catalog(client)
    r = client.get(f"{TAGS}/volume/cat1.sch1.v1")
    # Tags MVP excludes volume — FastAPI literal validation returns 422.
    assert r.status_code == 422, r.text


def test_column_four_part_wrong_count_400(client: TestClient) -> None:
    _seed(client)
    r = client.patch(
        f"{TAGS}/column/cat1.sch1.tbl1",
        json={"changes": [_set("pii")]},
    )
    assert r.status_code == 400, r.text


def test_column_unknown_404(client: TestClient) -> None:
    _seed(client)
    r = client.get(f"{TAGS}/column/cat1.sch1.tbl1.nope")
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# Rename invariance and append-only delete posture
# ---------------------------------------------------------------------------


def test_rename_catalog_preserves_tags(client: TestClient) -> None:
    _seed(client)
    client.patch(
        f"{TAGS}/table/cat1.sch1.tbl1",
        json={"changes": [_set("layer", "bronze")]},
    )
    # Rename the parent catalog.
    r = client.patch(f"{CATALOGS}/cat1", json={"new_name": "cat_renamed"})
    assert r.status_code == 200, r.text
    # Tag is still attached under the new full_name.
    r2 = client.get(f"{TAGS}/table/cat_renamed.sch1.tbl1")
    assert r2.status_code == 200, r2.text
    assert [t["key"] for t in r2.json()["tags"]] == ["layer"]


def test_delete_table_leaves_orphan_tag(client: TestClient) -> None:
    _seed(client)
    client.patch(
        f"{TAGS}/table/cat1.sch1.tbl1",
        json={"changes": [_set("layer", "bronze")]},
    )
    # Drop the table. Lookup by full_name now 404s — orphan rows are
    # unreachable rather than cascade-deleted (append-only posture).
    r = client.delete(f"{TABLES}/cat1.sch1.tbl1")
    assert r.status_code in (200, 204), r.text
    r2 = client.get(f"{TAGS}/table/cat1.sch1.tbl1")
    assert r2.status_code == 404, r2.text
