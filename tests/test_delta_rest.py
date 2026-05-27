"""Tests for the Delta REST Catalog API (ADR-0009).

Covers the 13 endpoints implemented under
``/api/2.1/unity-catalog/delta``: the CRUD happy paths, the
discriminated-union ``TableUpdate`` variants (implemented,
no-op, and 501 categories), the ``requirements`` pre-conditions,
the 204-returning routes, and the empty credential / metrics
stubs.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

API = "/api/2.1/unity-catalog"
DELTA = f"{API}/delta/v1"
CATALOGS = f"{API}/catalogs"
SCHEMAS = f"{API}/schemas"


def _make_parents(client: TestClient, catalog: str = "cat1", schema: str = "sch1") -> None:
    r = client.post(CATALOGS, json={"name": catalog})
    assert r.status_code == 200, r.text
    r = client.post(SCHEMAS, json={"name": schema, "catalog_name": catalog})
    assert r.status_code == 200, r.text


def _minimal_create_body(
    name: str = "orders",
    data_source_format: str = "DELTA",
    *,
    partition_columns: list[str] | None = None,
    columns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if columns is None:
        columns = [
            {"name": "id", "type": "long", "nullable": False, "metadata": {}},
            {
                "name": "amount",
                "type": {"type": "decimal", "precision": 10, "scale": 2},
                "nullable": True,
                "metadata": {"comment": "dollars"},
            },
        ]
    return {
        "name": name,
        "location": f"s3://bucket/{name}",
        "table-type": "MANAGED",
        "data-source-format": data_source_format,
        "columns": columns,
        "partition-columns": partition_columns or [],
        "protocol": {"min-reader-version": 1, "min-writer-version": 2},
        "properties": {"delta.enableDeletionVectors": "true"},
    }


def _create_delta_table(client: TestClient, name: str = "orders") -> dict[str, Any]:
    r = client.post(
        f"{DELTA}/catalogs/cat1/schemas/sch1/tables",
        json=_minimal_create_body(name),
    )
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def test_config_returns_endpoint_list(client: TestClient) -> None:
    r = client.get(
        f"{DELTA}/config",
        params={"catalog": "main", "protocol-versions": "1.0"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["protocol-version"] == "1.0"
    assert any("/v1/config" not in e and "/tables" in e for e in body["endpoints"])
    assert len(body["endpoints"]) == 12


def test_config_requires_catalog_query_param(client: TestClient) -> None:
    r = client.get(f"{DELTA}/config", params={"protocol-versions": "1.0"})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Create / load
# ---------------------------------------------------------------------------


def test_create_table_happy_path(client: TestClient) -> None:
    _make_parents(client)
    body = _create_delta_table(client)
    metadata = body["metadata"]
    assert metadata["table-uuid"]  # non-empty opaque id
    assert metadata["data-source-format"] == "DELTA"
    assert metadata["table-type"] == "MANAGED"
    assert metadata["securable-type"] == "TABLE"
    assert metadata["location"] == "s3://bucket/orders"
    assert metadata["etag"] == str(metadata["updated-time"])
    assert metadata["protocol"]["min-reader-version"] == 1
    assert metadata["protocol"]["min-writer-version"] == 2
    assert [c["name"] for c in metadata["columns"]] == ["id", "amount"]
    # Complex type round-trip
    assert metadata["columns"][1]["type"] == {
        "type": "decimal",
        "precision": 10,
        "scale": 2,
    }
    assert metadata["columns"][1]["metadata"] == {"comment": "dollars"}
    assert body["commits"] == []


def test_create_table_duplicate_returns_409(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = client.post(
        f"{DELTA}/catalogs/cat1/schemas/sch1/tables",
        json=_minimal_create_body("orders"),
    )
    assert r.status_code == 409, r.text


def test_create_table_unknown_schema_returns_404(client: TestClient) -> None:
    _make_parents(client)
    r = client.post(
        f"{DELTA}/catalogs/cat1/schemas/missing/tables",
        json=_minimal_create_body("orders"),
    )
    assert r.status_code == 404, r.text


def test_load_table_returns_delta_metadata(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = client.get(f"{DELTA}/catalogs/cat1/schemas/sch1/tables/orders")
    assert r.status_code == 200, r.text
    metadata = r.json()["metadata"]
    assert metadata["table-type"] == "MANAGED"
    assert len(metadata["columns"]) == 2


def test_load_table_unknown_returns_404(client: TestClient) -> None:
    _make_parents(client)
    r = client.get(f"{DELTA}/catalogs/cat1/schemas/sch1/tables/missing")
    assert r.status_code == 404


def test_partition_columns_round_trip(client: TestClient) -> None:
    _make_parents(client)
    r = client.post(
        f"{DELTA}/catalogs/cat1/schemas/sch1/tables",
        json=_minimal_create_body("orders", partition_columns=["id"]),
    )
    assert r.status_code == 200, r.text
    assert r.json()["metadata"]["partition-columns"] == ["id"]


# ---------------------------------------------------------------------------
# HEAD / list / delete / rename
# ---------------------------------------------------------------------------


def test_head_existing_table_204(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = client.head(f"{DELTA}/catalogs/cat1/schemas/sch1/tables/orders")
    assert r.status_code == 204
    assert r.content == b""


def test_head_missing_table_404(client: TestClient) -> None:
    _make_parents(client)
    r = client.head(f"{DELTA}/catalogs/cat1/schemas/sch1/tables/missing")
    assert r.status_code == 404


def test_list_tables(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client, "orders")
    _create_delta_table(client, "customers")
    r = client.get(f"{DELTA}/catalogs/cat1/schemas/sch1/tables")
    assert r.status_code == 200, r.text
    body = r.json()
    names = {i["name"] for i in body["identifiers"]}
    assert names == {"orders", "customers"}
    assert all(i["data-source-format"] == "DELTA" for i in body["identifiers"])


def test_delete_table_204(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = client.delete(f"{DELTA}/catalogs/cat1/schemas/sch1/tables/orders")
    assert r.status_code == 204
    r = client.get(f"{DELTA}/catalogs/cat1/schemas/sch1/tables/orders")
    assert r.status_code == 404


def test_rename_table_204(client: TestClient) -> None:
    _make_parents(client)
    body = _create_delta_table(client)
    original_id = body["metadata"]["table-uuid"]

    r = client.post(
        f"{DELTA}/catalogs/cat1/schemas/sch1/tables/orders/rename",
        json={"new-name": "orders_v2"},
    )
    assert r.status_code == 204

    r = client.get(f"{DELTA}/catalogs/cat1/schemas/sch1/tables/orders")
    assert r.status_code == 404

    r = client.get(f"{DELTA}/catalogs/cat1/schemas/sch1/tables/orders_v2")
    assert r.status_code == 200
    # Opaque id is preserved — this is the rename-invariance guarantee.
    assert r.json()["metadata"]["table-uuid"] == original_id


def test_rename_duplicate_returns_409(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client, "orders")
    _create_delta_table(client, "customers")
    r = client.post(
        f"{DELTA}/catalogs/cat1/schemas/sch1/tables/orders/rename",
        json={"new-name": "customers"},
    )
    assert r.status_code == 409, r.text


# ---------------------------------------------------------------------------
# UpdateTable
# ---------------------------------------------------------------------------


def _update(body: dict[str, Any]) -> dict[str, Any]:
    return {"requirements": [], "updates": [body]}


def _send_update(client: TestClient, body: dict[str, Any], table: str = "orders") -> Any:
    return client.post(
        f"{DELTA}/catalogs/cat1/schemas/sch1/tables/{table}",
        json=body,
    )


def test_update_set_properties(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _send_update(
        client,
        _update({"action": "set-properties", "updates": {"owner": "alice"}}),
    )
    assert r.status_code == 200, r.text
    assert r.json()["metadata"]["properties"]["owner"] == "alice"


def test_update_remove_properties(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _send_update(
        client,
        _update(
            {
                "action": "remove-properties",
                "removals": ["delta.enableDeletionVectors"],
            },
        ),
    )
    assert r.status_code == 200, r.text
    assert "delta.enableDeletionVectors" not in r.json()["metadata"]["properties"]


def test_update_set_table_comment(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _send_update(
        client,
        _update({"action": "set-table-comment", "comment": "order facts"}),
    )
    assert r.status_code == 200, r.text
    # The Delta wire shape doesn't expose comment in TableMetadata,
    # but the UC side should now see it.
    r = client.get(f"{API}/tables/cat1.sch1.orders")
    assert r.status_code == 200
    assert r.json()["comment"] == "order facts"


def test_update_set_columns_full_replacement(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    new_columns = [
        {"name": "id", "type": "long", "nullable": False, "metadata": {}},
        {"name": "new_field", "type": "string", "nullable": True, "metadata": {}},
    ]
    r = _send_update(
        client,
        _update({"action": "set-columns", "columns": new_columns}),
    )
    assert r.status_code == 200, r.text
    cols = r.json()["metadata"]["columns"]
    assert [c["name"] for c in cols] == ["id", "new_field"]


def test_update_set_partition_columns(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _send_update(
        client,
        _update({"action": "set-partition-columns", "partition-columns": ["id"]}),
    )
    assert r.status_code == 200, r.text
    assert r.json()["metadata"]["partition-columns"] == ["id"]


def test_update_set_protocol_is_noop(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _send_update(
        client,
        _update(
            {
                "action": "set-protocol",
                "protocol": {"min-reader-version": 3, "min-writer-version": 7},
            },
        ),
    )
    assert r.status_code == 200, r.text
    # soyuz discards per-table protocol; response carries the fixed default.
    proto = r.json()["metadata"]["protocol"]
    assert proto["min-reader-version"] == 1
    assert proto["min-writer-version"] == 2


def test_update_set_domain_metadata_is_noop(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _send_update(
        client,
        _update(
            {
                "action": "set-domain-metadata",
                "updates": {"delta.rowTracking": {"foo": "bar"}},
            },
        ),
    )
    assert r.status_code == 200, r.text


def test_update_add_commit_returns_501(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _send_update(
        client,
        _update(
            {
                "action": "add-commit",
                "commit": {
                    "version": 1,
                    "timestamp": 0,
                    "file-name": "00000.json",
                    "file-size": 100,
                    "file-modification-timestamp": 0,
                },
            },
        ),
    )
    assert r.status_code == 501, r.text
    assert r.json()["error_code"] == "COMMIT_COORDINATOR_UNSUPPORTED"


def test_update_set_latest_backfilled_version_returns_501(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _send_update(
        client,
        _update(
            {"action": "set-latest-backfilled-version", "latest-published-version": 42},
        ),
    )
    assert r.status_code == 501


# ---------------------------------------------------------------------------
# Requirements
# ---------------------------------------------------------------------------


def test_requirement_assert_table_uuid_success(client: TestClient) -> None:
    _make_parents(client)
    body = _create_delta_table(client)
    uuid = body["metadata"]["table-uuid"]
    r = _send_update(
        client,
        {
            "requirements": [{"type": "assert-table-uuid", "uuid": uuid}],
            "updates": [{"action": "set-properties", "updates": {"k": "v"}}],
        },
    )
    assert r.status_code == 200, r.text


def test_requirement_assert_table_uuid_failure_409(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _send_update(
        client,
        {
            "requirements": [{"type": "assert-table-uuid", "uuid": "00" * 16}],
            "updates": [{"action": "set-properties", "updates": {"k": "v"}}],
        },
    )
    assert r.status_code == 409, r.text


def test_requirement_assert_etag_success(client: TestClient) -> None:
    _make_parents(client)
    body = _create_delta_table(client)
    etag = body["metadata"]["etag"]
    r = _send_update(
        client,
        {
            "requirements": [{"type": "assert-etag", "etag": etag}],
            "updates": [{"action": "set-properties", "updates": {"k": "v"}}],
        },
    )
    assert r.status_code == 200, r.text


def test_requirement_assert_etag_stale_409(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _send_update(
        client,
        {
            "requirements": [{"type": "assert-etag", "etag": "0"}],
            "updates": [{"action": "set-properties", "updates": {"k": "v"}}],
        },
    )
    assert r.status_code == 409, r.text


# ---------------------------------------------------------------------------
# Staging tables + credentials + metrics stubs
# ---------------------------------------------------------------------------


def _make_parents_with_storage(client: TestClient) -> None:
    r = client.post(CATALOGS, json={"name": "cat1", "storage_root": "s3://bucket/root"})
    assert r.status_code == 200, r.text
    r = client.post(SCHEMAS, json={"name": "sch1", "catalog_name": "cat1"})
    assert r.status_code == 200, r.text


def test_create_staging_table(client: TestClient) -> None:
    _make_parents_with_storage(client)
    r = client.post(
        f"{DELTA}/catalogs/cat1/schemas/sch1/staging-tables",
        json={"name": "sales"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["table-type"] == "MANAGED"
    assert body["table-id"]  # opaque id returned
    assert body["location"].startswith("s3://bucket/root/")
    assert body["storage-credentials"] == []
    assert body["required-protocol"]["min-reader-version"] == 1


def test_get_table_credentials_empty(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = client.get(
        f"{DELTA}/catalogs/cat1/schemas/sch1/tables/orders/credentials",
        params={"operation": "READ"},
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"storage-credentials": []}


def test_get_table_credentials_unknown_table_404(client: TestClient) -> None:
    _make_parents(client)
    r = client.get(
        f"{DELTA}/catalogs/cat1/schemas/sch1/tables/missing/credentials",
        params={"operation": "READ"},
    )
    assert r.status_code == 404


def test_get_temporary_path_credentials_empty(client: TestClient) -> None:
    r = client.get(
        f"{DELTA}/temporary-path-credentials",
        params={"location": "s3://b/x", "operation": "READ_WRITE"},
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"storage-credentials": []}


def test_report_metrics_204(client: TestClient) -> None:
    _make_parents(client)
    body = _create_delta_table(client)
    uuid = body["metadata"]["table-uuid"]
    r = client.post(
        f"{DELTA}/catalogs/cat1/schemas/sch1/tables/orders/metrics",
        json={
            "table-id": uuid,
            "report": {
                "commit-report": {
                    "num-files-added": 3,
                    "num-bytes-added": 1024,
                },
            },
        },
    )
    assert r.status_code == 204


def test_report_metrics_unknown_table_404(client: TestClient) -> None:
    _make_parents(client)
    r = client.post(
        f"{DELTA}/catalogs/cat1/schemas/sch1/tables/missing/metrics",
        json={"table-id": "0" * 32, "report": {}},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Interop with the main UC API
# ---------------------------------------------------------------------------


def test_uc_api_table_loads_through_delta_api(client: TestClient) -> None:
    """A table created through the main UC API is readable via Delta."""
    _make_parents(client)
    r = client.post(
        f"{API}/tables",
        json={
            "name": "via_uc",
            "catalog_name": "cat1",
            "schema_name": "sch1",
            "table_type": "MANAGED",
            "data_source_format": "DELTA",
            "storage_location": "s3://bucket/via_uc",
            "columns": [
                {
                    "name": "x",
                    "type_text": "int",
                    "type_json": '{"type":"integer"}',
                    "type_name": "INT",
                    "position": 0,
                    "nullable": True,
                },
            ],
        },
    )
    assert r.status_code == 200, r.text
    r = client.get(f"{DELTA}/catalogs/cat1/schemas/sch1/tables/via_uc")
    assert r.status_code == 200, r.text
    metadata = r.json()["metadata"]
    assert metadata["columns"][0]["name"] == "x"
