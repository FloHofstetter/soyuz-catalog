<!-- markdownlint-disable MD030 -->
# Admin

Runbooks for running soyuz-catalog in production. The pages here assume the
operator already has a working soyuz instance from the
[Getting Started](../getting-started/installation.md) section.

<div class="grid cards" markdown>

-   :material-server-network:{ .lg .middle } **[Deployment](deployment.md)**

    ---

    Process model, reverse-proxy TLS, healthcheck, systemd and Docker
    patterns.

-   :material-database:{ .lg .middle } **[Backends (SQLite vs Postgres)](backends.md)**

    ---

    Which backend to use, how to size the connection pool, SQLite WAL
    caveats.

-   :material-cog:{ .lg .middle } **[Configuration](configuration.md)**

    ---

    Environment-driven configuration with task-oriented examples. The
    exhaustive per-variable list lives in the
    [Settings reference](../reference/settings.md).

-   :material-chart-timeline-variant:{ .lg .middle } **[Observability and audit log](observability.md)**

    ---

    Request logs, audit trail, metrics that matter for a metadata
    server.

</div>
