"""Unit tests for the Metric Views resource (ADR-0014)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

CATALOGS = "/api/2.1/unity-catalog/catalogs"
SCHEMAS = "/api/2.1/unity-catalog/schemas"
METRIC_VIEWS = "/api/2.1/unity-catalog/metric-views"
AUDIT_LOG = "/audit-log"


def _make_catalog(client: TestClient, name: str = "main") -> None:
    assert client.post(CATALOGS, json={"name": name}).status_code == 200


def _make_schema(client: TestClient, catalog_name: str = "main", name: str = "s") -> None:
    assert (
        client.post(SCHEMAS, json={"name": name, "catalog_name": catalog_name}).status_code == 200
    )


def _spec(**overrides: Any) -> dict[str, Any]:
    spec: dict[str, Any] = {
        "dimensions": [
            {"name": "order_date", "expr": "DATE_TRUNC('day', ordered_at)"},
            {"name": "region", "expr": "region", "comment": "Sales region"},
        ],
        "measures": [
            {"name": "revenue", "expr": "SUM(amount)"},
            {"name": "order_count", "expr": "COUNT(1)", "comment": "Orders"},
        ],
        "filter": "status = 'COMPLETE'",
    }
    spec.update(overrides)
    return spec


def _body(
    name: str = "sales_metrics",
    catalog_name: str = "main",
    schema_name: str = "s",
    **overrides: Any,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "name": name,
        "catalog_name": catalog_name,
        "schema_name": schema_name,
        "source_table_full_name": "main.s.orders",
        "spec": _spec(),
    }
    body.update(overrides)
    return body


def _post(client: TestClient, name: str = "sales_metrics", **overrides: Any) -> dict[str, Any]:
    r = client.post(METRIC_VIEWS, json=_body(name=name, **overrides))
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_metric_view(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = _post(client, comment="Daily sales rollup")
    assert body["name"] == "sales_metrics"
    assert body["catalog_name"] == "main"
    assert body["schema_name"] == "s"
    assert body["full_name"] == "main.s.sales_metrics"
    assert body["source_table_full_name"] == "main.s.orders"
    assert body["comment"] == "Daily sales rollup"
    assert body["id"]
    assert body["created_at"] > 0
    assert [m["name"] for m in body["spec"]["measures"]] == ["revenue", "order_count"]
    assert [d["name"] for d in body["spec"]["dimensions"]] == ["order_date", "region"]
    assert body["spec"]["filter"] == "status = 'COMPLETE'"


def test_create_without_dimensions_or_filter(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    spec = {"measures": [{"name": "n", "expr": "COUNT(1)"}]}
    body = _post(client, spec=spec)
    assert body["spec"]["dimensions"] == []
    assert body["spec"]["measures"][0]["expr"] == "COUNT(1)"
    assert "filter" not in body["spec"]


def test_create_missing_catalog_404(client: TestClient) -> None:
    r = client.post(METRIC_VIEWS, json=_body())
    assert r.status_code == 404
    assert r.json()["error_code"] == "NOT_FOUND"


def test_create_missing_schema_404(client: TestClient) -> None:
    _make_catalog(client)
    r = client.post(METRIC_VIEWS, json=_body(schema_name="missing"))
    assert r.status_code == 404


def test_create_duplicate_409(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    r = client.post(METRIC_VIEWS, json=_body())
    assert r.status_code == 409
    assert r.json()["error_code"] == "ALREADY_EXISTS"


def test_create_same_name_in_other_schema_ok(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _make_schema(client, name="s2")
    _post(client)
    _post(client, schema_name="s2")


def test_create_empty_measures_422(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.post(METRIC_VIEWS, json=_body(spec={"dimensions": [], "measures": []}))
    assert r.status_code == 422


def test_create_extra_field_422(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    body = _body()
    body["storage_location"] = "file:///tmp/x"
    r = client.post(METRIC_VIEWS, json=body)
    assert r.status_code == 422


def test_create_extra_field_in_spec_entry_422(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    spec = {"measures": [{"name": "n", "expr": "COUNT(1)", "agg": "sum"}]}
    r = client.post(METRIC_VIEWS, json=_body(spec=spec))
    assert r.status_code == 422


def test_create_duplicate_measure_names_400(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    spec = {
        "measures": [
            {"name": "revenue", "expr": "SUM(a)"},
            {"name": "revenue", "expr": "SUM(b)"},
        ],
    }
    r = client.post(METRIC_VIEWS, json=_body(spec=spec))
    assert r.status_code == 400
    assert r.json()["error_code"] == "INVALID_ARGUMENT"


def test_create_dimension_measure_name_collision_400(client: TestClient) -> None:
    """Dimensions and measures share one flat column namespace."""
    _make_catalog(client)
    _make_schema(client)
    spec = {
        "dimensions": [{"name": "revenue", "expr": "revenue_bucket"}],
        "measures": [{"name": "revenue", "expr": "SUM(amount)"}],
    }
    r = client.post(METRIC_VIEWS, json=_body(spec=spec))
    assert r.status_code == 400


def test_create_malformed_source_table_name_400(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    for bad in ("orders", "s.orders", "a.b.c.d", "a..c"):
        r = client.post(METRIC_VIEWS, json=_body(source_table_full_name=bad))
        assert r.status_code == 400, bad


def test_create_does_not_require_source_table_to_exist(client: TestClient) -> None:
    """The source reference is resolved by the consumer at compile time."""
    _make_catalog(client)
    _make_schema(client)
    body = _post(client, source_table_full_name="other.elsewhere.not_registered")
    assert body["source_table_full_name"] == "other.elsewhere.not_registered"


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


def test_get_metric_view(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    r = client.get(f"{METRIC_VIEWS}/main.s.sales_metrics")
    assert r.status_code == 200
    assert r.json()["full_name"] == "main.s.sales_metrics"


def test_get_not_found(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.get(f"{METRIC_VIEWS}/main.s.missing")
    assert r.status_code == 404


def test_get_malformed_full_name_400(client: TestClient) -> None:
    r = client.get(f"{METRIC_VIEWS}/not_three_parts")
    assert r.status_code == 400


def test_parent_rename_propagates(client: TestClient) -> None:
    """Schema renames flow into full_name — the row stores opaque ids."""
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    r = client.patch(f"{SCHEMAS}/main.s", json={"new_name": "renamed"})
    assert r.status_code == 200
    r = client.get(f"{METRIC_VIEWS}/main.renamed.sales_metrics")
    assert r.status_code == 200
    assert r.json()["full_name"] == "main.renamed.sales_metrics"
    assert client.get(f"{METRIC_VIEWS}/main.s.sales_metrics").status_code == 404


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_metric_views(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client, name="b")
    _post(client, name="a")
    r = client.get(METRIC_VIEWS, params={"catalog_name": "main", "schema_name": "s"})
    assert r.status_code == 200
    body = r.json()
    assert [v["name"] for v in body["metric_views"]] == ["b", "a"]
    assert body.get("next_page_token") is None


def test_list_missing_parent_404(client: TestClient) -> None:
    r = client.get(METRIC_VIEWS, params={"catalog_name": "main", "schema_name": "s"})
    assert r.status_code == 404


def test_list_pagination(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    for n in ("v0", "v1", "v2", "v3"):
        _post(client, name=n)
    r1 = client.get(
        METRIC_VIEWS,
        params={"catalog_name": "main", "schema_name": "s", "max_results": 2},
    )
    body1 = r1.json()
    assert [v["name"] for v in body1["metric_views"]] == ["v0", "v1"]
    assert body1["next_page_token"]
    r2 = client.get(
        METRIC_VIEWS,
        params={
            "catalog_name": "main",
            "schema_name": "s",
            "page_token": body1["next_page_token"],
        },
    )
    body2 = r2.json()
    assert [v["name"] for v in body2["metric_views"]] == ["v2", "v3"]
    assert body2.get("next_page_token") is None


def test_list_rejects_out_of_range_max_results(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.get(
        METRIC_VIEWS,
        params={"catalog_name": "main", "schema_name": "s", "max_results": -1},
    )
    assert r.status_code == 422
    r = client.get(
        METRIC_VIEWS,
        params={"catalog_name": "main", "schema_name": "s", "max_results": 0},
    )
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_patch_rename(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    r = client.patch(
        f"{METRIC_VIEWS}/main.s.sales_metrics",
        json={"new_name": "sales_kpis"},
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "main.s.sales_kpis"
    assert client.get(f"{METRIC_VIEWS}/main.s.sales_metrics").status_code == 404
    assert client.get(f"{METRIC_VIEWS}/main.s.sales_kpis").status_code == 200


def test_patch_rename_collision_409(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client, name="a")
    _post(client, name="b")
    r = client.patch(f"{METRIC_VIEWS}/main.s.a", json={"new_name": "b"})
    assert r.status_code == 409


def test_patch_replaces_spec(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    new_spec = {"measures": [{"name": "n", "expr": "COUNT(1)"}]}
    r = client.patch(f"{METRIC_VIEWS}/main.s.sales_metrics", json={"spec": new_spec})
    assert r.status_code == 200
    body = r.json()
    assert body["spec"]["dimensions"] == []
    assert [m["name"] for m in body["spec"]["measures"]] == ["n"]
    assert "filter" not in body["spec"]


def test_patch_spec_duplicate_names_400(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    bad = {"measures": [{"name": "n", "expr": "a"}, {"name": "n", "expr": "b"}]}
    r = client.patch(f"{METRIC_VIEWS}/main.s.sales_metrics", json={"spec": bad})
    assert r.status_code == 400


def test_patch_source_and_comment(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    r = client.patch(
        f"{METRIC_VIEWS}/main.s.sales_metrics",
        json={"source_table_full_name": "main.s.orders_v2", "comment": "v2"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["source_table_full_name"] == "main.s.orders_v2"
    assert body["comment"] == "v2"


def test_patch_malformed_source_400(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    r = client.patch(
        f"{METRIC_VIEWS}/main.s.sales_metrics",
        json={"source_table_full_name": "two.parts"},
    )
    assert r.status_code == 400


def test_patch_empty_body_is_noop(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    created = _post(client)
    r = client.patch(f"{METRIC_VIEWS}/main.s.sales_metrics", json={})
    assert r.status_code == 200
    assert r.json()["spec"] == created["spec"]


def test_patch_unknown_field_422(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    r = client.patch(f"{METRIC_VIEWS}/main.s.sales_metrics", json={"id": "boom"})
    assert r.status_code == 422


def test_patch_not_found(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.patch(f"{METRIC_VIEWS}/main.s.missing", json={"comment": "x"})
    assert r.status_code == 404


def test_patch_updates_updated_at(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    created = _post(client)
    r = client.patch(f"{METRIC_VIEWS}/main.s.sales_metrics", json={"comment": "x"})
    assert r.json()["updated_at"] > created["updated_at"]


# ---------------------------------------------------------------------------
# Delete + parent cascade
# ---------------------------------------------------------------------------


def test_delete_metric_view(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    r = client.delete(f"{METRIC_VIEWS}/main.s.sales_metrics")
    assert r.status_code == 200
    assert client.get(f"{METRIC_VIEWS}/main.s.sales_metrics").status_code == 404


def test_delete_not_found(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    r = client.delete(f"{METRIC_VIEWS}/main.s.missing")
    assert r.status_code == 404


def test_schema_delete_blocked_by_metric_views(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    r = client.delete(f"{SCHEMAS}/main.s")
    assert r.status_code == 409
    assert "metric views" in r.json()["message"]


def test_schema_force_delete_cascades_metric_views(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    r = client.delete(f"{SCHEMAS}/main.s", params={"force": "true"})
    assert r.status_code == 200
    # Recreating the same address must yield a fresh, empty namespace.
    _make_schema(client)
    r = client.get(METRIC_VIEWS, params={"catalog_name": "main", "schema_name": "s"})
    assert r.status_code == 200
    assert r.json()["metric_views"] == []


def test_catalog_force_delete_cascades_metric_views(client: TestClient) -> None:
    _make_catalog(client)
    _make_schema(client)
    _post(client)
    r = client.delete(f"{CATALOGS}/main", params={"force": "true"})
    assert r.status_code == 200
    _make_catalog(client)
    _make_schema(client)
    r = client.get(METRIC_VIEWS, params={"catalog_name": "main", "schema_name": "s"})
    assert r.status_code == 200
    assert r.json()["metric_views"] == []


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def test_mutations_are_audited(client: TestClient) -> None:
    run_id = "11111111-2222-3333-4444-555555555555"
    headers = {"X-Agent-Run-Id": run_id}
    _make_catalog(client)
    _make_schema(client)
    r = client.post(METRIC_VIEWS, json=_body(), headers=headers)
    assert r.status_code == 200
    r = client.patch(
        f"{METRIC_VIEWS}/main.s.sales_metrics",
        json={"comment": "x"},
        headers=headers,
    )
    assert r.status_code == 200
    r = client.delete(f"{METRIC_VIEWS}/main.s.sales_metrics", headers=headers)
    assert r.status_code == 200

    rows = client.get(AUDIT_LOG, params={"agent_run_id": run_id}).json()
    actions = [row["action"] for row in rows]
    assert actions == [
        "metric_view.created",
        "metric_view.updated",
        "metric_view.deleted",
    ]
    assert all(row["target"] == "main.s.sales_metrics" for row in rows)
