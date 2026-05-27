# ADR-0009: Delta REST Catalog API as a secondary surface over existing tables

- **Status:** Accepted
- **Date:** 2026-04-15
- **Deciders:** @FloHofstetter
- **Supersedes:** —

## Context

The unitycatalog OSS project ships **two** OpenAPI spec files:

1. `api/all.yaml` — the main Unity Catalog REST API that soyuz
   implements. Generic table/catalog/schema/volume resources
   addressed through `/api/2.1/unity-catalog/*`.
2. `api/delta.yaml` — a second, Delta-centric spec introduced more
   recently. Inspired by the Iceberg REST Catalog (IRC) but
   Delta-native: clients (Delta Kernel 4.0+, Spark with the Delta
   connector) use it to load and mutate Delta tables using the
   native Delta protocol wire shapes (`DeltaColumn`,
   `DeltaProtocol`, `TableMetadata` with kebab-case field names).

An earlier iteration of soyuz covered `all.yaml` in full but did
**not** implement `delta.yaml`. Delta clients that discover soyuz
through a Delta Kernel 4.0+ setup would therefore see a 404 on the
`/delta/v1/config` probe and abort. The catalog surface needs to be
complete against the upstream specs it claims to track — otherwise
soyuz would advertise UC compatibility while missing the second
protocol.

This ADR fills that gap.

## Decision

Implement `delta.yaml` as a **thin translation layer over existing
`Table` and `StagingTable` storage**. Every endpoint in the Delta
surface operates on the same ORM rows the main UC API already
manages. No new tables, no migration, no second data model.

### Routing

The router prefix is `/delta`, included under the main `api_prefix`
so the effective full paths are
`/api/2.1/unity-catalog/delta/v1/...`. The `/v1` segment is part of
each route literal, not a FastAPI include layer, because the spec
treats it as part of the route identity. Route definitions live in
[soyuz_catalog/api/routes/delta_rest.py](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/routes/delta_rest.py).

### Column round-tripping

Delta's `DeltaColumn.type` is either a primitive string (`"long"`,
`"decimal(10,2)"`) or a complex-type object (`struct`, `array`,
`map`) whose own `type` field discriminates the variant. OpenAPI
cannot express this union, and Delta clients parse the field
through their own `DataTypeJsonSerDe`. soyuz stores the full
`DeltaColumn` payload (`type` + `metadata`) verbatim inside
`Column.type_json` as a JSON envelope
`{"type": ..., "metadata": ...}`. On load, the service layer parses
the envelope back out and returns a byte-identical `DeltaColumn`.

Columns written through the main UC API (which uses soyuz'
`ColumnInfo`, not `DeltaColumn`) have a different `type_json` shape
— just the type payload, no envelope. The translation helper in
[delta_rest_service.py](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/services/delta_rest_service.py)
detects this and wraps the value in an empty envelope so a table
created through one surface and read through the other still
produces a valid Delta response.

### Synthesised fields

- `etag` = `str(Table.updated_at)`. Every mutation bumps
  `updated_at` so a stale etag fails the `assert-etag` requirement
  without a new database column.
- `table-uuid` = `Table.id`. Already a 32-char hex opaque id; the
  match is exact.
- `DeltaProtocol` = fixed default `(min-reader=1, min-writer=2,
  reader-features=[], writer-features=[])` on every load response.
  soyuz does not track per-table protocol versions; rejecting
  `set-protocol` updates would break clients, so the service
  accepts and discards them.

### `UpdateTable` action categories

The `TableUpdate` discriminated union has ~10 action variants.
This decision splits them into three categories:

| Category     | Actions                                                                                                | Behaviour                                                                 |
|--------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| Implemented  | `set-properties`, `remove-properties`, `set-table-comment`, `set-columns`, `set-partition-columns`     | Mutate the stored row; `updated_at` bumped.                               |
| Accept-and-discard | `set-protocol`, `set-domain-metadata`, `remove-domain-metadata`                                  | Parsed but silently ignored. See column below for why.                    |
| Rejected 501 | `add-commit`, `set-latest-backfilled-version`, `update-metadata-snapshot-version`                      | Raise `CommitCoordinatorUnsupportedError` → 501 `COMMIT_COORDINATOR_UNSUPPORTED` per ADR-0006. |

The accept-and-discard category is the compromise: Delta clients
always emit `set-protocol` on schema evolution and
`set-domain-metadata` on clustering config changes, even against
catalogs that do not track those. Rejecting them with 400 would
break every Delta client on write; accepting them as a no-op lets
the client progress without soyuz pretending to store state it
does not.

The 501 category matches the posture from
[ADR-0006](0006-coordinated-commits.md): soyuz is not a Delta
commit coordinator, and these actions are commit-coordinator
territory. The dedicated `COMMIT_COORDINATOR_UNSUPPORTED` error
code lets clients distinguish "permanent no-coordinator" from "not
yet wired" (`NOT_IMPLEMENTED`), same reasoning that applies to the
`/delta/preview/commits` POST.

### `requirements` pre-conditions

Both spec-defined requirement types are implemented:

- `assert-table-uuid` → string compare against `Table.id`.
- `assert-etag` → string compare against `str(Table.updated_at)`.

A failure on either raises `ConflictError` mapped to 409 with error
code `REQUIREMENT_NOT_MET` — distinct from the `ALREADY_EXISTS`
409 the duplicate-name path emits, so clients can tell the two
apart. Requirements are validated **before** any mutation; a
failure on any one rejects the whole batch.

### Credential and metrics endpoints

The Delta spec defines four endpoints that soyuz cannot implement
truthfully:

1. `getTableCredentials`
2. `getStagingTableCredentials`
3. `getTemporaryPathCredentials`
4. `reportMetrics`

All four **return 200** with an empty-stub body rather than 501.
The rationale mirrors the OpenLineage "drop and count" posture
(ADR-0008): Delta clients that get a 501 on any of these abort the
whole write path; clients that get an empty credential list fall
through to their configured `file://` or externally-vended path
and keep progressing. `reportMetrics` is `accept-and-discard` for
the same reason — a 501 would make every Delta commit log a
client-side error over a non-feature.

The empty-credential stub is consistent with the existing
temporary-credentials posture (see `DIVERGENCES.md` under
**Permissions / Credentials**). The existence of this entry
does **not** change the project-wide rule "never vend real cloud
credentials" — soyuz is still credential-vending-free; the empty
list is explicitly an empty list, not a deception.

### Schema validation stays strict

Every new model in
[soyuz_catalog/api/delta_schemas.py](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/api/delta_schemas.py)
uses `ConfigDict(extra="forbid", populate_by_name=True)`. The
`extra="allow"` exception made for `OpenLineageEvent` in ADR-0008
does **not** carry over — spec-sourced wire shapes always stay
strict. This is non-negotiable: the whole point of soyuz is to
fix the silent-accept-garbage class of bugs that motivate the
project.

## Consequences

- soyuz' route count grows by 13 endpoints under
  `/api/2.1/unity-catalog/delta/v1/...`.
- The spec-conformance test now covers two YAML files: `all.yaml`
  (main API) and `delta.yaml` (Delta API). Any route registered
  under `/delta/v1/` that is not in `delta.yaml` fails the new
  `test_delta_rest_paths_are_subset_of_delta_yaml` test, matching
  the existing guard for the main API.
- The first table-rename path in soyuz lands in
  `table_service.rename_table` as a side effect. The main UC API
  does not expose it (the spec has no table-rename endpoint), but
  the function is public because both surfaces share the same
  service layer.
- Round-tripping through the Delta surface is interop-safe with
  the main UC API: a table created via `/tables` is readable via
  `/delta/v1/catalogs/{c}/schemas/{s}/tables/{t}` and vice versa.
  Regression test:
  `tests/test_delta_rest.py::test_uc_api_table_loads_through_delta_api`.
- `DIVERGENCES.md` carries a Delta REST Catalog API section
  documenting the accept-and-discard `TableUpdate` actions, the 501
  commit-coordinator category, the empty credential stubs, and the
  `reportMetrics` posture.
- No database migration. No new ORM model. Only soyuz' existing
  storage is touched.

## Migration path if the upstream Delta spec evolves

Every Delta-shaped thing soyuz exposes lives in
`delta_rest_service.py` and `delta_schemas.py` — the storage
layer underneath is oblivious to the surface. A schema change
upstream therefore touches only those two files plus tests, not
the database.

If Databricks eventually publishes a *third* spec that extends the
Delta shape (per-table protocol versions, domain-metadata
persistence), soyuz can introduce storage for those fields as a
migration without breaking either existing surface — the
translation layer gets a real source for what it currently
synthesises, and clients see no wire change.

## References

- [Delta REST Catalog spec](https://github.com/unitycatalog/unitycatalog/blob/main/api/delta.yaml) (upstream)
- [ADR-0001](0001-stack-and-conventions.md) — `extra="forbid"` policy this ADR preserves.
- [ADR-0002](0002-spec-is-the-contract.md) — spec-as-source-of-truth philosophy.
- [ADR-0006](0006-coordinated-commits.md) — no-commit-coordinator posture that drives the 501 update category.
- [ADR-0008](0008-openlineage-as-lineage-contract.md) — the only other `extra="allow"` exception soyuz has; this ADR explicitly declines the same carve-out.
- `soyuz_catalog/api/routes/delta_rest.py` — the 13 route handlers.
- `soyuz_catalog/services/delta_rest_service.py` — the translation layer.
- `soyuz_catalog/api/delta_schemas.py` — the Pydantic models.
- `tests/test_delta_rest.py` — 34 tests across structural CRUD, update variants, requirements, and stub endpoints.
- `DIVERGENCES.md` section **Delta REST Catalog API**.
