"""Regression tests for audit-log persistence.

The audit trail is written by ``audit_service.log_action`` from the
mutation routes and read back via ``GET /audit-log``. Previously the
helper only ``flush()``-ed the row into a transaction nobody ever
committed, so ``get_db``'s ``session.close()`` rolled every audit row
back at request teardown — the read API was permanently empty. These
tests pin the end-to-end write→read path through real HTTP requests.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
TABLES = "/api/2.1/unity-catalog/tables"
AUDIT_LOG = "/audit-log"

RUN_ID = "9f0e8d7c6b5a4f3e2d1c0b9a8f7e6d5c"


def _table_body(name: str = "t") -> dict[str, Any]:
    return {
        "name": name,
        "catalog_name": "main",
        "schema_name": "s",
        "table_type": "MANAGED",
        "data_source_format": "DELTA",
        "columns": [
            {
                "name": "c0",
                "type_text": "int",
                "type_json": '{"type":"integer"}',
                "type_name": "INT",
                "position": 0,
            },
        ],
        "storage_location": "s3://bucket/t",
    }


def test_mutation_audit_rows_survive_the_request(client: TestClient) -> None:
    """Regression: audit rows must be committed, not just flushed.

    The mutation routes call ``log_action`` *after* their service
    function committed; the helper must commit the audit row itself or
    the request-teardown ``session.close()`` discards it.
    """
    headers = {"X-Agent-Run-Id": RUN_ID, "X-Principal": "flo"}
    assert client.post(CATALOGS, json={"name": "main"}, headers=headers).status_code == 200
    assert (
        client.post(
            SCHEMAS,
            json={"name": "s", "catalog_name": "main"},
            headers=headers,
        ).status_code
        == 200
    )
    assert client.post(TABLES, json=_table_body(), headers=headers).status_code == 200

    # Fresh request — fresh session. Rows must still be there.
    r = client.get(AUDIT_LOG, params={"agent_run_id": RUN_ID})
    assert r.status_code == 200
    rows = r.json()
    actions = [row["action"] for row in rows]
    assert "schema.created" in actions
    assert "table.created" in actions
    created = next(row for row in rows if row["action"] == "table.created")
    assert created["target"] == "main.s.t"
    assert created["principal"] == "flo"
    assert created["agent_run_id"] == RUN_ID


def test_table_delete_is_audited(client: TestClient) -> None:
    client.post(CATALOGS, json={"name": "main"})
    client.post(SCHEMAS, json={"name": "s", "catalog_name": "main"})
    client.post(TABLES, json=_table_body())
    assert client.delete(f"{TABLES}/main.s.t").status_code == 200

    r = client.get(AUDIT_LOG)
    assert r.status_code == 200
    actions = [row["action"] for row in r.json()]
    assert "table.deleted" in actions
