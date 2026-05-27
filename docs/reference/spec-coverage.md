# Unity Catalog spec coverage map

This page is the answer to *"which parts of the Unity Catalog REST API does
soyuz-catalog actually implement, and how completely?"*. It is the contract
view — the row labels are the resource families in the
[`unitycatalog/api/all.yaml`](https://github.com/unitycatalog/unitycatalog/blob/main/api/all.yaml)
OpenAPI document, not soyuz's own routing tree.

A green ✅ means the spec endpoint exists at the wire level and returns the
shape the spec defines. Where soyuz's behaviour intentionally diverges from
the Java reference implementation, the row links to the relevant
[divergence](../divergences.md). Where soyuz adds endpoints outside the spec,
they are listed under [Over-the-spec extensions](#over-the-spec-extensions)
below, not folded into spec rows.

## Spec-defined resources

| Spec resource | Endpoints | soyuz status | Notes |
|---|---|---|---|
| **Catalogs** | `POST` `GET` `LIST` `PATCH` `DELETE` | ✅ Full | Plus the foreign-catalog variant for [Lakehouse Federation](../adr/0013-connections-and-foreign-catalogs.md). `PATCH` with empty `properties={}` clears rather than no-ops ([divergence](../divergences.md)). |
| **Schemas** | `POST` `GET` `LIST` `PATCH` `DELETE` | ✅ Full | Cascade gate on `DELETE` rejects non-empty schemas unless the spec's `force=true` flag is set. |
| **Tables** | `POST` `GET` `LIST` `DELETE` | ✅ Full | No `PATCH` — the spec defines none, table metadata is immutable after create. Staging tables live under a separate resource. |
| **Columns** | embedded in Table | ✅ Full | `type_text`, `type_json`, `type_name`, `position`, `nullable`, `partition_index`, comment, mask. |
| **Volumes** | `POST` `GET` `LIST` `PATCH` `DELETE` | ✅ Full | Plus over-the-spec [file IO routes](../divergences.md) for single-node deployments. |
| **Functions** | `POST` `GET` `LIST` `DELETE` | ✅ Full | SQL routine metadata; no execution surface. |
| **Registered Models** | `POST` `GET` `LIST` `PATCH` `DELETE` | ✅ Full | Plus the model-version state machine (`POST /models/{name}/versions`, `PATCH /models/{name}/versions/{version}`, status transitions). |
| **Permissions** | `GET` / `PATCH` `/permissions/<type>/<full_name>` | ✅ Full | Direct grants only. soyuz does not *enforce* — see [ADR-0005](../adr/0005-permissions-without-enforcement.md). The dedicated effective-permissions traversal route is listed under [Over-the-spec extensions](#over-the-spec-extensions) because the spec defines the concept but not the route. |
| **Storage Credentials** | `POST` `GET` `LIST` `PATCH` `DELETE` | ✅ Metadata-only | Names, principals, references — no actual cloud key material stored; no token vending. |
| **External Locations** | `POST` `GET` `LIST` `PATCH` `DELETE` | ✅ Metadata-only | URL + credential reference, no path validation against live storage. |
| **Temporary Credentials** | `POST` per resource type | ✅ Stub shape | Spec-conformant request/response shape; the implementation returns a placeholder rather than minting real STS/SAS/OAuth tokens. See [Concepts → Credentials](../concepts/credentials.md). |
| **Metastore Summary** | `GET /metastore_summary` | ✅ Full | |
| **Staging Tables** | `POST` `GET` `DELETE` | ✅ Full | Two-phase write pattern used by external writers. |
| **Delta Commits** | `POST /delta/preview/commits` | ✅ Passthrough | Coordinator behaviour clarified in [ADR-0011](../adr/0011-delta-commit-coordinator.md). |
| **Delta REST Catalog** | secondary surface under `/delta/v1/*` | ✅ Full | See [ADR-0009](../adr/0009-delta-rest-catalog-as-secondary-surface.md). |

## Over-the-spec extensions

The spec does not cover these surfaces; soyuz adds them because real
Databricks-aware clients expect them. Each is anchored in an ADR and a
divergence entry.

| Extension | Surface | ADR |
|---|---|---|
| Tags on securables | `GET` / `PATCH` `/tags/<type>/<full_name>` | [ADR-0010](../adr/0010-tags-as-extension.md) |
| OpenLineage ingestion + traversal | `POST /lineage`, `GET /lineage/...` | [ADR-0008](../adr/0008-openlineage-as-lineage-contract.md) |
| Declared table constraints | embedded in Table responses + Delta-schemas surface | [ADR-0012](../adr/0012-table-constraints.md) |
| Connections (Lakehouse Federation) | `POST` `GET` `LIST` `PATCH` `DELETE` `/connections` plus foreign-catalog variant | [ADR-0013](../adr/0013-connections-and-foreign-catalogs.md) |
| Effective permissions traversal | `GET /effective-permissions/<type>/<full_name>` | [ADR-0005](../adr/0005-permissions-without-enforcement.md) |
| Audit log read API | `GET /audit-log` | [Divergence: audit log](../divergences.md) |
| Volume file IO | `GET` / `POST` / `DELETE` `/volumes/{full_name}/files/*` | [Divergence: volumes file IO](../divergences.md) |

## Out of scope by design

Three categories of functionality are deliberately *not* implemented and
will not be added without a redesign. They are inherent to soyuz's role as
a metadata server.

- **Cloud credential vending.** Soyuz never mints STS, SAS, or OAuth tokens.
  Clients fetch credentials from their cloud SDK and pass them to soyuz at
  rest as metadata only.
- **Query execution and federated query proxying.** Soyuz tells clients
  *where* data lives; it does not run queries or proxy them through.
- **Reading or writing Parquet/Delta file content.** Engines (Spark,
  delta-rs, Trino) hit object storage directly. Soyuz never opens
  `_delta_log` or a Parquet footer.

## How this map stays honest

The `tests/test_openapi_conformance.py` suite walks every path in
`unitycatalog/api/all.yaml` and asserts that soyuz mounts it (or skips it
with an explicit divergence reason). A new spec path that is unimplemented
fails CI. A soyuz path that is not in the spec must either match an
extension in this map or be added to it.

## See also

- [REST API reference](api.md) — request/response details per route.
- [UC OSS compatibility](uc-oss-compatibility.md) — point-in-time
  compatibility snapshot vs the Java reference.
- [Divergences](../divergences.md) — behaviour differences, all
  spec-justified.
