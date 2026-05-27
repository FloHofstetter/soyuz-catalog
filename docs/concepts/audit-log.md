# Audit log

soyuz-catalog writes one append-only audit row per successful mutation
and exposes them on a single read endpoint, `GET /audit-log`. Upstream
Unity Catalog OSS has no audit surface — its Java reference logs
nothing about who created, modified, or deleted which securable. The
soyuz extension exists because agent-driven clients (LLM workflows,
pipeline orchestrators) need to cross-reference UC mutations back to
their own per-run views, and a server-side audit table is the
shortest path.

The endpoint is mounted at the root (`/audit-log`), not under the
Unity Catalog spec prefix, so it stays outside the spec-conformance
gate and a spec-only client never sees it.

## What gets written

A mutation route calls
`services/audit_service.log_action(db, action, target, detail)` after
its database write commits. The row carries:

| Field | Source |
|---|---|
| `action` | Dotted route identifier — `tag.updated`, `tables.create_table`, `schemas.delete_schema`. Convention is `<resource>.<verb>`. |
| `target` | The securable that was mutated — `sales.fact.orders`, `catalog:sales`, `tag:table:sales.fact.orders`. |
| `principal` | Captured from the `X-Principal` request header. |
| `agent_run_id` | Captured from the `X-Agent-Run-Id` request header. |
| `client_ip` | Connection-level (or the first hop of `X-Forwarded-For` if the proxy attaches it). |
| `detail` | Action-specific JSON — e.g. the list of tag changes in a batch, the before/after owner on a permissions update. `None` when the action + target line is enough. |
| `created_at` | Server time at write (ms-epoch). |

!!! info "Best-effort writes"

    An audit-write failure is logged but never rolls back the
    underlying mutation. The audit log is a forensic aid, not a
    tamper-resistant compliance store.

The write is **best-effort**. An audit-write failure is logged at
WARNING but never rolls back the underlying mutation — a transient
database hiccup is allowed to lose an audit row rather than block a
successful schema create.

The middleware lifts `X-Principal` and `X-Agent-Run-Id` from request
headers into request-scoped `ContextVar`s, so route handlers do not
pass them explicitly. The two headers are the contract; nothing
prevents an upstream proxy from forwarding the same values it pulled
from a JWT, an OIDC session, or a mTLS client cert.

## Why the proxy attaches identity, not soyuz

soyuz does not authenticate. The deployment pattern is the same as
for grants:

```text
[ clients ] --> [ auth proxy / IdP ] --> [ soyuz ]
```

The proxy authenticates, attaches `X-Principal` (and optionally
`X-Agent-Run-Id`), and decides whether to forward the call. soyuz
then services the request, records the principal in the audit log,
and returns the spec-correct response. This is the same offload
model documented in
[Permissions model § Why no enforcement](permissions-model.md#why-no-enforcement),
and the audit log is exactly the trail that makes the offload
auditable.

If the proxy attaches nothing, the audit row stores `principal:
NULL` — visible but not attributable. That is a deployment
misconfiguration, not a soyuz bug.

## The `agent_run_id` filter

`GET /audit-log?agent_run_id=<uuid>` returns every audit row for one
run, in oldest-first order. Agent-driven clients that forward
`X-Agent-Run-Id` on every mutating call get a single round-trip
answer to *"which UC mutations did this run make?"* — the cross-index
soyuz's audit log was designed for.

Without the filter, `GET /audit-log?limit=N` returns the most-recent
N rows across all runs, newest first. `limit` is bounded `[1, 1000]`
and defaults to 200. This is the operator-style view: "what just
happened on this server?"

## What is and isn't covered

**Covered** (the minimum write-path surface):

- Tag updates (`tags.update_tags`).
- Table create + delete.
- Schema create + update + delete.

Every other mutation route follows the same pattern when a real
consumer asks; the six above are the documented minimum. The audit
log is a thin, easily-extended hook — a missing route is one
`log_action` call away from coverage.

**Not covered:**

- **Reads.** Audit is mutation-only. If you need read tracing, use
  the request log.
- **Failed mutations.** `log_action` fires after the DB write
  commits, before the response is sent. A request that errored
  before the commit never lands in the audit table.
- **Background processes.** soyuz has none — a single foreground
  process serves every request.
- **Network-level outcome.** A row exists for every successful
  commit, even when the response was lost in transit. soyuz cannot
  tell what the client observed.

## When this is enough, and when it is not

The audit log is enough for:

- **Operational forensics.** "Who removed the `pii` tag from this
  table?" — one query.
- **Per-run agent cross-indexing.** "What did `run-abc-123` do?" —
  one query with `?agent_run_id=`.
- **Detecting unattributed mutations.** A row with `principal: NULL`
  is visible signal that the upstream proxy did not attach a header.

It is **not** enough for tamper-resistant compliance audit. The rows
live in the same database as the mutations they describe. An
operator with DB access can rewrite them. If you need an audit trail
that survives an insider with database credentials, ship the rows to
an append-only external store — typically by tailing structured logs
into Loki / Elasticsearch / a SIEM, or by scheduled SELECT into an
S3 bucket with object-lock retention.

## See also

- [Walkthrough: querying the audit log](../guides/walkthroughs/audit-log.md)
  — set principal headers, make mutations, query the resulting rows.
- [Permissions model § Why no enforcement](permissions-model.md#why-no-enforcement)
  — the same proxy-offload story from the grants side.
- [Observability and audit log (admin)](../admin/observability.md)
  — the operator view: where audit lines join the request log, what
  to watch.
- [Extensions over the spec](extensions-over-spec.md) — where audit
  fits in the broader extension picture.
- [Divergences → Audit log](../divergences.md) — wire-level
  definition and the explicit conformance-test skip.
