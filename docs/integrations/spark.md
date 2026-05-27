# Apache Spark

soyuz-catalog supports Apache Spark through the upstream JVM
[`unitycatalog-spark`](https://github.com/unitycatalog/unitycatalog/tree/main/connectors/spark)
connector (`io.unitycatalog.spark.UCSingleCatalog`) plugged into a Spark
session. Spark sees soyuz as just another Unity Catalog endpoint and
reaches it through the standard UC REST surface.

This page is the human-readable twin of
[`tests/test_spark_compatibility.py`](https://github.com/FloHofstetter/soyuz-catalog/blob/main/tests/test_spark_compatibility.py).
Every "works" row below corresponds to a parametrised case in that file
— grep the case ids to jump from a row here to the exact assertion.

## TL;DR

**soyuz is spec-complete for every Spark surface the JVM `UCSingleCatalog`
connector can actually reach.** External Delta tables, schema DDL,
reads, writes, joins, drops — all work end-to-end against soyuz.

The remaining "no" rows are **upstream** connector limitations: the
connector throws `UnsupportedOperationException` for `ALTER` and
`RENAME`, ships no `VolumesApi` for `CREATE VOLUME`, and Spark's own
Delta SQL extension intercepts `USING delta` DDL before the UC plugin is
invoked (so Spark's managed-Delta path never reaches soyuz's commit
coordinator). Any client that *does* reach the coordinator — a direct
Delta-Kernel client, `delta-rs`, or a future connector revision that
wires managed-Delta DDL through the configured UC catalog — gets the
full feature.

The full
[`POST /delta/preview/commits`](../guides/walkthroughs/delta-commit.md)
contract (200 / 400 / 409 / 422 / 429) is implemented and
regression-pinned at the HTTP level.

## Configuring Spark

A typical Spark session configuration:

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
        .appName("soyuz-demo")
        .config("spark.sql.catalog.soyuz",                   "io.unitycatalog.spark.UCSingleCatalog")
        .config("spark.sql.catalog.soyuz.uri",               "http://localhost:8000")
        .config("spark.sql.catalog.soyuz.token",             "<unused>")
        .config("spark.sql.extensions",                      "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog",           "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.jars.packages",
                "io.unitycatalog:unitycatalog-spark_2.13:0.4.0,io.delta:delta-spark_2.13:3.2.0")
        .getOrCreate()
)
```

The connector treats the `token` field as a bearer token in the
`Authorization: Bearer` header. soyuz has no auth surface so any string
is accepted; in production the proxy in front of soyuz consumes the
token.

## Category A — Operations that work

Regression-pinned. If any of these starts raising, the compatibility
test fails loudly.

- `SHOW SCHEMAS IN soyuz` — case `A-show-schemas`
- `DESCRIBE SCHEMA soyuz.<schema>` — case `A-describe-schema`
- `CREATE TABLE soyuz.<schema>.<t> (…) USING delta LOCATION 'file://…'`
  — case `A-create-external-delta`
- `INSERT INTO …` against an external Delta table — case
  `A-insert-external-delta`
- `SELECT … FROM …` against an external Delta table — case
  `A-select-external-delta`
- `DESCRIBE TABLE EXTENDED …` — case `A-describe-table-extended`
- `SHOW TABLES IN soyuz.<schema>` — case `A-show-tables`
- Two-table `JOIN` across external Delta tables — case
  `A-join-two-external-delta`
- `DROP TABLE …` on an external Delta table — case
  `A-drop-external-delta`

`CREATE SCHEMA` and `DROP SCHEMA` through Spark SQL also work — they
map to the standard `POST/DELETE /schemas` routes. The compatibility
fixture seeds the test schema via a direct HTTP call so the
arrange/act/assert boundary stays clean.

## Category B — soyuz-blocked by design

Currently empty. The `EXPECTED_501` outcome constant in the test suite
is kept alive for future cases. Cloud credential vending is still out of
scope, but `UCSingleCatalog` does not exercise it on local-filesystem
warehouses, so the matrix has no case for it. The `temporary-table-
credentials` path returns a local passthrough for `file://`, which is
why external Delta works against a local warehouse.

## Category C — Upstream JVM connector limitations

These are *not* soyuz gaps. `UCSingleCatalog` raises
`UnsupportedOperationException` (or never wires up the API at all)
before any HTTP call reaches soyuz. The compatibility test pins each one
so a connector upgrade that lifts a limitation fails the matrix and
forces a conscious re-categorisation.

- **`ALTER TABLE … ADD COLUMN` / any `ALTER TABLE` variant** — the
  connector throws `UnsupportedOperationException("Altering a table is
  not supported yet")` at the SQL planner. Case:
  `C-alter-table-add-column`.
- **`ALTER TABLE … RENAME TO …`** — same exception, different message.
  Case: `C-alter-table-rename`.
- **Volumes (`CREATE VOLUME`, `SHOW VOLUMES`, …)** — `UCSingleCatalog`
  does not instantiate a `VolumesApi`. Spark's stock SQL parser (no
  volume grammar extension is registered) rejects the statement with
  `PARSE_SYNTAX_ERROR`. Case: `C-create-volume`.
- **Managed Delta tables (`CREATE TABLE … USING delta` without
  `LOCATION`)** — Spark's Delta SQL extension intercepts `USING delta`
  DDL at analysis time and reroutes it through `spark_catalog`
  (configured as `DeltaCatalog` per the upstream UC recipe), which does
  not know about the UC-registered schema. The analyzer fails with
  `SCHEMA_NOT_FOUND` before the UC plugin is invoked — Spark's catalog
  plugin never gets a chance to call `POST /delta/preview/commits` on
  soyuz. This is an upstream Spark + Delta + connector integration
  issue. The coordinator contract is exercised end-to-end by direct
  HTTP in `tests/test_delta_commits.py`. Case: `C-managed-delta-insert`.
- **`MERGE` / `UPDATE` / `DELETE` on Delta tables** — work via Delta's
  own path-based writer when the table is external. They are not in the
  compatibility matrix because the read/write gate already exercises the
  same write path.

## Category D — Delta REST Kernel is not reached by Spark

soyuz exposes a parallel Delta-Kernel REST surface under `/delta/v1/…`
([ADR-0009](../adr/0009-delta-rest-catalog-as-secondary-surface.md)).
**Spark does not reach it.** `UCSingleCatalog` routes table reads
through the standard UC `getTable` call and then hands off to Spark's
path-based Delta reader, which opens the `_delta_log` directory
directly. There is no Spark SQL statement that causes the connector to
call `/delta/v1/…`.

This is not a bug. The Delta REST surface targets a *different client
population* — direct Delta-Kernel clients that want the REST coordinator
surface without running a full Spark session. Both surfaces share the
same storage layer, so a table created via the standard UC API is
readable via the Delta REST API and vice versa.

## How this page stays honest

Every Category A entry above corresponds to a `WORKS` case in
[`tests/test_spark_compatibility.py`](https://github.com/FloHofstetter/soyuz-catalog/blob/main/tests/test_spark_compatibility.py).
Every Category C entry is an `EXPECTED_CONNECTOR_THROW` case. Category B
is currently empty. The test runs under `pytest -m integration` and
requires the `spark` optional extra —
`pytest.importorskip("pyspark")` gates collection so the default suite
stays green.

If a future connector revision changes what Spark can do against soyuz
— either flipping a Category C row or introducing a Category B
regression — update both this page and the test matrix in the same
commit. The regression net only pays rent if it stays in sync with the
prose.

## See also

- [Concepts → Delta commit handling](../concepts/delta-commits.md)
- [ADR-0009 — Delta REST Catalog as secondary surface](../adr/0009-delta-rest-catalog-as-secondary-surface.md)
- [ADR-0011 — Delta commit coordinator](../adr/0011-delta-commit-coordinator.md)
- [delta-rs integration](delta-rs.md) — the Python path that does reach
  the coordinator.
