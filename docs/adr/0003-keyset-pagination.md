# ADR-0003: Keyset pagination for list endpoints

- **Status:** Accepted
- **Date:** 2026-04-14
- **Deciders:** @FloHofstetter

## Context

The Unity Catalog REST API specifies `max_results` / `page_token` on every
list endpoint and a `next_page_token` in every list response. Phases 1 and 2
of soyuz-catalog accepted the parameters for wire compatibility but ignored
them: every call returned the full result set and `next_page_token` was
always `null`. That is fine for a read-round-trip test against a tempdir
Delta table, but it breaks the moment a real catalog grows past a few
thousand rows — a client has no way to page through, and an unbounded
response is a denial-of-service vector at the response-serialisation layer
even before the network cost hits.

soyuz therefore needs a real pagination implementation. The four list
queries (catalogs, schemas, tables, volumes) all walk a single indexed
table filtered by at most one parent foreign key, so any design choice
applies uniformly — the decision is about strategy, not about per-resource
tradeoffs.

## Decision

Use **keyset pagination** on the tuple `(created_at, id)`, not `OFFSET /
LIMIT`.

- Order every list query by `created_at ASC, id ASC`. Both columns exist
  on every resource, `created_at` is never mutated after insert, and `id`
  is a UUID4 primary key — together they form a stable total order.
- The cursor is an opaque `page_token = base64url(json({"c":
  created_at_ms, "i": row_id}))` with no padding. JSON (rather than a
  raw tuple) reserves room for a future filter-hash guard without a
  version bump.
- `decode_page_token` rejects any tampered / malformed token with
  `400 INVALID_ARGUMENT`. The token is **not** HMACed: it is not a
  security boundary, only a tamper-evidence signal, and the service
  layer already has the `extra="forbid"` /
  `UNKNOWN_*_OPERATION`-rejection policy of failing loudly on garbage
  input.
- `max_results` defaults to `100` and is capped at `1000`. The route-layer
  `Query(ge=1, le=1000)` bounces out-of-range values as `422` before they
  reach the service; the service itself defends with a
  `400 INVALID_ARGUMENT` when called directly.
- Fetch `max_results + 1` rows; if the sentinel row exists, drop it and
  emit a `next_page_token` built from the **last returned** row. This
  sidesteps the phantom-empty-page bug where the last page has exactly
  `max_results` rows.
- All four services share one helper module,
  `soyuz_catalog.pagination`, with `encode_page_token`,
  `decode_page_token`, `apply_keyset`, and `build_next_token`. Adding a
  new paginated list endpoint is a two-call change in the service.

## Consequences

- **Positive:** pagination is stable under concurrent inserts — a row
  inserted between two `GET` calls either appears on a future page or
  does not appear at all, but never causes a previously-returned row
  to be skipped or repeated (the failure mode of `OFFSET`-based
  pagination). The page-size cap gives a bounded response size per
  call, independent of catalog growth.
- **Negative:** list ordering is no longer name-sorted. Clients that
  pretty-printed the earlier output and relied on alphabetical order
  will see a change — documented in `DIVERGENCES.md`. The UC OpenAPI
  spec does not define a list ordering, so this is not a spec
  violation, but it is a user-visible behavior change.
- **Neutral:** cursor tokens are opaque but not versioned today. If a
  future change needs to rewrite the payload shape, it can piggy-back
  on the existing `{"c", "i"}` shape check (mismatched shape already
  rejects as 400), which gives us a grace period to roll forward
  without breaking in-flight clients.

## Alternatives considered

- **OFFSET / LIMIT.** Simple, idiomatic, and wrong under concurrent
  inserts — a row inserted between two `GET` calls at the tail of the
  current page causes the next page's first row to be skipped or
  repeated depending on whether the new row lands before or after the
  offset cursor. Rejected because soyuz is a catalog, which is
  write-often on the table/volume scale, and the UC spec's opaque
  `page_token` shape was designed precisely to enable keyset.
- **Surrogate `seq` integer column.** A dedicated monotonically
  increasing sequence column on every resource would give us a
  single-column cursor. Rejected because `(created_at, id)` is already
  available on every model, does not require a migration, and gives
  the same stability properties as long as `created_at` is never
  mutated (which it is not — `updated_at` is the mutable sibling).
- **HMAC-signed tokens.** Would prevent clients from hand-editing a
  token to jump to an arbitrary position. Rejected because the token
  is not a security boundary: a client that can `GET /catalogs` can
  already see every catalog; no information is hidden by an unsigned
  token, and the shape check in `decode_page_token` already rejects
  any tamper that is not a plausible valid cursor.
