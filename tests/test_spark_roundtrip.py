"""End-to-end Spark smoke test against a live soyuz server.

Validates that soyuz is a drop-in for the **JVM** UC ecosystem by
running the upstream ``unitycatalog-spark`` connector against
single-node Spark in ``local[*]`` mode. The session-scoped fixture
builds a real JVM via ``pyspark`` (the ``spark`` optional extra),
points the connector at a live soyuz server, and runs
write/read/JOIN/DESCRIBE/list operations.

Marked :mod:`@pytest.mark.integration` so it is skipped from the default
suite (``pyproject.toml`` ``addopts = "-m 'not integration'"``); opt in
with ``pytest -m integration``. Lazy-imports ``pyspark`` so a default
install without the ``spark`` extra skips cleanly instead of erroring
at collection time.

Two test functions: ``test_external_delta_roundtrip_via_spark`` is the
must-pass gate covering external Delta tables with an explicit
``LOCATION``. ``test_managed_delta_table_creation_via_spark`` is a
strict-xfail discovery test: the connector routes managed Delta table
creation through ``createStagingTable`` + ``generateTemporaryTable
Credentials`` + the Delta coordinated-commits protocol. The
staging-id fallthrough in ``credentials_service`` lets the first two
calls succeed, but the path eventually exercises a coordinator action
on the Delta REST Kernel surface (``/delta/v1/``) that returns 501
(ADR-0009, ADR-0011), so the Delta writer aborts at the first
``INSERT``. The xfail pins that exact failure mode and will flip to
a real failure the day those coordinator actions land.

The heavy fixture plumbing (module-scoped hypercorn live server, JVM
SparkSession with the UCSingleCatalog plugin wired to it) lives in
:mod:`tests._spark_fixtures` so the compatibility audit module can
share it. See that module's docstring for why the fixtures are not in
``conftest.py``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pyspark = pytest.importorskip("pyspark")
hypercorn = pytest.importorskip("hypercorn")

from pyspark.sql import SparkSession  # noqa: E402

from tests._spark_helpers import CATALOG_NAME, bootstrap_catalog  # noqa: E402

pytest_plugins = ("tests._spark_fixtures",)
pytestmark = pytest.mark.integration


def test_external_delta_roundtrip_via_spark(
    spark_session: SparkSession,
    module_live_server: str,
    tmp_path: Path,
) -> None:
    """Write + read + JOIN + DESCRIBE an external Delta table via Spark.

    The must-pass gate for JVM-Spark compatibility. Uses external Delta tables with an
    explicit ``LOCATION`` clause — Spark's path-based Delta writer
    handles the commit directly against the local filesystem, so the
    connector never routes through ``createStagingTable`` or Delta's
    coordinated-commits protocol. Both of those paths land in the
    managed-table test below.
    """
    schema = "ext"
    warehouse = tmp_path / "warehouse"
    bootstrap_catalog(module_live_server, f"file://{warehouse}", schema)

    table_a = tmp_path / "ta"
    table_b = tmp_path / "tb"

    spark_session.sql(
        f"CREATE TABLE {CATALOG_NAME}.{schema}.ta (id INT, name STRING) "
        f"USING delta LOCATION 'file://{table_a}'"
    )
    spark_session.sql(f"INSERT INTO {CATALOG_NAME}.{schema}.ta VALUES (1, 'a'), (2, 'b')")

    rows = spark_session.sql(
        f"SELECT id, name FROM {CATALOG_NAME}.{schema}.ta ORDER BY id"
    ).collect()
    assert [(r.id, r.name) for r in rows] == [(1, "a"), (2, "b")]

    assert (table_a / "_delta_log").is_dir(), "Delta did not materialise a commit"

    describe = {
        row.col_name: row.data_type
        for row in spark_session.sql(
            f"DESCRIBE TABLE EXTENDED {CATALOG_NAME}.{schema}.ta"
        ).collect()
        if row.col_name
    }
    assert describe.get("Provider", "").lower() == "delta"

    spark_session.sql(
        f"CREATE TABLE {CATALOG_NAME}.{schema}.tb (id INT, tag STRING) "
        f"USING delta LOCATION 'file://{table_b}'"
    )
    spark_session.sql(f"INSERT INTO {CATALOG_NAME}.{schema}.tb VALUES (1, 'x'), (2, 'y')")

    joined = spark_session.sql(
        f"SELECT a.id, a.name, b.tag FROM "
        f"{CATALOG_NAME}.{schema}.ta a JOIN "
        f"{CATALOG_NAME}.{schema}.tb b ON a.id = b.id ORDER BY a.id"
    ).collect()
    assert [(r.id, r.name, r.tag) for r in joined] == [(1, "a", "x"), (2, "b", "y")]

    tables = {
        row.tableName
        for row in spark_session.sql(f"SHOW TABLES IN {CATALOG_NAME}.{schema}").collect()
    }
    assert {"ta", "tb"} <= tables


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Managed Delta via Spark does not reach soyuz's commit coordinator: "
        "Spark's Delta SQL extension intercepts `USING delta` DDL and reroutes "
        "it through `spark_catalog` (wired to DeltaCatalog in the fixture) "
        "before the UCSingleCatalog plugin is invoked. The analyzer "
        "short-circuits with SCHEMA_NOT_FOUND because `compat`/`mgd` are not "
        "schemas `spark_catalog` knows. ADR-0011 ships the "
        "passthrough Delta commit coordinator at POST /delta/preview/commits — "
        "it is correct per the UC spec and its full 200/400/409/422/429 matrix "
        "is exercised by tests/test_delta_commits.py — but it only serves "
        "clients that actually call that endpoint. Direct Delta Kernel clients "
        "do; the JVM Spark connector at its current (0.3.0) revision does not "
        "for managed Delta. This xfail flips to a real pass the day an upstream "
        "connector version wires Spark's Delta extension through UCSingleCatalog "
        "so that managed-Delta DDL reaches the configured UC catalog plugin. "
        "The upstream UC docs at docs/integrations/unity-catalog-spark.md carry "
        "a TODO ('we need to cover both parquet and delta') confirming the same "
        "gap from the other side."
    ),
)
def test_managed_delta_table_creation_via_spark(
    spark_session: SparkSession,
    module_live_server: str,
    tmp_path: Path,
) -> None:
    """Managed Delta table creation via Spark — pinned on the upstream connector gap.

    soyuz ships a fully-working Delta commit coordinator (ADR-0011),
    but the JVM ``UCSingleCatalog`` connector (``unitycatalog-spark``
    0.3.0) does not route Spark's managed-Delta DDL through the configured
    UC catalog plugin — Spark's Delta SQL extension intercepts the statement
    at analysis time and reroutes through ``spark_catalog``, so soyuz's
    coordinator is never consulted. The failure mode is
    ``[SCHEMA_NOT_FOUND] spark_catalog.mgd`` from Spark's analyzer, not any
    HTTP response from soyuz. See the xfail reason above for the full
    rationale.
    """
    schema = "mgd"
    warehouse = tmp_path / "warehouse_managed"
    bootstrap_catalog(module_live_server, f"file://{warehouse}", schema)

    spark_session.sql(f"CREATE TABLE {CATALOG_NAME}.{schema}.mt (id INT, name STRING) USING delta")
    spark_session.sql(f"INSERT INTO {CATALOG_NAME}.{schema}.mt VALUES (1, 'a')")
    rows = spark_session.sql(f"SELECT id, name FROM {CATALOG_NAME}.{schema}.mt").collect()
    assert [(r.id, r.name) for r in rows] == [(1, "a")]
