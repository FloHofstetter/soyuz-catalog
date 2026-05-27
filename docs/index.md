<!-- markdownlint-disable MD030 MD033 -->

<section class="soyuz-hero" markdown>

# soyuz-catalog

A clean Python reference implementation of the [Unity Catalog REST API spec](https://github.com/unitycatalog/unitycatalog).

</section>

FastAPI + SQLAlchemy. No JVM. No half-finished endpoints. The goal is a
complete, correct, fast metadata catalog server that other tools can talk to
— without the operational and behavioural rough edges of the official Java
reference implementation.

<div class="grid cards" markdown>

-   :material-shield-check:{ .lg .middle } **Spec-conformant**

    ---

    Faithful to `unitycatalog/api/all.yaml`. Every divergence from the
    Java reference is pinned by a regression test.

    [:octicons-arrow-right-24: Spec coverage](reference/spec-coverage.md)

-   :material-database-search:{ .lg .middle } **Metadata only**

    ---

    No table data, no credentials in transit, no enforcement —
    a metadata server that other tools authenticate against.

    [:octicons-arrow-right-24: Permissions model](concepts/permissions-model.md)

-   :material-puzzle:{ .lg .middle } **Eight extensions**

    ---

    Tags, lineage, declared constraints, audit log, effective
    permissions, connections, Delta REST, volume file IO.

    [:octicons-arrow-right-24: Extensions index](concepts/extensions-over-spec.md)

</div>

[Quickstart :material-rocket:](getting-started/quickstart.md){ .md-button .md-button--primary }
[REST API :material-api:](reference/api.md){ .md-button }
[GitHub :material-github:](https://github.com/FloHofstetter/soyuz-catalog){ .md-button }

<div class="soyuz-stats">
<div class="soyuz-stat"><strong>14</strong>spec-defined resources</div>
<div class="soyuz-stat"><strong>8</strong>over-the-spec extensions</div>
<div class="soyuz-stat"><strong>0</strong>silently dropped fields</div>
<div class="soyuz-stat"><strong>MIT</strong>pure-Python stack</div>
</div>

## Try it

=== "cURL"

    ```bash
    curl http://localhost:8000/api/2.1/unity-catalog/catalogs
    ```

=== "Python SDK"

    ```python
    from soyuz_catalog_client import Client
    from soyuz_catalog_client.api.catalogs import list_catalogs

    client = Client(base_url="http://localhost:8000")
    print([c.name for c in list_catalogs.sync(client=client).catalogs])
    ```

=== "Spark SQL"

    ```sql
    -- after configuring spark.sql.catalog.soyuz against
    -- http://localhost:8000 (see Spark integration guide)
    SHOW SCHEMAS IN soyuz;
    ```

## Works with these clients

<div class="grid cards" markdown>

-   :material-apache-kafka:{ .lg .middle } **[Apache Spark](integrations/spark.md)**

    ---

    JVM `unitycatalog-spark` connector for external Delta tables.

-   :material-language-rust:{ .lg .middle } **[delta-rs](integrations/delta-rs.md)**

    ---

    Rust/Python Delta Lake client via the Delta REST Catalog surface.

-   :material-chart-line:{ .lg .middle } **[MLflow](integrations/mlflow.md)**

    ---

    Registered Models as an MLflow Model Registry backend.

-   :material-language-python:{ .lg .middle } **[Python SDK](integrations/python-sdk.md)**

    ---

    The OpenAPI-generated client covering every soyuz route.

-   :material-language-java:{ .lg .middle } **[JVM client](integrations/jvm-client.md)**

    ---

    The official Java client shipped alongside Unity Catalog OSS.

</div>

## Why this exists

Unity Catalog (UC) is Databricks' table-metadata service. The REST API is
openly specified at [unitycatalog/unitycatalog](https://github.com/unitycatalog/unitycatalog),
and the OSS reference implementation is a Java server under
`unitycatalog/server/`. The Java server works for engines that only do
lookups, but several endpoints implement only part of the spec or behave
inconsistently with the JSON shapes the spec declares — concretely, a
`PATCH` with `{"properties": {}}` is a no-op rather than clearing
properties, unknown fields are silently dropped, and several edge cases
around table metadata are inconsistently populated.

soyuz-catalog is a second implementation of the same wire contract,
written in a stack that matches the Python data ecosystem, with the spec
treated as authoritative. Where soyuz and the Java server disagree, soyuz
diverges *toward* the spec, and every divergence is pinned by a regression
test. See [Divergences](divergences.md) and the
[Spec coverage map](reference/spec-coverage.md) for the concrete list.

On top of the spec, soyuz mirrors the Databricks-side extensions that real
clients expect — tags, lineage (OpenLineage), declared constraints,
connections (Lakehouse Federation), and a parallel Delta REST Catalog
surface. Each lives in an ADR and is excluded from the spec-conformance
gate so that spec-only clients see only the spec. See
[Extensions over the spec](concepts/extensions-over-spec.md).

## Status

The full spec-defined resource set is implemented. soyuz speaks the Unity
Catalog wire contract as a drop-in for compatible clients — the
[Python `unitycatalog` SDK](https://pypi.org/project/unitycatalog/), the
JVM `unitycatalog-spark` connector for external Delta,
[`delta-rs`](https://github.com/delta-io/delta-rs), and MLflow's Model
Registry.

**Spec-defined resources** — verbatim from `unitycatalog/api/all.yaml`:

| Resource              | Status        | Notes |
|-----------------------|---------------|-------|
| Catalogs              | ✅ Implemented | Full CRUD, foreign-catalog variant for Lakehouse Federation |
| Schemas               | ✅ Implemented | Full CRUD, cascade gate on delete |
| Tables                | ✅ Implemented | Create / read / delete (no `PATCH` — spec defines none) |
| Volumes               | ✅ Implemented | Full CRUD plus file IO under `/files` |
| Functions             | ✅ Implemented | Full CRUD |
| Registered Models     | ✅ Implemented | Full CRUD plus the model-version state machine |
| Permissions           | ✅ Implemented | Direct grants + inherited (effective) computation |
| Storage Credentials   | ✅ Implemented | Metadata-only — no token vending |
| External Locations    | ✅ Implemented | Metadata-only |
| Temporary Credentials | ✅ Stub        | Spec-conformant shape; no real STS / SAS / OAuth vending |
| Metastore Summary     | ✅ Implemented | |
| Staging Tables        | ✅ Implemented | |
| Delta Commits         | ✅ Implemented | Passthrough commit coordinator ([ADR-0011](adr/0011-delta-commit-coordinator.md)) |
| Delta REST Catalog    | ✅ Implemented | Secondary spec surface from `delta.yaml` ([ADR-0009](adr/0009-delta-rest-catalog-as-secondary-surface.md)) |

**Over-the-spec extensions** — supported by Databricks, absent from
UC OSS, mirrored here so Databricks-aware clients work end-to-end:

| Extension              | Status        | ADR |
|------------------------|---------------|-----|
| OpenLineage ingestion + traversal | ✅ Implemented | [ADR-0008](adr/0008-openlineage-as-lineage-contract.md) |
| Tags on securables    | ✅ Implemented | [ADR-0010](adr/0010-tags-as-extension.md) |
| Declared table constraints | ✅ Implemented | [ADR-0012](adr/0012-table-constraints.md) |
| Connections (Lakehouse Federation) | ✅ Implemented | [ADR-0013](adr/0013-connections-and-foreign-catalogs.md) |
| Audit log read API    | ✅ Implemented | — |
| Volume file IO        | ✅ Implemented | — |

**Explicitly out of scope** — metadata-only is design principle 3:

- Cloud credential vending (STS / SAS / OAuth)
- Query execution and federated query proxying
- Reading or writing Parquet / Delta file content (clients hit storage
  directly)

## Where to start

**New here?** Read [Concepts → Origin](concepts/origin.md) first, then
[Architecture](concepts/architecture.md). About 15 minutes.

**Want to run it?** [Getting Started → Installation](getting-started/installation.md)
takes you from `git clone` to a curl against `/catalogs` in five minutes.

**Looking up an endpoint?** [Reference → REST API](reference/api.md) or
the [Spec coverage map](reference/spec-coverage.md).

**Integrating a specific client?** See [Integrations](integrations/index.md)
for Spark, MLflow, delta-rs, and the Python SDK.

## Quick links

- [Getting Started](getting-started/installation.md)
- [Concepts](concepts/index.md)
- [Guides](guides/index.md) — including [HTTP walkthroughs](guides/walkthroughs/catalog-schema-table.md)
- [Admin runbooks](admin/index.md)
- [Integrations](integrations/index.md)
- [REST API reference](reference/api.md)
- [Spec coverage map](reference/spec-coverage.md)
- [Divergences from UC OSS](divergences.md)
- [Decisions (ADRs)](adr/README.md)
- [Contributing](development/contributing.md)
