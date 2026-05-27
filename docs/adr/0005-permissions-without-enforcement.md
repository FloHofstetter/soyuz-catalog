# ADR-0005: Permissions without enforcement

- **Status:** Accepted
- **Date:** 2026-04-14
- **Deciders:** @FloHofstetter

## Context

soyuz closes the last spec gap in the `/permissions/...` area of the
Unity Catalog REST API: soyuz-catalog persists and returns grants
via `GET` and `PATCH /permissions/{securable_type}/{full_name}`. The
spec says nothing about who must *enforce* the grants — it only
defines the read/write shape of the grant table itself — but leaving
the question unanswered would let a future reader assume that the
existence of these endpoints means soyuz checks grants elsewhere.

It does not. soyuz-catalog is intentionally an authentication- and
authorisation-free catalog server, and every other spec endpoint
continues to ignore the `permissions` table entirely.

## Decision

**soyuz-catalog persists grants but never enforces them.** The
`/permissions/...` endpoints are a storage backend for an
external auth proxy; any consumer that needs real access control
runs soyuz behind a proxy that reads the grants and rejects or
allows upstream requests before they reach the catalog server.

The following design points flow from this decision.

1. **Opaque `securable_id` over full_name.** Every
   `permissions` row stores the resolved target's opaque `id`
   column, not the client-facing `full_name`. A rename of any
   parent in the `catalog.schema.table` hierarchy therefore leaves
   existing grants attached — the same rename-invariance trick
   that `external_locations.credential_id` uses. The resolver in
   `soyuz_catalog.services.permissions_service.resolve_securable`
   walks the spec's dotted address on write and read, validates
   the segment count strictly (no silent acceptance of a 2-part
   name on a 3-part type), and raises `InvalidRequestError` /
   `NotFoundError` in the same 400/404 shape as every other
   service.
2. **No foreign key from `permissions.securable_id`.** The column
   is polymorphic by design — it references whichever of the nine
   resource tables matches `securable_type`. Nine partial FKs plus
   an unchecked `metastore` singleton would buy nothing the
   service-level cascade does not already buy, and SQL does not
   support the shape natively without a trigger. The cascade is
   owned by each resource's `delete_*` service and runs
   unconditionally (no `force=true` gate), because grants are not
   first-class children the way tables or volumes are.
3. **Per-type privilege allow-set as a hard 400.** UC OSS Java
   accepts any `Privilege` value on any `SecurableType` at API
   time and defers rejection to the (non-existent-in-OSS)
   enforcement layer. soyuz-catalog rejects at write time: a
   `PATCH` that adds `SELECT` on a catalog surfaces as `400
   INVALID_ARGUMENT` before any row is written. This is one more
   entry in the silent-accept-garbage divergence class the
   project exists to fix. The allow-set is a flat dict in
   `permissions_service.py`, hand-curated from the
   `x-enum-descriptions` of the upstream `Privilege` enum, and
   documented verbatim in `DIVERGENCES.md`. `remove` lists are
   **not** gated — removing a privilege that was never allowed on
   this type is harmless and makes cleanup after a future
   allow-set tightening possible.
4. **Additive PATCH, not replace-style.** Unlike every other
   `PATCH` route in this project, permissions use the spec's
   `UpdatePermissions { changes: PermissionsChange[] }` shape:
   clients submit a batch of add / remove operations rather than
   a full desired state. The asymmetry is not a soyuz choice — it
   is the spec — and is called out in `DIVERGENCES.md` so a
   reader does not wonder why this one PATCH is special. Within a
   single change, overlapping entries resolve as *add wins*
   (removes are applied first); the spec does not pin a
   tiebreaker and soyuz picks the one that is consistent with
   "the user wanted the privilege after the call".
5. **Idempotency via pre-check, not database unique index.** The
   `(securable_type, securable_id, principal, privilege)`
   composite unique index is the grant identity, but
   `update_permissions` pre-checks the existing set for the
   principal before inserting so a duplicate add never triggers
   an `IntegrityError` rollback — the rollback would discard
   every earlier change in the same batch. A concurrent racing
   PATCH that slips past the pre-check still hits the unique
   index and surfaces as 500; clients retry. This matches the
   race strategy used by every other `create_*` in the service
   layer.
6. **Storage-only, explicitly.** No other endpoint in soyuz —
   not `GET /tables/{full_name}`, not the `/temporary-*`
   credential-vending stubs, not `DELETE /catalogs/{name}` —
   consults the `permissions` table. The only cross-endpoint
   interaction is the cascade hook from every `delete_*`
   service, which wipes grants attached to the deleted row and
   any children. If a future consumer needs enforcement, the
   right answer is a proxy in front of soyuz, not a second
   sprint to wire the grants into every other route handler.

The proxy-layer story itself is deliberately out of scope for this
ADR. A follow-up ADR will cover it if the need materialises.

## Consequences

- Every UC client can round-trip permissions without surprises, but
  the grants are decorative unless something outside soyuz enforces
  them.
- The per-type allow-set is a knob the project owns. A future
  upstream `Privilege` enum addition is a one-line `schemas.py`
  change plus an allow-set entry; the docs / tests catch up in the
  same commit.
- Nine `delete_*` services now carry a cascade hook into
  `permissions_service.wipe_permissions_for`. A tenth resource type
  added in a later sprint must do the same or it will silently leak
  stale grants across recreated rows.
- The decision reinforces the no-auth-in-catalog posture that every
  earlier ADR has taken: soyuz-catalog is a data plane, not an
  identity plane.
