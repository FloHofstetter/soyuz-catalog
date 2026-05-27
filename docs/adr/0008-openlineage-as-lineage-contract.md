# ADR-0008: OpenLineage as the lineage contract

- **Status:** Accepted
- **Date:** 2026-04-15
- **Deciders:** @FloHofstetter
- **Supersedes:** —

## Context

Unity Catalog OSS ships no lineage. There is no `Lineage` resource in
`~/git/unitycatalog/api/all.yaml`, the Java server has no lineage
tables, and the upstream clients have no lineage SDK. Databricks holds
lineage as a managed-only feature and has not published a spec. Any
lineage work in soyuz is therefore **net-new ground**, not porting —
and we have to commit to a shape without an upstream fallback.

soyuz needs lineage to be useful as an over-the-spec extension that
does not pretend to be part of UC. Posture: pick an **external**
contract that already has a producer ecosystem, persist
events against soyuz' existing opaque-id primitives so rename
invariance carries over for free, and keep the ingestion layer
forward-compatible so a new producer facet does not crash soyuz.

## Decision

Adopt **OpenLineage** (https://openlineage.io/) as the lineage
ingestion contract.

1. **Transport**: `POST /lineage/v1/events` accepts an OpenLineage
   `RunEvent` JSON body and returns 201 with a small summary
   (`run_id`, `state`, `accepted_edges`, `rejected_datasets`).
2. **Persistence**: two tables — `lineage_runs` (one row per OL
   `runId`) and `lineage_edges` (one row per resolved
   source × target pair per run). Primary keys are soyuz' standard
   32-char hex; the `runId` is the OpenLineage UUID with hyphens
   stripped.
3. **Securable resolution**: OL dataset `name` is interpreted as a
   `catalog.schema.table` full_name and resolved via the existing
   `permissions_service.resolve_securable` helper. Datasets that do
   not resolve — because they are not in UC — are **silently dropped
   and counted**, not rejected with 400. OpenLineage producers
   legitimately emit events for non-UC tables and a 400 would make
   soyuz unusable as a drop-in sink.
4. **Operation label**: the edge `operation` column stores
   `job.name` verbatim. It is the closest 1:1 across producers;
   richer OpenLineage facets vary by emitter and would pin soyuz
   to one producer's conventions.
5. **Rename invariance**: edges are keyed on opaque table ids, never
   full_names. `full_name` is reconstructed at response time by
   joining `Table → Schema → Catalog`. A catalog or schema rename
   propagates for free — the same mechanism every other soyuz
   resource uses.
6. **Append-only history**: edges are **not** cascade-deleted when a
   referenced table is dropped. Lineage is history; dangling ids
   render on the wire as `full_name = null`. The only cascade is
   `lineage_edges.run_id → lineage_runs.id ON DELETE CASCADE`,
   because deleting a run logically drops its graph contribution.
7. **State semantics**: run state is last-write-wins keyed by run id.
   OpenLineage producers occasionally redeliver or reorder events
   (a restarted worker emitting `RUNNING` after an earlier
   `COMPLETE`), and a strict monotonic state machine would reject
   legitimate retries.
8. **Schema validation exception**: the `OpenLineageEvent` request
   body is `ConfigDict(extra="allow")`. This is a **scoped,
   documented** exception to the soyuz-wide `extra="forbid"` policy.
   OpenLineage evolves independently of soyuz and new facets must
   not crash producers. Every soyuz *response* shape and every
   spec-sourced request shape stay strict. See
   [ADR-0001](0001-stack-and-conventions.md) for the underlying
   policy.
9. **Scope — tables only (MVP)**: volumes, functions, and registered
   models all have the same 32-char opaque id shape, so extending
   the ingestor to accept them is a non-breaking storage change
   that will land in a dedicated sprint when there is a concrete
   consumer asking. The MVP rejects non-table dataset names by
   construction: `resolve_securable(..., "table", ...)` is the only
   call the service makes.

## Consequences

- soyuz diverges further from UC OSS. Documented in
  `DIVERGENCES.md` under the **Lineage** entry.
- If upstream `all.yaml` eventually ships a UC lineage API, soyuz
  can add the spec endpoints as a translation layer over the same
  `lineage_runs` / `lineage_edges` tables — no data migration
  required. OpenLineage and a hypothetical UC lineage API overlap
  semantically (run + edges) so translation is cheap.
- The `extra="allow"` exception on `OpenLineageEvent` is a small
  surface area blast-radius: one class, justified here, flagged in
  CHANGELOG. Reviewers catching `extra="allow"` elsewhere should
  reject it unless a similar ADR exists.
- Traversal uses a Postgres recursive CTE and a SQLite iterative
  BFS fallback, both capped at `lineage_service.MAX_DEPTH = 10`.
  The cap is generous for real pipelines but prevents an accidental
  `?depth=1000` from issuing a full-table scan.

## Alternatives considered

- **Invent a soyuz-native lineage protocol.** Rejected: no producer
  ecosystem, and soyuz already has a "track upstream" philosophy
  ([ADR-0002](0002-spec-is-the-contract.md)). Anchoring on an
  external standard is consistent with that spirit even though the
  standard is not `all.yaml`.
- **Wait for Databricks to publish a UC lineage API.** Rejected:
  a real consumer is asking now. The migration-path clause above
  keeps the option open.
- **Store full_names instead of opaque ids.** Rejected: breaks the
  rename-invariance property every other soyuz resource relies on.
  The whole opaque-id strategy used elsewhere (permissions, tags)
  would be pointless if lineage re-introduced the full_name dependency.

## References

- OpenLineage spec: https://openlineage.io/docs/spec
- [ADR-0001](0001-stack-and-conventions.md) — stack and conventions,
  including the `extra="forbid"` policy this ADR carves an exception
  from.
- [ADR-0005](0005-permissions-without-enforcement.md) — the
  opaque-id-for-rename-invariance pattern this ADR reuses.
- `soyuz_catalog/services/lineage_service.py` — implementation.
- `DIVERGENCES.md` — the Lineage entry documenting this as a soyuz
  extension.
