# Divergences from UC OSS Java reference implementation

soyuz-catalog treats the Unity Catalog OpenAPI spec at
`unitycatalog/api/all.yaml` as the source of truth. Where the spec is silent
or ambiguous, soyuz makes the choice that respects replace-style PATCH
semantics and rejects malformed requests instead of silently dropping data.
This file lists every place soyuz behaves differently from the official Java
server.

## Audit log

Upstream UC OSS / `all.yaml` define no audit surface — the reference
Java server logs nothing about who created/modified/deleted which
securable.  Agent-driven clients that need to cross-reference UC
mutations back to their own per-run views (the "which UC mutations
did this run make?" question) have nowhere to look, so soyuz adds
an audit table and one read endpoint:

- New `audit_log` table (Alembic 015) with `action` / `target` /
  `principal` / `agent_run_id` / `client_ip` / `detail` /
  `created_at` columns.
- `RequestIDMiddleware` captures `X-Principal` + `X-Agent-Run-Id`
  request headers into request-scoped `ContextVar`s.
- `services/audit_service.log_action(db, action, target, detail)`
  persists one row per successful mutation.  Best-effort —
  insertion failures are logged but do not break the underlying
  mutation route.
- `GET /audit-log` (root-mounted, like `/lineage` and `/tags`)
  supporting `?agent_run_id=<uuid>` filter and `limit` (1-1000,
  default 200).
- Six routes call `log_action` after a successful mutation:
  `tags.update_tags`, `tables.create_table`, `tables.delete_table`,
  `schemas.create_schema`, `schemas.update_schema`,
  `schemas.delete_schema`.  Other mutation routes follow the same
  pattern when a real consumer asks; these six are the bare
  minimum coverage of the soyuz write path.

The test at
`tests/test_openapi_conformance.py::test_soyuz_paths_are_subset_of_uc_spec`
skips `/audit-log` explicitly; the endpoint lives in
`DIVERGENCES.md` rather than `all.yaml` because it is deliberately
an over-the-spec feature, not a spec drift.

## Volumes: file IO

Upstream UC OSS and `all.yaml` describe only the five volume metadata
endpoints (create, list, get, update, delete). A real UC deployment
delegates file IO to whichever storage backend the volume was created
against — S3, ABFSS, GCS — via pre-signed URLs and separate
object-store credentials.

soyuz adds four routes under the existing `/volumes` root so
single-node deployments can store and serve files without provisioning
an object store:

- `POST {prefix}/volumes/{full_name}/files?path=…`
- `GET  {prefix}/volumes/{full_name}/files`
- `GET  {prefix}/volumes/{full_name}/files/{path:path}`
- `DELETE {prefix}/volumes/{full_name}/files/{path:path}`

Backend dispatch lives in `soyuz_catalog/storage/volume_files.py`
behind a `VolumeFileBackend` protocol. Today only `file://` is
implemented; cloud backends (s3 / abfss / gs) plug in as new classes
satisfying the protocol plus a case in `get_backend`.
Path-traversal attempts are rejected at the backend layer with
400 `INVALID_ARGUMENT`.

The test at
`tests/test_openapi_conformance.py::test_soyuz_paths_are_subset_of_uc_spec`
skips this family explicitly; the endpoint set lives in
`DIVERGENCES.md` rather than `all.yaml` because it is deliberately
an over-the-spec feature, not a spec drift.

## Pagination

### `max_results=0` means "use server default"

An earlier version of soyuz modelled pagination as `Query(ge=1, le=1000)`
and the service-layer `_effective_limit` treated anything `<= 0` as an
`INVALID_ARGUMENT` 422. Real-client testing proved this was wrong: the
upstream JVM `UCSingleCatalog` connector (from
`unitycatalog/connectors/spark`) calls `listTables(max_results=0)` on
every `SHOW TABLES` / catalog load, using `0` as the "I want the server
default" sentinel. Soyuz was 422'ing every single one of those calls,
breaking Spark SQL catalog discovery end-to-end.

The fix: `max_results=0` **and** `max_results=None` both resolve to
`DEFAULT_MAX_RESULTS` (100). Negative values and values above
`MAX_MAX_RESULTS` (1000) are still rejected. Route-level
`Query(ge=0, le=1000)` and service-level `_effective_limit` both
carry the new semantics; the `apply_keyset` gate stays as the last
line of defence against a caller that bypasses the route layer.

Applies to every list endpoint in soyuz (catalogs, schemas, tables,
volumes, functions, registered models, model versions, credentials,
external locations) — all nine routes share the same
`Query(ge=0, …)` template.

Regression tests:
`tests/test_pagination.py::test_apply_keyset_accepts_zero_as_default`,
plus the existing `test_list_rejects_out_of_range_max_results` in
`tests/test_catalogs.py`, `tests/test_schemas.py`,
`tests/test_tables.py`, and `tests/test_volumes.py` were flipped to
assert `max_results=0 → 200` (and use `-1` as the 422 sentinel).

## Catalogs

### `PATCH /catalogs/{name}` with `{"properties": {}}` clears all properties

UC OSS Java treats an empty properties map as "field not sent" and skips the
update entirely (`CatalogRepository.updateCatalog`, the early-return path
when `getProperties() == null || isEmpty()`). There is no documented way to
clear properties in UC OSS.

soyuz interprets the presence of the key in the JSON body literally: sending
`{"properties": {}}` replaces the stored properties with the empty map. This
matches the obvious reading of replace-style PATCH semantics and gives clients
a way to clear properties at all.

Regression test: `tests/test_catalogs.py::test_patch_empty_properties_clears`.

### `PATCH /catalogs/{name}` with unknown / read-only fields returns 422

UC OSS Java accepts request bodies with fields like `owner` (which is
read-only and not in the `UpdateCatalog` schema) and silently ignores them,
returning 200. The caller cannot tell the field was dropped.

soyuz's `UpdateCatalog` Pydantic model uses `extra="forbid"`, so any unknown
field — including `owner` — is rejected with HTTP 422 and a clear validation
error. Same treatment applies to `CreateCatalog`.

Regression test: `tests/test_catalogs.py::test_patch_owner_rejected`.

### `DELETE /catalogs/{name}` refuses when schemas exist unless `force=true`

UC OSS Java's `CatalogRepository.deleteCatalog` rejects the delete with
`FAILED_PRECONDITION` when the catalog has children and `force=false`, and
cascades when `force=true`. soyuz implements the same two-mode behaviour,
but explicitly in the service layer rather than relying on a database-level
`ON DELETE CASCADE`, so the cascade path is trivially testable on SQLite.
This is a behavioural *match*, not a divergence — it is listed here so that
future readers can see where the rule lives (`catalog_service.delete_catalog`).

Regression tests:
`tests/test_schemas.py::test_delete_catalog_with_schemas_conflict_409` and
`tests/test_schemas.py::test_delete_catalog_with_schemas_force_cascades`.

### `CatalogInfo.storage_location` is derived, id-keyed, and rename-invariant

The UC OpenAPI spec defines `storage_location` on `CatalogInfo` as
*"an automatically generated unique path under storage_root. Example:
`s3://bucket/ucroot/__unitystorage/catalogs/{catalog_id}`"*. soyuz
derives the field once on `create_catalog` from `storage_root` plus
the opaque `id`, and deliberately leaves `update_catalog` alone:
renaming a catalog must **not** recompute the derived path, because a
naive recompute would silently invalidate every child resource whose
physical layout keys on the old path. The same rule applies to
`SchemaInfo.storage_location`, which is derived from the schema's own
`storage_root` when present, falling back to the parent catalog's
`storage_root`.

UC OSS Java's `CatalogRepository` almost certainly uses a different
suffix layout than the `__unitystorage/{kind}/{id}` path soyuz emits —
the spec example is non-normative. This is a divergence by design:
soyuz emits a stable, round-trippable path that matches the spec
example verbatim rather than trying to byte-match Java's private
convention.

Regression tests:
`tests/test_catalogs.py::test_create_catalog_derives_storage_location_from_root`,
`tests/test_catalogs.py::test_rename_catalog_preserves_storage_location`,
`tests/test_schemas.py::test_create_schema_falls_back_to_parent_catalog_root`,
`tests/test_schemas.py::test_rename_schema_preserves_storage_location`.

## Schemas

### `PATCH /schemas/{full_name}` with `{"properties": {}}` clears all properties

Same UC OSS bug as the catalog PATCH: an empty properties map is treated as
"field not sent" and the update is skipped. soyuz honours the replace-style
reading and replaces the stored map with the empty map when the key is
present in the JSON body.

Regression test: `tests/test_schemas.py::test_patch_empty_properties_clears`.

### `PATCH /schemas/{full_name}` with unknown / read-only fields returns 422

Same fix as catalogs. `UpdateSchema` is declared with `extra="forbid"`, so
any field not in the spec's `UpdateSchema` shape — including the read-only
`owner`, `catalog_name`, `full_name` — is rejected with HTTP 422 rather than
silently dropped.

Regression tests:
`tests/test_schemas.py::test_patch_schema_unknown_field_422` and
`tests/test_schemas.py::test_patch_schema_owner_rejected_422`.

### Malformed `full_name` returns 400 instead of 404

UC OSS Java attempts to look up a schema with a malformed `full_name` (e.g.
missing dot) and surfaces a `NOT_FOUND`. soyuz parses the path parameter
eagerly in `schema_service.parse_full_name` and returns
`INVALID_ARGUMENT` (HTTP 400) when it is not exactly two non-empty
dot-separated parts, so clients get a clearer signal that the bug is in
their URL construction, not in the server state.

Regression test: `tests/test_schemas.py::test_get_schema_malformed_full_name_400`.

The same rejection path applies to table ``full_name`` values, which must
be exactly three non-empty dot-separated parts
(`catalog.schema.table`).

## Tables

### `PATCH /tables/{full_name}` returns 405 Method Not Allowed

The UC OpenAPI spec defines no `UpdateTable` request model and no PATCH
endpoint for tables. UC OSS Java nevertheless accepts a PATCH body and
silently ignores most of its contents — the same bug class soyuz exists
to fix. soyuz registers no PATCH handler on the tables router, so
FastAPI returns 405 Method Not Allowed for any PATCH to a table. Clients
that need to "update" a table must delete and recreate it.

Regression test: `tests/test_tables.py::test_patch_table_returns_405`.

### `POST /tables` rejects unknown fields, including inside `columns[i]`

`CreateTable` and `ColumnInfo` are both declared with `extra="forbid"`,
so a typo anywhere in the request body — including inside a column
entry, e.g. `type_neme` instead of `type_name` — is rejected with HTTP
422. UC OSS Java drops unknown column fields silently, which means a
typo in a column type survives the round-trip undetected.

Regression tests:
`tests/test_tables.py::test_create_table_unknown_field_rejected` and
`tests/test_tables.py::test_create_table_unknown_column_field_rejected`.

## Volumes

### `PATCH /volumes/{full_name}` with an empty body is a no-op

UC OSS Java's `VolumeRepository.updateVolume` dereferences fields on the
update payload without a null guard and surfaces an `INTERNAL` 500 when
the client sends `{}`. soyuz reads `model_fields_set` and returns the
unchanged volume with HTTP 200 — sending an empty PATCH body should be a
trivial round-trip, not a server error.

Regression test: `tests/test_volumes.py::test_patch_volume_empty_body_is_noop`.

### `PATCH /volumes/{full_name}` rejects immutable / unknown fields with 422

The UC spec restricts volume updates to `new_name` and `comment` only;
`storage_location` and `volume_type` are immutable and `properties` does
not exist on a volume. UC OSS Java accepts request bodies containing
`storage_location` or unknown fields and silently ignores them, returning
200 — the caller cannot tell their change was dropped.

soyuz's `UpdateVolume` model is declared with `extra="forbid"`, so any
field outside `{new_name, comment}` is rejected with HTTP 422. This makes
"this storage path is wrong, let me PATCH it" fail loudly instead of
appearing to succeed.

Regression tests:
`tests/test_volumes.py::test_patch_volume_unknown_field_422`,
`tests/test_volumes.py::test_patch_volume_storage_location_rejected_422`,
`tests/test_volumes.py::test_patch_volume_type_rejected_422`.

### `POST /volumes` rejects unknown fields with 422

`CreateVolume` is declared with `extra="forbid"`, same UC OSS bug-fix
policy as every other create body in this project. A typo like
`volumetype` instead of `volume_type` is rejected with 422 instead of
silently creating a volume with a missing required field.

Regression test: `tests/test_volumes.py::test_create_volume_unknown_field_rejected`.

### `DELETE /schemas/{full_name}` refuses when tables or volumes exist unless `force=true`

Symmetric to the `DELETE /catalogs` cascade-gate rule: a schema that
still owns tables or volumes cannot be dropped without `force=true`,
which then cascades through the ORM relationships
(`Schema.tables`, `Schema.volumes`, both `cascade="all, delete-orphan"`)
and from there into `Table.columns`. This is a behavioural *match*
with UC OSS Java — listed here so that future readers can see where
the rule lives (`schema_service.delete_schema`). Both child kinds are
reported in the rejection message when both block the delete.

The full cascade chain is therefore
`catalog → schema → {table → column, volume}`, gated symmetrically at
every step (catalog gates on schemas, schema gates on tables and
volumes, table cascades columns unconditionally because columns have
no independent existence).

Regression tests:
`tests/test_volumes.py::test_delete_schema_with_volumes_conflict_409`,
`tests/test_volumes.py::test_delete_schema_with_volumes_force_cascades`,
`tests/test_tables.py::test_delete_schema_with_tables_conflict_409`,
`tests/test_tables.py::test_delete_schema_with_tables_force_cascades`,
and
`tests/test_tables.py::test_delete_catalog_force_cascades_through_tables_and_columns`.

### Malformed volume `full_name` returns 400 instead of 404

Same rule as schemas and tables: `volume_service.parse_full_name`
rejects anything that is not exactly three non-empty dot-separated
parts with `INVALID_ARGUMENT`, giving clients a clearer signal than UC
OSS's 404.

Regression test: `tests/test_volumes.py::test_get_volume_malformed_full_name_400`.

## Storage credentials

### `CredentialInfo.aws_iam_role.unity_catalog_iam_arn` is always absent

The UC spec defines `unity_catalog_iam_arn` on `AwsIamRoleResponse` as
"the ARN of the AWS IAM identity the Unity Catalog server itself uses
to assume the client-supplied role" — the server-side half of the
confused-deputy mitigation. soyuz has no runtime IAM identity of its
own (cloud-identity work is out of scope per the README) so the column
exists on the model for shape-fidelity but is always `None`. The
credential routes serialise with `response_model_exclude_none=True`,
so the field is simply absent from the JSON response rather than
appearing as `null`.

Regression test: `tests/test_credentials_crud.py::test_create_credential_minimal`.

### `Credential.aws_iam_role.external_id` is minted on create and never rotated

UC OSS Java does not document whether PATCH on a credential's
`aws_iam_role` payload rotates the server-minted `external_id`. soyuz
mints the value once on `create_credential` and deliberately does
**not** rotate it on PATCH: the value exists specifically to prevent
confused-deputy attacks on STS role assumption, and leaking it through
a rotate path would defeat that purpose. The spec defines no
explicit rotate-external-id operation, so this is a conservative
reading rather than a conscious divergence.

Regression test:
`tests/test_credentials_crud.py::test_update_credential_preserves_external_id_on_role_replace`.

### `CredentialPurpose` is validated as a single-value `Literal["STORAGE"]`

The UC spec defines exactly one purpose (`STORAGE`) today. soyuz types
the field as `Literal["STORAGE"]` on both request and response shapes,
so a typo like `STORGE` — or a future upstream purpose soyuz has not
updated for — surfaces as 422 at the Pydantic layer instead of
landing in the database. This is the same "silently-accept-garbage"
rejection policy the rest of the project applies everywhere.

Regression test:
`tests/test_credentials_crud.py::test_create_credential_invalid_purpose_422`.

### `DELETE /credentials/{name}?force=true` cascades through external locations

One of the few places soyuz aligns with UC OSS Java rather than
diverging: when `force=true` is passed, the service deletes every
referencing external location first and then removes the credential
row in the same transaction. Without `force`, the delete is rejected
with 409 `ALREADY_EXISTS` and the error message names the number of
external locations still bound. Mirrors the
`DELETE /catalogs/{name}?force=true` shape used for
catalog→schema→table→column cascade.

## Temporary credentials

### `POST /temporary-{table,volume}-credentials` return a per-scheme stub, no real tokens

The UC OpenAPI spec defines two endpoints that vend short-lived cloud
credentials (S3 STS tokens, Azure user-delegation SAS, or GCP OAuth
tokens) scoped to a specific table or volume. Real vending needs
boto3 / azure-identity / google-auth as runtime dependencies and
per-deployment IAM configuration, and is explicitly out of scope.
Until a downstream deployment wires that up soyuz
ships a spec-conformant **stub**: the response shape matches
`TemporaryCredentials` exactly, `expiration_time` is always populated
(one hour from now), and the cloud-specific field is selected from the
resolved row's `storage_location` scheme:

| scheme      | cloud field on the wire                              |
|-------------|------------------------------------------------------|
| `s3`, `s3a` | `aws_temp_credentials: {}`                           |
| `abfss`     | `azure_user_delegation_sas: {}`                      |
| `gs`        | `gcp_oauth_token: {}`                                |
| `file` / legacy / unparseable | *(none — expiration-only)*         |

The nested object is deliberately *empty*: populating placeholder
strings would risk a client treating them as real credentials;
returning `None` would make the per-cloud routing invisible on the
wire. An empty dict is spec-legal (every nested field is optional in
the UC OpenAPI schema) and unambiguously signals "the server routed
you to cloud X, but no token was minted". The read path stays lax for
legacy rows whose `storage_location` is `NULL` or a bare path — those
fall through to the expiration-only branch,
matching the write-path-only validation rule from the "Storage URIs"
section below.

This is a behavioural *stub*, not an intentional divergence — it is
listed here so future readers can find the rationale in one place.

Regression tests:
`tests/test_temporary_credentials.py::test_table_credentials_file_scheme_returns_expiration_only`,
`tests/test_temporary_credentials.py::test_table_credentials_routes_per_storage_scheme`,
`tests/test_temporary_credentials.py::test_volume_credentials_file_scheme_returns_expiration_only`,
`tests/test_temporary_credentials.py::test_volume_credentials_routes_per_storage_scheme`,
and
`tests/test_temporary_credentials.py::test_resolve_scheme_falls_back_for_missing_and_legacy_locations`.

### `POST /temporary-{table,volume}-credentials` reject the `UNKNOWN_*_OPERATION` sentinel

The UC spec defines `TableOperation` and `VolumeOperation` as tri-state
enums where the first member (`UNKNOWN_TABLE_OPERATION` /
`UNKNOWN_VOLUME_OPERATION`) exists only as a protobuf default. UC OSS
Java accepts the sentinel and proceeds as if no operation had been
requested. soyuz's service layer rejects it with HTTP 400
`INVALID_ARGUMENT` — a real client must send `READ` / `READ_WRITE` or
`READ_VOLUME` / `WRITE_VOLUME`. Accepting the sentinel would reproduce
the same silently-accept-garbage behaviour that `extra="forbid"` is
everywhere else written to prevent.

Regression tests:
`tests/test_temporary_credentials.py::test_table_credentials_rejects_unknown_operation_sentinel`
and
`tests/test_temporary_credentials.py::test_volume_credentials_rejects_unknown_operation_sentinel`.

### `POST /temporary-path-credentials` follows the same stub policy

Soyuz also exposes a path-addressed variant. Unlike the table/volume
variants the URL is client-supplied, so the URI parser runs on the
write-path strictness setting: an empty / unparseable /
unsupported-scheme URL surfaces as 400 rather than the read-path lax
fallback. The `UNKNOWN_PATH_OPERATION` sentinel is rejected with 400
for the same reason the table/volume sentinels are rejected; real
callers must send `PATH_READ`, `PATH_READ_WRITE`, or
`PATH_CREATE_TABLE`. Routing on the parsed URL scheme produces
byte-identical stub shapes to the per-table/volume table above, so a
future consumer that wants credentials "for the staging-table URL"
can use this endpoint with the `staging_location` returned by
`POST /staging-tables` instead of shoe-horning the staging id through
`/temporary-table-credentials` (soyuz does not treat staging-table
rows as regular tables — see the "Staging tables" section below).

Regression tests:
`tests/test_temporary_path_credentials.py::test_path_credentials_routes_per_scheme`,
`tests/test_temporary_path_credentials.py::test_path_credentials_file_scheme_returns_expiration_only`,
`tests/test_temporary_path_credentials.py::test_path_credentials_rejects_unknown_operation_sentinel`,
and
`tests/test_temporary_path_credentials.py::test_path_credentials_rejects_unsupported_scheme`.

## Metastore

### `GET /metastore_summary` returns only `metastore_id`

The upstream UC OpenAPI `GetMetastoreSummaryResponse` schema defines
exactly one field: `metastore_id`. Databricks-flavoured forks of the
spec return a much richer summary (name, storage root, region, owner,
cloud, …) but the upstream `all.yaml` we pin as the contract does
not, and soyuz refuses to silently extend it. The backing row is
bootstrapped lazily on the first call — soyuz has no
`CreateMetastore` endpoint and the spec does not expose one either,
so the service layer mints a UUID-hex id on the first request and
returns that same id forever after. Each soyuz deployment therefore
reports a distinct stable id, and test fixtures get a fresh id per
in-memory engine without extra plumbing.

Regression tests:
`tests/test_metastore_summary.py::test_metastore_summary_bootstraps_lazily`,
`tests/test_metastore_summary.py::test_metastore_summary_is_stable_across_calls`,
and
`tests/test_metastore_summary.py::test_metastore_summary_creates_exactly_one_row`.

## Staging tables

### `POST /staging-tables` is allocation-only; rows are not resolvable as regular tables

The UC OpenAPI spec flags the staging-table endpoint as
`WARNING: experimental` and describes a two-step protocol: the
server allocates a URL, the client writes data under it, and a
follow-up *promote* step turns the allocation into a real managed
table. soyuz implements the allocation half only — the promote step
would need the managed-table materialisation work that stays
explicitly out of scope. As a consequence:

- There is no per-schema uniqueness on `(schema_id, name)`. Two
  concurrent POSTs for the same triple succeed with distinct ids and
  distinct `staging_location` URLs, so clients can retry safely.
- `staging_location` is derived from the parent schema's
  `storage_location` first (itself derived via `derive_managed_location`),
  falling back to the catalog's bare `storage_root`.
  Both being absent is a 400: the whole point of the endpoint is to
  hand back a URL, so refusing the request at allocation time is
  better than letting the client cache a `None`.
- A UUID-hex segment under `__staging__/` keeps two allocations under
  the same name from colliding on disk even with no uniqueness
  constraint.
- Staging-table ids **are** resolvable through
  `POST /temporary-table-credentials`. The resolver tries the real-table
  lookup first, and on a miss falls through to the staging-table service
  before returning 404. An earlier version kept staging ids out of this
  path on the grounds that clients should use
  `POST /temporary-path-credentials` with the returned `staging_location`
  instead, but the upstream JVM `UCSingleCatalog` connector does not
  honour that split — it creates a staging table and then immediately
  vends credentials against the same id — so the resolver serves both
  shapes. The staging row's `staging_location` scheme drives the same
  per-scheme stub dispatcher as real tables, so the response shape is
  identical between the two code paths.
- There is no GET / LIST / DELETE / PATCH route for staging tables
  — the upstream spec defines only the POST. The rows are
  short-lived by design.

Regression tests:
`tests/test_staging_tables.py::test_staging_table_happy_path`,
`tests/test_staging_tables.py::test_staging_table_two_allocations_under_same_name_succeed`,
`tests/test_staging_tables.py::test_staging_table_requires_storage_root_on_parent`,
`tests/test_staging_tables.py::test_staging_table_parent_rename_propagates_to_response`,
`tests/test_temporary_credentials.py::test_table_credentials_resolves_staging_table_id`,
and
`tests/test_temporary_credentials.py::test_table_credentials_staging_fallthrough_routes_file_scheme`.

<!--
ADR-0011 removed the soyuz-side "Managed Delta tables via Spark"
divergence that ADR-0006 had put here. soyuz is now a passthrough Delta
commit coordinator for file:// tables with a real 200 / 400 / 409 / 429
contract at POST /delta/preview/commits, so soyuz no longer diverges
from upstream for this endpoint.

What remains is upstream: Spark's Delta SQL extension intercepts
`USING delta` DDL before the UC plugin is invoked, so Spark's
managed-Delta flow never reaches soyuz's coordinator and the analyzer
fails with SCHEMA_NOT_FOUND from spark_catalog. The upstream UC docs
themselves carry a TODO for covering managed Delta. Not a soyuz
divergence — the coordinator contract is exercised end-to-end by
tests/test_delta_commits.py. The Spark-layer consequence is pinned by
tests/test_spark_roundtrip.py::test_managed_delta_table_creation_via_spark
(strict xfail, reason cites the connector gap) and by
tests/test_spark_compatibility.py::C-managed-delta-insert.
-->

The staging-id fallthrough in `credentials_service` (see the "Staging
tables" entry above) remains correct on its own merits — it fixes the
JVM connector's `createStagingTable` →
`generateTemporaryTableCredentials` hand-off.

## Functions

### `PATCH /functions/{full_name}` returns 405

The UC OpenAPI spec defines no `UpdateFunction` operation: the
`/functions/{name}` path carries only `GET` and `DELETE`. UC OSS
Java appears to accept arbitrary PATCH bodies on the matching URL
and return 200 (the same "silently accept garbage" bug class that
`extra="forbid"` rejects on request bodies). soyuz registers no
PATCH handler for the functions resource, and FastAPI surfaces the
absent method as 405 Method Not Allowed — same shape as the tables
resource (see the Tables section).

Regression test: `tests/test_functions.py::test_patch_function_returns_405`.

### `routine_body` / `sql_data_access` / `security_type` pinned as `Literal`

The three enum fields on `FunctionInfo` (`routine_body` ∈ {SQL,
EXTERNAL}, `sql_data_access` ∈ {CONTAINS_SQL, READS_SQL_DATA,
NO_SQL}, `security_type` ∈ {DEFINER}) are all typed as
`typing.Literal` on `CreateFunction`. A typo or an out-of-band
value — including the protobuf default sentinels that some UC
clients still send — surfaces as 422 at the Pydantic layer instead
of landing in the database as a free-form string. This is the same
`extra="forbid"`-class policy the rest of the project applies
everywhere.

Regression tests:
`tests/test_functions.py::test_create_function_invalid_routine_body_422`,
`tests/test_functions.py::test_create_function_invalid_sql_data_access_422`.

### `FunctionParameterInfo` rejects unknown fields inside the `parameters` array

The UC spec defines `FunctionParameterInfo` with a fixed set of
fields (`name`, `type_text`, `type_json`, `type_name`, `position`,
optional mode / type / default / comment / precision / scale /
interval_type). soyuz serialises parameter lists into a single
JSON column, so an unchecked unknown key would round-trip silently
and mask a client bug indefinitely. `extra="forbid"` on
`FunctionParameterInfo` rejects any extra field at the Pydantic
layer — same logic as the already-pinned `ColumnInfo.extra="forbid"`
that guards the `columns` array on tables.

Regression test:
`tests/test_functions.py::test_create_function_unknown_parameter_field_422`.

### `input_params` / `return_params` stored as JSON blobs, not child rows

The UC REST surface treats a function's parameter lists as a
read-only read-at-once blob: there is no
`/functions/{name}/parameters` sub-resource, no partial-update
operation, no individual-parameter lookup. soyuz takes this at its
word and stores the two arrays as single JSON columns
(`{"parameters": [...]}`) on the `functions` row instead of paying
for a child table and the join that implies. The wire shape is
identical to the spec and UC OSS Java makes the same call.

## Registered models

### `DELETE /models/{full_name}?force=true` cascades through model versions

Mirrors the `/catalogs/{name}?force=true` and
`/credentials/{name}?force=true` policy: without `force` the
delete is rejected with 409 `ALREADY_EXISTS` and the error message
names the number of versions still bound; with `force=true` the
service deletes every child `ModelVersion` first and then removes
the registered model row, all in one transaction. UC OSS Java's
referenced behaviour is "all versions of the model must have
already been deleted" (quoting the spec description) — soyuz is
strictly *more* permissive here when the client opts in with
`force`, which is the same shape used for every other parent
resource in this project.

Regression tests:
`tests/test_registered_models.py::test_delete_registered_model_refused_when_versions_exist`,
`tests/test_registered_models.py::test_delete_registered_model_force_cascades_versions`.

### `CreateRegisteredModel` rejects `storage_location`

The UC `CreateRegisteredModel` schema does **not** define a
`storage_location` field — the field exists only on the
`RegisteredModelInfo` response where it is a server-owned optional.
soyuz's `CreateRegisteredModel` Pydantic model uses
`extra="forbid"`, so a client that sends `storage_location` on
create gets a 422. soyuz also never derives the field itself
(unlike catalogs / schemas / tables which compute a managed
location from `storage_root`): the column exists for
shape-fidelity but stays `None` until a real consumer asks for a
derivation rule. This is a deliberately tight reading of the spec
rather than the silently-accept-garbage behaviour the project
rejects everywhere else.

Regression test:
`tests/test_registered_models.py::test_create_registered_model_unknown_field_422`.

## Model versions

### `ModelVersion.status` is always `READY` on soyuz-created rows

The UC `ModelVersionStatus` enum defines four states:
`MODEL_VERSION_STATUS_UNKNOWN`, `PENDING_REGISTRATION`,
`FAILED_REGISTRATION`, `READY`. Three of them only make sense
when the server runs an asynchronous registration pipeline that
watches artifact uploads (the MLflow Model Registry flow). soyuz
does not: every `POST /models/versions` commits immediately and
the row's status is set to `READY` at create time. The other three
states cannot arise from soyuz's own writes.

The column stays as a free-form `String(32)` rather than a SQL
`CHECK` constraint so that a future migration-in of real UC data
can carry non-`READY` rows without rejecting them at the DB layer.
`UpdateModelVersion` is typed as `{"comment": str | None}` only,
with `extra="forbid"`, so a client cannot overwrite the status
through the update endpoint.

The UC spec also defines a `PATCH /models/{full_name}/versions/
{version}/finalize` endpoint whose only documented effect is to
flip `PENDING_REGISTRATION` → `READY`. soyuz does not register
this route because there is no non-`READY` state to finalise. A
client that hits the path gets a 404 from FastAPI; the follow-up
sprint that adds the real async pipeline will wire up the handler.

Regression tests:
`tests/test_model_versions.py::test_create_version_happy_path`
(asserts `status == "READY"` on create),
`tests/test_model_versions.py::test_patch_version_status_rejected_422`.

### Monotonic version numbering by `MAX(version) + 1`, 409 on race

The UC spec defines `version` as a server-assigned monotonic
integer per registered model but says nothing about the assignment
strategy. soyuz computes `MAX(version) + 1` scoped to the parent
`registered_model_id` in the same transaction as the insert and
lets the `(registered_model_id, version)` unique constraint catch
concurrent creates. The second caller in a race gets 409
`ALREADY_EXISTS` with a message asking them to retry, same shape
as a duplicate-name collision on any other resource. A
`SELECT ... FOR UPDATE` on the parent would be tidier but costs an
extra round-trip per create and does not work on SQLite
(row-level locking is a PostgreSQL-only feature). The racy-retry
compromise is what UC OSS Java also does.

Regression test:
`tests/test_model_versions.py::test_create_version_auto_increments`.

## Storage URIs

### `storage_location` / `storage_root` schemes are validated on write

UC OSS Java accepts any string for a table / volume ``storage_location``
or a schema ``storage_root`` — including bare paths, unknown URI
schemes, and empty strings — and pushes the eventual failure down to
whichever engine first tries to open the path. That is the same
*silently-accept-garbage* bug class that ``extra="forbid"`` and the
``UNKNOWN_*_OPERATION`` sentinel rejection exist to prevent.

soyuz-catalog parses every storage URI at write time via
`soyuz_catalog.storage.parse_storage_uri` and rejects schemes outside
`{file, s3, s3a, abfss, gs}` with HTTP 400 `INVALID_ARGUMENT`. A missing
scheme (e.g. a bare `/tmp/foo`) and an empty string are rejected the
same way. The parse is purely syntactic: it does not touch the network,
does not check bucket existence, and does not normalise the path, so a
client still gets back exactly the string it sent on a round-trip GET.

Read paths are deliberately *not* validated: rows written before this
check was added may have legacy free-form values and must keep loading.
Only ``create_*`` calls gate on the parser. Updates are unaffected
because tables have no PATCH route at all and ``UpdateVolume`` already
rejects ``storage_location`` as immutable.

The ``/temporary-{table,volume}-credentials`` endpoints reuse the same
parser to select the response shape (see the "Temporary credentials"
section above), but the parse is wrapped in a read-path-lax fallback:
legacy rows whose ``storage_location`` does not round-trip through
``parse_storage_uri`` route to the expiration-only branch instead of
raising.

Regression tests:
`tests/test_storage_uri.py` (parser in isolation),
`tests/test_tables.py::test_create_table_rejects_unsupported_storage_scheme`,
`tests/test_tables.py::test_create_table_rejects_bare_path_storage_location`,
`tests/test_volumes.py::test_create_volume_rejects_unsupported_storage_scheme`,
and
`tests/test_schemas.py::test_create_schema_rejects_unsupported_storage_root_scheme`.

## Keyset pagination

### List endpoints order by `(created_at, id)`, not by name

UC OSS Java's list endpoints do not document a total order — they fall
out of whatever the underlying JPA query planner picks, which in
practice is usually the clustered index and *usually* name-sorted but
is not guaranteed.

soyuz orders every list endpoint by `(created_at ASC, id ASC)` — the
tuple that the keyset pagination cursor is built from. Both columns are on every resource,
`created_at` is never mutated after insert, and `id` is a UUID4
primary key, so together they form a stable total order that survives
concurrent inserts without the phantom-page / skipped-row failure
mode of `OFFSET`-based pagination. The UC OpenAPI spec defines no
list ordering, so this is not a spec violation, but it is a
user-visible change: `GET /catalogs` now returns rows in insertion
order rather than alphabetical order.

See `docs/adr/0003-keyset-pagination.md` (ADR-0003) for the full
design rationale.

Regression tests:
`tests/test_pagination.py` (helpers in isolation),
`tests/test_catalogs.py::test_list_multi_page_walk`,
`tests/test_catalogs.py::test_list_boundary_exact_page_size`,
`tests/test_schemas.py::test_list_schemas_multi_page_walk`,
`tests/test_tables.py::test_list_tables_multi_page_walk`, and
`tests/test_volumes.py::test_list_volumes_multi_page_walk`.

### Tampered or unparseable `page_token` returns 400, not a silent reset

A malformed `page_token` — tampered base64, wrong JSON shape, wrong
value types — is rejected by
`soyuz_catalog.pagination.decode_page_token` as HTTP 400
`INVALID_ARGUMENT`. A lax implementation would treat a broken token
as "start from the beginning", which is indistinguishable from a
successful page walk and would silently serve the first page forever
if a client's token storage ever corrupted. This is the same
silently-accept-garbage bug class that `extra="forbid"` and the
`UNKNOWN_*_OPERATION` sentinel rejection exist to prevent.

Regression tests:
`tests/test_pagination.py::test_decode_rejects_non_base64`,
`tests/test_pagination.py::test_decode_rejects_wrong_shape`,
`tests/test_catalogs.py::test_list_rejects_tampered_page_token`,
`tests/test_schemas.py::test_list_schemas_rejects_tampered_page_token`,
`tests/test_tables.py::test_list_tables_rejects_tampered_page_token`,
and
`tests/test_volumes.py::test_list_volumes_rejects_tampered_page_token`.

## Error envelope

### Every 4xx/5xx uses the same `{error_code, message, request_id}` body

UC OSS Java (and stock FastAPI) return at least two error shapes: the
service-layer envelope for semantic failures, and the pydantic / Jackson
validation shape for request-body problems. A client talking to both paths
has to branch on shape as well as status code.

soyuz normalises every error response — 400, 404, 409, 422, 500 — into a
single body:

```json
{
  "error_code": "INVALID_ARGUMENT",
  "message": "body.name: Field required",
  "request_id": "9c4f...",
  "details": [ ... optional, only on 422 ... ]
}
```

On 422 the original pydantic `errors()` list is preserved under `details`
so structured clients keep everything they had before; `message` is a
flattened one-line summary for callers that just print it to the user.

Uncaught `Exception`s are caught inside `RequestIDMiddleware` (not via a
FastAPI exception handler, because the generic-`Exception` handler lives
in Starlette's `ServerErrorMiddleware` *above* user middleware and would
lose the correlation header) and returned as a 500 with
`error_code = "INTERNAL"`.

Regression tests:
`tests/test_validation_envelope.py::test_422_uses_envelope_on_missing_field`,
`tests/test_validation_envelope.py::test_422_uses_envelope_on_extra_forbidden_field`,
`tests/test_error_envelope_contract.py::test_every_known_error_has_envelope`,
and
`tests/test_error_envelope_contract.py::test_500_fallback_has_envelope`.

### `X-Request-ID` correlation header

Every request gets a UUID-hex correlation ID, minted by
`RequestIDMiddleware` (or accepted from the inbound `X-Request-ID` header
if it parses as a valid UUID — malformed inbound values are replaced
rather than propagated, same silently-accept-garbage rule as everywhere
else). The ID is echoed back as the `X-Request-ID` response header and
included in every error body as `request_id`, and it is also attached to
every log record via a `contextvars`-based logging filter so access-log
lines and error responses can be correlated one-to-one.

This is a soyuz addition; UC OSS Java offers no request-correlation
header.

Regression tests:
`tests/test_request_id.py::test_mints_uuid_when_header_absent`,
`tests/test_request_id.py::test_honours_valid_inbound_request_id`,
`tests/test_request_id.py::test_rejects_malformed_inbound_request_id`,
and
`tests/test_request_id.py::test_error_body_contains_request_id`.

## Permissions

### Storage-only, no enforcement

The `/permissions/{securable_type}/{full_name}` endpoints persist
grants and return them on demand, but soyuz-catalog **never consults
the `permissions` table on any other endpoint**. Access control is
expected to live in an auth proxy in front of soyuz; this server is
a data plane, not an identity plane. See
[ADR-0005](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0005-permissions-without-enforcement.md) for
the full rationale and the proxy-offload design.

UC OSS Java takes the same stance in practice (OSS ships no
enforcement layer) but does not document the decision; a reader who
greps for `permission` in the soyuz codebase would otherwise
reasonably wonder whether the CRUD surface is hooked into some
hidden check.

### Per-type privilege allow-set

UC OSS Java accepts any `Privilege` enum value on any
`SecurableType` at API time — the Java server does not know which
privileges make sense on which targets, and defers the validation
to the enforcement layer it does not ship. soyuz-catalog rejects at
write time with `400 INVALID_ARGUMENT` before any row is inserted:
a `PATCH` that adds `SELECT` on a catalog, or `CREATE SCHEMA` on a
table, is a 400 with a clear error message.

The allow-set is hand-curated from the upstream `Privilege` enum's
`x-enum-descriptions` and lives in
`soyuz_catalog.services.permissions_service._ALLOWED_PRIVILEGES`.
The current mapping:

| Securable           | Allowed privileges                                                                              |
|---------------------|-------------------------------------------------------------------------------------------------|
| `metastore`         | `CREATE CATALOG`, `CREATE EXTERNAL LOCATION`, `CREATE STORAGE CREDENTIAL`                       |
| `catalog`           | `USE CATALOG`, `CREATE SCHEMA`                                                                  |
| `schema`            | `USE SCHEMA`, `CREATE TABLE`, `CREATE FUNCTION`, `CREATE VOLUME`, `CREATE MODEL`                |
| `table`             | `SELECT`, `MODIFY`                                                                              |
| `function`          | `EXECUTE`                                                                                       |
| `volume`            | `READ VOLUME`                                                                                   |
| `registered_model`  | `EXECUTE`                                                                                       |
| `external_location` | `READ FILES`, `WRITE FILES`, `CREATE EXTERNAL TABLE`, `CREATE EXTERNAL VOLUME`, `CREATE MANAGED STORAGE` |
| `credential`        | `CREATE EXTERNAL LOCATION`                                                                      |

`remove` lists are **not** gated — removing a privilege that was
never allowed on this type is harmless (no row to delete) and makes
cleanup after a future allow-set tightening possible.

Regression test:
`tests/test_permissions.py::test_disallowed_privilege_for_type_400`.

### `PATCH /permissions/...` is additive, not replace-style

Every other `PATCH` route in soyuz is replace-style: a field present
in the body is written through, absent fields are untouched, and
`properties: {}` clears all properties (see the `## Catalogs`
section). Permissions break the pattern: the spec's
`UpdatePermissions { changes: PermissionsChange[] }` shape is
explicitly additive — clients submit a batch of add / remove
operations rather than a full desired state.

This is not a soyuz choice, it is the upstream spec. The asymmetry
is documented here so a reader does not wonder why this one PATCH
route has a different contract from the other eight.

Within a single change, `add` and `remove` may reference the same
privilege. The spec is silent on precedence; soyuz applies removes
first, then adds, so the net effect is **add wins**. This
tiebreaker matches the obvious reading of "the user wanted the
privilege after the call".

Regression tests:
`tests/test_permissions.py::test_patch_add_then_remove`,
`tests/test_permissions.py::test_patch_idempotent_add`,
`tests/test_permissions.py::test_patch_add_wins_on_overlap`.

### Cascade on parent delete, always

When any securable is deleted via its own `DELETE` endpoint, every
grant attached to it — and to any descendants — is wiped in the
same transaction. The cascade is **not gated by `force=true`**:
grants are not first-class children the way tables or volumes are,
and a parent-delete flow that left stale grants pointing at a
now-free id would be a real privilege bug once the id is reused.

The cascade is implemented at the service layer by
`soyuz_catalog.services.permissions_service.wipe_permissions_for`,
which every `delete_*` service calls before committing. For
composite deletes (catalog → schemas → tables, etc.) the parent
service collects the full descendant id set up front and issues
one bulk `DELETE FROM permissions` per securable type.

Regression tests:
`tests/test_permissions.py::test_delete_catalog_cascades_permissions`,
`tests/test_permissions.py::test_delete_credential_force_cascades_location_grants`.

### Effective computation (over-the-spec)

**soyuz-specific, over-the-spec extension.** Upstream `all.yaml` and
the UC OSS Java server define only the **direct-grant** form —
`GET /permissions/{securable_type}/{full_name}` returns grants bound
to exactly that row, with no inheritance walking. A client that
wants to answer "what privileges does Alice *effectively* have on
this table" has to pull the grants at the table, schema, catalog,
and metastore levels separately and do the union itself. soyuz
moves the computation server-side with a dedicated endpoint:

```
GET /api/2.1/unity-catalog/effective-permissions/{securable_type}/{full_name}
```

The response shape is identical to the direct-grant endpoint
(`PermissionsList` / `PrivilegeAssignment`), so clients can swap
URLs without changing their grant-display code.

**Inheritance rule.** Effective privileges for a principal `P` on a
securable `L` are the set-union of every privilege granted to `P` on
`L` or on any of `L`'s ancestors in the resource hierarchy, computed
dynamically at read time against the current `permissions` table. The
ancestor chains (leaf → root) are:

| Leaf type          | Chain                                              |
|--------------------|----------------------------------------------------|
| `metastore`        | `[metastore]`                                      |
| `catalog`          | `[catalog, metastore]`                             |
| `external_location`| `[external_location, metastore]`                   |
| `credential`       | `[credential, metastore]`                          |
| `schema`           | `[schema, catalog, metastore]`                     |
| `table`            | `[table, schema, catalog, metastore]`              |
| `volume`           | `[volume, schema, catalog, metastore]`             |
| `function`         | `[function, schema, catalog, metastore]`           |
| `registered_model` | `[registered_model, schema, catalog, metastore]`   |

The walk is **leaf-ward only**: inheritance flows from ancestors to
descendants, never the reverse. A table-level grant does not show up
when querying effective permissions on its parent schema.

**Set-union, no conflict resolution.** UC grants are additive (no
deny rows), so set-union is the only honest aggregation. There is
no precedence rule because there is no conflict — a principal either
has a privilege at some level of the chain or it does not. The
endpoint returns the *set* without tracking which ancestor
contributed each privilege; clients that need provenance must fall
back to the N direct lookups the existing
`GET /permissions/{type}/{name}` endpoint already supports.

**Out of scope for the MVP.**

- **No `inherited_from` annotation.** Databricks' effective-permissions
  shows which ancestor row contributed each privilege; soyuz's MVP
  returns the unioned set only so clients can reuse the existing
  `PrivilegeAssignment` shape. The response shape can be extended later
  if a real consumer asks.
- **No privilege *applicability* filter.** Databricks filters by
  "which privileges make sense at this level" (e.g., `CREATE
  CATALOG` on a table is nonsense). soyuz unions everything as an
  MVP — the union never invents privileges that weren't granted
  somewhere, so the filter is cosmetic.
- **No column-level support.** `resolve_securable` does not handle
  `column` as a securable type; effective-permissions inherits the
  same scope.
- **No writes.** Only `GET` is implemented — the effective set is a
  view over the underlying `permissions` table, not stored state.

**Conformance test skip.** The new endpoint prefix
`/api/2.1/unity-catalog/effective-permissions/` is skipped in
`tests/test_openapi_conformance.py` alongside `/lineage/`, `/tags/`,
and `/delta/v1/` so the `all.yaml` subset check stays accurate.

Regression tests: `tests/test_effective_permissions.py::*` — 15
cases covering inheritance flow, sibling isolation, union across
levels, principal filter, and one sanity case per securable type
that has a non-trivial chain (volume / function / registered
model / metastore).

## Delta commits preview

`GET /delta/preview/commits` and `POST /delta/preview/commits` are
the two `DeltaCommits` operations defined by the upstream spec. Both
are implemented in soyuz, but under semantics the spec author would
recognise as stricter than a UC OSS Java deployment.

### `getCommits` returns an empty commits list by construction

The spec describes `commits` as *"the unbackfilled Delta commits
currently being tracked by the UC coordinator"*. soyuz runs no
commit coordinator — it has no write path into Delta tables, no
tracking table, and no notion of an unbackfilled commit. The
spec-conformant answer to *"which commits is the coordinator
tracking?"* is therefore *"none, always"*, and that is what the
endpoint returns: `commits: []` plus an accurate
`latest_table_version` sourced from `DeltaTable(path).version()` on
the underlying `_delta_log/` on disk.

A client that reads the list as *"commits I still need to backfill"*
(the correct reading of the spec) sees a consistent answer and
proceeds. A client that expected the full backfilled history would
have been wrong about the endpoint's meaning regardless of
implementation — `DeltaTable.history()` is the right data source for
that case, and it is available client-side without going through
UC.

**TODO for follow-up.** If a real consumer ever needs the history
passthrough, extend
`soyuz_catalog.services.delta_commits_service.get_commits` to
populate the list from `DeltaTable(path).history()` plus
`os.stat()` on `_delta_log/*.json` — the spec's
`file_name` / `file_size` / `file_modification_timestamp` fields
all come from the commit-log files on disk.

### `file://` storage only

Only `file://` Delta tables are supported on the read path. Any
other scheme — `s3`, `s3a`, `abfss`, `gs` — returns **501 Not
Implemented**, because opening a cloud Delta table from the
server-side would require the credential-vending layer that is
an explicit non-goal. The 501 message names the offending scheme so
a client knows what to change.

<!--
ADR-0011: the "commit returns 501" divergence is retired.
`POST /delta/preview/commits` is now a real passthrough Delta commit
coordinator for file:// tables, tracked via the
`delta_unbackfilled_commits` table. The dedicated
`COMMIT_COORDINATOR_UNSUPPORTED` error code is still alive but narrower:
it now applies only to the Delta REST Kernel UpdateTable coordinator
actions (`add-commit`, `set-latest-backfilled-version`,
`update-metadata-snapshot-version`) on `/delta/v1/`, which remain
unimplemented for the secondary surface — see ADR-0009 / ADR-0011.
-->

### Delta REST Kernel `UpdateTable` coordinator actions still return 501

On the Delta REST Kernel secondary surface (`/delta/v1/`, ADR-0009),
the `UpdateTable` discriminated union carries three coordinator
actions — `add-commit`, `set-latest-backfilled-version`,
`update-metadata-snapshot-version` — that soyuz has not yet unified
against the ADR-0011 passthrough coordinator storage. These actions
return **501** with `error_code = "COMMIT_COORDINATOR_UNSUPPORTED"`
via `soyuz_catalog.exceptions.CommitCoordinatorUnsupportedError`. The
upstream spec lists 501 as a valid response for these actions, so the
divergence is purely at the error-code level (discoverability). A
future change can unify both coordinator surfaces against the same
storage.

### Optional `delta` extra gates the runtime dep

`deltalake` is not a hard install requirement. It is promoted from a
dev-only dependency to an optional extra (`pip install
soyuz-catalog[delta]`) so that installs that never touch the
`/delta/preview/commits` endpoints stay slim. If the extra is
absent, the endpoint returns 501 with an install hint in the error
message rather than a 500 `ImportError`.

Regression tests:
`tests/test_delta_commits.py::*` (unit),
`tests/test_delta_roundtrip.py::test_delta_get_commits_preview`
(integration).

## Lineage

### Lineage is a soyuz-only extension

Upstream Unity Catalog OSS has no lineage: not in
`unitycatalog/api/all.yaml`, not in the Java server, not in the
clients. soyuz adds lineage as a genuine over-the-spec extension
anchored on **OpenLineage** as the ingestion contract. See
[ADR-0008](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0008-openlineage-as-lineage-contract.md) for the
full rationale.

Three endpoints live at the **root**, not under
`/api/2.1/unity-catalog`, so that OpenLineage producers can point at
a fixed `/lineage/v1/events` path matching the wider OpenLineage
ecosystem's conventions:

- `POST /lineage/v1/events`
- `GET /lineage/upstream/{full_name}?depth=N`
- `GET /lineage/downstream/{full_name}?depth=N`

`tests/test_openapi_conformance.py::test_soyuz_paths_are_subset_of_uc_spec`
explicitly skips any path under `/lineage/` for the same reason the
`/healthz` liveness probe is skipped: the path is real and must not
disappear, but it is not in `all.yaml` and the subset check cannot
be strict about it.

### `OpenLineageEvent` uses `extra="allow"`

Every other request body in soyuz is strict-`extra="forbid"`:
silently dropping unknown fields is the UC OSS Java bug we exist to
fix. `OpenLineageEvent` is the single documented exception. OpenLineage
is an external standard that evolves on its own schedule, and a
producer shipping a new facet must not crash soyuz's ingestion
endpoint. Every soyuz *response* model — including
`LineageIngestResponse`, `LineageNode`, `LineageEdgeOut`, and
`LineageGraphResponse` — stays `extra="forbid"`, so soyuz still
controls its own output shape. The carve-out is scoped to one class
and called out in ADR-0008; reviewers catching `extra="allow"`
elsewhere in the codebase should reject it unless a similar ADR
covers it.

### Tables-only MVP scope

Only `catalog.schema.table` dataset names are resolved. Volumes,
functions, and registered models all have the same 32-char opaque
id shape soyuz lineage uses, so extending the ingestor to accept
them is a non-breaking storage change that will land in a dedicated
sprint when there is a concrete consumer asking. The MVP rejects
non-table dataset names **by construction** — the service calls
`permissions_service.resolve_securable(..., "table", ...)` and
nothing else. Rejected datasets are silently dropped and counted in
the ingest response, not surfaced as 400s, so an OpenLineage
producer that emits events for a mix of UC and non-UC tables still
gets its UC edges recorded.

### Append-only history (dangling edges survive table deletion)

`lineage_edges` rows are **not** cascade-deleted when a referenced
table is dropped. Lineage is history; deleting a table must not
rewrite the past. Edges whose `source_securable_id` or
`target_securable_id` no longer resolves are rendered on the wire
with `full_name = null` so clients can still see the shape of the
historical graph. The only cascade in the lineage data model is
`lineage_edges.run_id → lineage_runs.id ON DELETE CASCADE`, because
deleting a run logically drops its graph contribution.

Regression tests:
`tests/test_lineage.py::test_table_delete_leaves_dangling_edge`,
`tests/test_lineage.py::test_rename_invariance`.

## Delta REST Catalog API

### Second spec surface tracked by a second subset test

soyuz implements the Delta REST Catalog API defined by
`~/git/unitycatalog/api/delta.yaml` as a parallel REST surface to
the main `all.yaml`-derived API. 13 new routes land under
`/api/2.1/unity-catalog/delta/v1/`, operating on the existing
`Table` / `StagingTable` storage through a translation layer. No
new database schema, no migration. See
[ADR-0009](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0009-delta-rest-catalog-as-secondary-surface.md).

`tests/test_openapi_conformance.py::test_delta_rest_paths_are_subset_of_delta_yaml`
asserts every `/delta/v1/...` route soyuz registers is in
`delta.yaml`, mirroring the existing all.yaml subset check. The
main-API subset check skips `/delta/v1/` paths (but not
`/delta/preview/commits`, which is part of `all.yaml`).

### `UpdateTable` actions: implemented / accept-and-discard / 501

The spec's `TableUpdate` discriminated union has ~10 action
variants. soyuz splits them into three categories:

- **Implemented** (mutate the row, bump `updated_at`):
  `set-properties`, `remove-properties`, `set-table-comment`,
  `set-columns`, `set-partition-columns`.
- **Accept-and-discard** (parsed, validated, silently ignored):
  `set-protocol`, `set-domain-metadata`,
  `remove-domain-metadata`. soyuz does not track per-table
  protocol versions or domain metadata; Delta clients
  nevertheless always emit these on schema evolution / clustering
  config changes, and a 400 rejection would break the client on
  every write. The service accepts the payload and discards it;
  the next `loadTable` response echoes the fixed default
  `DeltaProtocol` so well-behaved clients see no drift within a
  single session.
- **Rejected 501 `COMMIT_COORDINATOR_UNSUPPORTED`** (see also
  ADR-0006): `add-commit`, `set-latest-backfilled-version`,
  `update-metadata-snapshot-version`. These are commit-coordinator
  territory and soyuz has a permanent "no coordinator" posture.

### `requirements` pre-conditions surface as 409 `REQUIREMENT_NOT_MET`

Both `assert-table-uuid` and `assert-etag` are implemented
against real soyuz state. A failure maps to 409 with the
dedicated `REQUIREMENT_NOT_MET` error code — **not**
`ALREADY_EXISTS`, which soyuz uses for duplicate-name conflicts.
The distinct code lets clients tell a stale-state failure apart
from a duplicate-name collision.

The etag is synthesised from `Table.updated_at` (no dedicated
column); every mutation bumps it and therefore invalidates stale
etags automatically.

### Empty credential stubs (`storage-credentials: []`)

Four Delta credential-vending endpoints return a 200 with an
**empty** `storage-credentials` list:

1. `GET /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}/credentials`
2. `GET /delta/v1/staging-tables/{id}/credentials`
3. `GET /delta/v1/temporary-path-credentials`
4. `.../staging-tables` (on the `storage-credentials` field of the response body)

soyuz does not vend cloud credentials (out of scope).
A 501 would abort every Delta write path on the client; an empty
list lets the client fall through to its configured `file://` or
externally-vended path and keep progressing. This is explicitly
an **empty** list, not a deception — it is a statement that soyuz
has no credentials to offer. Consistent with the existing
temporary-credentials stub posture.

### `reportMetrics` accept-and-discard

`POST /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}/metrics`
returns 204 No Content. The body is parsed (so malformed
payloads surface as 422) and the path is probed (so unknown
tables surface as 404) but the metrics payload is discarded.
soyuz has no metrics sink; rejecting these with 501 would make
every Delta write log a client-side error over a non-feature.

### First table rename path lands in `table_service.rename_table`

The Delta REST surface requires a `POST .../rename` endpoint;
the main UC REST spec has no table rename. The new service
function is public at the service-layer level (both surfaces
share the same backend) but is **only** exposed through the Delta
route — the main `/tables/{full_name}` endpoint still has no
PATCH. This matches the spec: `all.yaml` does not define a
rename action for tables.

Regression tests: `tests/test_delta_rest.py::test_rename_table_204`,
`tests/test_delta_rest.py::test_rename_duplicate_returns_409`.

### Interop: a table written through one surface is readable through the other

Both surfaces operate on the same `Table` / `Column` rows. A
table created via `POST /api/2.1/unity-catalog/tables`
(`ColumnInfo` shape, soyuz' `type_json` as a bare type payload) is
readable via `GET /api/2.1/unity-catalog/delta/v1/catalogs/{c}/schemas/{s}/tables/{t}`
(`DeltaColumn` shape, soyuz wraps the `type_json` in an empty
`{type, metadata}` envelope at read time). The Delta load returns
a spec-shaped response in that case even though the columns were
never written through the Delta path. Regression test:
`tests/test_delta_rest.py::test_uc_api_table_loads_through_delta_api`.

## Tags

**soyuz-specific, over-the-spec extension. See ADR-0010.** Unity
Catalog OSS and `all.yaml` define no tags resource; Databricks
supports tags on catalogs / schemas / tables / columns as a
first-class governance primitive but has published no spec. soyuz
adds tags as a root-mounted extension, deliberately *not* nested under
`/api/2.1/unity-catalog/`, so the divergence is obvious in URL logs
and the `tests/test_openapi_conformance.py` skip rule stays greppable
alongside `/lineage/` and `/delta/v1/`.

### Shape

- `GET /tags/{securable_type}/{full_name}` — returns
  `{"tags": [{"key", "value", "created_at", "updated_at"}, ...]}`
  sorted by key. Empty result is `{"tags": []}`, never 404.
- `PATCH /tags/{securable_type}/{full_name}` — body
  `{"changes": [{"op": "set" | "remove", "key", "value"?}, ...]}`.
  Returns the full post-change state. Empty `changes` is a valid
  no-op.
- `securable_type` is narrower than the UC `SecurableType` enum:
  `catalog`, `schema`, `table`, `column` only. Volume / function /
  registered_model are a non-breaking additive future extension.

### Column addressing

Tags introduce the only 4-part full_name in soyuz:
`catalog.schema.table.column`. The tags service resolves the three
leading segments via `permissions_service.resolve_securable`, then
looks up the column by `(table_id, name)` and stores the opaque
`Column.id` on the row. Column renames therefore preserve the tag;
the column and its tags move together.

### Additive PATCH (not replace-style)

Unlike every other PATCH in soyuz, tags use an additive shape. Two
clients editing disjoint key sets must not clobber each other, which
rules out replace-style PATCH. Overlapping operations within a single
batch resolve as **set wins**: `(remove key, set key)` ends with the
key present. This is the opposite of "last operation wins" and
matches the multi-writer invariant — two clients setting the same
key after one client removed it should not leave a gap.

### Rename invariance and append-only delete

Tags are keyed on opaque row ids, never full_names — the same trick
permissions (ADR-0005) and lineage (ADR-0008) use. Renaming a
catalog / schema / table / column leaves every attached tag intact.

Dropping the underlying resource does **not** cascade-delete its
tags. The opaque `securable_id` is unique per creation, so a new
resource created with the same name gets a new id and cannot inherit
the stale tags — they become unreachable orphans rather than a
governance bug surface. Every `delete_*` service stays unchanged.

Regression tests: `tests/test_tags.py` (rename-invariance via
`test_rename_catalog_preserves_tags`, append-only via
`test_delete_table_leaves_orphan_tag`, set-wins tiebreaker via
`test_patch_set_wins_over_remove_in_same_batch`).

## Table constraints

ADR-0012 adds `PRIMARY KEY`, `FOREIGN KEY`, `CHECK`, and named
`NOT NULL` constraints on tables. Databricks supports them; UC OSS
`all.yaml` has none. Net-new over-the-spec, same posture as the
lineage (ADR-0008) and tags (ADR-0010) extensions.

### Metadata-only, no enforcement

soyuz persists declared constraints and returns them on every
`GET /tables/{full_name}` but never enforces them at write time —
there is no query engine. A client that declares `PRIMARY KEY (id)`
and then inserts duplicates gets no complaint from soyuz. The value
is interoperability: Spark / dbt / downstream catalog UIs that read
declared constraints to display schema documentation or pick join
strategies see the same metadata they would against Databricks.

### Mutations ride on Delta REST `UpdateTable`, not a new main-REST PATCH

The main UC REST `/tables` surface has no `PATCH` (405) and the
constraints extension deliberately does not reopen that invariant.
Mutations flow through two new actions on the Delta REST `UpdateTable`
discriminated union at
`POST /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}`:

- `add-constraint` — validates per type (column existence, at-most-
  one PK, FK parent resolution) then inserts a row on the new
  `table_constraints` table. Invalid payload → 400 `INVALID_ARGUMENT`;
  second PK → 409 `ALREADY_EXISTS`; duplicate name on the same table
  → 409.
- `drop-constraint` — removes by name. `if_exists=false` (default) on
  a missing name → 404 `NOT_FOUND`; `if_exists=true` → 200 no-op.

Reads surface on the main UC REST via a new `table_constraints`
field on `TableInfo`, populated from the live rows at response time.
The field is `None` (not `[]`) when the table has no declared
constraints, matching how other optional nested fields behave.

### Wire shape mirrors Databricks

The envelope (`TableConstraint`) and the four per-type payloads
(`PrimaryKeyConstraint` / `ForeignKeyConstraint` / `CheckConstraint`
/ `NotNullConstraint`) mirror `databricks.sdk.service.catalog` so a
client that already knows Databricks shape does not have to relearn.

### Rename invariance via opaque ids

Rows are keyed on the opaque `Table.id`, never on the user-facing
full name — same trick permissions (ADR-0005), tags (ADR-0010), and
lineage (ADR-0008) use. Renaming the parent table (or any of its
parents) leaves every constraint attached. Foreign keys store a
second opaque id — `parent_table_id` — so renaming the *referenced*
table also leaves the declaration intact; response shapes
reconstruct `parent_table` as a three-part name from the live
parent chain. If the referenced table has since been deleted the
response renders `parent_table` as the sentinel
`<deleted>.<deleted>.<deleted>` — append-only history in the same
sense as lineage / tags orphans.

### Named `NOT NULL` is orthogonal to `Column.nullable`

Named NOT NULL constraints are a *second* concept alongside the
unnamed `Column.nullable` flag, not a replacement. Adding or
dropping the named constraint deliberately does **not** flip the
column flag. Databricks models them the same way; flipping the flag
as a side effect would reintroduce the silent-side-effects class that
the "no table PATCH" invariant was designed to prevent.

Regression tests: `tests/test_table_constraints.py` (CRUD matrix
per type, duplicate / uniqueness / PK-uniqueness, rename invariance
for both the owning and the referenced side, delete cascade,
transactional batch).

## Connections and foreign catalogs

ADR-0013 adds a metastore-level `/connections` CRUD resource and a
`catalog.type = FOREIGN` variant that binds to a connection instead
of owning a managed storage root. Databricks ships this as Lakehouse
Federation; UC OSS `all.yaml` defines **none** of it — neither the
`Connection` schema, nor `CatalogType`, nor the `/connections`
endpoints. Net-new over-the-spec, same posture as the lineage
(ADR-0008), tags (ADR-0010), and effective-permissions extensions.

### Metadata only, no query proxying

soyuz persists connection definitions and returns them on every
read, but it **never** opens a connection to the external system.
Federated query execution is a query-engine concern and lives
outside the catalog — same out-of-scope posture as cloud
credential vending. A client that writes a Snowflake connection
and then expects `SELECT` to route through soyuz is out of scope.

### Foreign catalogs are mutually exclusive with managed storage

`CreateCatalog` accepts `type="FOREIGN"` only together with
`connection_name`, and only when `storage_root` is absent. Any
mixed shape — `type="FOREIGN"` without `connection_name`,
`type="FOREIGN"` with `storage_root`, or `type="MANAGED"` with
`connection_name` — surfaces as 400 `INVALID_ARGUMENT` instead
of silently persisting a half-valid row. A `connection_name`
that does not resolve surfaces as 404.

### Catalog `type` is immutable after create

`UpdateCatalog` does not expose the `type` field at all.
Flipping a managed catalog to foreign (or vice versa) would
orphan the other variant's state: the managed catalog's
`storage_location` is computed once at create time and
referenced by child resources, so a switch to foreign would
strand every child. Databricks treats this conversion as a
create-new-and-migrate operation and soyuz matches. A PATCH
body that sets `type` surfaces as 422 (unknown field under
`extra="forbid"`).

### Rename invariance for connection bindings

Foreign catalogs store `connection_id`, not `connection_name`.
The wire field `connection_name` is reconstructed at response
time from the live `Connection` relationship so
a connection rename propagates to every bound foreign catalog
without a fan-out UPDATE — same trick used for
`external_locations.credential_name`.

### No per-connector option validation

`options` is a free-form `dict[str, str]` passthrough. soyuz
does **not** validate per-connector option sets (a `host` for
POSTGRESQL, a `sfUrl` for SNOWFLAKE, a `projectId` for
BIGQUERY): it has no query side to enforce them against, and
Databricks' exact per-connector option surface is undocumented
in the upstream spec. Any validation would be a guess that
drifts silently with every Databricks release. The wire
`connection_type` is still a pinned `Literal` of the common
connector set, so typos on the enum itself (`POSTGRES` vs
`POSTGRESQL`) surface as 422 at the pydantic layer.

### Sensitive options are stored in plaintext

`options` values are stored verbatim in the JSON column. A
`password` or `token` key gets no special treatment — same posture
as `Credential` records today. Field-level encryption can be
retrofitted additively without touching wire shapes; the JSON column
is stringly-typed so a wrapper at the service layer would slot in
without a schema migration.

### Delete cascade with `force=true` delegates to `catalog_service`

`DELETE /connections/{name}?force=true` walks every referencing
foreign catalog and calls
`catalog_service.delete_catalog(force=True)` per row, rather
than bulk-deleting. The delegation is deliberate: a bulk ORM
delete would bypass the grants-cascade the catalog service
owns and would duplicate logic that already exists one module
over.

Regression tests: `tests/test_connections_crud.py` (CRUD
matrix, rename, pagination, force-cascade) and
`tests/test_catalogs_foreign.py` (create mixed shapes, PATCH
type-immutability, connection rebind, rename propagation).
