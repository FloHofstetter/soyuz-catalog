<!-- markdownlint-disable MD030 -->
# Extensions over the spec

soyuz-catalog implements eight surfaces that do not exist in the
Unity Catalog OpenAPI document (`unitycatalog/api/all.yaml`). Each is
anchored in an Architecture Decision Record, mounted under a
distinct URL prefix so a spec-only client never sees it, and
explicitly excluded from the spec-conformance gate. The reason any
of them exist is the same: a real client (delta-rs, MLflow, an
OpenLineage producer, a JVM federation engine, an LLM agent runner)
expects the surface, and the Java reference does not provide it.

This page is the index. Each extension has its own concept page or
walkthrough — the deep dive lives there, not here.

<div class="grid cards" markdown>

-   :material-tag-multiple:{ .lg .middle } **Tags on securables**

    ---

    Key–value tags on catalogs, schemas, tables, columns. Survive
    parent rename via opaque IDs.

    [:octicons-arrow-right-24: Walkthrough](../guides/walkthroughs/tags.md)

-   :material-source-branch:{ .lg .middle } **Lineage (OpenLineage)**

    ---

    Ingest `RunEvent` payloads, walk upstream/downstream at dataset or
    column granularity.

    [:octicons-arrow-right-24: Concept](lineage.md)

-   :material-format-list-checks:{ .lg .middle } **Declared table constraints**

    ---

    PK / FK / CHECK / named NOT NULL as metadata. Engine validates,
    soyuz catalogs.

    [:octicons-arrow-right-24: Concept](table-constraints.md)

-   :material-database-arrow-left:{ .lg .middle } **Connections (Lakehouse Federation)**

    ---

    Typed references to external metadata sources, foreign catalogs
    backed by them.

    [:octicons-arrow-right-24: Walkthrough](../guides/walkthroughs/foreign-catalog.md)

-   :material-shield-account:{ .lg .middle } **Effective permissions**

    ---

    One call returns direct + inherited grants across the hierarchy.

    [:octicons-arrow-right-24: Concept](permissions-model.md#effective-permissions)

-   :material-source-commit:{ .lg .middle } **Delta REST Catalog**

    ---

    Parallel `/delta/v1/*` surface from `delta.yaml`, sharing storage
    with the UC API.

    [:octicons-arrow-right-24: Concept](delta-commits.md)

-   :material-clipboard-text-clock:{ .lg .middle } **Audit log read API**

    ---

    One row per successful mutation, filterable by `agent_run_id`.

    [:octicons-arrow-right-24: Concept](audit-log.md)

-   :material-file-multiple:{ .lg .middle } **Volume file IO**

    ---

    Single-node file IO under `/volumes/{name}/files/*` via a
    pluggable backend.

    [:octicons-arrow-right-24: Concept](volume-files.md)

</div>

## The extensions

### Tags on securables

A tag is a key + optional value attached to a catalog, schema, table,
or column. Tags survive rename of the parent (anchored on the opaque
ID) and are dropped only when the parent itself is force-deleted.
The PATCH shape is additive: a single request can `set` and `remove`
keys in one batch.

- Surface: `GET` / `PATCH` `/tags/<type>/<full_name>`
- ADR: [0010 — Tags as an extension](../adr/0010-tags-as-extension.md)
- Walkthrough: [Attaching tags](../guides/walkthroughs/tags.md)

### Lineage (OpenLineage)

soyuz speaks [OpenLineage](https://openlineage.io/) on the ingest
side. A producer (Spark, Airflow, dbt, a custom script) posts
`RunEvent` payloads; soyuz parses them into nodes (runs) and edges
(dataset reads and writes, optionally with column-level granularity)
and exposes traversal endpoints to walk upstream and downstream.

- Surface: `POST /lineage`, `GET /lineage/...`
- ADR: [0008 — OpenLineage as lineage contract](../adr/0008-openlineage-as-lineage-contract.md)
- Concept page: [Lineage](lineage.md)
- Walkthrough: [Posting and traversing lineage](../guides/walkthroughs/lineage.md)

### Declared table constraints

`PRIMARY KEY`, `FOREIGN KEY`, `CHECK`, and named `NOT NULL`
declarations as metadata-only rows on tables. soyuz stores and
returns them; the query engine validates.

- Surface: embedded in table responses; mutation through the Delta
  REST `UpdateTable` action union.
- Concept page: [Table constraints](table-constraints.md)
- ADR: [0012 — Table constraints](../adr/0012-table-constraints.md)
- Walkthrough: [Declared table constraints](../guides/walkthroughs/declared-constraints.md)

### Connections (Lakehouse Federation)

A connection is a typed reference to an external metadata source
(MySQL, Postgres, Snowflake, BigQuery, Redshift, …). Foreign catalogs
derive their schemas and tables from the connection rather than from
direct soyuz storage. The federation engine that resolves a foreign
catalog into actual rows lives elsewhere — soyuz stores the
connection metadata and the foreign-catalog mapping.

- Surface: `POST` `GET` `LIST` `PATCH` `DELETE` `/connections`;
  foreign catalogs use the existing catalog routes with a
  `connection_name` field.
- ADR: [0013 — Connections and foreign catalogs](../adr/0013-connections-and-foreign-catalogs.md)
- Walkthrough: [Foreign catalog from a connection](../guides/walkthroughs/foreign-catalog.md)

### Effective permissions

The dedicated `GET /effective-permissions/{type}/{full_name}` route
returns the union of direct grants on a securable and grants
inherited from every ancestor in the hierarchy, in one call. The
upstream spec defines the *concept* of effective permissions
(the `inherited_from_*` fields on Permission rows) but not the
dedicated route — that piece is soyuz-specific.

- Surface: `GET /effective-permissions/{type}/{full_name}`
- Concept page: [Permissions model § Effective permissions](permissions-model.md#effective-permissions)
- ADR: [0005 — Permissions without enforcement](../adr/0005-permissions-without-enforcement.md)
- Walkthrough: [Grants and effective permissions](../guides/walkthroughs/grants-and-effective.md)

### Delta REST Catalog (secondary surface)

A parallel REST surface defined in `delta.yaml`, designed for direct
Delta-Kernel clients that want catalog access without speaking the
full Unity Catalog API. soyuz exposes it under `/delta/v1/...`. Both
surfaces share the same storage, so a table created via the UC API
is readable via the Delta REST API and vice versa.

- Surface: `/delta/v1/*`
- ADR: [0009 — Delta REST Catalog as secondary surface](../adr/0009-delta-rest-catalog-as-secondary-surface.md)
- Integration: [delta-rs](../integrations/delta-rs.md)

### Audit log read API

soyuz writes one row per successful mutation and exposes them on a
single read endpoint with an `?agent_run_id=` cross-index for
agent-driven clients.

- Surface: `GET /audit-log`
- Concept page: [Audit log](audit-log.md)
- Divergence entry: [DIVERGENCES.md → Audit log](../divergences.md)

### Volume file IO

Four routes under `/volumes/{full_name}/files/*` that let single-node
deployments store and serve files without provisioning an object
store. Backed by a pluggable `VolumeFileBackend` protocol — today
the `file://` backend is implemented; cloud backends drop in as new
classes.

- Surface: `GET` / `POST` / `DELETE` `/volumes/{full_name}/files/*`
- Concept page: [Volume files](volume-files.md)
- Walkthrough: [Files API on a volume](../guides/walkthroughs/volume-files.md)
- Divergence entry: [DIVERGENCES.md → Volumes: file IO](../divergences.md)

## Why these, and not others

Three rules govern what becomes an extension.

1. **A real client expects it.** soyuz does not invent surfaces
   speculatively. Each extension was added because a known client
   (delta-rs, MLflow, an OpenLineage producer, a JVM federation
   engine, an LLM agent runner) relies on it.
2. **It does not break spec callers.** Extension routes live under
   distinct prefixes (`/tags`, `/lineage`, `/connections`,
   `/effective-permissions`, `/audit-log`, `/delta/v1`,
   `/volumes/{name}/files`) so a spec-only client never sees them.
3. **It has an ADR or divergence entry.** Every extension has a
   formal record explaining what alternatives were considered, why
   the chosen shape won, and what would force a redesign.

## See also

- [Spec is the contract](spec-is-the-contract.md) — how spec routes
  are kept honest while extensions live alongside.
- [Spec coverage map](../reference/spec-coverage.md) — the
  at-a-glance view of both spec routes and extensions.
- [Divergences](../divergences.md) — behaviour differences from the
  Java reference (extensions appear here when relevant).
