# ADR-0012: Table constraints as metadata-only declarations

- **Status:** Accepted
- **Date:** 2026-04-15
- **Deciders:** @FloHofstetter

## Context

Databricks' Unity Catalog supports declared `PRIMARY KEY`, `FOREIGN
KEY`, `CHECK`, and named `NOT NULL` constraints on tables. Upstream
UC OSS `all.yaml` defines none of them — neither the wire shape nor
the endpoints — so adding them to soyuz is a net-new over-the-spec
extension, the same posture as lineage (ADR-0008) and tags
(ADR-0010).

A Spark-compatibility audit established that Spark itself does not
emit constraint DDL through the UC connector, so the
feature's value is **not** "make another Spark statement work". It
is interoperability with the broader catalog tooling ecosystem:
dbt's model tests, downstream catalog UIs that render ER diagrams,
query planners that pick join strategies from declared FKs, and
governance tools that flag tables missing a primary key all read
declared constraints to do their job.

Three questions shape the design:

1. **Does soyuz enforce?** No — there is no query engine. Declared
   constraints are metadata, nothing more.
2. **Which wire surface carries mutations?** The main UC REST
   `/tables` route has no `PATCH` (405) and reopening that invariant
   for a net-new feature is the opposite of what the decision
   protected against.
3. **How do we keep the declarations rename-invariant?** Every
   other over-the-spec feature in this project keys on the opaque
   resource id so a rename of any ancestor leaves the attached
   metadata in place. Constraints should do the same, and foreign
   keys need the opaque-id trick on *both* sides.

## Decision

1. **Metadata-only, no enforcement.** soyuz persists and returns
   declared constraints but never checks them on any write path.
   Inserts that violate a declared constraint are not rejected by
   soyuz; enforcement is the query engine's job. Documented in
   DIVERGENCES.md.

2. **Mutations ride on the Delta REST `UpdateTable` union (ADR-0009).**
   Two new actions — `add-constraint` and
   `drop-constraint` — are added to the existing discriminated
   union at `POST /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}`.
   No new routes on the main UC REST surface; the 405 on
   `PATCH /tables` stays. Reads are added as an optional
   `table_constraints` field on `TableInfo`, populated from the
   live rows at response time.

3. **Flat polymorphic-JSON storage.** A new `table_constraints`
   table with one row per declaration and a JSON `definition`
   whose shape depends on `constraint_type`. Same pattern as
   `permissions`, `tags`, and `lineage_edges`. The alternative —
   four dedicated tables per type — would multiply migrations and
   query plans without moving any validation out of the service
   layer (per-type validation is declarative either way). The
   chosen shape loses index-backed queries of the form "all FKs
   referencing table X", which soyuz has no current consumer for.

4. **Rename invariance via opaque ids.** Rows key on `Table.id`.
   Foreign keys additionally key on `parent_table_id` — the
   resolved opaque id of the referenced table, not the wire
   full_name. Responses re-materialise the three-part full_name
   from the live parent chain at read time. If the referenced
   table has been deleted, the response renders `parent_table`
   as the sentinel `<deleted>.<deleted>.<deleted>` — append-only
   history, same as lineage / tags orphans.

5. **Named `NOT NULL` is orthogonal to `Column.nullable`.** The
   existing unnamed `Column.nullable` flag stays authoritative for
   the column's nullability. A named `NOT_NULL` constraint is a
   *second*, separately-addressed row that carries a user-chosen
   name. Adding or dropping the named constraint deliberately does
   not flip the column flag. Flipping it would reintroduce the
   silent-side-effects class that the "no table PATCH" invariant was
   designed to prevent, and Databricks models the two concepts the
   same way.

6. **Wire shape mirrors the Databricks SDK.** The envelope
   (`TableConstraint`) and the four per-type payloads
   (`PrimaryKeyConstraint` / `ForeignKeyConstraint` /
   `CheckConstraint` / `NotNullConstraint`) mirror
   `databricks.sdk.service.catalog` so a client that already
   knows Databricks shape does not have to relearn. The envelope
   is a thin union — exactly one per-type field is populated per
   constraint — and zero/multi violations raise 400
   `INVALID_ARGUMENT` at the service layer.

## Consequences

1. `delete_table` gains a cascade step that wipes declared
   constraints on the owning table. Constraints on *other* tables
   that reference this one stay behind as append-only orphans,
   matching lineage / tags. A future change can tighten this to
   "409 unless force" if a consumer asks.

2. The Delta REST surface picks up the two new actions for free
   because the discriminated union already flows through
   `update_delta_table`. The main UC REST `/tables` PATCH 405 is
   preserved.

3. Constraint names are unique per table. Cross-table reuse is
   legal because the opaque `Table.id` is unique per creation,
   which keeps the user-facing name space clean.

4. The main UC REST `TableInfo` grows an optional
   `table_constraints` field. Existing clients that ignore
   unknown fields are unaffected; existing fixtures that do not
   populate it stay stable because the field is `None` (not
   `[]`) when no constraints are declared.

## Alternatives considered

- **Reopen main UC REST `PATCH /tables` for constraints only.**
  Rejected: the 405 is a soyuz invariant with a direct line to
  the UC OSS "silently drops unknown fields" bug class, and
  constraints are a weak reason to reopen it when a second
  mutation surface already exists.

- **Enforce constraints at write time.** Rejected: soyuz is a
  catalog, not a query engine. Enforcing would mean executing
  CHECK predicates, which requires a SQL parser and evaluator
  in a dialect the client chose — scope explosion for no real
  consumer.

- **Four dedicated tables per constraint type.** Rejected: four
  migrations instead of one, four sets of ORM relationships,
  and no validation moves out of the service layer. The flat
  polymorphic-JSON shape matches the three existing auxiliary
  tables in the project and keeps the surface small.

- **Flip `Column.nullable` when adding / dropping a named
  `NOT_NULL`.** Rejected: silent side effects class, and
  Databricks itself treats the two as orthogonal.
