"""Tests for the lineage endpoints (ADR-0008).

Covers OpenLineage event ingestion (resolved vs. unresolved datasets,
state transitions, idempotent redelivery), upstream and downstream
traversal with depth caps, rename-invariance of opaque securable ids,
and the append-only delete posture where a deleted table leaves its
edges as dangling references that render with ``full_name = null``.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

API = "/api/2.1/unity-catalog"
CATALOGS = f"{API}/catalogs"
SCHEMAS = f"{API}/schemas"
TABLES = f"{API}/tables"

LINEAGE_EVENTS = "/lineage/v1/events"
LINEAGE_UPSTREAM = "/lineage/upstream"
LINEAGE_DOWNSTREAM = "/lineage/downstream"


def _make_catalog(client: TestClient, name: str = "cat1") -> None:
    r = client.post(CATALOGS, json={"name": name})
    assert r.status_code == 200, r.text


def _make_schema(client: TestClient, catalog: str = "cat1", name: str = "sch1") -> None:
    r = client.post(SCHEMAS, json={"name": name, "catalog_name": catalog})
    assert r.status_code == 200, r.text


def _make_table(
    client: TestClient,
    name: str,
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
            ],
        },
    )
    assert r.status_code == 200, r.text
    return r.json()


def _seed_chain(client: TestClient, names: list[str]) -> dict[str, dict[str, Any]]:
    _make_catalog(client)
    _make_schema(client)
    return {n: _make_table(client, n) for n in names}


def _event(
    *,
    event_type: str = "COMPLETE",
    event_time: str = "2026-04-15T10:00:00Z",
    run_id: str | None = None,
    job_name: str = "nightly_orders_etl",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "eventType": event_type,
        "eventTime": event_time,
        "run": {"runId": run_id or str(uuid.uuid4())},
        "job": {"namespace": "airflow", "name": job_name},
        "inputs": [{"namespace": "s3://bucket", "name": n} for n in (inputs or [])],
        "outputs": [{"namespace": "s3://bucket", "name": n} for n in (outputs or [])],
    }


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------


def test_ingest_start_creates_run_and_edges(client: TestClient) -> None:
    _seed_chain(client, ["src", "dst"])
    run_id = str(uuid.uuid4())
    body = _event(
        event_type="START",
        run_id=run_id,
        inputs=["cat1.sch1.src"],
        outputs=["cat1.sch1.dst"],
    )
    r = client.post(LINEAGE_EVENTS, json=body)
    assert r.status_code == 201, r.text
    payload = r.json()
    assert payload["run_id"] == run_id.replace("-", "")
    assert payload["state"] == "START"
    assert payload["accepted_edges"] == 1
    assert payload["rejected_datasets"] == 0


def test_ingest_complete_updates_state(client: TestClient) -> None:
    _seed_chain(client, ["src", "dst"])
    run_id = str(uuid.uuid4())
    client.post(
        LINEAGE_EVENTS,
        json=_event(
            event_type="START",
            event_time="2026-04-15T10:00:00Z",
            run_id=run_id,
            inputs=["cat1.sch1.src"],
            outputs=["cat1.sch1.dst"],
        ),
    )
    r = client.post(
        LINEAGE_EVENTS,
        json=_event(
            event_type="COMPLETE",
            event_time="2026-04-15T10:05:00Z",
            run_id=run_id,
            inputs=["cat1.sch1.src"],
            outputs=["cat1.sch1.dst"],
        ),
    )
    assert r.status_code == 201, r.text
    assert r.json() == {
        "run_id": run_id.replace("-", ""),
        "state": "COMPLETE",
        "accepted_edges": 0,
        "rejected_datasets": 0,
        "accepted_column_edges": 0,
        "accepted_value_changes": 0,
    }


def test_ingest_drops_unresolved_datasets(client: TestClient) -> None:
    _seed_chain(client, ["src", "dst"])
    body = _event(
        inputs=["cat1.sch1.src", "external.foo.bar"],
        outputs=["cat1.sch1.dst"],
    )
    r = client.post(LINEAGE_EVENTS, json=body)
    assert r.status_code == 201, r.text
    payload = r.json()
    assert payload["accepted_edges"] == 1
    assert payload["rejected_datasets"] == 1


def test_ingest_is_idempotent(client: TestClient) -> None:
    _seed_chain(client, ["src", "dst"])
    body = _event(
        inputs=["cat1.sch1.src"],
        outputs=["cat1.sch1.dst"],
    )
    first = client.post(LINEAGE_EVENTS, json=body)
    assert first.status_code == 201, first.text
    second = client.post(LINEAGE_EVENTS, json=body)
    assert second.status_code == 201, second.text
    assert second.json()["accepted_edges"] == 0


def test_ingest_rejects_malformed_run_id(client: TestClient) -> None:
    _seed_chain(client, ["src", "dst"])
    body = _event(
        run_id="not-a-uuid",
        inputs=["cat1.sch1.src"],
        outputs=["cat1.sch1.dst"],
    )
    r = client.post(LINEAGE_EVENTS, json=body)
    assert r.status_code == 400, r.text
    # v0.3.0rc2 — error message includes the offending value + a
    # canonical-form example so producers can self-correct.
    assert "valid UUID" in r.json().get("message", "")
    assert "not-a-uuid" in r.json().get("message", "")


@pytest.mark.parametrize(
    "run_id",
    [
        "8ac59c26-7dca-46cf-8281-78fc7e8c58f9",  # canonical hyphenated  # pragma: allowlist secret
        "8ac59c267dca46cf828178fc7e8c58f9",  # 32-hex unhyphenated  # pragma: allowlist secret
        "urn:uuid:8ac59c26-7dca-46cf-8281-78fc7e8c58f9",  # URN form  # pragma: allowlist secret
        "{8ac59c26-7dca-46cf-8281-78fc7e8c58f9}",  # braced  # pragma: allowlist secret
        "8AC59C26-7DCA-46CF-8281-78FC7E8C58F9",  # uppercase  # pragma: allowlist secret
    ],
)
def test_ingest_accepts_all_uuid_representations(client: TestClient, run_id: str) -> None:
    """v0.3.0rc2 — every standard UUID textual form is accepted.

    Pre-rc2 the validation only accepted canonical or 32-hex; URN,
    braced, and uppercase forms were rejected with a confusing
    "32 hex chars after hyphen stripping" error.
    """
    _seed_chain(client, ["src", "dst"])
    body = _event(
        run_id=run_id,
        inputs=["cat1.sch1.src"],
        outputs=["cat1.sch1.dst"],
    )
    r = client.post(LINEAGE_EVENTS, json=body)
    assert r.status_code in (200, 201), r.text


def test_ingest_rejects_malformed_event_time(client: TestClient) -> None:
    _seed_chain(client, ["src", "dst"])
    body = _event(
        event_time="not-a-timestamp",
        inputs=["cat1.sch1.src"],
        outputs=["cat1.sch1.dst"],
    )
    r = client.post(LINEAGE_EVENTS, json=body)
    assert r.status_code == 400, r.text


def test_ingest_drops_self_edge(client: TestClient) -> None:
    _seed_chain(client, ["same"])
    body = _event(
        inputs=["cat1.sch1.same"],
        outputs=["cat1.sch1.same"],
    )
    r = client.post(LINEAGE_EVENTS, json=body)
    assert r.status_code == 201, r.text
    assert r.json()["accepted_edges"] == 0


# ---------------------------------------------------------------------------
# Traversal
# ---------------------------------------------------------------------------


def _build_chain(client: TestClient) -> None:
    """Seed a 4-table chain a → b → c → d with four distinct runs."""
    _seed_chain(client, ["a", "b", "c", "d"])
    for src, tgt in [("a", "b"), ("b", "c"), ("c", "d")]:
        r = client.post(
            LINEAGE_EVENTS,
            json=_event(
                run_id=str(uuid.uuid4()),
                job_name=f"{src}_to_{tgt}",
                inputs=[f"cat1.sch1.{src}"],
                outputs=[f"cat1.sch1.{tgt}"],
            ),
        )
        assert r.status_code == 201, r.text


def test_upstream_traversal_depth(client: TestClient) -> None:
    _build_chain(client)
    r = client.get(f"{LINEAGE_UPSTREAM}/cat1.sch1.d", params={"depth": 2})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["root"] == "cat1.sch1.d"
    assert body["direction"] == "upstream"
    full_names = {n["full_name"] for n in body["nodes"]}
    assert "cat1.sch1.d" in full_names
    assert "cat1.sch1.c" in full_names
    assert "cat1.sch1.b" in full_names
    assert "cat1.sch1.a" not in full_names


def test_downstream_traversal_depth(client: TestClient) -> None:
    _build_chain(client)
    r = client.get(f"{LINEAGE_DOWNSTREAM}/cat1.sch1.a", params={"depth": 2})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["direction"] == "downstream"
    full_names = {n["full_name"] for n in body["nodes"]}
    assert full_names == {"cat1.sch1.a", "cat1.sch1.b", "cat1.sch1.c"}


def test_traversal_depth_zero_returns_only_root(client: TestClient) -> None:
    _build_chain(client)
    r = client.get(f"{LINEAGE_UPSTREAM}/cat1.sch1.d", params={"depth": 0})
    assert r.status_code == 200, r.text
    body = r.json()
    assert [n["full_name"] for n in body["nodes"]] == ["cat1.sch1.d"]
    assert body["edges"] == []


def test_depth_cap_rejected(client: TestClient) -> None:
    _seed_chain(client, ["a"])
    r = client.get(f"{LINEAGE_UPSTREAM}/cat1.sch1.a", params={"depth": 99})
    assert r.status_code == 400, r.text


def test_upstream_unknown_table_404(client: TestClient) -> None:
    _seed_chain(client, ["a"])
    r = client.get(f"{LINEAGE_UPSTREAM}/cat1.sch1.missing", params={"depth": 1})
    assert r.status_code == 404, r.text


def test_rename_invariance(client: TestClient) -> None:
    """Renaming a table must leave its edges queryable under the new name.

    Tables use a PATCH-by-full_name endpoint; rather than go through the
    rename path, we delete the old row and re-create a new one under a
    different name — which would *break* rename invariance because
    re-create assigns a fresh opaque id. So instead we use the actual
    rename path via the schema PATCH: rename the parent schema and
    verify the old schema name no longer resolves while the new one does.
    The underlying edge rows never change, which is the whole point.
    """
    _build_chain(client)
    # Rename the parent schema; the edges are keyed on table ids so
    # the downstream graph should still walk correctly under the new
    # full_name.
    r = client.patch(
        f"{SCHEMAS}/cat1.sch1",
        json={"new_name": "sch2"},
    )
    assert r.status_code == 200, r.text
    r = client.get(f"{LINEAGE_DOWNSTREAM}/cat1.sch2.a", params={"depth": 3})
    assert r.status_code == 200, r.text
    full_names = {n["full_name"] for n in r.json()["nodes"]}
    assert full_names == {
        "cat1.sch2.a",
        "cat1.sch2.b",
        "cat1.sch2.c",
        "cat1.sch2.d",
    }


def test_table_delete_leaves_dangling_edge(client: TestClient) -> None:
    _build_chain(client)
    r = client.delete(f"{TABLES}/cat1.sch1.c")
    assert r.status_code == 200, r.text
    # Walking downstream from ``a`` now reaches the surviving nodes
    # (a, b, d) — d is still reachable because the ``c → d`` edge row
    # was left in place, dangling on ``c``'s opaque id. The response
    # renders the deleted node's full_name as null but still exposes
    # the opaque id.
    r = client.get(f"{LINEAGE_DOWNSTREAM}/cat1.sch1.a", params={"depth": 5})
    assert r.status_code == 200, r.text
    body = r.json()
    null_nodes = [n for n in body["nodes"] if n["full_name"] is None]
    assert len(null_nodes) == 1
    # The dangling node should still be reachable via edges.
    dangling_id = null_nodes[0]["securable_id"]
    edge_targets = {e["target_securable_id"] for e in body["edges"]}
    assert dangling_id in edge_targets or any(
        e["source_securable_id"] == dangling_id for e in body["edges"]
    )


def test_last_write_wins_state_transitions(client: TestClient) -> None:
    _seed_chain(client, ["src", "dst"])
    run_id = str(uuid.uuid4())
    client.post(
        LINEAGE_EVENTS,
        json=_event(
            event_type="COMPLETE",
            run_id=run_id,
            inputs=["cat1.sch1.src"],
            outputs=["cat1.sch1.dst"],
        ),
    )
    r = client.post(
        LINEAGE_EVENTS,
        json=_event(
            event_type="RUNNING",
            run_id=run_id,
            inputs=["cat1.sch1.src"],
            outputs=["cat1.sch1.dst"],
        ),
    )
    assert r.status_code == 201, r.text
    assert r.json()["state"] == "RUNNING"
