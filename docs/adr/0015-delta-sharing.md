# ADR-0015: Delta Sharing server as a soyuz extension

- **Status:** Accepted
- **Date:** 2026-06-11
- **Deciders:** @FloHofstetter

## Context

The open [Delta Sharing protocol](https://github.com/delta-io/delta-sharing/blob/main/PROTOCOL.md)
is the de-facto standard for cross-organisation table sharing:
recipients hold a profile file (endpoint + bearer token) and any
Delta Sharing client — pandas, Spark, Power BI — can list shares and
read table data without coupling to the provider's catalog. Databricks
ships shares and recipients as first-class UC securables; upstream
UC OSS `all.yaml` defines none of it, and soyuz tables (file://-backed
Delta tables, ADR-0011's coordinator notwithstanding) have no way to
be consumed from outside the catalog's own API.

Two surfaces are needed: a **management** side (which tables are in
which share, which recipient tokens may read them) and the
**protocol** side recipients actually speak. The protocol brings two
constraints soyuz has never had before: its *own* error envelope
(`{"errorCode", "message"}`), and **authentication** — the bearer
token is part of the wire contract itself, so the ADR-0005 "auth
lives in the front proxy" posture cannot apply to it.

## Decision

Implement both surfaces as an over-the-spec extension (ADR-0008/0010/
0013/0014 posture): documented in `DIVERGENCES.md`, skipped by the
conformance subset check.

1. **Management transport** under the UC prefix (like connections):
   CRUD `/shares` and `/recipients`, `POST`/`DELETE
   /shares/{name}/objects` for table membership,
   `PUT`/`DELETE /shares/{name}/recipients/{recipient_name}` for
   grants, `POST /recipients/{name}/rotate-token`. No auth — the
   proxy owns it, per ADR-0005.
2. **Protocol transport** mounted at the root under
   `/delta-sharing/` (like `/lineage/` — the path layout is an
   external wire contract recipients embed in profile files):
   `shares` list/get, derived `schemas` / `tables` / `all-tables`
   lists, `version`, `metadata`, and `query`, with wire shapes —
   camelCase pagination (`maxResults` / `pageToken` /
   `nextPageToken`), NDJSON `protocol` / `metaData` / `file` action
   lines, the `Delta-Table-Version` header — pinned to PROTOCOL.md.
   Every protocol route requires `Authorization: Bearer <token>`;
   errors use the protocol envelope via a dedicated
   `SharingProtocolError` + handler, never the soyuz one.
3. **Persistence**: four tables. `shares` (flat, name-unique),
   `share_objects` (`share_id`, three-part `table_full_name`,
   optional two-part `shared_as` alias), `recipients` (name-unique,
   `bearer_token_hash`), `share_grants`
   (`share_id` × `recipient_id`, unique pair, idempotent PUT).
   Objects and grants are weak composition — share/recipient deletes
   cascade them at the service layer with no `force` gate, the way
   table columns ride along with their table.
4. **Tokens are hashed, plaintext-once.** Only the SHA-256 of a
   bearer token is stored (unique-indexed for the constant-time
   lookup path); the plaintext appears exactly twice in any
   recipient's life — the create response and each rotate response —
   and never in the audit log. Rotation invalidates the old token
   immediately; there is no activation-link flow, no expiry windows,
   no IP allow-lists (all additive future work).
5. **Share objects bind by table *name*, not opaque id.** The Delta
   Sharing ecosystem is name-keyed end to end (the management wire
   adds by full name, the protocol addresses `share.schema.table`,
   the reference server's config binds names), so the share stores
   `table_full_name` and resolves it live at read time. A renamed or
   dropped table falls out of the share — protocol reads return 404
   until it is re-added. This is a deliberate, documented exception
   to the opaque-id rename-invariance rule; see Alternatives.
   `shared_as` re-homes a table inside the share's two-level
   namespace, and the *effective placement* must be unique per share
   (409 at add time) so every protocol address resolves to at most
   one table.
6. **Snapshot reads via `deltalake`** (same optional-`delta`-extra
   posture as the commit coordinator, ADR-0011): version resolution,
   pinned-`version` query bodies, Delta-format `schemaString`, and
   the active-file list with `partitionValues` and
   `numRecords`-only `stats`. Tables whose Delta protocol demands
   `minReaderVersion > 1` (column mapping, deletion vectors) are
   refused with 400 `UNSUPPORTED_TABLE_FEATURES` instead of being
   served silently-wrong parquet. Timestamp queries and
   `startingVersion`/`endingVersion` (CDF) return 501. Cloud
   storage schemes return 501 — serving them needs the out-of-scope
   credential-vending layer.
7. **soyuz serves the file bytes itself.** Cloud Delta Sharing
   servers return pre-signed object-store URLs; soyuz' tables are
   `file://`-backed, so each `file.url` points back at
   `GET /delta-sharing/files/{file_id}?token=…` on the same server.
   The token is a stateless HMAC-SHA256 handle over the absolute
   path + file id + expiry (`storage/signed_urls.py`), keyed by
   `SOYUZ_SHARING_SIGNING_KEY` (or a per-process random key), with
   a TTL from `SOYUZ_SHARING_FILE_URL_TTL_SECONDS` surfaced as the
   protocol's `expirationTimestamp`. Possession of an unexpired
   handle *is* the authorisation — exactly the pre-signed-URL model
   — so the download route carries no bearer check. Add-action
   paths are resolved and verified under the table root before
   signing, and the signature covers the full path, so traversal
   via a crafted log or a hand-edited handle fails closed (403).
8. **Protocol list pagination is in-memory** over the resolved
   placement lists, cursored on the last item's key (not an
   offset). Every protocol list is *derived* — placements only
   exist after `shared_as` aliasing — and bounded by a share's
   object count, so the ADR-0003 DB keyset machinery has nothing to
   key on. The cursor still resumes stably under concurrent
   membership changes.
9. **Permissive `query` request body** (`extra="allow"`): the
   protocol evolves independently and newer clients send fields
   like `maxFiles`; rejecting them with 422 would break real
   recipients. Same documented exception to the `extra="forbid"`
   policy as the OpenLineage shapes (ADR-0008). Predicate and limit
   hints are accepted and ignored — the protocol defines them as
   non-binding.

### What soyuz does NOT do

- **No CDF, no streaming, no deletion vectors, no delta response
  format.** The capabilities header is ignored and responses are
  always parquet-format; tables needing more are refused loudly.
- **No recipient activation flow.** Tokens are handed to the
  provider admin, who delivers them out of band.
- **No cloud pre-signing.** `file://` only; cloud schemes 501.

## Consequences

- **Positive:** any off-the-shelf Delta Sharing client can read
  soyuz-catalogued tables with a two-line profile file. The full
  loop — share, grant, query, download, verify parquet bytes — is
  pinned by an end-to-end test against a real Delta table.
- **Negative:** soyuz now has a (deliberately small) authenticated
  surface and a secret-bearing column, both of which need the care
  documented above; the name-keyed share binding means table
  renames silently un-share until re-added; conformance skips grow
  by three prefixes.
- **Neutral:** the protocol error envelope and camelCase shapes live
  in their own modules (`api/sharing_schemas.py`,
  `SharingProtocolError`), so the UC surface's conventions stay
  untouched. If upstream UC OSS ever ships sharing in `all.yaml`,
  the management wire shapes reconcile in place; the protocol side
  is pinned to PROTOCOL.md, not to UC, and would not move.

## Alternatives considered

- **Bind share objects to opaque `table_id`** (the ADR-0005/0008/
  0010 rename-invariance rule). Rejected: the protocol exposes
  *names*, so a renamed table would either silently change its
  protocol address (breaking recipients' saved
  `share.schema.table` coordinates mid-stream) or require a frozen
  alias snapshot — at which point the binding is name-keyed anyway.
  Re-adding after a rename is the honest, ecosystem-consistent
  behaviour, and `shared_as` gives providers a stable external name
  that survives internal renames.
- **DB-row download grants instead of HMAC handles.** Rejected: a
  row per file per query is write amplification on the hottest read
  path, needs garbage collection, and buys nothing — expiry and
  tamper-evidence are exactly what an HMAC provides statelessly.
  The cost (a restart invalidates in-flight handles under the
  default per-process key) is bounded by the 15-minute TTL.
- **Replay `_delta_log` JSON by hand instead of using `deltalake`.**
  Rejected: hand-replay breaks on checkpointed or log-cleaned
  tables and re-implements kernel logic the project already depends
  on for the commit coordinator's version fallback. The price is
  `numRecords`-only `stats` (the kernel does not expose raw stats
  strings), which the protocol marks optional.
- **Mount the protocol under the UC prefix.** Rejected: recipients
  configure a base endpoint in their profile file and the protocol
  paths hang directly off it; hiding them under
  `/api/2.1/unity-catalog` would be a spec-looking URL for a
  non-UC contract — the same argument that put lineage at the root
  (ADR-0008).
- **Enforce share grants through the permissions table.** Rejected:
  grants-to-recipients are a different identity domain (bearer
  tokens, not principals) with different semantics (visibility, not
  privilege sets); forcing them into `permissions` rows would
  overload ADR-0005's storage-only model with the one consumer that
  actually enforces.

## References

- [Delta Sharing PROTOCOL.md](https://github.com/delta-io/delta-sharing/blob/main/PROTOCOL.md)
  — the wire contract the protocol surface pins.
- [ADR-0005](0005-permissions-without-enforcement.md) — the
  auth-proxy posture the management surface keeps and the protocol
  surface deliberately breaks.
- [ADR-0011](0011-delta-commit-coordinator.md) — the
  `deltalake`-with-501-fallback posture reused for snapshot reads.
- [ADR-0013](0013-connections-and-foreign-catalogs.md) /
  [ADR-0014](0014-metric-views.md) — the over-the-spec extension
  template.
- `soyuz_catalog/services/sharing_service.py`,
  `soyuz_catalog/services/delta_sharing_service.py`,
  `soyuz_catalog/storage/signed_urls.py` — implementation.
- `DIVERGENCES.md` — the Delta Sharing entry.
