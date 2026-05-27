<!-- markdownlint-disable MD030 -->
# Guides

Task-oriented pages. Each guide walks one concrete job from start to finish.
For the conceptual *why* behind these workflows, see [Concepts](../concepts/index.md);
for the wire-level surface, see [REST API reference](../reference/api.md).

## Operational guides

<div class="grid cards" markdown>

-   :material-database-arrow-right:{ .lg .middle } **[Backing soyuz with Postgres](backing-with-postgres.md)**

    ---

    Switch from the default SQLite to a Postgres-backed deployment.

-   :material-database-sync:{ .lg .middle } **[Migrations with Alembic](migrations.md)**

    ---

    Running, generating, and rolling back schema migrations.

-   :material-backup-restore:{ .lg .middle } **[Backup and restore](backup-restore.md)**

    ---

    Patterns for both backends.

-   :material-help-circle:{ .lg .middle } **[Troubleshooting and FAQ](troubleshooting.md)**

    ---

    Common errors with their causes and fixes.

</div>

## HTTP walkthroughs

Deterministic curl/httpie sequences. Each step lists the exact request and
the expected response, so a fresh shell against a fresh server reproduces
the result. Useful as live documentation and as a learning tour.

<div class="grid cards" markdown>

-   :material-console:{ .lg .middle } **1. [Catalog → schema → table](walkthroughs/catalog-schema-table.md)**

    ---

    Build the three-level resource hierarchy with curl.

-   :material-console:{ .lg .middle } **2. [Attaching tags](walkthroughs/tags.md)**

    ---

    Add and remove tags on a securable, rename-safe.

-   :material-console:{ .lg .middle } **3. [Declared table constraints](walkthroughs/declared-constraints.md)**

    ---

    Set PK + FK + named NOT NULL via the Delta REST surface.

-   :material-console:{ .lg .middle } **4. [Posting and traversing lineage](walkthroughs/lineage.md)**

    ---

    Emit an OpenLineage event and walk upstream/downstream.

-   :material-console:{ .lg .middle } **5. [Posting a Delta commit](walkthroughs/delta-commit.md)**

    ---

    Drive the passthrough coordinator end-to-end.

-   :material-console:{ .lg .middle } **6. [Grants and effective permissions](walkthroughs/grants-and-effective.md)**

    ---

    PATCH a grant and read it back through the effective view.

-   :material-console:{ .lg .middle } **7. [Querying the audit log](walkthroughs/audit-log.md)**

    ---

    Drive `X-Principal` + `X-Agent-Run-Id` and filter the audit feed.

-   :material-console:{ .lg .middle } **8. [Foreign catalog from a connection](walkthroughs/foreign-catalog.md)**

    ---

    Wire a Lakehouse-Federation foreign catalog from scratch.

-   :material-console:{ .lg .middle } **9. [Files API on a volume](walkthroughs/volume-files.md)**

    ---

    Upload, download, and delete bytes through the volume IO routes.

</div>
