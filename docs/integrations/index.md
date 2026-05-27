<!-- markdownlint-disable MD030 -->
# Integrations

soyuz-catalog implements the Unity Catalog REST contract, so any client
written against that contract works without modification. The pages here
document the clients that have been exercised against soyuz, the endpoints
they touch, and the known limitations of each one.

<div class="grid cards" markdown>

-   :material-apache-kafka:{ .lg .middle } **[Apache Spark](spark.md)**

    ---

    The JVM `unitycatalog-spark` connector for external Delta tables.

-   :material-language-rust:{ .lg .middle } **[delta-rs and python-delta](delta-rs.md)**

    ---

    The Rust/Python Delta Lake client, reaching soyuz through the
    Delta REST Catalog surface.

-   :material-chart-line:{ .lg .middle } **[MLflow Tracking](mlflow.md)**

    ---

    Registered Models as an MLflow Model Registry backend.

-   :material-language-python:{ .lg .middle } **[Python SDK (generated client)](python-sdk.md)**

    ---

    The in-tree OpenAPI-generated client covering every soyuz route.

-   :material-language-java:{ .lg .middle } **[JVM unitycatalog client](jvm-client.md)**

    ---

    The official Java client shipped alongside Unity Catalog OSS.

</div>

## How a new integration fits

A new client should not need any soyuz-side change. If it speaks the spec
([coverage map](../reference/spec-coverage.md)), it works. If it relies on
an over-the-spec surface (tags, lineage, connections), soyuz already mirrors
the Databricks-side shape — see [Extensions over the spec](../concepts/extensions-over-spec.md).

If you hit a divergence that breaks a client, file it as a bug — soyuz
treats the [OpenAPI spec](https://github.com/unitycatalog/unitycatalog/blob/main/api/all.yaml)
as the contract, not the Java reference implementation.
