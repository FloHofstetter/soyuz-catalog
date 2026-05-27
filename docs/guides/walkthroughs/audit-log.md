# Walkthrough — Querying the audit log

> **Goal:** make a few mutations attributing them to different
> principals and one agent run, then query the audit log unfiltered
> and by `agent_run_id`.
>
> **Surface:** `GET /audit-log` (root-mounted, not under
> `/api/2.1/unity-catalog`). Mutation routes call `log_action`
> after a successful write; `X-Principal` and `X-Agent-Run-Id` request
> headers carry the identity.
>
> **Prereqs:** soyuz running on `:8000`.

```bash
BASE=http://127.0.0.1:8000/api/2.1/unity-catalog
AUDIT=http://127.0.0.1:8000/audit-log
H="content-type:application/json"
```

## 1. Create a catalog attributed to Alice

The proxy in front of soyuz normally attaches `X-Principal`; here we
forge it on the client side to drive the audit-log behaviour
end-to-end.

**Action**

```bash
curl -sX POST "$BASE/catalogs" -H $H \
     -H "X-Principal: alice@example.com" \
     -d '{"name":"audit_demo"}' > /dev/null
```

**Expect**

`200 OK`. soyuz stored the catalog and wrote one audit row with
`principal=alice@example.com`.

## 2. Create a schema attributed to an agent run

This is the cross-index the audit log was designed for: the agent
forwards the same `X-Agent-Run-Id` on every mutation it makes during
a run so the run's UC effects can be listed in one query.

**Action**

```bash
curl -sX POST "$BASE/schemas" -H $H \
     -H "X-Principal: agent-runner@example.com" \
     -H "X-Agent-Run-Id: run-2026-001" \
     -d '{"name":"raw","catalog_name":"audit_demo"}' > /dev/null
```

**Expect**

`200 OK`. The audit row carries both `principal` and
`agent_run_id="run-2026-001"`.

## 3. Tag the catalog attributed to a third principal

Tag PATCHes are mutation routes — they land in the audit log.

**Action**

```bash
curl -sX PATCH "http://127.0.0.1:8000/tags/catalog/audit_demo" -H $H \
     -H "X-Principal: bob@example.com" \
     -d '{"changes":[{"op":"set","key":"owner","value":"data-team"}]}' > /dev/null
```

**Expect**

`200 OK`. A third audit row exists, this one with
`action="tag.updated"` and `target="catalog:audit_demo"`.

## 4. Read the full audit log (operator view)

Without a filter the endpoint returns rows newest-first up to
`limit` (default 200, max 1000).

**Action**

```bash
curl -s "$AUDIT?limit=10" \
  | jq '[.[] | {action, target, principal, agent_run_id}]'
```

**Expect**

The three rows above, newest first:

```json
[
  {"action": "tag.updated",        "target": "catalog:audit_demo", "principal": "bob@example.com",         "agent_run_id": null},
  {"action": "schemas.create_schema","target": "audit_demo.raw",   "principal": "agent-runner@example.com","agent_run_id": "run-2026-001"},
  {"action": "catalogs.create_catalog","target": "audit_demo",     "principal": "alice@example.com",       "agent_run_id": null}
]
```

(Action names match what the routes pass to `log_action`; exact
spellings can shift if a route renames its handler — the values
above are what HEAD emits today.)

## 5. Filter by `agent_run_id` (per-run view)

This is the query that answers *"what did `run-2026-001` do?"*.
Order flips to oldest-first within the run so the sequence of
mutations reads top-to-bottom in time order.

**Action**

```bash
curl -s "$AUDIT?agent_run_id=run-2026-001" \
  | jq '[.[] | {action, target, created_at}]'
```

**Expect**

Exactly one row — the schema creation. The catalog create (Alice)
and the tag PATCH (Bob) were not attributed to this run and are
filtered out.

## 6. A mutation without `X-Principal`

The proxy may have a misconfiguration that drops the header. soyuz
still services the request and still writes an audit row; the
`principal` field is just `null`.

**Action**

```bash
curl -sX PATCH "http://127.0.0.1:8000/tags/catalog/audit_demo" -H $H \
     -d '{"changes":[{"op":"set","key":"sla","value":"tier-2"}]}' > /dev/null
curl -s "$AUDIT?limit=1" \
  | jq '.[0] | {action, target, principal, client_ip}'
```

**Expect**

```json
{"action": "tag.updated", "target": "catalog:audit_demo", "principal": null, "client_ip": "127.0.0.1"}
```

A `null` principal is signal: either the proxy isn't attaching the
header, or the request hit soyuz directly. `client_ip` still
identifies the connection.

## 7. Clean up

```bash
curl -sX DELETE "$BASE/schemas/audit_demo.raw?force=true" \
     -H "X-Principal: cleanup-bot" > /dev/null
curl -sX DELETE "$BASE/catalogs/audit_demo" \
     -H "X-Principal: cleanup-bot" > /dev/null
```

The deletes themselves land in the audit log under
`schemas.delete_schema` / `catalogs.delete_catalog` — handy when
diagnosing "where did this catalog go?" later.

## What you did *not* do

You did not authenticate against soyuz. The `X-Principal` /
`X-Agent-Run-Id` headers are *forwarded identity* — in a real
deployment a front proxy authenticates the caller (OIDC, OAuth,
mTLS, …) and attaches verified headers. soyuz trusts the proxy and
writes whatever it forwards. That is the proxy-offload model;
see [Permissions model § Why no enforcement](../../concepts/permissions-model.md#why-no-enforcement).

## See also

- [Concepts → Audit log](../../concepts/audit-log.md) — what gets
  written, what does not, and where the audit log stops being
  enough.
- [Admin → Observability and audit log](../../admin/observability.md)
  — operator-side view: where audit lines join the request log,
  what to watch.
- [Concepts → Permissions model](../../concepts/permissions-model.md)
  — why identity comes from the proxy.
- [Divergences → Audit log](../../divergences.md) — wire-level
  definition and the explicit conformance-test skip.
