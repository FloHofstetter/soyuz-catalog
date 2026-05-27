# Observability and audit log

soyuz-catalog emits three kinds of operational signal: request logs from
uvicorn, application logs from the Python logger, and a structured audit
log persisted to the database. This page covers what each contains, what
metrics are worth watching, and how the audit log is queried.

## Process logs

uvicorn writes one line per request to stdout. With
`SOYUZ_STRUCTURED_LOGGING=1`, the same lines come out as JSON:

```json
{"timestamp": "...", "level": "INFO", "request_id": "...",
 "method": "POST", "path": "/api/2.1/unity-catalog/catalogs",
 "status_code": 200, "duration_ms": 12.3}
```

soyuz's `RequestIDMiddleware` attaches a `request_id` and reads
`X-Principal` + `X-Agent-Run-Id` from the request headers — visible in
the log line and forwarded into the audit log entries written during the
same request.

Application-level logs (configuration warnings, startup migrations, SoyuzError
context) come through the same stream at INFO or higher. Switch to
DEBUG when investigating SQL behaviour — SQLAlchemy then logs every
statement.

## Audit log

Mutation routes call `services/audit_service.log_action()` after a
successful change. The write is best-effort — an audit-write failure is
logged but does not roll back the underlying mutation. The audit row
records:

| Field | Source |
|---|---|
| `action` | The route handler (e.g. `tables.create_table`) |
| `target` | The securable being mutated (e.g. `sales.fact.orders`) |
| `principal` | `X-Principal` request header |
| `agent_run_id` | `X-Agent-Run-Id` request header |
| `client_ip` | Connection-level (or `X-Forwarded-For` first hop) |
| `detail` | Structured per-action payload |
| `created_at` | Server time at write |

### Read the audit log

```bash
curl "http://127.0.0.1:8000/audit-log?limit=20" | jq
```

Filter by run:

```bash
curl "http://127.0.0.1:8000/audit-log?agent_run_id=<uuid>&limit=200" | jq
```

`limit` is bounded `[1, 1000]`, default `200`.

### Coverage and limits

What is and isn't audited (mutation-only, best-effort, no read
tracing), the proxy-offload identity model, and the cases where the
log alone is not enough — those live on
[Concepts → Audit log](../concepts/audit-log.md). This page covers the
operator-facing pieces only: where audit rows sit in the operational
stack, how to query them, and what to do when something looks wrong.

## Metrics worth watching

soyuz does not export Prometheus metrics directly — the deployment is
small enough that the request log carries enough signal. If you want
metrics, the right pattern is a sidecar that reads structured logs and
emits counters.

The numbers worth tracking:

- **Request rate** — total requests/minute, by method/route.
- **p99 latency** — the long tail on `POST /tables`, `PATCH /tags/...`,
  `POST /lineage/v1/events` is where Postgres tuning shows up.
- **Error rate** — 4xx by route and 5xx anywhere. A spike in 422 from
  one client is usually a schema-validation regression in that client.
- **Database connection pool exhaustion** — visible in SQLAlchemy logs
  as `TimeoutError`. If you see it, raise the pool or the worker count.
- **Audit-write failures** — these appear as warnings in the application
  log with the original action context. Persistent failures point at a
  storage problem.

## Distributed traces

If you front soyuz with a tracing-aware proxy (Envoy, Linkerd) the
`request_id` header from `RequestIDMiddleware` is propagated and can be
used to join soyuz logs to upstream/downstream service traces. soyuz does
not natively export OpenTelemetry today — adding it is a one-router
change to wire the SDK if needed.

## Forensics walkthrough

Suppose someone reports that `sales.fact.orders` had its `pii` tag
removed unexpectedly. Trace:

```bash
# Find the audit entry for the tag removal
curl "http://127.0.0.1:8000/audit-log?limit=1000" \
   | jq '.entries[] | select(.action=="tags.update_tags" and .target=="sales.fact.orders")'
```

Each match shows the principal, the agent run id (if the caller passed
one), the client IP, and the detail payload — typically the list of
key/value changes in that batch.

If the principal header is empty, the proxy upstream of soyuz did not
attach one. Auth-layer logs are the next stop; from soyuz's side the
audit entry is as much as the system knows.

## See also

- [Concepts → Audit log](../concepts/audit-log.md) — what gets
  written, why, and where the log stops being enough.
- [Walkthrough: querying the audit log](../guides/walkthroughs/audit-log.md)
  — drive the principal / agent-run-id flow end-to-end.
- [Concepts → Permissions model](../concepts/permissions-model.md) — why
  identity comes from the proxy.
- [Divergences → Audit log](../divergences.md) — the formal entry.
- [Deployment](deployment.md) — proxy headers for principal capture.
