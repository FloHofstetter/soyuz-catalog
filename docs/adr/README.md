# Decisions

This directory holds Architecture Decision Records (ADRs) for
soyuz-catalog. An ADR captures one significant decision: *why* it was
made, *what* alternatives were considered, and *what* the consequences
are. Once accepted, an ADR is **immutable** — if the decision changes,
write a new ADR that supersedes the old one. Do not edit history.

ADRs are short. One page is the goal; two is the ceiling. If a record is
growing into a design doc, split the design doc out and keep the ADR a
pointer.

## When to write one

Write an ADR when a decision is:

- **Hard to reverse** — database engine, URL prefix, public response
  shapes.
- **Cross-cutting** — touches multiple modules or contracts.
- **Non-obvious in retrospect** — a future contributor will read the code
  and ask "why is this like this?".

Do *not* write one for routine implementation choices that are visible
in a single function or PR.

## Format

Use [`0000-template.md`](0000-template.md) as the starting point.
Filenames follow `NNNN-kebab-case-title.md`, where `NNNN` is the next
free zero-padded number.

---

## Foundational

The shape of the project: stack, contract, storage, conventions.

- [ADR-0001 — Stack and conventions](0001-stack-and-conventions.md).
  FastAPI + SQLAlchemy 2.0 (sync) + Alembic + Pydantic, no JVM, Python
  3.14+, Google-style docstrings, ruff + pyright + pydoclint. The
  foundational technology and convention choices.
- [ADR-0002 — Spec is the contract](0002-spec-is-the-contract.md). The
  Unity Catalog OpenAPI document is authoritative; the Java reference
  implementation is a behaviour reference, not an authority. Every
  divergence is documented and pinned by a regression test.
- [ADR-0003 — Keyset pagination](0003-keyset-pagination.md). List
  endpoints paginate by cursor, not offset, to avoid the silent
  data-skip class of bugs.
- [ADR-0004 — Postgres as a supported backend](0004-postgres-as-supported-backend.md).
  SQLite for development, Postgres for production — both are first-class
  and run in CI.

## Spec posture

How soyuz relates to clients and the spec.

- [ADR-0005 — Permissions without enforcement](0005-permissions-without-enforcement.md).
  soyuz stores grants and computes effective permissions but does not
  enforce them. Authentication and authorization live in the proxy in
  front of soyuz.
- [ADR-0007 — Generated client over hand-written SDK](0007-generated-client-over-hand-written-sdk.md).
  The in-tree Python client is generated from soyuz's own
  `/openapi.json` rather than hand-written. A CI gate prevents the
  client and the server from drifting apart.

## Extensions

Surfaces beyond the open spec, mirrored from Databricks UC because real
clients expect them.

- [ADR-0008 — OpenLineage as lineage contract](0008-openlineage-as-lineage-contract.md).
  Lineage ingest uses the OpenLineage RunEvent format rather than a
  soyuz-native shape.
- [ADR-0009 — Delta REST Catalog as secondary surface](0009-delta-rest-catalog-as-secondary-surface.md).
  A parallel `/delta/v1/...` REST surface for direct Delta-Kernel
  clients, sharing storage with the standard UC surface.
- [ADR-0010 — Tags as an extension](0010-tags-as-extension.md). Tags on
  catalogs / schemas / tables / columns are anchored on opaque UUIDs so
  they survive parent renames.
- [ADR-0012 — Table constraints](0012-table-constraints.md).
  Declared `PRIMARY KEY`, `FOREIGN KEY`, and `NOT NULL` constraints as
  metadata-only declarations; soyuz does not validate row data against
  them.
- [ADR-0013 — Connections and foreign catalogs](0013-connections-and-foreign-catalogs.md).
  Lakehouse Federation: typed references to external metadata sources
  plus foreign-catalog variants of the standard catalog routes.
- [ADR-0014 — Metric views](0014-metric-views.md). Semantic-layer
  dimension/measure definitions stored and validated by soyuz,
  compiled and executed by the consumer.

## Operational

How soyuz coordinates with clients at the data layer.

- [ADR-0011 — Delta commit coordinator (passthrough implementation)](0011-delta-commit-coordinator.md).
  Supersedes [ADR-0006](0006-coordinated-commits.md). soyuz coordinates
  Delta commit version numbers but never touches the Delta log file —
  the client owns storage IO.

## Superseded

ADRs that have been replaced by a newer decision. They are kept for
context.

- [ADR-0006 — Coordinated commits — no coordinator](0006-coordinated-commits.md).
  Superseded by ADR-0011. The original decision was to omit the
  commit coordinator entirely; ADR-0011 walks that back and ships a
  passthrough implementation.

## Complete index

| # | Title | Status |
|---|---|---|
| [0001](0001-stack-and-conventions.md) | Stack and conventions | Accepted |
| [0002](0002-spec-is-the-contract.md)  | Spec is the contract  | Accepted |
| [0003](0003-keyset-pagination.md)     | Keyset pagination     | Accepted |
| [0004](0004-postgres-as-supported-backend.md) | Postgres as a supported backend | Accepted |
| [0005](0005-permissions-without-enforcement.md) | Permissions without enforcement | Accepted |
| [0006](0006-coordinated-commits.md) | Coordinated commits — no coordinator | Superseded by [0011](0011-delta-commit-coordinator.md) |
| [0007](0007-generated-client-over-hand-written-sdk.md) | Generated client over hand-written SDK | Accepted |
| [0008](0008-openlineage-as-lineage-contract.md) | OpenLineage as lineage contract | Accepted |
| [0009](0009-delta-rest-catalog-as-secondary-surface.md) | Delta REST Catalog as secondary surface | Accepted |
| [0010](0010-tags-as-extension.md) | Tags as an extension | Accepted |
| [0011](0011-delta-commit-coordinator.md) | Delta commit coordinator — passthrough implementation | Accepted |
| [0012](0012-table-constraints.md) | Table constraints | Accepted |
| [0013](0013-connections-and-foreign-catalogs.md) | Connections and foreign catalogs | Accepted |
| [0014](0014-metric-views.md) | Metric views | Accepted |
