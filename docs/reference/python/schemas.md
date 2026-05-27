# Pydantic Schemas

Request and response schemas for the REST API.

## Main UC API (`all.yaml` surface)

::: soyuz_catalog.api.schemas

## Delta REST Catalog API (`delta.yaml` surface)

Native Delta protocol wire shapes for the secondary Delta REST
Catalog surface — see
[ADR-0009](../../adr/0009-delta-rest-catalog-as-secondary-surface.md).
Every model uses `ConfigDict(extra="forbid", populate_by_name=True)`
with kebab-case `Field(alias=…)` so Python stays snake_case while
the wire matches the spec.

::: soyuz_catalog.api.delta_schemas
