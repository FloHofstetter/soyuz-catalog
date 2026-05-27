# ADR-0010: Tags as a soyuz extension

- **Status:** Accepted
- **Date:** 2026-04-15
- **Deciders:** @FloHofstetter
- **Supersedes:** —

## Context

Unity Catalog OSS ships no tags. There is no `Tag` resource in
`~/git/unitycatalog/api/all.yaml`, the Java server has no tag tables,
and the upstream clients have no tag SDK. Databricks supports tags on
catalogs, schemas, tables, and columns as a first-class governance
primitive, but has not published a spec for the wire format. Users
coming from Databricks expect to attach `owner`, `pii`, `domain`, and
similar key/value metadata to their securables, and soyuz-catalog
currently forces them to drop that context.

This ADR adds tags as a genuine **over-the-spec extension**, the same
posture lineage takes ([ADR-0008](0008-openlineage-as-lineage-contract.md)):
pick a shape that matches the consumer expectation, persist it against
soyuz' existing opaque-id primitives so rename invariance carries over
for free, and document the divergence loudly so a future upstream spec
can replace it without drama.

## Decision

Implement tags as a flat, opaque-id-keyed extension mounted at the root
URL path (not under `/api/2.1/unity-catalog`).

1. **Transport**: two endpoints, both at the root of the server:
   - `GET /tags/{securable_type}/{full_name}` — return the current tag
     set, sorted by key.
   - `PATCH /tags/{securable_type}/{full_name}` — apply an additive
     batch of `{op: "set" | "remove", key, value?}` changes and return
     the post-change state.
2. **Persistence**: one table, `tags`, with one row per
   `(securable_type, securable_id, key)` tuple. A composite unique
   constraint enforces the set-semantics: re-setting an existing key
   updates the row in place, and removing a missing key is a no-op.
   Primary keys are soyuz' standard 32-char hex.
3. **Securable resolution**: the service extends
   `permissions_service.resolve_securable` with a 4-part
   `catalog.schema.table.column` case for column-level tags. The
   resolver walks the opaque-id chain and returns the leaf row's id,
   which is what every `tags` row stores.
4. **Rename invariance**: tags are keyed on opaque row ids, never
   full_names. Renaming a catalog / schema / table / column leaves
   every attached tag intact, the same mechanism permissions
   ([ADR-0005](0005-permissions-without-enforcement.md)) and lineage
   ([ADR-0008](0008-openlineage-as-lineage-contract.md)) use.
5. **Additive PATCH, not replace-style**: unlike the catalog / schema /
   table PATCH routes, `PATCH /tags/...` submits set/remove operations
   rather than a full desired state. Two clients editing disjoint key
   sets must not clobber each other's tags. Overlapping operations
   within a single batch resolve as *set wins* — `(remove key, set
   key)` ends with the key present. This is the opposite of a naive
   "last operation wins" and matches the multi-writer invariant: two
   clients setting the same key after one client removed it should
   not leave a gap.
6. **Append-only delete posture**: dropping the underlying resource
   does **not** cascade-delete its tags. The opaque `securable_id` is
   unique per creation, so a new resource with the same full_name
   cannot inherit stale tags — the old rows become unreachable
   orphans rather than a privilege-bug surface. Every `delete_*`
   service stays unchanged. Same posture as `lineage_edges`.
7. **MVP scope — catalog / schema / table / column**: volumes,
   functions, and registered models all share the 32-char opaque id
   shape, so extending the service to accept them is a non-breaking
   additive change that will land when there is a concrete consumer
   asking. The MVP rejects non-MVP types at the route boundary via a
   narrow `TagSecurableType` literal.
8. **Strict request validation**: `UpdateTags` and `TagChange` are
   `ConfigDict(extra="forbid")` — there is no OpenLineage-style
   external contract to accommodate here, so the soyuz-wide
   `extra="forbid"` policy applies without exception.

## Consequences

- soyuz diverges further from UC OSS. Documented in `DIVERGENCES.md`
  under **Tags** with the wire format and the set-wins tiebreaker.
- `/tags/` is the third skip in `tests/test_openapi_conformance.py`
  alongside `/lineage/` and `/delta/v1/`. Each skip is its own `if`
  with a comment so the intent stays greppable.
- If upstream `all.yaml` eventually ships a UC tags API, soyuz can
  add the spec endpoints as a translation layer over the same `tags`
  table — no data migration required.
- Column addressing uses a 4-part `catalog.schema.table.column`
  full_name that does not appear anywhere else in soyuz. Documented
  in `DIVERGENCES.md` and the REST reference.
- Tag values are unconstrained `Text`. No length cap, no structured
  value schema — mirrors how Databricks' UI treats tag values.

## Alternatives considered

- **Per-resource `tags JSON` columns.** Rejected: spreads schema churn
  across every resource table (catalog, schema, table, column, and
  later volume / function / model), makes column-level tagging
  especially awkward, and would need a custom serialiser to round-trip
  through every PATCH path. The flat `(type, id, key, value)` table is
  one migration and one query pattern for every securable.
- **Replace-style PATCH** (same shape as catalog / schema / table
  update). Rejected: incompatible with multi-writer workflows that
  edit disjoint key sets, which is the primary use case for
  governance tags. Two pipelines each writing their own tag would
  clobber each other on every update.
- **Store full_names instead of opaque ids.** Rejected: breaks the
  rename-invariance property every other soyuz resource relies on —
  same argument as ADR-0008.
- **Mount under `/api/2.1/unity-catalog/tags/`**. Rejected: hides the
  over-the-spec divergence behind a spec-looking URL and complicates
  the conformance-test skip rule. The lineage precedent (root-mounted)
  keeps the divergence obvious in server logs.
- **Wait for Databricks to publish a UC tags API.** Rejected: real
  consumers are already asking, the migration-path clause above keeps
  the option open, and the opaque-id keying is the only
  forward-compatible detail that matters.

## References

- [ADR-0001](0001-stack-and-conventions.md) — stack and conventions,
  including the `extra="forbid"` policy that applies without
  exception here.
- [ADR-0005](0005-permissions-without-enforcement.md) — the
  opaque-id-for-rename-invariance pattern this ADR reuses.
- [ADR-0008](0008-openlineage-as-lineage-contract.md) — the
  over-the-spec-extension template this ADR follows.
- `soyuz_catalog/services/tags_service.py` — implementation.
- `DIVERGENCES.md` — the Tags entry documenting this as a soyuz
  extension.
