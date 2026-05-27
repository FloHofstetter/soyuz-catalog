# ADR-0011: Delta commit coordinator — passthrough implementation

- **Status:** Accepted
- **Date:** 2026-04-15
- **Deciders:** @FloHofstetter
- **Supersedes:** [ADR-0006](0006-coordinated-commits.md)

## Context

[ADR-0006](0006-coordinated-commits.md) formalised soyuz's "no commit
coordinator" posture and pinned `POST /delta/preview/commits` to return
501 `COMMIT_COORDINATOR_UNSUPPORTED`. The decision cited two concerns —
multi-writer correctness (optimistic concurrency + a backfill watchdog)
and absence of a real consumer — and catalogued a four-code-site exit
ramp for the day either concern dissolved.

A Spark compatibility audit identified managed-Delta as the **only**
remaining gap between soyuz and a complete Spark workflow: every other
Spark SQL statement `UCSingleCatalog` can emit already works against
soyuz or is blocked by the upstream JVM connector itself.

Re-reading the upstream protocol against
`~/git/unitycatalog/server/src/main/java/io/unitycatalog/server/persist/DeltaCommitRepository.java`
(lines 152–414) and the Delta Kernel client at
`~/git/delta/kernel/unitycatalog/src/main/java/io/delta/kernel/unitycatalog/UCCatalogManagedCommitter.java`
showed both ADR-0006 concerns were overstated:

- **OCC is a `UNIQUE(table_id, commit_version)` constraint.** Two
  writers racing on version N — one wins via the unique constraint,
  the other's `IntegrityError` translates to 409 and the client
  retries at N+1. This is the exact pattern `Permission`, `Tag`, and
  `LineageEdge` already use in soyuz. No lock manager, no version
  vectors, no watchdog.
- **Backfill is the *client's* job, not the coordinator's.** The
  Delta Kernel client writes the staged commit file to
  `_delta_log/.tmp/<uuid>.json`, POSTs to the coordinator, receives
  200, and **publishes** the file to `_delta_log/NNNNN.json` itself.
  Readers that encounter unbackfilled commits in the GET response
  apply them **in-memory** (`snapshotBuilder.withLogData(...)`). A
  client crash between commit and publish leaves an orphaned
  coordinator row — and the next reader handles it by applying the
  row in memory on the next read. soyuz needs no background loop.

With the correctness story reducing to a unique constraint,
ADR-0006's rejection rationale no longer holds. ADR-0006's own
exit ramp already enumerated the four code sites — schemas, ORM,
service, route — so this decision is a direct execution of that
exit plan, updated with the observations above.

A note on the consumer story, because it changed during
implementation: the audit identified the JVM `UCSingleCatalog`
connector as the expected consumer and the upstream
`unitycatalog-spark` 0.3.0 smoke test fails with SCHEMA_NOT_FOUND
from Spark's analyzer, **before** the UC catalog plugin is
invoked. The failure is inside Spark: the Delta SQL extension
intercepts `USING delta` DDL and reroutes it through
`spark_catalog` (configured as `DeltaCatalog` per the upstream UC
recipe), and `DeltaCatalog` does not know about UC-registered
schemas. This is an upstream Spark / Delta / connector integration
issue — the upstream UC docs themselves carry a TODO for covering
managed Delta in the managed-table section. The coordinator
shipped by this sprint therefore serves two populations today:
direct Delta Kernel clients (`delta-rs`, any client speaking the
REST coordinator protocol), and any future `unitycatalog-spark`
revision that fixes the Spark-side routing. It is spec-complete
per the UC OpenAPI contract; whether Spark reaches it is a
separate concern that a future upstream connector revision will
close.

## Decision

**soyuz-catalog ships a passthrough Delta commit coordinator for
local-filesystem (`file://`) Delta tables.** `POST /delta/preview/commits`
persists commits to a new `delta_unbackfilled_commits` table keyed on
`(table_id, commit_version)` with a unique constraint, enforces
`commit_version == latest + 1` at the service layer, catches
`IntegrityError` from the unique constraint and translates it to 409,
prunes rows on `latest_backfilled_version` (preserving the pruned-boundary
row via an `is_backfilled_latest_commit` flag, matching the upstream
Java implementation), and caps each table at 10 unbackfilled rows
(matching upstream's `MAX_NUM_COMMITS_PER_TABLE`). `GET /delta/preview/commits`
returns the unbackfilled rows within the requested window and reports
`latest_table_version` as the max commit version the coordinator has
seen (falling back to `DeltaTable(path).version()` when the table has
no coordinator rows, preserving the original read-path for freshly
attached tables). Multi-writer correctness comes from the database
unique constraint alone — there is no lock manager, no version
vector, and no background watchdog.

Cloud storage schemes remain `NotImplementedError` (the same gate
`get_commits` already enforces) because cloud read-through requires
the out-of-scope credential-vending layer. `DeltaMetadata` and
`DeltaUniform` on the request body are accepted as opaque dicts and
discarded — soyuz does not interpret Iceberg-conversion or protocol-
upgrade metadata, and the upstream protocol treats both fields as
pass-throughs to the Delta Kernel client anyway.

## Consequences

- **Positive.** soyuz is now spec-complete for
  `POST /delta/preview/commits`: the full 200 / 400 / 409 / 422 /
  429 / 501 contract is implemented and regression-pinned at the
  HTTP level by `tests/test_delta_commits.py`. Any client that
  calls the endpoint — `delta-rs`, direct Delta Kernel clients, or
  any future `unitycatalog-spark` connector revision that routes
  managed-Delta DDL through the configured UC catalog — gets the
  full feature. The "Managed Delta tables via Spark" entry in
  `DIVERGENCES.md` is deleted — it described a soyuz-side gap that
  no longer exists.
- **Neutral.** Spark's own managed-Delta path (via the current
  `unitycatalog-spark` 0.3.0 connector) does **not** reach the
  coordinator, and this ADR does not change that. Spark's Delta SQL
  extension intercepts `USING delta` DDL at analysis time and reroutes
  it through `spark_catalog` before the UC catalog plugin is invoked;
  the failure mode is `SCHEMA_NOT_FOUND` from the analyzer, not any
  HTTP response from soyuz. This is an upstream Spark / Delta /
  connector integration gap — the upstream UC docs themselves carry a
  TODO ("we need to cover both parquet and delta") for managed tables.
  `test_managed_delta_table_creation_via_spark` therefore stays
  `xfail(strict=True)` with a reason pointing at the connector gap,
  and the Spark compatibility matrix case moves from Category B
  (`EXPECTED_501`) to Category C (`EXPECTED_CONNECTOR_THROW`),
  alongside ALTER / RENAME / VOLUME. The xfail flips to a real pass
  the day an upstream connector revision wires managed-Delta DDL
  through the named UC catalog.
- **Positive.** The coordinator reuses soyuz's existing
  `IntegrityError → ConflictError` plumbing with no new concurrency
  primitives. The entire OCC story is a single `UniqueConstraint` on
  `(table_id, commit_version)` in
  `soyuz_catalog/models.py`. Nothing
  in the service layer holds a lock, opens a new transaction, or
  runs a background job.
- **Negative.** soyuz now owns a write-path resource it did not own
  before. A new table (`delta_unbackfilled_commits`) and a new
  migration are permanent parts of the schema. The endpoint's surface
  expands from "always 501" to a real 200 / 400 / 409 / 429 matrix
  with corresponding regression tests.
- **Negative.** Because the new table has **no foreign key** on
  `table_id` (matching the `Tag` / `LineageEdge` / `Permission`
  pattern of addressing resources by opaque id), a `DROP TABLE`
  leaves commit rows orphaned. This is the same semantic all three
  precedent tables already have, and orphans are unreachable
  without the original table's opaque id. Consequence recorded here
  so the next reader does not re-discover it.
- **Neutral.** `CommitCoordinatorUnsupportedError` and its dedicated
  error code `COMMIT_COORDINATOR_UNSUPPORTED` are retired: the
  class, the 501 mapping, and all string references in tests and
  docs are removed. The generic `NotImplementedError` remains for
  the cloud-scheme fallthrough.
- **Neutral.** The cap at 10 unbackfilled commits per table matches
  upstream (`MAX_NUM_COMMITS_PER_TABLE`). Clients that exceed it
  receive 429 `TOO_MANY_REQUESTS` — a new exception class,
  `TooManyRequestsError`, joins the existing domain-exception set
  in `soyuz_catalog/exceptions.py`.

## Alternatives considered

- **Keep ADR-0006 and advise users to use external Delta tables.**
  Rejected: the Spark compatibility audit established that this was
  the sole remaining Spark gap, and the correctness argument that
  motivated ADR-0006
  no longer stands once the protocol's OCC story is read as a unique
  constraint. Leaving it open means Spark users must know about the
  managed-vs-external distinction, which is a leaky abstraction the
  catalog is supposed to hide.
- **Implement a locking / version-vector coordinator.** Rejected on
  simplicity grounds: the upstream Java server does not use locks
  either — it relies on the same uniqueness-plus-retry loop. Adding
  a lock layer would ship machinery that neither the spec nor the
  upstream reference implementation requires.
- **Implement a background backfill watchdog.** Rejected because
  the Delta Kernel client self-publishes and the Delta Kernel reader
  applies unbackfilled rows in memory. A watchdog would be
  duplicative state at best and a correctness hazard at worst (two
  backfillers racing).
- **Support cloud storage in this sprint.** Deferred: cloud
  read-through still needs credential vending, which is a separate
  scope decision. The existing `file://` gate stays, the same way
  `get_commits` already gates it.
