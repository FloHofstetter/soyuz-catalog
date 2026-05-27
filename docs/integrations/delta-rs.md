# delta-rs and python-delta

[`delta-rs`](https://github.com/delta-io/delta-rs) is the Rust
implementation of the Delta Lake protocol with a Python binding
(`deltalake`). Unlike Spark, it does not need a JVM, runs in any Python
process, and speaks the Delta REST Catalog protocol directly. soyuz's
[Delta REST Catalog](../adr/0009-delta-rest-catalog-as-secondary-surface.md)
surface exists primarily for this client population.

## What it talks to

delta-rs reaches soyuz through two surfaces:

1. **Standard Unity Catalog REST** (`/api/2.1/unity-catalog/...`) — for
   catalog/schema/table discovery, the same routes Spark uses.
2. **Delta REST Catalog** (`/delta/v1/...`) — for the commit coordinator
   and managed Delta read paths. This is the surface defined in
   `unitycatalog/api/delta.yaml`.

A delta-rs client typically:

1. Looks up the table via the UC REST surface to resolve its
   `storage_location`.
2. Reads the Delta log file directly from that location.
3. When writing, either drives the commit coordinator via
   `/delta/preview/commits` or `/delta/v1/...` (managed) or writes
   directly to the log (external + own coordination).

soyuz never reads or writes the Delta log file. The coordinator role is
passthrough — see
[Concepts → Delta commit handling](../concepts/delta-commits.md).

## Reading an external Delta table

The standard path:

```python
from deltalake import DeltaTable

dt = DeltaTable(
    "file:///tmp/lake/bronze/events",
    storage_options=None,
)
df = dt.to_pandas()
```

This reads the table directly from its filesystem location. delta-rs
does not call soyuz at all in this code path — the table location was
discovered out-of-band (configuration file, environment variable,
manual lookup against soyuz).

To wire in soyuz as the catalog, use the UC client:

```python
from unitycatalog.client import ApiClient, Configuration
from unitycatalog.client.api import TablesApi

config = Configuration(host="http://localhost:8000/api/2.1/unity-catalog")
client = ApiClient(configuration=config)
tables = TablesApi(client)

info = tables.get_table("lake.bronze.events")
dt = DeltaTable(info.storage_location)
df = dt.to_pandas()
```

soyuz is the metadata source; delta-rs handles the data.

## Writing a managed Delta table

When a client wants soyuz to coordinate writes, it uses
`/delta/preview/commits` for each version. delta-rs has support for the
coordinator pattern; see
[Walkthrough: posting a Delta commit](../guides/walkthroughs/delta-commit.md)
for the bare HTTP form and the
[delta-rs documentation](https://delta-io.github.io/delta-rs/) for the
Python API.

The high-level flow:

```python
from deltalake import write_deltalake
import pyarrow as pa

table = pa.table({"id": [1, 2, 3], "payload": ["a", "b", "c"]})

write_deltalake(
    "file:///tmp/lake/bronze/events",
    table,
    mode="append",
    # …plus coordinator configuration when using managed Delta.
)
```

For external tables, `write_deltalake` does not need to call soyuz —
the writer owns the coordination via the file lock on `_delta_log/`. For
managed tables, the coordinator is required so concurrent writers do not
race.

## Why this integration is cleaner than Spark

Three reasons delta-rs reaches more of soyuz than Spark does:

1. **No SQL parser intercepting `USING delta`.** delta-rs is a library,
   not a SQL engine. The client decides which catalog to call; there is
   no "managed Delta is rerouted to `spark_catalog`" failure mode.
2. **Direct coordinator calls.** delta-rs implements the `/delta/v1`
   surface explicitly; the JVM Spark connector does not.
3. **Pure Python, no JVM.** Easier to deploy and debug in the same
   process as soyuz, especially during development.

The flip side is that delta-rs covers a narrower feature surface than
Spark — `MERGE`, complex catalog queries, and full SQL semantics are
not its target.

## When to use delta-rs

- You want managed Delta writes through soyuz without a JVM.
- Your producer/consumer code is already Python.
- You need to drive the commit coordinator explicitly (e.g. from an
  ETL framework like Airflow or Dagster).

## When *not* to use delta-rs

- You need full SQL with `MERGE`, window functions, complex joins.
- Your existing pipeline is on Spark and the JVM cost is paid already.
- You need the Spark catalyst optimizer.

## See also

- [Concepts → Delta commit handling](../concepts/delta-commits.md)
- [ADR-0009](../adr/0009-delta-rest-catalog-as-secondary-surface.md)
- [Walkthrough: posting a Delta commit](../guides/walkthroughs/delta-commit.md)
- [delta-rs project](https://github.com/delta-io/delta-rs)
- [Apache Spark integration](spark.md) — the JVM alternative.
