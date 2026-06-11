# REST API Reference

soyuz-catalog implements the Unity Catalog REST API. All routes are mounted
under the prefix `/api/2.1/unity-catalog` (configurable via
`SOYUZ_API_PREFIX`). The wire contract follows the OpenAPI spec at
[`unitycatalog/api/all.yaml`](https://github.com/unitycatalog/unitycatalog/blob/main/api/all.yaml).
Where soyuz diverges from UC OSS, see [Divergences](../divergences.md).

## Pagination

Every list endpoint (`GET /catalogs`, `GET /schemas`, `GET /tables`,
`GET /volumes`) supports keyset pagination via two query parameters:

- `max_results` (int, optional) — page size, default `100`, capped at
  `1000`. Out-of-range values return `422`.
- `page_token` (string, optional) — opaque cursor from the previous
  call's `next_page_token`. Omit on the first page.

Every list response carries a `next_page_token` field. When it is
non-`null` the caller should pass it as `page_token` on the next
request; when it is `null` the current page is the last one.

Results are ordered by `(created_at ASC, id ASC)` — insertion order,
with the UUID `id` as a deterministic tiebreaker. This is a change
from earlier alphabetical ordering; see
[Divergences](../divergences.md).

Tampered or unparseable `page_token` values are rejected with
`400 INVALID_ARGUMENT` rather than silently treated as "start over".
Clients should treat the token as fully opaque — its shape is not
stable across soyuz versions. See
[ADR-0003](../adr/0003-keyset-pagination.md) for the design
rationale.

## Storage URIs

Every `storage_root` (on catalogs and schemas) and every
`storage_location` (on tables and volumes) is parsed at write time and
rejected with HTTP 400 `INVALID_ARGUMENT` unless its scheme is one of:

- `file` — local filesystem (used by the delta-rs integration tests).
- `s3` / `s3a` — AWS S3, including the Hadoop-style `s3a` variant.
- `abfss` — Azure Data Lake Storage Gen2.
- `gs` — Google Cloud Storage.

Missing schemes (e.g. a bare `/tmp/foo`) and empty strings are rejected
the same way. Read paths are deliberately not validated, so rows
written before this rule was introduced continue to load. UC OSS Java
accepts any string here — see
[Divergences](../divergences.md).

## Catalogs

A **catalog** is the top-level namespace in Unity Catalog. It contains
schemas, which contain tables and volumes.

### `POST /catalogs`

Create a new catalog.

**Request body** (`CreateCatalog`):

| Field             | Type                  | Required | Notes                                                   |
|-------------------|-----------------------|----------|---------------------------------------------------------|
| `name`            | string                | yes      | Catalog name (unique)                                   |
| `comment`         | string                | no       | Free-form description                                   |
| `properties`      | map<string,string>    | no       | Arbitrary key-value metadata                            |
| `storage_root`    | string                | no       | Storage root URL (managed catalogs only)                |
| `type`            | `MANAGED` \| `FOREIGN`| no       | Defaults to `MANAGED`. See [Connections](#connections). |
| `connection_name` | string                | no       | Required when `type=FOREIGN`                            |
| `options`         | map<string,string>    | no       | Connector options (foreign catalogs)                    |

**Response**: `200 OK` with a `CatalogInfo` body. When `storage_root`
is supplied, the response also carries a derived
`storage_location` of the form
`{storage_root}/__unitystorage/catalogs/{id}` — see
[Managed storage location](#managed-storage-location) below.

For foreign catalogs the response reconstructs `connection_name`
from the live connection row so a connection rename propagates
automatically; `storage_root` / `storage_location` stay `null`
and `type` reads back as `FOREIGN`.

**Errors**:

- `409 ALREADY_EXISTS` — a catalog with the same name already exists.
- `422` — the request body is malformed or contains unknown fields.
- `400 INVALID_ARGUMENT` — `storage_root` uses an unsupported URI
  scheme. See [Storage URIs](#storage-uris). Also raised on mixed
  managed/foreign shapes: `type=FOREIGN` without `connection_name`,
  `type=FOREIGN` with `storage_root`, or `type=MANAGED` (explicit
  or default) with `connection_name`.
- `404 NOT_FOUND` — `type=FOREIGN` with a `connection_name` that
  does not resolve to an existing connection.

#### Managed storage location

`CatalogInfo.storage_location` is derived on create from
`storage_root` plus the opaque catalog `id`, matching the UC OpenAPI
spec example `s3://bucket/ucroot/__unitystorage/catalogs/{id}`. The
derivation is keyed on `id`, not `name`, so **a rename does not
recompute the path**: any child resource whose physical layout
depends on the managed location stays valid after
`PATCH /catalogs/{name}` with a `new_name`. When `storage_root` is
`None` the derived `storage_location` is `None` as well. The same
rule applies to `SchemaInfo.storage_location`, which derives from
the schema's own `storage_root` if set and otherwise falls back to
the parent catalog's `storage_root`. See
[Divergences](../divergences.md) for the full rationale.

### `GET /catalogs`

List catalogs with keyset pagination. See [Pagination](#pagination)
for the shared `max_results` / `page_token` / `next_page_token`
contract.

**Response**: `200 OK` with `{"catalogs": [...], "next_page_token": ...}`.

### `GET /catalogs/{name}`

Fetch a single catalog.

**Response**: `200 OK` with a `CatalogInfo` body, or `404 NOT_FOUND`.

### `PATCH /catalogs/{name}`

Update an existing catalog. Replace-style semantics: any field present in the
request body is written to the row; fields absent from the body are left
untouched.

**Request body** (`UpdateCatalog`):

| Field             | Type               | Notes                                                    |
|-------------------|--------------------|----------------------------------------------------------|
| `new_name`        | string             | Rename to this name                                      |
| `comment`         | string             | Replace the comment                                      |
| `properties`      | map<string,string> | Replace the entire properties map (incl. `{}`)           |
| `connection_name` | string             | Rebind a foreign catalog (rejected on managed catalogs)  |
| `options`         | map<string,string> | Replace the connector options map (foreign catalogs)     |

!!! note "UC OSS bug fix"
    `PATCH {"properties": {}}` **clears all properties** in soyuz, where UC OSS
    treats it as a no-op. See [Divergences](../divergences.md).

!!! note "UC OSS bug fix"
    Unknown or read-only fields (e.g. `owner`) return `422` instead of being
    silently dropped. See [Divergences](../divergences.md).

!!! note "Type is immutable"
    `type` is **not** a PATCH field. Flipping a managed catalog to
    foreign (or vice versa) has no defined semantics — a managed
    catalog's `storage_location` is computed once at create time and
    referenced by child resources, so the switch would strand every
    child. See [ADR-0013](../adr/0013-connections-and-foreign-catalogs.md)
    and [Divergences](../divergences.md).

**Response**: `200 OK` with the updated `CatalogInfo`.

### `DELETE /catalogs/{name}`

Delete a catalog.

**Query parameters**:

- `force` (bool, optional) — cascade flag. When `true`, deletes every child
  schema (and, transitively, every child table, column, and volume) via the
  service-layer cascade chain. When `false` (the default) and the catalog
  still owns schemas, the delete is rejected with `409 ALREADY_EXISTS`.

**Response**: `200 OK` with `{}`, or `404 NOT_FOUND`.

## Schemas

A **schema** lives inside exactly one catalog and groups tables and volumes.
Schema names are only unique within their parent catalog, so every endpoint
addresses a schema by its two-part `full_name` `"catalog_name.schema_name"`.

### `POST /schemas`

Create a new schema under an existing catalog.

**Request body** (`CreateSchema`):

| Field          | Type               | Required | Notes                          |
|----------------|--------------------|----------|--------------------------------|
| `name`         | string             | yes      | Schema name (unique per catalog)|
| `catalog_name` | string             | yes      | Parent catalog name            |
| `comment`      | string             | no       | Free-form description          |
| `properties`   | map<string,string> | no       | Arbitrary key-value metadata   |
| `storage_root` | string             | no       | Storage root URL               |

**Response**: `200 OK` with a `SchemaInfo` body. `full_name` is computed at
response time from the live parent catalog name, so a catalog rename
propagates to every child schema for free.

**Errors**:

- `404 NOT_FOUND` — the parent catalog does not exist.
- `409 ALREADY_EXISTS` — a schema with this name already exists in the catalog.
- `422` — malformed body or unknown fields.
- `400 INVALID_ARGUMENT` — `storage_root` uses an unsupported URI
  scheme. See [Storage URIs](#storage-uris).

### `GET /schemas`

List schemas under a catalog with keyset pagination.

**Query parameters**:

- `catalog_name` (string, required) — parent catalog name.
- `max_results`, `page_token` — see [Pagination](#pagination).

**Response**: `200 OK` with `{"schemas": [...], "next_page_token": ...}`.

### `GET /schemas/{full_name}`

Fetch a single schema by `catalog_name.schema_name`.

**Response**: `200 OK` with a `SchemaInfo`, `404 NOT_FOUND`, or
`400 INVALID_ARGUMENT` if `full_name` is not exactly two non-empty
dot-separated parts.

### `PATCH /schemas/{full_name}`

Update an existing schema. Same replace-style semantics as
`PATCH /catalogs`.

**Request body** (`UpdateSchema`):

| Field        | Type               | Notes                                 |
|--------------|--------------------|---------------------------------------|
| `new_name`   | string             | Rename to this name                   |
| `comment`    | string             | Replace the comment                   |
| `properties` | map<string,string> | Replace the entire properties map     |

!!! note "`storage_root` is set-on-create"
    `storage_root` is **not** part of `UpdateSchema` — set it once on
    `POST /schemas` and treat it as immutable thereafter. Mutating
    `storage_root` on a schema that already has managed tables would
    orphan their underlying Delta files, which UC semantics forbid.
    A PATCH that includes `storage_root` is rejected with `422`
    (same `extra="forbid"` policy as every other unknown field). To
    correct a wrong `storage_root` on an empty schema, drop and
    recreate it.

!!! note "UC OSS bug fixes"
    Same two UC OSS divergences as `PATCH /catalogs`: `{"properties": {}}`
    clears all properties, and unknown or read-only fields return `422`
    instead of being silently dropped. See [Divergences](../divergences.md).

**Response**: `200 OK` with the updated `SchemaInfo`.

### `DELETE /schemas/{full_name}`

Delete a schema.

**Query parameters**:

- `force` (bool, optional) — cascade flag. When `false` and the schema still
  owns tables, volumes, functions, registered models, or metric views, the
  delete is rejected with `409 ALREADY_EXISTS`. When `true`, cascades
  through every child of all five kinds (tables together with their
  columns, registered models together with their versions).

**Response**: `200 OK` with `{}`, `404 NOT_FOUND`, or
`400 INVALID_ARGUMENT` on a malformed `full_name`.

## Tables

A **table** is the innermost layer of the three-level namespace and lives
inside exactly one schema. Every endpoint addresses a table by its
three-part `full_name` `"catalog_name.schema_name.table_name"`.

### `POST /tables`

Create a new table under an existing schema.

**Request body** (`CreateTable`):

| Field                | Type               | Required | Notes                                                |
|----------------------|--------------------|----------|------------------------------------------------------|
| `name`               | string             | yes      | Table name (unique per schema)                       |
| `catalog_name`       | string             | yes      | Parent catalog name                                  |
| `schema_name`        | string             | yes      | Parent schema name (relative to catalog)             |
| `table_type`         | string             | yes      | `MANAGED`, `EXTERNAL`, …                             |
| `data_source_format` | string             | yes      | `DELTA`, `PARQUET`, `CSV`, …                         |
| `columns`            | list<ColumnInfo>   | yes      | Column metadata (see `ColumnInfo`)                   |
| `storage_location`   | string             | yes      | Physical storage URL                                 |
| `comment`            | string             | no       | Free-form description                                |
| `properties`         | map<string,string> | no       | Arbitrary key-value metadata                         |

Each element of `columns` is a `ColumnInfo` with `name`, `type_text`,
`type_json`, `type_name`, and optional `position`/
`type_precision`/`type_scale`/`type_interval_type`/`comment`/`nullable`/`partition_index`.

`position` may be omitted on **every** column, in which case columns are
auto-numbered from list order (0-based). Mixing explicit and omitted
positions, or repeating an explicit position, is rejected with
`400 INVALID_ARGUMENT` — previously these payloads tripped the
`UNIQUE(table_id, position)` constraint and were misreported as
`409 "Table already exists"`.

**Response**: `200 OK` with a `TableInfo`. `full_name` is computed from the
live parent catalog and schema names at response time, so a rename of
either parent propagates to every child table for free.

`TableInfo` also carries an optional `table_constraints` field
([ADR-0012](../adr/0012-table-constraints.md)) populated from the live
`table_constraints` rows at response
time. The value is `None` (not `[]`) when the table has no declared
constraints. Each entry is a `TableConstraint` envelope with a
user-chosen `name` and exactly one of `primary_key_constraint`,
`foreign_key_constraint`, `check_constraint`, or
`named_table_constraint` populated. See
[Divergences](../divergences.md) for the metadata-only posture and the
naming-decision rationale. Mutations ride on the Delta REST
`UpdateTable` discriminated union (`add-constraint` /
`drop-constraint` actions) — there is no main-REST PATCH for
constraints.

**Errors**:

- `404 NOT_FOUND` — parent catalog or schema does not exist.
- `409 ALREADY_EXISTS` — a table with this name already exists in the schema.
- `422` — malformed body, unknown top-level field, **or unknown field inside
  any `columns[i]`**.
- `400 INVALID_ARGUMENT` — `storage_location` uses an unsupported URI
  scheme (see [Storage URIs](#storage-uris)), duplicate explicit column
  `position` values, or a mix of explicit and omitted positions.

!!! note "UC OSS bug fix"
    `CreateTable` and `ColumnInfo` both use `extra="forbid"`, so a typo like
    `type_neme` inside a column entry returns `422` instead of being silently
    dropped. See [Divergences](../divergences.md).

### `GET /tables`

List tables under a schema with keyset pagination.

**Query parameters**:

- `catalog_name` (string, required).
- `schema_name` (string, required).
- `max_results`, `page_token` — see [Pagination](#pagination).

**Response**: `200 OK` with `{"tables": [...], "next_page_token": ...}`.

### `GET /tables/{full_name}`

Fetch a single table by `catalog_name.schema_name.table_name`.

**Response**: `200 OK` with a `TableInfo`, `404 NOT_FOUND`, or
`400 INVALID_ARGUMENT` on a malformed `full_name`.

### `PATCH /tables/{full_name}` → `405 Method Not Allowed`

The UC OpenAPI spec defines **no** `UpdateTable` request model and **no**
PATCH endpoint for tables, so soyuz registers no handler and FastAPI
answers any PATCH with `405 Method Not Allowed`. Clients that need to
"update" a table must delete and recreate it. See
[Divergences](../divergences.md).

### `DELETE /tables/{full_name}`

Delete a table. Columns cascade unconditionally through the ORM
relationship — a column has no independent existence.

**Query parameters**:

- `force` (bool, optional) — accepted for route-signature stability,
  currently a no-op.

**Response**: `200 OK` with `{}`, `404 NOT_FOUND`, or
`400 INVALID_ARGUMENT` on a malformed `full_name`.

## Volumes

A **volume** is a storage location registered under a schema, parallel to
tables. Volume names are only unique within their parent schema, so every
endpoint addresses a volume by its three-part `full_name`
`"catalog_name.schema_name.volume_name"`.

### `POST /volumes`

Create a new volume under an existing schema.

**Request body** (`CreateVolume`):

| Field              | Type   | Required | Notes                                      |
|--------------------|--------|----------|--------------------------------------------|
| `name`             | string | yes      | Volume name (unique per schema)            |
| `catalog_name`     | string | yes      | Parent catalog name                        |
| `schema_name`      | string | yes      | Parent schema name                         |
| `volume_type`      | enum   | yes      | `MANAGED` or `EXTERNAL` (spec enum)        |
| `storage_location` | string | no       | Physical storage URL                       |
| `comment`          | string | no       | Free-form description                      |

Volumes have no `properties` map — the UC `VolumeInfo` shape does not
define one and soyuz does not silently extend the spec.

**Response**: `200 OK` with a `VolumeInfo`.

**Errors**: same shape as `POST /tables`, including the
`400 INVALID_ARGUMENT` on an unsupported `storage_location` scheme.
MANAGED volumes that omit `storage_location` entirely are unaffected —
the scheme check only fires when the field is present.

### `GET /volumes`

List volumes under a schema with keyset pagination. Same
`catalog_name` + `schema_name` query parameters as `GET /tables` plus
the shared `max_results` / `page_token` (see
[Pagination](#pagination)).

### `GET /volumes/{full_name}`

Fetch a single volume.

### `PATCH /volumes/{full_name}`

Update a volume. The UC spec restricts volume updates to `new_name` and
`comment` only — `storage_location` and `volume_type` are immutable.

**Request body** (`UpdateVolume`):

| Field      | Type   | Notes                 |
|------------|--------|-----------------------|
| `new_name` | string | Rename to this name   |
| `comment`  | string | Replace the comment   |

!!! note "UC OSS bug fix"
    `PATCH` with an empty body `{}` returns the unchanged volume with `200 OK`
    instead of UC OSS's `INTERNAL` 500. Immutable fields
    (`storage_location`, `volume_type`) and unknown fields return `422`
    instead of being silently dropped. See [Divergences](../divergences.md).

**Response**: `200 OK` with the updated `VolumeInfo`.

### `DELETE /volumes/{full_name}`

Delete a volume. `force` is accepted but a no-op — volumes have no
child resources.

## Storage credentials

Metastore-level CRUD for named storage credentials that external
locations bind to for governance. Not to be confused with
`/temporary-*-credentials`, which is the per-request credential
vending stub — the two are entirely separate resources in the UC spec
even though they share the word "credentials".

soyuz ships only the `aws_iam_role` payload shape, matching the
upstream `all.yaml`. Azure and GCP variants that exist in forks are
deliberately out of scope — adding them without a spec change would
reintroduce the silent-spec-extension bug class the project refuses
to tolerate.

### `POST /credentials`

Create a storage credential.

**Request body** (`CreateCredentialRequest`):

| Field          | Type                 | Required | Notes                                  |
|----------------|----------------------|----------|----------------------------------------|
| `name`         | string               | yes      | Unique across the metastore            |
| `purpose`      | enum                 | no       | `STORAGE` (only value defined today)   |
| `comment`      | string               | no       |                                        |
| `aws_iam_role` | `AwsIamRoleRequest`  | no       | `{"role_arn": "arn:aws:iam::…"}`       |

**Response** (`CredentialInfo`, `exclude_none=True`):

```json
{
  "name": "prod-s3",
  "id": "abc123…",
  "purpose": "STORAGE",
  "aws_iam_role": {
    "role_arn": "arn:aws:iam::123456789012:role/soyuz",
    "external_id": "b5c3…"
  },
  "created_at": 1744637000123
}
```

`external_id` is server-minted on create and never rotated on PATCH.
`unity_catalog_iam_arn` is always absent from the wire — soyuz has no
runtime IAM identity of its own (see [Divergences](../divergences.md)).

### `GET /credentials`

List credentials with keyset pagination and an optional `?purpose=`
filter. Only `STORAGE` is a valid filter value today; anything else
returns 422.

### `GET /credentials/{name}`

Fetch a credential by name. 404 if missing.

### `PATCH /credentials/{name}`

Replace-style PATCH. `new_name`, `comment`, `owner`, and `aws_iam_role`
are updatable. Any other field (including `id`, `purpose`,
`created_at`) is rejected with 422. An empty body is a no-op. PATCHing
`aws_iam_role` replaces `role_arn` only; `external_id` is preserved.

### `DELETE /credentials/{name}`

Delete a credential. If any external location still binds to it,
returns 409 unless `?force=true` is passed — with `force=true` the
service cascades through every referencing external location first,
matching UC OSS Java behaviour.

## External locations

Metastore-level CRUD for named external locations — each row binds a
storage URL to a credential for governance. External locations are
the anchor that external tables and volumes hang off of in UC's
governance model; the minimal shape (`url` + `credential_name`)
matches the upstream `all.yaml`.

### `POST /external-locations`

Create an external location.

**Request body** (`CreateExternalLocation`):

| Field             | Type   | Required | Notes                                           |
|-------------------|--------|----------|-------------------------------------------------|
| `name`            | string | yes      | Unique across the metastore                     |
| `url`             | string | yes      | Storage URL, scheme-validated                   |
| `credential_name` | string | yes      | Name of an existing credential to bind to       |
| `comment`         | string | no       |                                                 |

`credential_id` is read-only and rejected with 422 on create — the
server resolves `credential_name` to an id and stores the **id** on
the row. A subsequent credential rename surfaces the new name on
every bound external location automatically, with no fan-out UPDATE
(pinned by
`test_credential_rename_propagates_to_external_location_read`).

**Response** (`ExternalLocationInfo`):

```json
{
  "name": "prod-landing",
  "id": "…",
  "url": "s3://bucket/landing",
  "credential_name": "prod-s3",
  "credential_id": "…",
  "created_at": 1744637000123
}
```

**Errors**:

- `400 INVALID_ARGUMENT` — `url` uses an unsupported scheme.
- `404 NOT_FOUND` — no credential with the given `credential_name`.
- `409 ALREADY_EXISTS` — duplicate `name`.
- `422` — missing required field, unknown field, or `credential_id`
  supplied on the request body.

### `GET /external-locations`

List external locations with keyset pagination.

### `GET /external-locations/{name}`

Fetch by name. 404 if missing.

### `PATCH /external-locations/{name}`

Replace-style PATCH. `new_name`, `url`, `credential_name`, `comment`,
and `owner` are updatable. Changing `url` re-runs the scheme gate;
changing `credential_name` re-resolves to a new `credential_id` (404
if the new name does not resolve). Empty body is a no-op.

### `DELETE /external-locations/{name}`

Delete. External locations have no child resources, so there is no
`force` parameter.

## Connections

Over-the-spec extension ([ADR-0013](../adr/0013-connections-and-foreign-catalogs.md)).
Databricks Lakehouse Federation-style connection definitions that
foreign catalogs bind to. soyuz stores metadata only — it never
proxies queries to the external system. Upstream UC OSS
`all.yaml` defines no `/connections` surface, so these routes are
flagged in [Divergences](../divergences.md) and skipped by the
conformance subset check.

### `POST /connections`

Create a new connection.

**Request body** (`CreateConnection`):

| Field             | Type                 | Required | Notes                                  |
|-------------------|----------------------|----------|----------------------------------------|
| `name`            | string               | yes      | Connection name (unique)               |
| `connection_type` | enum                 | yes      | `SNOWFLAKE`, `POSTGRESQL`, `MYSQL`, `REDSHIFT`, `BIGQUERY`, `DATABRICKS`, `HTTP`, `SQLSERVER`, `GLUE` |
| `options`         | map<string,string>   | no       | Free-form connector options (not validated per-type) |
| `read_only`       | bool                 | no       | Metadata flag, defaults to `false` (never enforced by soyuz) |
| `comment`         | string               | no       | Free-form description                  |
| `owner`           | string               | no       | Owner principal                        |

**Response**: `200 OK` with a `ConnectionInfo` body.

**Errors**:

- `409 ALREADY_EXISTS` — duplicate `name`.
- `422` — missing required field, unknown field, or
  `connection_type` not in the pinned enum.

### `GET /connections`

List connections with keyset pagination. See [Pagination](#pagination).

### `GET /connections/{name}`

Fetch by name. `404 NOT_FOUND` if missing.

### `PATCH /connections/{name}`

Replace-style PATCH. `new_name`, `options`, `read_only`, `comment`,
and `owner` are updatable. `connection_type` is **not** exposed on
the update shape — flipping a live connection from Postgres to
Snowflake would orphan every bound foreign catalog's options dict,
so the type is frozen at create time. Empty body is a no-op.

### `DELETE /connections/{name}`

Delete.

**Query parameters**:

- `force` (bool, optional) — cascade flag. When `false` (default)
  and any foreign catalog references the connection, the delete is
  rejected with `409`. When `true`, every referencing foreign
  catalog is deleted first via the regular catalog cascade
  (schemas → tables/volumes/functions/models, grants wiped along
  the way) before the connection row itself is removed.

## Metric views (over-the-spec)

Over-the-spec extension ([ADR-0014](../adr/0014-metric-views.md)).
A semantic-layer definition store: each metric view bundles named
dimensions and measures over one source table, addressed by the same
three-part `catalog.schema.name` full name tables use. soyuz stores
and shape-validates the definition only — compiling the view into
SQL and executing it is the consumer's job, and the `expr` strings
are opaque to soyuz. Upstream UC OSS `all.yaml` defines no
semantic-layer surface, so these routes are flagged in
[Divergences](../divergences.md) and skipped by the conformance
subset check.

### `POST /metric-views`

Create a new metric view under an existing schema.

**Request body** (`CreateMetricView`):

| Field                    | Type             | Required | Notes                                       |
|--------------------------|------------------|----------|---------------------------------------------|
| `name`                   | string           | yes      | Metric view name (unique per schema)        |
| `catalog_name`           | string           | yes      | Parent catalog (must exist)                 |
| `schema_name`            | string           | yes      | Parent schema (must exist)                  |
| `source_table_full_name` | string           | yes      | Three-part `catalog.schema.table` reference; shape-checked but **not** resolved |
| `spec`                   | `MetricViewSpec` | yes      | See below                                   |
| `comment`                | string           | no       | Free-form description                       |
| `owner`                  | string           | no       | Owner principal                             |

**`MetricViewSpec`**:

| Field        | Type                             | Required | Notes                                        |
|--------------|----------------------------------|----------|----------------------------------------------|
| `dimensions` | list of `{name, expr, comment?}` | no       | May be empty                                 |
| `measures`   | list of `{name, expr, comment?}` | yes      | At least one entry                           |
| `filter`     | string                           | no       | Opaque SQL predicate applied pre-aggregation |

**Response**: `200 OK` with a `MetricViewInfo` body (includes the
computed `full_name`).

**Errors**:

- `404 NOT_FOUND` — parent catalog or schema does not exist.
- `409 ALREADY_EXISTS` — duplicate `name` under the schema.
- `400 INVALID_ARGUMENT` — `source_table_full_name` is not a
  three-part name, or a dimension/measure name appears twice across
  the combined set (the compiled view exposes them in one flat
  column namespace).
- `422` — missing required field, unknown field, empty `measures`,
  or empty `name` / `expr` strings.

### `GET /metric-views`

List metric views under a schema with keyset pagination. Requires
`catalog_name` and `schema_name` query parameters; a bogus parent
address surfaces as `404`, not an empty page. See
[Pagination](#pagination).

### `GET /metric-views/{full_name}`

Fetch by three-part full name. `404 NOT_FOUND` if any of catalog,
schema, or metric view is missing; `400 INVALID_ARGUMENT` when the
name is not exactly three dot-separated parts.

### `PATCH /metric-views/{full_name}`

Replace-style PATCH. `new_name`, `source_table_full_name`, `spec`,
`comment`, and `owner` are updatable. `spec` replaces the whole
stored definition (a per-dimension merge would have no predictable
semantics) and is re-run through the duplicate-name gate. Empty body
is a no-op. A rename collides on the per-schema unique constraint
with `409`.

### `DELETE /metric-views/{full_name}`

Delete. No `force` flag — metric views own no child resources.
Deleting the parent schema or catalog requires `force=true` while
metric views exist underneath, and the force-cascade removes them
(same gate as tables / volumes / functions / models).

## Functions

Per-schema CRUD for SQL and EXTERNAL-language routines. Shape mirrors
the upstream `FunctionInfo` / `CreateFunction` pair: every structural
field must be supplied on create, and the UC spec defines no
`UpdateFunction` operation so PATCH returns 405. Addressed by
three-part `full_name` on every non-list endpoint, same pattern as
tables and volumes.

### `POST /functions`

Create a function under an existing schema. The request body is
double-wrapped per the UC spec:

```json
{
  "function_info": {
    "name": "add_one",
    "catalog_name": "main",
    "schema_name": "s",
    "input_params": {
      "parameters": [
        {"name": "x", "type_text": "int", "type_json": "{\"type\":\"int\"}", "type_name": "INT", "position": 0}
      ]
    },
    "data_type": "INT",
    "full_data_type": "INT",
    "return_params": {"parameters": []},
    "routine_body": "SQL",
    "routine_definition": "SELECT x + 1",
    "parameter_style": "S",
    "is_deterministic": true,
    "sql_data_access": "CONTAINS_SQL",
    "is_null_call": false,
    "security_type": "DEFINER",
    "specific_name": "add_one"
  }
}
```

**Required fields** (inside `function_info`): `name`, `catalog_name`,
`schema_name`, `input_params`, `data_type`, `full_data_type`,
`routine_body` ∈ `{SQL, EXTERNAL}`, `routine_definition`,
`parameter_style` = `S`, `is_deterministic`, `sql_data_access` ∈
`{CONTAINS_SQL, READS_SQL_DATA, NO_SQL}`, `is_null_call`,
`security_type` = `DEFINER`, `specific_name`.

**Optional**: `return_params`, `routine_dependencies`,
`external_language`, `comment`, `properties` (free-form escaped
string per the spec).

**Errors**:

- `404 NOT_FOUND` — parent catalog or schema missing.
- `409 ALREADY_EXISTS` — duplicate `(schema_id, name)`.
- `422` — missing wrapper, missing required field, unknown field
  (including inside `input_params.parameters[i]`), or enum mismatch.

### `GET /functions`

List functions under a schema with keyset pagination. Both
`catalog_name` and `schema_name` query parameters are **required**
per the UC spec; a missing parent is 404 rather than an empty list.

### `GET /functions/{full_name}`

Fetch a function by `catalog.schema.function`. 400 on a malformed
full name, 404 on any missing segment.

### `PATCH /functions/{full_name}` → `405 Method Not Allowed`

The UC spec defines no `UpdateFunction` endpoint. soyuz registers
no handler and FastAPI surfaces the absent method as 405, same shape
as the tables resource. See `DIVERGENCES.md` for the rationale.

### `DELETE /functions/{full_name}`

Delete. Functions have no child resources, so there is no `force`
parameter.

## Registered models

Per-schema CRUD container for ML model metadata, addressed by
three-part `full_name`. Registered models own a sub-resource of
`ModelVersion` rows — see the next section. Unlike tables and
volumes, the UC `CreateRegisteredModel` schema does **not** carry
`storage_location`; soyuz does not derive a managed location on
create and stores `None` for the column until a real consumer asks
for a derivation rule.

### `POST /models`

Create a registered model.

| Field           | Type   | Required | Notes                              |
|-----------------|--------|----------|------------------------------------|
| `name`          | string | yes      | Unique within the parent schema    |
| `catalog_name`  | string | yes      |                                    |
| `schema_name`   | string | yes      |                                    |
| `comment`       | string | no       |                                    |

`storage_location` is **not** accepted on create (422) — it is a
server-owned response field only.

**Errors**: 404 on missing parent; 409 on duplicate name; 422 on
unknown or missing fields.

### `GET /models`

List registered models with keyset pagination. Both `catalog_name`
and `schema_name` query filters are **optional** — a metastore-wide
listing is legal. Passing `schema_name` alone without
`catalog_name` is 400 because schema names are not metastore-unique.

### `GET /models/{full_name}`

Fetch by `catalog.schema.model`. 400 / 404 as for the other
full-name resources.

### `PATCH /models/{full_name}`

Replace-style PATCH. The UC spec allows exactly two fields —
`new_name` and `comment`. `extra="forbid"` rejects any other
attempt (422). Empty body is a no-op; `new_name` collision on the
per-schema unique index surfaces as 409.

### `DELETE /models/{full_name}`

Delete. Refuses with 409 when child model versions exist unless
`force=true` is passed, which cascades through every version in one
transaction. See `DIVERGENCES.md`.

## Model versions

Sub-resource of a registered model, addressed by
`(catalog.schema.model, version_int)`. Unusual URL shape: POST lives
at a flat `/models/versions`, everything else is nested under the
parent's `full_name`.

### `POST /models/versions`

Create a new version of an existing registered model. The parent is
addressed by three body fields rather than a URL path parameter:

```json
{
  "model_name": "rf",
  "catalog_name": "main",
  "schema_name": "s",
  "source": "s3://artifacts/rf/v1",
  "run_id": "…optional…",
  "comment": "…optional…"
}
```

The `version` integer is server-assigned as `MAX(version) + 1`
scoped to the parent; concurrent creates race on the
`(registered_model_id, version)` unique constraint and the loser
gets 409 with a retry hint. `status` is always `READY` on
soyuz-created rows — see `DIVERGENCES.md`.

### `GET /models/{full_name}/versions`

List versions of a registered model with keyset pagination. Ordered
by `(created_at, id)`, not by `version`, so two versions created in
the same millisecond disambiguate cleanly.

### `GET /models/{full_name}/versions/{version}`

Fetch by parent `full_name` + integer version. 404 on either miss.

### `PATCH /models/{full_name}/versions/{version}`

Replace-style PATCH. The UC spec permits only `comment` —
`source`, `run_id`, `status`, and `version` itself are all
immutable. Any other field is rejected with 422.

### `DELETE /models/{full_name}/versions/{version}`

Delete a single version.

## Temporary credentials

Two sibling endpoints that — per the UC spec — vend short-lived cloud
credentials (S3 STS tokens, Azure user-delegation SAS, or GCP OAuth
tokens) scoped to a specific table or volume. Real STS/SAS/OAuth vending
requires boto3/azure-identity/google-auth and per-deployment IAM
configuration and stays explicitly out of scope.

soyuz ships these endpoints as **spec-conformant stubs**: the response
shape matches `TemporaryCredentials` exactly, `expiration_time` is
always populated (one hour from now), and the cloud-specific field is
selected from the resolved row's `storage_location` scheme. The nested
object is always empty — it signals which cloud path the server would
route through without ever returning a real token.

| scheme       | response shape on the wire                                         |
|--------------|--------------------------------------------------------------------|
| `s3`, `s3a`  | `{"aws_temp_credentials": {}, "expiration_time": …}`               |
| `abfss`      | `{"azure_user_delegation_sas": {}, "expiration_time": …}`          |
| `gs`         | `{"gcp_oauth_token": {}, "expiration_time": …}`                    |
| `file` / legacy | `{"expiration_time": …}`                                         |

See [Divergences](../divergences.md) for the full rationale.

### `POST /temporary-table-credentials`

Request a credential for a table, addressed by opaque `table_id` so the
credential stays valid across a rename of any parent.

**Request body** (`GenerateTemporaryTableCredential`):

| Field       | Type   | Required | Notes                                       |
|-------------|--------|----------|---------------------------------------------|
| `table_id`  | string | yes      | Opaque table id from `TableInfo.table_id`   |
| `operation` | enum   | yes      | `READ` or `READ_WRITE`                      |

**Response** (`TemporaryCredentials`, `exclude_none=True`) — example for
an `s3://` table:

```json
{"aws_temp_credentials": {}, "expiration_time": 1744637000123}
```

A `file://` table returns `{"expiration_time": 1744637000123}`; see the
per-scheme table above for the other cloud shapes.

**Errors**:

- `404 NOT_FOUND` — no table *and* no staging-table row with that id.
  The resolver tries the real-table lookup first and falls through to
  `staging_table_service.get_staging_table_by_id` before returning 404;
  see [Divergences](../divergences.md) "Staging tables".
- `400 INVALID_ARGUMENT` — `operation` is the `UNKNOWN_TABLE_OPERATION`
  sentinel. The spec defines this enum value only as a protobuf default
  and accepting it here would reproduce the UC OSS "silently-accept-
  garbage" pattern that soyuz exists to fix.
- `422` — malformed body, unknown fields, or an `operation` value outside
  the three defined enum members.

### `POST /temporary-volume-credentials`

Mirrors `/temporary-table-credentials`: same request/response shape, same
stub contract.

**Request body** (`GenerateTemporaryVolumeCredential`):

| Field       | Type   | Required | Notes                                        |
|-------------|--------|----------|----------------------------------------------|
| `volume_id` | string | yes      | Opaque volume id from `VolumeInfo.volume_id` |
| `operation` | enum   | yes      | `READ_VOLUME` or `WRITE_VOLUME`              |

**Errors**: same shape as the table variant — the rejected sentinel is
`UNKNOWN_VOLUME_OPERATION`.

### `POST /temporary-path-credentials`

Request a credential for an arbitrary storage URL rather than a
soyuz-tracked table/volume row. Same stub contract and per-scheme
routing table as the sibling endpoints — the handler runs the
client-supplied URL through the `parse_storage_uri` validator
and dispatches to the shared per-scheme response builder.

**Request body** (`GenerateTemporaryPathCredential`):

| Field       | Type   | Required | Notes                                                |
|-------------|--------|----------|------------------------------------------------------|
| `url`       | string | yes      | Storage URL with a supported scheme                  |
| `operation` | enum   | yes      | `PATH_READ`, `PATH_READ_WRITE`, or `PATH_CREATE_TABLE` |

**Errors**:

- `400 INVALID_ARGUMENT` — `url` is empty, has no scheme, or uses an
  unsupported scheme, or `operation` is the `UNKNOWN_PATH_OPERATION`
  sentinel.
- `422` — malformed body, unknown fields, or an `operation` value
  outside the four defined enum members.

## Metastore

### `GET /metastore_summary`

Return the metastore identity. The response shape is the upstream
`GetMetastoreSummaryResponse`, which defines exactly one field:

```json
{"metastore_id": "f4d1…"}
```

The backing row is created lazily on the first call and then reused
forever — two deployments therefore report distinct stable ids, and
test fixtures get a fresh id per in-memory engine. See
[Divergences](../divergences.md) for why soyuz deliberately does not
return the richer Databricks-flavoured summary (name, storage root,
region, cloud, …).

## Staging tables

Experimental endpoint from the UC spec: allocate a
`(catalog, schema, name)` tuple and receive an opaque id plus a
server-derived `staging_location` URL. soyuz implements the allocation
half only — the follow-up *promote* step that turns an allocation
into a managed `Table` requires the managed-table materialisation
work that stays explicitly out of scope.

### `POST /staging-tables`

**Request body** (`CreateStagingTable`):

| Field          | Type   | Required | Notes                            |
|----------------|--------|----------|----------------------------------|
| `name`         | string | yes      | Staging-table name               |
| `catalog_name` | string | yes      | Parent catalog name              |
| `schema_name`  | string | yes      | Parent schema, relative to catalog |

**Response** (`StagingTableInfo`):

```json
{
  "name": "t",
  "catalog_name": "main",
  "schema_name": "s",
  "id": "b7f1…",
  "staging_location": "s3://bucket/root/__unitystorage/schemas/<schema_id>/__staging__/<alloc>/t"
}
```

`staging_location` is derived from the parent schema's
`storage_location` first (itself a deterministic derivation under
`__unitystorage/schemas/`), falling back to the catalog's bare
`storage_root` when the schema has neither its own `storage_root` nor
an inherited `storage_location`. A UUID-hex segment under
`__staging__/` keeps concurrent allocations from colliding on disk,
which is why there is deliberately no uniqueness constraint on
`(schema_id, name)`: two POSTs with the same body succeed with
distinct ids and distinct URLs so clients can retry safely.

Staging-table ids **are** resolvable through
`/temporary-table-credentials`. The resolver tries the
real-table lookup first and falls through to the staging-table service
on a miss, routing the staging row's `staging_location` through the
same per-scheme stub dispatcher as a real table. The upstream JVM
`UCSingleCatalog` connector depends on this behaviour. Clients that
want credentials addressed by URL rather than id can still use
`/temporary-path-credentials`. See [Divergences](../divergences.md).

**Errors**:

- `404 NOT_FOUND` — unknown `catalog_name` or `schema_name`.
- `400 INVALID_ARGUMENT` — neither the schema nor the catalog has a
  usable storage location, or the resolved root has an unsupported
  scheme.
- `422` — malformed body or unknown fields (`extra="forbid"` rejects
  server-derived fields like `storage_location` and `id` on create).

## Permissions

Persist and return grants on any Unity Catalog
securable. soyuz-catalog is a **storage backend only** — no other
endpoint consults the `permissions` table, and enforcement is
expected to live in an auth proxy in front of this server. See
[ADR-0005](../adr/0005-permissions-without-enforcement.md) and
[Divergences](../divergences.md).

The two endpoints share one URL shape:

```
/api/2.1/unity-catalog/permissions/{securable_type}/{full_name}
```

`securable_type` is one of the nine upstream `SecurableType` enum
values: `metastore`, `catalog`, `schema`, `table`, `function`,
`volume`, `registered_model`, `external_location`, `credential`. An
unknown value returns `422` from FastAPI path-parameter validation.
`full_name` is the spec-shaped dotted address: one segment for
`catalog` / `credential` / `external_location`, two for `schema`
(`catalog.schema`), three for `table` / `volume` / `function` /
`registered_model` (`catalog.schema.name`), and the live
`metastore_id` from `/metastore_summary` for `metastore`. The
segment count is enforced strictly — a 2-part name passed to a
3-part type returns `400`.

Grants are keyed internally on the resolved row's opaque `id`, not
the `full_name`, so a rename of any parent leaves existing grants
attached without a fan-out `UPDATE` — the same rename-invariance
trick `external_locations.credential_id` uses. The opaque binding
never surfaces on the wire; clients continue to address securables
by `full_name`.

### `GET /permissions/{securable_type}/{full_name}`

**Query parameters**:

| Name        | Type   | Required | Notes                                            |
|-------------|--------|----------|--------------------------------------------------|
| `principal` | string | no       | Filter the response to a single principal's grants |

**Response** (`PermissionsList`):

```json
{
  "privilege_assignments": [
    {"principal": "alice@example.com", "privileges": ["USE CATALOG"]},
    {"principal": "engineering", "privileges": ["CREATE SCHEMA", "USE CATALOG"]}
  ]
}
```

The response is sorted by principal and each principal's privilege
list is sorted too, so two calls against unchanged state return
byte-identical bodies.

**Errors**: `404` if any segment of the full_name does not resolve,
`400` if the segment count is wrong for the given type, `422` if
the path `securable_type` is unknown.

### `PATCH /permissions/{securable_type}/{full_name}`

**Request body** (`UpdatePermissions`):

```json
{
  "changes": [
    {
      "principal": "alice@example.com",
      "add": ["USE CATALOG"],
      "remove": []
    }
  ]
}
```

Unlike every other `PATCH` route in soyuz, this endpoint is
additive: clients submit a batch of add / remove operations rather
than a full desired state. Every element in `changes` is processed
in order; `remove` is applied before `add` within one change, so if
the same privilege appears in both lists the net effect is *add
wins*. All three fields on `PermissionsChange` (`principal`,
`add`, `remove`) are required per the upstream spec — clients that
only want to add must still send an empty `remove` list (and vice
versa).

Duplicate adds within the same batch are deduped and do not cause
unique-index collisions; re-adding an existing grant across batches
is a no-op. Removing a non-existent grant is also a no-op.

Every `add` entry is validated against the per-type privilege
**allow-set** (documented in
[Divergences](../divergences.md)) **before any row is written**:
a single disallowed pair anywhere in the batch rejects the whole
request with `400 INVALID_ARGUMENT` and leaves the grant table
untouched. `remove` lists are not gated by the allow-set.

**Response**: the full post-change `PermissionsList` for the
securable (not filtered by principal), so clients do not need a
follow-up `GET` after every update.

**Errors**: `404` if the address does not resolve, `400` for bad
segment counts or disallowed privileges, `422` for an unknown
`securable_type` or malformed body (`extra="forbid"` on every
request model).

**Cascade on parent delete**: when a securable is removed via its
own `DELETE` endpoint, every grant attached to it and to its
descendants disappears in the same transaction. The cascade is
unconditional — it is **not** gated by `force=true`. A catalog
delete wipes grants on the catalog itself plus every schema,
table, volume, function, and registered model under it; a
credential delete with `force=true` also wipes grants on the
external locations it cascaded through.

## Effective permissions (over-the-spec)

One read-only endpoint at
`/effective-permissions/{securable_type}/{full_name}` that returns
the **inherited** grant set for a securable. Upstream `all.yaml`
defines only the direct-grant sibling under `/permissions/`; soyuz
adds effective-computation as a first-class service so every client
gets the same answer. See the "Permissions: effective computation"
section in [Divergences](../divergences.md) for the full inheritance
rule and the conformance-test skip.

### `GET /effective-permissions/{securable_type}/{full_name}`

Compute the effective (inherited) grant set by walking the ownership
chain (`leaf → schema → catalog → metastore`) and union-ing
privileges per principal.

- **Path parameters** — identical to the direct-grant sibling:
  `securable_type` as a `Literal` (422 on unknown values),
  `full_name` as a dotted address whose segment count must match
  the type.
- **Query parameters** — `principal=<id>` optional filter that
  trims the response to one assignment. Useful for "does `P` have
  `X` on `L`?" checks that do not need the whole grant matrix over
  the wire.

**Response**: a `PermissionsList` identical in shape to
`GET /permissions/{type}/{name}` — clients can swap URLs with no
other code change. The `privilege_assignments` list is sorted by
principal for stable diffs, and each principal's privilege list is
sorted too.

Example request / response:

```
GET /api/2.1/unity-catalog/effective-permissions/table/cat1.sch1.tbl1
```

```json
{
  "privilege_assignments": [
    {"principal": "alice@example.com",
     "privileges": ["SELECT", "USE CATALOG", "USE SCHEMA"]}
  ]
}
```

Here `alice` was granted `USE CATALOG` on `cat1`, `USE SCHEMA` on
`cat1.sch1`, and `SELECT` on `cat1.sch1.tbl1` — three direct grants
at three levels, unioned into a single three-privilege set because
the effective view walks the chain for you.

**Inheritance rule.** Set-union across the chain; no precedence,
because UC grants are additive (no deny rows). The chain walk is
leaf-ward only: a table-level grant never appears when querying
effective permissions on the table's parent schema. See the
[Divergences](../divergences.md) entry for the full ancestor chain
per securable type and the out-of-scope list (no `inherited_from`
annotation, no applicability filter, no column-level support, no
writes).

**Errors**: `404` if the address does not resolve, `400` for bad
segment counts, `422` for an unknown `securable_type`. Empty
chain-grants return `{"privilege_assignments": []}` rather than
404 — "no grants anywhere along the chain" is a valid state.

## Delta commits (coordinator)

Two sibling operations at `/delta/preview/commits`.
[ADR-0011](../adr/0011-delta-commit-coordinator.md) describes the
**passthrough Delta commit coordinator** posture for `file://` Delta
tables: commits are
persisted to the `delta_unbackfilled_commits` table, version
ordering is enforced at the service layer, and the
`(table_id, commit_version)` unique constraint is the entire
optimistic-concurrency story (racing writers serialise through the
database; the loser observes 409). The coordinator is a passthrough
in the sense that Delta Kernel clients self-publish staged commit
files to `_delta_log/NNNNN.json` on receipt of a 200 — soyuz runs
no backfill watchdog and readers apply unbackfilled rows in-memory.

### `GET /delta/preview/commits`

List the unbackfilled commits the coordinator currently tracks for a
table. Request body (the spec models this endpoint as GET-with-body):

```json
{
  "table_id": "a3f1...",
  "table_uri": "file:///tmp/round_trip",
  "start_version": 0,
  "end_version": 5
}
```

- `table_id` — required. Resolved through the opaque-id path, so the
  lookup is rename-invariant.
- `table_uri` — required. Must match the table's registered
  `storage_location` exactly; a mismatch returns `400 INVALID_ARGUMENT`
  per the upstream spec.
- `start_version` — required. Inclusive lower bound on the returned
  `commits` rows.
- `end_version` — optional. Inclusive upper bound when present.

Response:

```json
{
  "commits": [
    {
      "version": 1,
      "timestamp": 1700000000001,
      "file_name": "00000000000000000001.json",
      "file_size": 123,
      "file_modification_timestamp": 1700000000001
    }
  ],
  "latest_table_version": 1
}
```

- `commits` — the live coordinator rows in
  `[start_version, end_version]`, excluding the internal
  `is_backfilled_latest_commit` anchor (the anchor is state that
  preserves the high-water version after a prune; returning it to
  the client would confuse Delta Kernel readers, which only want
  rows they have not yet applied).
- `latest_table_version` — the highest version the coordinator has
  ever seen for the table (max over **all** live rows, including the
  anchor), falling back to `DeltaTable(path).version()` on the
  on-disk log when the coordinator has no rows for the table — the
  Catalog read-path, preserved for freshly-attached tables.

**Only `file://` storage is supported.** Cloud schemes
(`s3`, `s3a`, `abfss`, `gs`) return `501 NOT_IMPLEMENTED` pending
credential vending (out of scope). The `deltalake`
runtime is an optional extra (`pip install soyuz-catalog[delta]`);
without it the endpoint also returns 501 with an install hint.

Errors:

- `404 NOT_FOUND` — no table with `table_id` exists.
- `400 INVALID_ARGUMENT` — `table_uri` mismatch, or the table has no
  registered `storage_location`.
- `501 NOT_IMPLEMENTED` — non-`file://` scheme, or `delta` extra not
  installed.

### `POST /delta/preview/commits`

Register an unbackfilled commit and/or acknowledge a completed
client-side publish. The request fuses two conceptually independent
operations the Delta Kernel client may send together:

```json
{
  "table_id": "a3f1...",
  "table_uri": "file:///tmp/round_trip",
  "commit_info": {
    "version": 1,
    "timestamp": 1700000000001,
    "file_name": "00000000000000000001.json",
    "file_size": 123,
    "file_modification_timestamp": 1700000000001
  },
  "latest_backfilled_version": 0,
  "metadata": {},
  "uniform": {}
}
```

- `commit_info` — optional. Registers a new unbackfilled commit at
  `version`. The client has already written the staged commit file
  to `_delta_log/.tmp/<uuid>.json`; soyuz records the file metadata
  and the client publishes on receipt of the 200.
- `latest_backfilled_version` — optional. Signals that the client
  has published everything up to the given version; soyuz prunes
  rows at earlier versions and flags the row at
  `commit_version == latest_backfilled_version` with
  `is_backfilled_latest_commit = True` so GET can still report the
  correct high-water version.
- `metadata`, `uniform` — optional opaque pass-through dicts. Delta
  Kernel forwards them to downstream consumers (protocol upgrades,
  Iceberg conversion hints); soyuz stores neither.

At least one of `commit_info` / `latest_backfilled_version` must be
present — an empty request is rejected with `422` at the schema
layer. The write path runs first so the new row's persistence does
not depend on the prune.

Response: `200 OK` with an empty JSON object `{}` on success.

Errors:

- `400 INVALID_ARGUMENT` — `commit_info.version > current latest + 1`
  (version gap), or `latest_backfilled_version > current latest`
  (cannot acknowledge a publish past the highest version the
  coordinator has seen), or `table_uri` mismatch.
- `409 ALREADY_EXISTS` — `commit_info.version <= current latest`
  (pre-check), or a concurrent writer won the race for the same
  `(table_id, commit_version)` at the database unique constraint.
- `422` — empty body (neither `commit_info` nor
  `latest_backfilled_version` present), `extra` field (the request
  is `extra="forbid"`), or any other schema validation failure.
- `429 TOO_MANY_REQUESTS` — per-table cap of 10 unbackfilled
  commits reached; the client must publish existing staged commits
  before adding more. Matches the upstream Java server's
  `MAX_NUM_COMMITS_PER_TABLE`.
- `501 NOT_IMPLEMENTED` — non-`file://` scheme, or `delta` extra
  not installed.

The Spark roundtrip test
(`test_managed_delta_table_creation_via_spark`) exercises this
endpoint end-to-end: it creates a managed Delta table via
`UCSingleCatalog`, inserts a row, and reads it back — the full
coordinator path including staged-commit registration, client-side
publish, and subsequent read.

## Delta REST Catalog API

The unitycatalog OSS project ships a **second** OpenAPI spec file
at `~/git/unitycatalog/api/delta.yaml` — the Delta REST Catalog
API. It is Delta-centric (inspired by the Iceberg REST Catalog)
and uses native Delta protocol shapes (`DeltaColumn`,
`DeltaProtocol`, `TableMetadata`) with a distinctive kebab-case
wire convention. soyuz adds 13 endpoints under
`/api/2.1/unity-catalog/delta/v1/` to implement it (see
[ADR-0009](../adr/0009-delta-rest-catalog-as-secondary-surface.md)).

Storage is **reused**: every endpoint operates on the same soyuz
`Table` / `StagingTable` rows the main UC API manages. A table
created via `POST /api/2.1/unity-catalog/tables` is loadable via
`GET /api/2.1/unity-catalog/delta/v1/catalogs/{c}/schemas/{s}/tables/{t}`
and vice versa. See
[ADR-0009](../adr/0009-delta-rest-catalog-as-secondary-surface.md)
for the translation strategy.

The 13 endpoints:

| Method | Path                                                               | Purpose                         |
|--------|--------------------------------------------------------------------|---------------------------------|
| GET    | `/delta/v1/config`                                                 | Protocol + endpoint advertisement |
| POST   | `/delta/v1/catalogs/{c}/schemas/{s}/tables`                        | Create table                    |
| GET    | `/delta/v1/catalogs/{c}/schemas/{s}/tables`                        | List tables                     |
| GET    | `/delta/v1/catalogs/{c}/schemas/{s}/tables/{t}`                    | Load table metadata             |
| POST   | `/delta/v1/catalogs/{c}/schemas/{s}/tables/{t}`                    | Apply updates                   |
| DELETE | `/delta/v1/catalogs/{c}/schemas/{s}/tables/{t}`                    | Delete table (204)              |
| HEAD   | `/delta/v1/catalogs/{c}/schemas/{s}/tables/{t}`                    | Existence check (204/404)       |
| POST   | `/delta/v1/catalogs/{c}/schemas/{s}/tables/{t}/rename`             | Rename table (204)              |
| GET    | `/delta/v1/catalogs/{c}/schemas/{s}/tables/{t}/credentials`        | Empty credential stub           |
| POST   | `/delta/v1/catalogs/{c}/schemas/{s}/tables/{t}/metrics`            | Accept-and-discard (204)        |
| POST   | `/delta/v1/catalogs/{c}/schemas/{s}/staging-tables`                | Allocate staging table          |
| GET    | `/delta/v1/staging-tables/{id}/credentials`                        | Empty credential stub           |
| GET    | `/delta/v1/temporary-path-credentials`                             | Empty credential stub           |

### `GET /delta/v1/config`

Returns the fixed list of 12 endpoint paths and the negotiated
protocol version `"1.0"`. Query parameters `catalog` and
`protocol-versions` are required by spec and validated but do not
branch behaviour — soyuz has a single implementation.

### `POST /delta/v1/catalogs/{c}/schemas/{s}/tables`

Creates a Delta table. Example body:

```json
{
  "name": "orders",
  "location": "s3://bucket/orders",
  "table-type": "MANAGED",
  "data-source-format": "DELTA",
  "columns": [
    {"name": "id", "type": "long", "nullable": false, "metadata": {}},
    {"name": "amount", "type": {"type": "decimal", "precision": 10, "scale": 2},
     "nullable": true, "metadata": {}}
  ],
  "partition-columns": ["id"],
  "protocol": {"min-reader-version": 1, "min-writer-version": 2},
  "properties": {"delta.enableDeletionVectors": "true"}
}
```

Response is a full `LoadTableResponse` with the newly-synthesised
`etag`, `table-uuid` (= `Table.id`), and fixed `DeltaProtocol`.

**Column translation.** `DeltaColumn.type` is a string-or-object
union that OpenAPI cannot express cleanly. soyuz stores the full
`{type, metadata}` payload verbatim in `Column.type_json` so
`loadTable` returns a byte-identical `DeltaColumn`.

**Synthesised fields.** Every `loadTable` response carries:

- `etag` = `str(Table.updated_at)`. Any mutation bumps
  `updated_at`, invalidating stale etags.
- `table-uuid` = `Table.id` (32-char opaque hex).
- `protocol` = fixed default `(min-reader=1, min-writer=2)`.
  soyuz does not track per-table protocol versions; client values
  on create / `set-protocol` are accepted and discarded.
- `commits` = always `[]` (no commit coordinator, ADR-0006).

### `POST /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}` (update)

`UpdateTableRequest` carries two arrays: `requirements` and
`updates`. Requirements run first; a failure on any short-circuits
the whole batch with 409 before any mutation.

**Supported requirements:**

| Type                | Behaviour                                                        |
|---------------------|------------------------------------------------------------------|
| `assert-table-uuid` | String compare against `Table.id`. Fail → 409 `REQUIREMENT_NOT_MET`. |
| `assert-etag`       | String compare against `str(Table.updated_at)`. Fail → 409 `REQUIREMENT_NOT_MET`. |

**Update action categories:**

| Category            | Actions                                                                                                | Behaviour                                           |
|---------------------|--------------------------------------------------------------------------------------------------------|-----------------------------------------------------|
| Implemented         | `set-properties`, `remove-properties`, `set-table-comment`, `set-columns`, `set-partition-columns`, `add-constraint`, `drop-constraint` | Mutate the stored row; `updated_at` bumped. `add-constraint` / `drop-constraint` reference [ADR-0012](../adr/0012-table-constraints.md) — declared metadata-only constraints (PK / FK / CHECK / named NOT NULL). |
| Accept-and-discard  | `set-protocol`, `set-domain-metadata`, `remove-domain-metadata`                                        | Parsed, validated, silently ignored. ADR-0009.      |
| Rejected 501        | `add-commit`, `set-latest-backfilled-version`, `update-metadata-snapshot-version`                      | `COMMIT_COORDINATOR_UNSUPPORTED` (ADR-0006).        |

The response is the post-update `LoadTableResponse` with the
bumped etag.

### `POST /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}/rename`

Renames a table in place. 204 No Content on success; 409 if the
target name already exists under the same schema. **The opaque id
is preserved** — every downstream reference keyed on it
(permissions, lineage edges, credential vending) stays valid
without a fan-out update.

### Credential endpoints (3 stubs)

`getTableCredentials`, `getStagingTableCredentials`, and
`getTemporaryPathCredentials` all return `200 {"storage-credentials": []}`.
soyuz does not vend cloud credentials (consistent with the
existing temporary-credentials stub posture). Delta clients that
use the returned location directly via `file://` or an externally
configured credential see no difference. A 404 still surfaces for
unknown table / staging-table addresses so a broken integration
does not silently succeed.

### `POST .../metrics`

Accept-and-discard: the body is parsed (a malformed payload
returns 422) and the path is probed (unknown table → 404), but
the metrics themselves are dropped — soyuz has no metrics sink.
Returns 204 No Content. Rejecting these would log a client-side
error on every Delta write over a non-feature. See ADR-0009.

## Lineage (over-the-spec)

Upstream Unity Catalog OSS has no lineage. soyuz adds lineage as a
genuine over-the-spec extension anchored on
[OpenLineage](https://openlineage.io) as the ingestion contract —
every major batch/stream framework (Spark, dbt, Airflow, Flink,
Dagster) already emits OpenLineage events natively, so soyuz gets a
producer ecosystem without inventing a client-side protocol. See
[ADR-0008](../adr/0008-openlineage-as-lineage-contract.md) and
`DIVERGENCES.md` under **Lineage**.

The three lineage endpoints live at the **root**, *not* under
`/api/2.1/unity-catalog`:

- `POST /lineage/v1/events`
- `GET /lineage/upstream/{full_name}?depth=N`
- `GET /lineage/downstream/{full_name}?depth=N`

The depth cap is `lineage_service.MAX_DEPTH = 10`; `depth=0` is a
valid no-op that returns only the root node.

### `POST /lineage/v1/events`

Accepts any OpenLineage `RunEvent` body. Only a small fixed set of
fields is extracted (`eventType`, `eventTime`, `run.runId`,
`job.namespace`, `job.name`, `inputs[]`, `outputs[]`); unknown
top-level keys and unknown sub-keys are **accepted and ignored** —
this is the single documented exception in soyuz to the
`extra="forbid"` policy, justified in ADR-0008 because OpenLineage
evolves independently of soyuz and a new facet must not crash
producers.

```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-04-15T10:05:00Z",
  "run": {"runId": "6f9a7bda-9f1d-4d2e-bc2c-6c1f9f2c8a11"},
  "job": {"namespace": "airflow", "name": "nightly_orders_etl"},
  "inputs":  [{"namespace": "s3://bucket", "name": "main.raw.orders"}],
  "outputs": [{"namespace": "s3://bucket", "name": "main.curated.orders"}]
}
```

Dataset `name` is interpreted as a `catalog.schema.table` full_name
and resolved through the same helper the Permissions resource uses
(`permissions_service.resolve_securable`). Datasets that do not
resolve — because the table is not in UC, or the segment count is
wrong — are silently dropped and counted in the response rather
than rejected with 400. OpenLineage producers legitimately emit
events for non-UC tables; a 400 would make soyuz unusable as a
drop-in sink.

Response (`201`):

```json
{
  "run_id": "6f9a7bda9f1d4d2ebc2c6c1f9f2c8a11",
  "state": "COMPLETE",
  "accepted_edges": 1,
  "rejected_datasets": 0
}
```

`run_id` is the OpenLineage `runId` with hyphens stripped (soyuz'
32-char-hex PK shape). `accepted_edges` counts the edges actually
*inserted* on this call — a redelivered event reports `0` because
the unique constraint
`(run_id, source_securable_id, target_securable_id)` makes the
second insert a no-op. Run state is **last-write-wins** keyed by
run id: redelivered or out-of-order events overwrite the stored
state rather than being rejected, because OpenLineage producers
occasionally retry.

Self-edges (a job that reads and writes the same table) are
dropped — legal in OpenLineage but add no useful signal and turn
traversal into a cycle.

Error responses:

- `400 INVALID_ARGUMENT` — `run.runId` is not a UUID
  (post-hyphen-stripping it must be 32 hex characters) or
  `eventTime` does not parse as ISO-8601.
- `422 INVALID_ARGUMENT` — one of the required top-level fields
  (`eventType`, `eventTime`, `run.runId`, `job.namespace`,
  `job.name`) is missing or wrong-typed.

### `GET /lineage/upstream/{full_name}`

Walks backward from a table to the tables that fed it. `full_name`
is `catalog.schema.table`. `depth=N` (default `3`) bounds the walk;
`depth=0` returns only the root node with an empty edge list, which
is a valid probe for "does this table have any recorded lineage?"

Response (`200`):

```json
{
  "root": "main.curated.orders",
  "direction": "upstream",
  "nodes": [
    {"securable_id": "…32hex…", "full_name": "main.curated.orders", "depth": 0},
    {"securable_id": "…32hex…", "full_name": "main.raw.orders",      "depth": 1}
  ],
  "edges": [
    {
      "source_securable_id": "…32hex…",
      "target_securable_id": "…32hex…",
      "source_full_name": "main.raw.orders",
      "target_full_name": "main.curated.orders",
      "run_id": "6f9a7bda9f1d4d2ebc2c6c1f9f2c8a11",
      "operation": "nightly_orders_etl"
    }
  ]
}
```

A `full_name` of `null` in a node or edge means the underlying
table was deleted after the edge was recorded: lineage is
append-only history, and edges are deliberately **not**
cascade-deleted when a referenced table is dropped. Clients can
render dangling ids however they like (soyuz surfaces them as
`full_name: null`); the opaque id stays present so diffing two
traversal responses is still meaningful.

Error responses:

- `400 INVALID_ARGUMENT` — `depth` outside `[0, 10]`.
- `404 NOT_FOUND` — root `full_name` does not resolve.

### `GET /lineage/downstream/{full_name}`

Mirror: walks forward from a table to the tables it feeds. Same
shape, same caps, same dangling-edge semantics; only
`direction: "downstream"` and the edge orientation differ.

### Rename invariance

Because edges are keyed on opaque row ids, renaming a parent
catalog or schema propagates to every lineage response for free —
no fan-out `UPDATE`. The service reconstructs `full_name` at query
time by joining `Table → Schema → Catalog`. Regression test:
`tests/test_lineage.py::test_rename_invariance`.

## Tags (over-the-spec)

Upstream Unity Catalog OSS and `all.yaml` have no tags resource;
Databricks supports tags on catalogs / schemas / tables / columns
but has not published a spec. soyuz adds tags as a root-mounted
over-the-spec extension, following the same template as lineage.
See [ADR-0010](../adr/0010-tags-as-extension.md) and
`DIVERGENCES.md` under **Tags**.

The two tag endpoints live at the **root**, *not* under
`/api/2.1/unity-catalog`:

- `GET /tags/{securable_type}/{full_name}`
- `PATCH /tags/{securable_type}/{full_name}`

`securable_type` is one of `catalog`, `schema`, `table`, `column`.
Volume / function / registered_model are a non-breaking additive
future extension. `full_name` is 1 segment for `catalog`, 2 for
`schema`, 3 for `table`, and **4** for `column` —
`catalog.schema.table.column` is the only 4-part full_name in the
soyuz REST surface.

### `GET /tags/{securable_type}/{full_name}`

Returns the current tag set of the securable, sorted by key.
Empty is `{"tags": []}`, never 404.

Response (`200`):

```json
{
  "tags": [
    {"key": "owner", "value": "alice", "created_at": 1760000000000, "updated_at": 1760000000000},
    {"key": "pii",   "value": "true",  "created_at": 1760000000000, "updated_at": 1760000000000}
  ]
}
```

Error responses:

- `400 INVALID_ARGUMENT` — wrong segment count for the securable
  type (for example `column` with a 3-part name).
- `404 NOT_FOUND` — any segment of the full_name fails to resolve.
- `422 INVALID_ARGUMENT` — `securable_type` outside the MVP set.

### `PATCH /tags/{securable_type}/{full_name}`

Applies an additive batch of set/remove operations and returns
the full post-change tag set. Unlike every other PATCH in soyuz,
this shape is **not** replace-style — two clients editing disjoint
key sets must not clobber each other.

```json
{
  "changes": [
    {"op": "set",    "key": "owner", "value": "alice"},
    {"op": "set",    "key": "pii"},
    {"op": "remove", "key": "deprecated"}
  ]
}
```

`value` is optional: a `set` without `value` stores a valueless
flag tag (`pii`), matching Databricks' UI semantics. `remove`
ignores `value`. Unknown fields are rejected with `422`
(`extra="forbid"`).

Overlapping operations inside a single batch resolve as **set
wins**: `(remove key, set key)` ends with the key present. The
rationale is the multi-writer invariant — two clients setting
the same key after one client removed it should not leave a gap.
See ADR-0010.

An empty `changes` list is a valid no-op and returns the current
state without opening a write transaction.

Error responses:

- Same as `GET` for address validation.
- `422 INVALID_ARGUMENT` — `op` outside `{"set", "remove"}`, or an
  unknown field in the body.

### Rename invariance and append-only delete

Tags are keyed on opaque row ids, never full_names. Renaming a
catalog / schema / table / column leaves every attached tag
intact — the same mechanism permissions (ADR-0005) and lineage
(ADR-0008) use. Dropping the underlying resource does **not**
cascade-delete its tags: the opaque `securable_id` is unique per
creation, so a new resource with the same full_name gets a new id
and cannot inherit the stale tags. Regression tests:
`tests/test_tags.py::test_rename_catalog_preserves_tags` and
`tests/test_tags.py::test_delete_table_leaves_orphan_tag`.

## Error response shape

**Every** non-2xx response — including the 422 validation
path and any uncaught 500 — uses the same JSON envelope:

```json
{
  "error_code": "NOT_FOUND",
  "message": "Catalog 'main' does not exist",
  "request_id": "9c4ff4c9f2b64a3e9a3e3f1d3b1b6b4a"
}
```

On 422 the body additionally carries `details`, a pass-through of the
pydantic `errors()` list, so structured clients keep the per-field
breakdown they had before:

```json
{
  "error_code": "INVALID_ARGUMENT",
  "message": "body.name: Field required",
  "request_id": "…",
  "details": [
    {"type": "missing", "loc": ["body", "name"], "msg": "Field required", "input": {}}
  ]
}
```

| `error_code`       | HTTP status | When                                    |
|--------------------|-------------|-----------------------------------------|
| `INVALID_ARGUMENT` | 400 / 422   | Semantic or pydantic validation failure |
| `NOT_FOUND`        | 404         | Address does not resolve                |
| `ALREADY_EXISTS`   | 409         | Unique / delete-gate conflict           |
| `INTERNAL`         | 500         | Uncaught exception (envelope fallback)  |

### `X-Request-ID` correlation header

Every request is tagged with a UUID-hex correlation ID, returned on the
response as `X-Request-ID` and echoed in the error body as `request_id`.
Clients that already send an `X-Request-ID` header will see their value
reused if (and only if) it parses as a valid UUID; malformed inbound
values are replaced rather than propagated.

The same ID is attached to every log record via a `contextvars`-based
logging filter, so a `request_id` returned to the client and an
`access.log` line emitted server-side can be correlated one-to-one. Set
`SOYUZ_STRUCTURED_LOGGING=1` to switch the server from text logs to a
one-JSON-object-per-line format suitable for log shippers.
