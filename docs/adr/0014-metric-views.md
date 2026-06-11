# ADR-0014: Metric views as a soyuz extension

- **Status:** Accepted
- **Date:** 2026-06-11
- **Deciders:** @FloHofstetter

## Context

Databricks ships metric views as a first-class semantic-layer
securable: a named bundle of dimensions and measures over a source
table that BI tools and SQL clients can query as if it were a view.
Upstream UC OSS `all.yaml` — the contract soyuz pins (ADR-0002) —
defines none of this: no `MetricView` schema, no `/metric-views`
endpoints, nothing semantic-layer shaped at all. Consumers that want
to persist dimension/measure definitions next to the tables they
describe currently have nowhere to write.

Adding the feature follows the same posture as lineage (ADR-0008),
tags (ADR-0010), table constraints (ADR-0012), and connections
(ADR-0013): a deliberate over-the-spec extension tracked in
`DIVERGENCES.md`, skipped by `test_openapi_conformance.py`'s subset
check, and called out as such in the public docs.

One question shapes the design: **does soyuz compile or execute the
view?** No — soyuz stores and shape-validates the *definition* only.
Compiling a metric view into SQL and running it against the source
table is a query-engine concern that lives in the consumer, the same
boundary connections draw for federated query execution and
credentials draw for vending. `expr` strings are therefore opaque
payload: soyuz never parses them, and a typo'd expression surfaces
in the consumer's compiler, not here.

## Decision

Implement metric views as a definition store under
`{prefix}/metric-views`, structurally a sibling of functions.

1. **Transport**: five routes under the UC API prefix — `POST` /
   `GET` (list) / `GET /{full_name}` / `PATCH /{full_name}` /
   `DELETE /{full_name}`. Mounted under `api_prefix` (like
   connections, unlike the root-mounted lineage / tags) because
   metric views live in the same `catalog.schema.name` hierarchy as
   tables and keeping the CRUD next to the other three-part
   resources minimises URL surprises.
2. **Persistence**: one `metric_views` table keyed by soyuz'
   standard 32-char opaque hex id, unique on `(schema_id, name)`,
   with `catalog_id` denormalised for join-free list filtering —
   the exact `Function` shape. `catalog_name` / `schema_name` /
   `full_name` are reconstructed from the live parent chain at
   response time, so catalog and schema renames propagate for free.
3. **The spec column**: a single validated JSON document —
   `dimensions` (may be empty), `measures` (at least one, enforced
   by pydantic as 422), optional `filter` predicate. Each entry is
   `{name, expr, comment?}` with `extra="forbid"`. Dimension and
   measure names must be unique across the **combined** set
   (service-layer 400): the compiled view exposes them in one flat
   column namespace, so a dimension and a measure sharing a name
   would collide in the consumer's `SELECT` list.
4. **`source_table_full_name` is a loose, name-keyed reference.**
   It is shape-checked (three non-empty dot-separated parts, 400
   otherwise) but *not* resolved against the tables surface, and it
   does not track source-table renames. A metric view may
   legitimately be authored before its source table is registered —
   the same way a SQL view body can reference a yet-to-be-created
   table — and the consumer resolves the reference at compile time,
   which is also where a stale or typo'd reference surfaces. This is
   a deliberate exception to the opaque-id rule used everywhere
   else; see Alternatives.
5. **Parent gates**: create and list resolve the parent catalog +
   schema and 404 when either is missing. `delete_schema` /
   `delete_catalog` count metric views as cascade blockers (409
   without `force`) and bulk-delete them on `force=true` via the
   `delete_metric_views_for_schemas` hook — same FK-without-
   relationship pattern functions use, same explicit-cascade hook
   shape as `delete_constraints_for_tables` (ADR-0012).
6. **Replace-style PATCH** driven by `model_fields_set`: `new_name`,
   `source_table_full_name`, `spec`, `comment`, `owner`. `spec`
   replaces the whole stored document — a per-dimension merge would
   have no predictable semantics against an ordered list.
7. **Audit**: create / update / delete log `metric_view.*` actions
   through `audit_service.log_action`, same pattern as tables and
   tags.

### What soyuz does NOT do

- **No compilation, no execution, no SQL parsing.** `expr` and
  `filter` are stored verbatim.
- **No source-column validation.** soyuz does not check that the
  expressions reference real columns of the source table — that
  would require parsing the opaque SQL.
- **No permissions / tags integration in the MVP.** Metric views are
  not yet a securable type in the permissions or tags resolvers;
  both are additive future extensions because the row carries the
  standard 32-char opaque id.

## Consequences

- **Positive:** semantic-layer consumers get a durable, validated
  definition store addressed exactly like tables, with rename-safe
  parent binding and the standard list/pagination contract. The
  flat-namespace name check catches the one structural error soyuz
  *can* catch without parsing SQL.
- **Negative:** soyuz diverges further from UC OSS — documented in
  `DIVERGENCES.md` under **Metric views**, and
  `{PREFIX}/metric-views` becomes another conformance-test skip.
  The loose source reference means a renamed source table silently
  strands the views built on it until their owners re-point them.
- **Neutral:** if upstream ever ships a semantic-layer API in
  `all.yaml`, soyuz reconciles by editing the wire shapes in place
  (the `spec` JSON column is shape-agnostic), same reversibility
  argument as ADR-0013.

## Alternatives considered

- **Key the source reference on the opaque `table_id`** (the
  rename-invariance rule from ADR-0005/0008/0010). Rejected: it
  would force the source table to exist before the view can be
  authored, breaking the author-definitions-first workflow that is
  normal in semantic layers, and a metric view whose source was
  dropped-and-recreated (the standard ETL table-rebuild pattern,
  which produces a new opaque id) would strand on the *old* id even
  though the name still resolves. For a compile-time reference the
  name is the more honest key; the trade-off is documented on the
  model.
- **Normalise dimensions/measures into child rows** (one row per
  entry, like columns). Rejected: soyuz never queries individual
  entries — the consumer always reads the whole spec — so child rows
  would buy nothing except join fan-out and a second migration
  every time the entry shape grows a field.
- **Validate `expr` with a SQL parser.** Rejected: soyuz has no
  query side, so any dialect choice would be speculative and would
  reject valid consumer-dialect expressions. Same argument as the
  per-connector option validation rejected in ADR-0013.
- **Mount at the root** (like lineage / tags). Rejected: metric
  views are addressed by the same three-part full names as tables
  and the catalog-hierarchy extensions (connections) already live
  under the prefix; the conformance-test skip works either way.

## References

- [ADR-0010](0010-tags-as-extension.md) — the over-the-spec
  extension template this ADR follows.
- [ADR-0012](0012-table-constraints.md) — the explicit cascade-hook
  pattern reused for parent deletes.
- [ADR-0013](0013-connections-and-foreign-catalogs.md) — the
  metadata-only boundary argument and the under-the-prefix mounting
  precedent.
- `soyuz_catalog/services/metric_view_service.py` — implementation.
- `DIVERGENCES.md` — the Metric views entry documenting this as a
  soyuz extension.
