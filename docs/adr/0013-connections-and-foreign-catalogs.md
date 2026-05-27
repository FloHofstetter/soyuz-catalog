# ADR-0013: Connections and foreign catalogs (Lakehouse Federation)

- **Status:** Accepted
- **Date:** 2026-04-15
- **Deciders:** @FloHofstetter

## Context

Databricks' Unity Catalog ships Lakehouse Federation: a
`/connections` CRUD surface pointing at external query engines
(Snowflake, Postgres, Redshift, BigQuery, SQL Server, …) and a
`catalog.type = FOREIGN` variant whose binding to a connection
replaces the managed storage root. Upstream UC OSS `all.yaml` —
the contract soyuz pins (ADR-0002) — defines **none** of this.
Neither the `Connection` schema nor `CatalogType` nor the
`/connections` endpoints are present in the YAML.

Adding the feature therefore follows the same posture as lineage
(ADR-0008), tags (ADR-0010), and effective permissions: a deliberate
over-the-spec extension tracked in `DIVERGENCES.md`, skipped by
`test_openapi_conformance.py`'s subset check, and called out as such
in the public docs.

Three questions shape the design:

1. **Does soyuz proxy queries to the foreign system?** No —
   federated query execution is a query-engine concern and lives
   outside the catalog. soyuz stores connection metadata only,
   same boundary as credential vending.
2. **How does the catalog row record the foreign binding without
   bloating the managed shape?** A `type` column plus a nullable
   `connection_id` FK plus a free-form `options` JSON, all
   defaulting to the managed shape so existing rows and existing
   clients see no behaviour change.
3. **What happens when a foreign catalog's connection is
   renamed or deleted?** Rename propagates via the same
   connection-id-not-name trick external locations use for
   credentials. Delete is gated at the service layer (`force=true`
   cascades through the catalog, `force=false` returns 409) so the
   `force`-or-refuse semantics soyuz uses everywhere else carry over.

## Decision

This ADR adds three artefacts to the catalog:

**1. New metastore-level `connections` resource.** Flat
namespace, name-addressed CRUD (`POST`, `GET`, `LIST`, `PATCH`,
`DELETE`) under `/api/2.1/unity-catalog/connections`, opaque
UUID-hex `id` for rename-stable bindings. Structurally a sibling
of `credentials`: same cascade-with-force semantics, same keyset
pagination, same `extra="forbid"` request bodies, same
permissions-wipe on delete.

**2. Catalog row extension.** Three new columns on `catalogs`:

- `type`: `String(16)`, `NOT NULL`, defaults to `"MANAGED"` and is
  **immutable after create**. The wire shape is a pinned
  `Literal["MANAGED", "FOREIGN"]` so a typo is a 422, not a
  silently-stored typo. `UpdateCatalog` does not expose the field
  at all — flipping a managed catalog to foreign (or vice versa)
  would orphan the other variant's state and has no defined
  semantics.
- `connection_id`: `String(32)`, nullable FK to `connections.id`
  (named constraint `fk_catalogs_connection_id` so Alembic's
  batch-recreate on SQLite can drop and re-add it without
  stumbling on an auto-generated name). Set exactly when
  `type == "FOREIGN"`. The wire field `connection_name` is
  reconstructed at response time from the live relationship —
  same rename-invariance trick used for
  `external_locations.credential_name`.
- `options`: `JSON`, `NOT NULL`, defaults to `{}`. Passthrough
  `dict[str, str]`; used by foreign catalogs to carry
  connector-side projection rules (schema filter, table allow-
  list, …) and permitted but always empty on managed catalogs.

**3. Mutually-exclusive validation gates in `catalog_service`.**
`create_catalog` rejects the mixed shapes with 400
`INVALID_ARGUMENT`:

- `type="FOREIGN"` without `connection_name` → 400.
- `type="FOREIGN"` with `storage_root` → 400.
- `type="FOREIGN"` with a `connection_name` that does not
  resolve → 404.
- `type="MANAGED"` (or omitted) with `connection_name` → 400.
- Managed catalogs keep the existing storage-URI scheme gate on
  `storage_root`.

`update_catalog` rejects `connection_name` on a managed catalog
with 400 and allows it on a foreign catalog as a rebind (a
legitimate metadata edit — swapping out the external target).
`options` PATCH is replace-style like `properties`, allowed on
both variants.

`delete_connection(force=True)` delegates per-referencing
foreign catalog to `catalog_service.delete_catalog(force=True)`
rather than bulk-deleting rows. The delegation is deliberate: a
bulk ORM delete would bypass the grants-cascade the catalog
service owns and would re-implement logic that already exists
one module over.

### What soyuz does NOT do

- **No query proxying.** soyuz never opens a connection to the
  external system. Federated query execution is a query-engine
  concern, same out-of-scope posture as credential vending.
- **No per-connector option validation.** A `host` for
  `POSTGRESQL` and a `sfUrl` for `SNOWFLAKE` both flow through
  untouched. soyuz has no query side to enforce the option sets
  against, so validating them here would be speculative
  divergence. The wire `connection_type` is still a pinned
  `Literal` so typos on the enum itself surface as 422.
- **No secrets encryption.** Sensitive options (`password`,
  `token`, …) are stored in plaintext — same posture as
  credentials today. Field-level encryption can be retrofitted
  additively without touching wire shapes.
- **No `/foreign-schemas` or `/foreign-tables` routes.** Foreign
  catalogs expose the same child namespaces as managed catalogs
  (`/schemas`, `/tables`, `/volumes`) and are populated by the
  same CRUD endpoints. soyuz does not introspect the external
  system to auto-populate them.
- **No Delta REST Catalog tie-in.** The Delta REST Kernel surface
  (ADR-0009) is orthogonal: a table created under a foreign catalog
  cannot be loaded through `/delta/v1/` because the foreign engine
  owns the physical layout.

## Consequences

1. **Databricks clients that already speak the `Connection`
   shape can point at soyuz and round-trip connection
   definitions.** That is the value proposition: a catalog
   modelling tool or a dbt plugin that emits
   `CREATE CONNECTION ... TYPE postgresql` stops 404-ing on
   soyuz and starts persisting metadata.
2. **Catalog list responses grow three fields
   (`type`, `connection_name`, `options`).** Managed catalogs
   serialise with `type="MANAGED"`, `connection_name=null`, and
   `options={}`. Existing clients that read `CatalogInfo` keep
   working — all three fields are optional on the pydantic
   response model and additive on the wire. The generated
   soyuz-catalog Python client regenerates cleanly against the
   updated `/openapi.json` (verified by
   `scripts/check_client_drift.sh` in the same commit).
3. **The feature is reversible.** Nothing under
   `soyuz_catalog/services/`, `routes/`, or the SQL schema
   outside the connections migration depends on foreign catalogs
   being present. Dropping the migration and the
   `connection_service` module would roll the feature back
   without affecting any existing endpoint. That reversibility
   is the counterpart to being over-the-spec: the day upstream
   UC OSS ships its own `Connection` schema in `all.yaml`, soyuz
   reconciles by editing the existing wire shapes in place (or,
   if upstream diverges, documenting the delta in
   `DIVERGENCES.md`) rather than a rip-and-replace.
4. **Spec-conformance test gains a new skip prefix
   (`{PREFIX}/connections`).** Same pattern as the other four
   over-the-spec extensions. The skip list is the authoritative
   register of "soyuz knows this is not in `all.yaml`".
5. **A future secrets sprint can add field-level encryption on
   `options` without a schema migration.** The JSON column is
   stringly-typed, so a wrapper that detects sensitive keys at
   write time and decrypts them at read time slots in at the
   service layer.

## Alternatives considered

- **Model the foreign binding on a separate
  `foreign_catalogs` child table.** Rejected: the UC wire
  shape returns a single `CatalogInfo` regardless of variant,
  so a separate table would just force a join on every read for
  no benefit. The three extra columns on `catalogs` are dead
  weight on managed rows but the storage cost is noise against
  the existing JSON `properties` column.
- **Expose `type` as a PATCH field so a managed catalog can be
  converted to foreign in-place.** Rejected: the conversion has
  no physical meaning — a managed catalog's `storage_location`
  is computed once at create time and referenced by child
  resources, so flipping it to foreign would strand that
  reference. Creating a fresh foreign catalog and migrating
  children via the existing schema/table/volume routes is the
  supported path.
- **Validate per-connector `options` (e.g. require `host` for
  POSTGRESQL, `sfUrl` for SNOWFLAKE).** Rejected: soyuz has no
  query side to enforce them against, and Databricks' exact
  option sets are undocumented in the upstream spec. Any
  validation would be a guess that drifts with every
  Databricks release and silently rejects future clients.
