# ADR-0006: Coordinated commits — no coordinator

- **Status:** Superseded by [ADR-0011](0011-delta-commit-coordinator.md)
- **Date:** 2026-04-15
- **Deciders:** @FloHofstetter
- **Supersedes:** — (refines the original decision on `/delta/preview/commits`)
- **Superseded by:** [ADR-0011](0011-delta-commit-coordinator.md) — re-opens this decision and ships the passthrough coordinator as a first-class feature. The rationale below is preserved verbatim as historical record; see ADR-0011 for the current posture.

## Context

An earlier iteration shipped the `/delta/preview/commits` preview
resource with the following posture: `GET` returns an always-empty
`commits` list plus the latest on-disk version read from the underlying
`_delta_log/`, and `POST` raises a generic 501 via
`exceptions.NotImplementedError`. The rationale at the time was that
soyuz has no *unbackfilled-commit coordinator* — no place to stage
commits, no cross-writer locking, no backfill loop — and the spec
itself lists 501 as a valid response for the `commit` operation, so the
501 was a documented out rather than a divergence.

A subsequent live Spark + UC JVM connector smoke test
(`tests/test_spark_roundtrip.py`) discovered that the connector routes
**managed** Delta table creation through Delta's catalog-managed
(coordinated-commits) protocol — and the first call on that path is
exactly the `POST /delta/preview/commits` that soyuz returns 501 for.
External Delta tables (`LOCATION file://…`) round-trip cleanly; managed
Delta does not. The failure was pinned as `xfail(strict=True)` in
`test_managed_delta_table_creation_via_spark` and explicitly deferred
pending the coordinated-commits decision.

This ADR is that decision. Two options were on the table:

**(a) Minimal passthrough coordinator.** soyuz mints a commit row on
`POST /delta/preview/commits` without coordinating across writers — just
a version-gap check, an insert into a new `delta_unbackfilled_commits`
table, and a 200 response. Clients are expected to self-backfill. This
makes the managed-Delta xfail flip to passing.

**(b) Documented no-coordinator posture.** soyuz formalises its
non-coordinator status as a permanent decision and surfaces it via a
dedicated `error_code` on the existing 501, so clients and operators can
tell "this server is definitively not a Delta commit coordinator" apart
from "this endpoint is not yet wired up". The managed-Delta xfail stays
pinned, but now on an explicit rejection rather than a generic
"not implemented" — which is the real product signal this ADR is
supposed to produce.

The tension is between surface area (option a ships code for a feature
with no consumer yet) and honesty (option b admits that soyuz is not the
piece of infrastructure a Databricks-managed-commits client is looking
for). No real consumer has asked for managed Delta on soyuz; the only
caller found was the JVM UC connector exercising the path for
its own roundtrip test. Any correctness story for option (a) that
involves more than one writer requires optimistic concurrency on the
commit sequence and a backfill watchdog — both of which are
scope-creeping for a catalog server whose entire point is to be the thin
Python reimplementation of the UC REST spec, not a replacement for the
Databricks-managed commit coordinator.

## Decision

**soyuz-catalog will not act as a Delta commit coordinator.** The
`POST /delta/preview/commits` operation continues to return HTTP 501, but
via the dedicated exception class
`soyuz_catalog.exceptions.CommitCoordinatorUnsupportedError` carrying
`error_code = "COMMIT_COORDINATOR_UNSUPPORTED"`. The status code is
unchanged — the upstream spec explicitly lists 501 as a valid response
for this operation — but the error code is now distinct from the
generic `NOT_IMPLEMENTED` used elsewhere in the same module (the
`get_commits` cloud-scheme fallthrough and the missing-`delta`-extra
case, which *are* "not yet" conditions and should keep the generic
code).

## Consequences

1. **Managed Delta tables via the JVM UC Spark connector remain
   unsupported.** `test_managed_delta_table_creation_via_spark` stays
   `xfail(strict=True)`. Its reason string cites this ADR and the new
   error code; the failure mode is pinned as an explicit, typed
   rejection rather than a generic 501.
2. **External Delta tables remain the supported path.** The
   external-table roundtrip tests are the golden path. `DIVERGENCES.md`
   "Managed Delta tables via Spark" says so explicitly.
3. **`GetMetastoreSummaryResponse` is not extended** with a
   soyuz-invented capability flag. The upstream schema at
   `all.yaml` carries only `metastore_id`, and the JVM connector does
   not probe a soyuz extension before it calls `commit()`, so an added
   field would be dead wire. Clients that want to sniff the posture up
   front can call `POST /delta/preview/commits` with any body and inspect
   the `error_code` — which is exactly what the dedicated code is for.
4. **No ORM change, no new schemas.** The `DeltaCommit`,
   `DeltaCommitResponse`, and `DeltaCommitInfo` Pydantic models from the
   upstream spec remain unmodelled. The `delta_unbackfilled_commits`
   table remains unbuilt.

## Rejected alternative

**Option (a) — minimal passthrough coordinator.** Rejected for now on
surface-area grounds: soyuz has no consumer for managed Delta, and a
single-writer "mint a row, trust the client to backfill" stub would ship
a correctness footgun that a real multi-writer consumer would
immediately trip over. It is not rejected *forever* — ADR-0006 records it
as the future exit ramp.

## Future exit ramp (if a real consumer asks for managed Delta)

A future change can re-open this ADR and implement a minimal passthrough
without having to re-discover the surface area. The four code sites are:

1. **Schemas.** Add `DeltaCommit`, `DeltaCommitResponse`, and
   `DeltaCommitInfo` Pydantic models to
   `soyuz_catalog/api/schemas.py`, mirroring the upstream shapes at
   `~/git/unitycatalog/api/all.yaml` §§ `DeltaCommit` / `DeltaCommitInfo`
   / `DeltaCommitResponse`.
2. **ORM.** Add a `delta_unbackfilled_commits` table to
   `soyuz_catalog/models.py` keyed on `(table_id, commit_version)` with
   a uniqueness constraint so that the spec's 409 "version already
   exists" case is race-safe (the same IntegrityError → ConflictError
   pattern the rest of the service layer uses).
3. **Service.** Implement `delta_commits_service.commit()` with the
   version-gap check against the registered table's
   `latest_table_version + 1`, the insert, and the explicit 400 for
   `latest_backfilled_version ≥ commit_version` that the spec calls out.
4. **Route.** Update the handler at
   `soyuz_catalog/api/routes/delta_commits.py` (`commit()`) to dispatch
   to the service instead of raising `CommitCoordinatorUnsupportedError`.

At that point the exception class itself can either be retired or
repurposed as a feature-flag "this instance has the coordinator
disabled" signal, and the managed-Delta `xfail` flips to passing.
Rewrite `DIVERGENCES.md` accordingly in the same PR, and update this
ADR's status to `Superseded by ADR-NNNN`.
