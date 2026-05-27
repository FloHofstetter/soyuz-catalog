# Pagination

Every list endpoint in soyuz-catalog paginates with an opaque
`page_token` cursor that encodes the `(created_at, id)` tuple of the
last row on the previous page. There is no `offset`, no `page`
number, and no total count. A client requests one page at a time and
echoes the server's `next_page_token` verbatim to ask for the next.

The cursor design is fixed in
[ADR-0003](../adr/0003-keyset-pagination.md).

## Why keyset, not offset

Offset pagination has two problems that show up the moment a list
endpoint is genuinely useful: rows that shift past the offset
between page requests get **skipped**, and rows that move forward
get **served twice**. Both happen routinely under concurrent inserts
and deletes, which is exactly what UC catalogs see — pipelines
register tables while a UI is listing them.

Keyset pagination, by anchoring the next page to the last row of
the previous one rather than to a row count, sidesteps both. New
inserts before the cursor do not push old rows out of view; deletes
behind the cursor are invisible. The "natural" cost — random-access
into the middle of a list — is something soyuz consciously does not
support; the use case does not exist.

Performance is the secondary win: a keyset cursor backed by an
index on `(created_at, id)` is an `O(log N)` lookup regardless of
how deep into the list the client is. Offset pagination at page
1000 scans the previous 999 pages.

## The cursor shape

The token is `base64url(json({"c": <created_at_ms>, "i": <id>}))`
with no padding. JSON rather than a raw tuple so a future cursor
field can be added without a version byte. The token is opaque from
the client's perspective and is **not** a security boundary — it is
not HMACed.

Any decode failure (non-base64, non-JSON, wrong shape, wrong value
types) surfaces as `400 INVALID_ARGUMENT`. A tampered or stale token
fails loudly rather than quietly resetting to the first page,
which is the same silently-accept-garbage class that `extra="forbid"`
rejects on request bodies.

## Ordering and page size

Every list endpoint orders by `(created_at ASC, id ASC)` — oldest
first within a tie. `created_at` is ms-epoch and never mutated after
insert, so the order is stable across re-reads.

Page size is controlled by `max_results`:

| Value | Effect |
|---|---|
| Absent or `0` | Server default — 100 rows per page. |
| 1–1000 | Honoured verbatim. |
| Negative, or `> 1000` | `400 INVALID_ARGUMENT`. |

`0` resolving to the default rather than 422 is a documented
divergence from a strict reading of the spec — the upstream JVM
`UCSingleCatalog` connector sends `0` when it wants the server
default, and rejecting that call would break a known client. See
[DIVERGENCES.md → Pagination](../divergences.md).

## The end-of-list contract

`next_page_token` is present on every response **except** the last
page. Implementation-wise the service requests `limit + 1` rows; if
the sentinel row exists the page is full and another follows, if it
does not the page is the last one and the token is omitted. The
sentinel trick avoids the phantom-empty-final-page bug that bites
naïve `len(rows) == limit ? more : done` checks.

A client iterates correctly with:

```bash
TOKEN=""
while :; do
    RESP=$(curl -s "$BASE/catalogs?max_results=50&page_token=$TOKEN")
    echo "$RESP" | jq '.catalogs[]'
    TOKEN=$(echo "$RESP" | jq -r '.next_page_token // empty')
    [ -z "$TOKEN" ] && break
done
```

## Pitfalls

- **No backward pagination.** Cursors are forward-only. Clients
  that need the previous page re-walk from the start.
- **No stable position across renames.** The cursor walks rows in
  insertion order. A row renamed or updated does **not** move in
  the listing — `created_at` is immutable.
- **No cursor invalidation.** Tokens never expire. Holding a token
  for an hour and resuming is supported; the rows that appeared in
  the meantime are returned as part of the resumed walk.
- **Per-row inheritance does not bypass the order.** Filtered list
  endpoints (e.g. `?catalog_name=sales`) apply the cursor after the
  filter — the cursor refers to the position within the filtered
  set, not the global set.

## See also

- [ADR-0003](../adr/0003-keyset-pagination.md) — full design
  rationale and the alternatives that were rejected.
- [REST API reference](../reference/api.md) — every list endpoint
  documents its `max_results` and `page_token` parameters.
- [Divergences → Pagination](../divergences.md) — the `max_results=0`
  resolution and why it exists.
