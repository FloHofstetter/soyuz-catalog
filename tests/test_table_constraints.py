"""Tests for declared table constraints (ADR-0012).

Constraints are a Databricks-supported, UC OSS missing over-the-spec
extension. Reads surface on the main UC REST ``GET /tables`` via the
``table_constraints`` field on :class:`TableInfo`; mutations ride
on the Delta REST ``POST /delta/v1/.../tables/{t}`` ``UpdateTable``
union via the ``add-constraint`` / ``drop-constraint`` actions
(ADR-0009).
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

API = "/api/2.1/unity-catalog"
DELTA = f"{API}/delta/v1"
CATALOGS = f"{API}/catalogs"
SCHEMAS = f"{API}/schemas"
TABLES = f"{API}/tables"


def _make_parents(client: TestClient, catalog: str = "cat1", schema: str = "sch1") -> None:
    assert client.post(CATALOGS, json={"name": catalog}).status_code == 200
    assert client.post(SCHEMAS, json={"name": schema, "catalog_name": catalog}).status_code == 200


def _create_delta_table(
    client: TestClient,
    name: str = "orders",
    catalog: str = "cat1",
    schema: str = "sch1",
    columns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if columns is None:
        columns = [
            {"name": "id", "type": "long", "nullable": False, "metadata": {}},
            {"name": "amount", "type": "double", "nullable": True, "metadata": {}},
        ]
    body = {
        "name": name,
        "location": f"s3://bucket/{name}",
        "table-type": "MANAGED",
        "data-source-format": "DELTA",
        "columns": columns,
        "partition-columns": [],
        "protocol": {"min-reader-version": 1, "min-writer-version": 2},
        "properties": {},
    }
    r = client.post(f"{DELTA}/catalogs/{catalog}/schemas/{schema}/tables", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def _update(
    client: TestClient,
    table: str,
    updates: list[dict[str, Any]],
    catalog: str = "cat1",
    schema: str = "sch1",
) -> Any:
    return client.post(
        f"{DELTA}/catalogs/{catalog}/schemas/{schema}/tables/{table}",
        json={"requirements": [], "updates": updates},
    )


def _add(
    client: TestClient,
    table: str,
    constraint: dict[str, Any],
    **kwargs: str,
) -> Any:
    return _update(
        client,
        table,
        [{"action": "add-constraint", "constraint": constraint}],
        **kwargs,
    )


def _drop(
    client: TestClient,
    table: str,
    name: str,
    if_exists: bool = False,
) -> Any:
    return _update(
        client,
        table,
        [
            {
                "action": "drop-constraint",
                "name": name,
                "if-exists": if_exists,
            },
        ],
    )


def _get_table(client: TestClient, full_name: str = "cat1.sch1.orders") -> dict[str, Any]:
    r = client.get(f"{TABLES}/{full_name}")
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Happy paths — add each constraint type and read it back.
# ---------------------------------------------------------------------------


def test_add_primary_key_constraint(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _add(
        client,
        "orders",
        {
            "name": "orders_pk",
            "primary_key_constraint": {"child_columns": ["id"]},
        },
    )
    assert r.status_code == 200, r.text
    constraints = _get_table(client)["table_constraints"]
    assert len(constraints) == 1
    assert constraints[0]["name"] == "orders_pk"
    assert constraints[0]["primary_key_constraint"] == {"child_columns": ["id"]}
    assert constraints[0]["foreign_key_constraint"] is None


def test_add_check_constraint(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _add(
        client,
        "orders",
        {
            "name": "positive_amount",
            "check_constraint": {
                "child_columns": ["amount"],
                "sql_text": "amount > 0",
            },
        },
    )
    assert r.status_code == 200, r.text
    constraints = _get_table(client)["table_constraints"]
    assert constraints[0]["check_constraint"] == {
        "child_columns": ["amount"],
        "sql_text": "amount > 0",
    }


def test_add_named_not_null_constraint(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _add(
        client,
        "orders",
        {
            "name": "amount_not_null",
            "named_table_constraint": {"child_column": "amount"},
        },
    )
    assert r.status_code == 200, r.text
    constraints = _get_table(client)["table_constraints"]
    assert constraints[0]["named_table_constraint"] == {"child_column": "amount"}


def test_add_foreign_key_constraint(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client, name="customers")
    _create_delta_table(client, name="orders")
    # make customers have an 'id' primary-key column (already present)
    r = _add(
        client,
        "orders",
        {
            "name": "orders_customer_fk",
            "foreign_key_constraint": {
                "child_columns": ["id"],
                "parent_table": "cat1.sch1.customers",
                "parent_columns": ["id"],
            },
        },
    )
    assert r.status_code == 200, r.text
    body = _get_table(client)
    fk = body["table_constraints"][0]["foreign_key_constraint"]
    assert fk["parent_table"] == "cat1.sch1.customers"
    assert fk["parent_columns"] == ["id"]
    assert fk["child_columns"] == ["id"]


# ---------------------------------------------------------------------------
# Drop
# ---------------------------------------------------------------------------


def test_drop_existing_constraint(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    _add(
        client,
        "orders",
        {
            "name": "orders_pk",
            "primary_key_constraint": {"child_columns": ["id"]},
        },
    )
    r = _drop(client, "orders", "orders_pk")
    assert r.status_code == 200, r.text
    assert _get_table(client).get("table_constraints") is None


def test_drop_missing_without_if_exists_returns_404(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _drop(client, "orders", "missing")
    assert r.status_code == 404, r.text


def test_drop_missing_with_if_exists_is_noop(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _drop(client, "orders", "missing", if_exists=True)
    assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# Uniqueness / duplicates
# ---------------------------------------------------------------------------


def test_duplicate_constraint_name_on_same_table_409(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    first = _add(
        client,
        "orders",
        {
            "name": "dup",
            "check_constraint": {"sql_text": "amount > 0"},
        },
    )
    assert first.status_code == 200
    second = _add(
        client,
        "orders",
        {
            "name": "dup",
            "check_constraint": {"sql_text": "id > 0"},
        },
    )
    assert second.status_code == 409, second.text


def test_same_name_on_different_tables_ok(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client, name="orders")
    _create_delta_table(client, name="customers")
    assert (
        _add(
            client,
            "orders",
            {"name": "ck", "check_constraint": {"sql_text": "id > 0"}},
        ).status_code
        == 200
    )
    assert (
        _add(
            client,
            "customers",
            {"name": "ck", "check_constraint": {"sql_text": "id > 0"}},
        ).status_code
        == 200
    )


def test_second_primary_key_is_409(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    assert (
        _add(
            client,
            "orders",
            {
                "name": "pk1",
                "primary_key_constraint": {"child_columns": ["id"]},
            },
        ).status_code
        == 200
    )
    r = _add(
        client,
        "orders",
        {
            "name": "pk2",
            "primary_key_constraint": {"child_columns": ["amount"]},
        },
    )
    assert r.status_code == 409, r.text


# ---------------------------------------------------------------------------
# Validation: columns must exist
# ---------------------------------------------------------------------------


def test_pk_unknown_column_400(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _add(
        client,
        "orders",
        {
            "name": "bad",
            "primary_key_constraint": {"child_columns": ["nope"]},
        },
    )
    assert r.status_code == 400, r.text


def test_fk_unknown_child_column_400(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client, name="customers")
    _create_delta_table(client, name="orders")
    r = _add(
        client,
        "orders",
        {
            "name": "bad",
            "foreign_key_constraint": {
                "child_columns": ["nope"],
                "parent_table": "cat1.sch1.customers",
                "parent_columns": ["id"],
            },
        },
    )
    assert r.status_code == 400, r.text


def test_fk_unknown_parent_table_404(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client, name="orders")
    r = _add(
        client,
        "orders",
        {
            "name": "bad",
            "foreign_key_constraint": {
                "child_columns": ["id"],
                "parent_table": "cat1.sch1.ghost",
                "parent_columns": ["id"],
            },
        },
    )
    assert r.status_code == 404, r.text


def test_fk_unknown_parent_column_400(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client, name="customers")
    _create_delta_table(client, name="orders")
    r = _add(
        client,
        "orders",
        {
            "name": "bad",
            "foreign_key_constraint": {
                "child_columns": ["id"],
                "parent_table": "cat1.sch1.customers",
                "parent_columns": ["nope"],
            },
        },
    )
    assert r.status_code == 400, r.text


def test_not_null_unknown_column_400(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _add(
        client,
        "orders",
        {
            "name": "bad",
            "named_table_constraint": {"child_column": "nope"},
        },
    )
    assert r.status_code == 400, r.text


def test_empty_envelope_400(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _add(client, "orders", {"name": "bad"})
    assert r.status_code == 400, r.text


# ---------------------------------------------------------------------------
# Rename invariance
# ---------------------------------------------------------------------------


def test_rename_parent_table_preserves_constraint(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    _add(
        client,
        "orders",
        {
            "name": "orders_pk",
            "primary_key_constraint": {"child_columns": ["id"]},
        },
    )
    r = client.post(
        f"{DELTA}/catalogs/cat1/schemas/sch1/tables/orders/rename",
        json={"new-name": "orders_v2"},
    )
    assert r.status_code == 204, r.text
    body = _get_table(client, "cat1.sch1.orders_v2")
    assert body["table_constraints"][0]["name"] == "orders_pk"


def test_rename_fk_parent_preserves_fk(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client, name="customers")
    _create_delta_table(client, name="orders")
    _add(
        client,
        "orders",
        {
            "name": "fk1",
            "foreign_key_constraint": {
                "child_columns": ["id"],
                "parent_table": "cat1.sch1.customers",
                "parent_columns": ["id"],
            },
        },
    )
    r = client.post(
        f"{DELTA}/catalogs/cat1/schemas/sch1/tables/customers/rename",
        json={"new-name": "customers_v2"},
    )
    assert r.status_code == 204
    body = _get_table(client, "cat1.sch1.orders")
    fk = body["table_constraints"][0]["foreign_key_constraint"]
    assert fk["parent_table"] == "cat1.sch1.customers_v2"


# ---------------------------------------------------------------------------
# Cascade on delete
# ---------------------------------------------------------------------------


def test_delete_table_drops_its_constraints(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    _add(
        client,
        "orders",
        {
            "name": "orders_pk",
            "primary_key_constraint": {"child_columns": ["id"]},
        },
    )
    r = client.delete(f"{TABLES}/cat1.sch1.orders")
    assert r.status_code == 200
    _create_delta_table(client)
    body = _get_table(client)
    assert body.get("table_constraints") is None


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------


def test_batch_add_constraints_transactional(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _update(
        client,
        "orders",
        [
            {
                "action": "add-constraint",
                "constraint": {
                    "name": "pk",
                    "primary_key_constraint": {"child_columns": ["id"]},
                },
            },
            {
                "action": "add-constraint",
                "constraint": {
                    "name": "ck",
                    "check_constraint": {"sql_text": "amount > 0"},
                },
            },
        ],
    )
    assert r.status_code == 200, r.text
    names = {c["name"] for c in _get_table(client)["table_constraints"]}
    assert names == {"pk", "ck"}


def test_batch_rolls_back_on_failure(client: TestClient) -> None:
    _make_parents(client)
    _create_delta_table(client)
    r = _update(
        client,
        "orders",
        [
            {
                "action": "add-constraint",
                "constraint": {
                    "name": "pk",
                    "primary_key_constraint": {"child_columns": ["id"]},
                },
            },
            {
                "action": "add-constraint",
                "constraint": {
                    "name": "bad",
                    "primary_key_constraint": {"child_columns": ["ghost"]},
                },
            },
        ],
    )
    assert r.status_code == 400, r.text
    body = _get_table(client)
    assert body.get("table_constraints") is None
