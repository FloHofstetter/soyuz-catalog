# Services

Business logic for soyuz-catalog resources. Services are sync, take an
explicit SQLAlchemy `Session`, and raise the domain exceptions defined in
`soyuz_catalog.exceptions`.

## Catalog service

::: soyuz_catalog.services.catalog_service

## Schema service

::: soyuz_catalog.services.schema_service

## Table service

::: soyuz_catalog.services.table_service

## Volume service

::: soyuz_catalog.services.volume_service

## Credential service

::: soyuz_catalog.services.credential_service

## External location service

::: soyuz_catalog.services.external_location_service

## Connection service

::: soyuz_catalog.services.connection_service

## Function service

::: soyuz_catalog.services.function_service

## Registered model service

::: soyuz_catalog.services.registered_model_service

## Model version service

::: soyuz_catalog.services.model_version_service

## Temporary credentials service

::: soyuz_catalog.services.credentials_service

## Metastore service

::: soyuz_catalog.services.metastore_service

## Staging table service

::: soyuz_catalog.services.staging_table_service

## Permissions service

::: soyuz_catalog.services.permissions_service

## Delta commits service

::: soyuz_catalog.services.delta_commits_service

## Delta REST Catalog service

Translation layer between the Delta REST Catalog API (upstream
`delta.yaml`) and soyuz' existing `Table` / `StagingTable` storage.
Every function here wraps or delegates to the main `table_service` /
`staging_table_service`; there is no separate Delta storage model.
See [ADR-0009](../../adr/0009-delta-rest-catalog-as-secondary-surface.md)
for the design and `DIVERGENCES.md` under **Delta REST Catalog API**
for the wire-level divergences.

::: soyuz_catalog.services.delta_rest_service

## Lineage service

Over-the-spec extension: OpenLineage event ingestion and graph
traversal. Upstream Unity Catalog OSS has no lineage; see
[ADR-0008](../../adr/0008-openlineage-as-lineage-contract.md) for the
rationale and `DIVERGENCES.md` under **Lineage** for the wire-level
divergences.

::: soyuz_catalog.services.lineage_service

## Tags service

Over-the-spec extension: key/value tags on catalogs, schemas, tables,
and columns. Databricks supports tags but UC OSS and `all.yaml` do
not; see [ADR-0010](../../adr/0010-tags-as-extension.md) for the
rationale and `DIVERGENCES.md` under **Tags** for the wire-level
divergences.

::: soyuz_catalog.services.tags_service

## Table constraints service

Over-the-spec extension: declared `PRIMARY KEY`, `FOREIGN KEY`,
`CHECK`, and named `NOT NULL` constraints on tables. Databricks
supports them but UC OSS / `all.yaml` do not; see
[ADR-0012](../../adr/0012-table-constraints.md) for the rationale
and `DIVERGENCES.md` under **Table constraints** for the
metadata-only posture and wire shape.

::: soyuz_catalog.services.constraints_service

## Keyset pagination helpers

Shared list-pagination helpers used by every `list_*` service call
(`list_catalogs`, `list_schemas`, `list_tables`, `list_volumes`).
Lives outside the `services/` package because it has no DB schema
knowledge of its own — it takes a prebuilt `select(Model).where(...)`
and a model class and returns the same statement with the keyset
cursor, ORDER BY, and LIMIT applied. See
[ADR-0003](../../adr/0003-keyset-pagination.md) for the design
rationale.

::: soyuz_catalog.pagination

## Storage URI parser

Shared write-path helper used by every create-resource service to
validate `storage_location` / `storage_root` scheme. Lives outside the
`services/` package because it has no DB or FastAPI dependency.

::: soyuz_catalog.storage.uri
