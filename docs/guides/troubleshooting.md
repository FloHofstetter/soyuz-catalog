# Troubleshooting and FAQ

Common failure modes seen against soyuz-catalog, with the symptom, the
cause, and the fix. Skim this page when something does not work; most
issues here resolve in under a minute.

## `422 Unprocessable Entity` on a `POST` that looks correct

**Symptom**

```json
{
  "error_code": "INVALID_PARAMETER_VALUE",
  "message": "Extra inputs are not permitted",
  "details": [{"loc": ["body", "propeerties"]}]
}
```

**Cause**

The request body has an unknown field. soyuz sets `extra="forbid"` on
every request model and refuses to silently drop fields — most often
this is a typo (`propeerties` vs `properties`), but it also catches
clients trying to send fields that exist in Databricks UC but not in the
open spec.

**Fix**

Check `loc` for the offending field name. Fix the typo or remove the
unsupported field. If the field is one you expect soyuz to accept and it
is in `unitycatalog/api/all.yaml`, file a bug — that is a spec-coverage
gap.

This behaviour is one of the deliberate divergences from UC OSS Java
(which silently drops unknown fields); see
[Spec is the contract](../concepts/spec-is-the-contract.md).

## `PATCH` with `{"properties": {}}` cleared all properties

**Symptom**

You sent `PATCH /catalogs/foo` with `{"properties": {}}` expecting a
no-op and the catalog's properties are now empty.

**Cause**

soyuz implements replace-style PATCH semantics: any field present in the
body is written, including the empty map. Fields absent from the body
are untouched.

**Fix**

If you wanted a no-op, omit the `properties` field entirely. If you
wanted to clear properties, congratulations — that worked.

UC OSS Java treats `properties={}` as a no-op (a documented divergence;
see [DIVERGENCES.md](../divergences.md)). Clients moving from UC OSS to
soyuz need to audit their PATCH calls for this assumption.

## `400 BAD_REQUEST` on `DELETE` of a non-empty catalog or schema

**Symptom**

```json
{
  "error_code": "INVALID_STATE",
  "message": "Cannot delete non-empty schema 'sales.fact'; pass force=true to cascade"
}
```

**Cause**

soyuz's cascade gate refuses to delete a parent that still has
children, on the principle that cascading delete should be an explicit
choice.

**Fix**

Add `?force=true` to the delete URL, or delete the children first.

## `409 Conflict` on `POST /tables`

**Symptom**

A `POST /tables` returns `409` when you try to create a table.

**Cause**

A table with the same `(catalog, schema, name)` already exists. soyuz
treats names as unique within a schema.

**Fix**

Either use a different name, or `DELETE` the existing table first. If
you intended to update — there is no `PATCH` on tables (the spec
defines none). Drop and recreate is the spec-conformant pattern.

## Pagination cursor returns `400 INVALID_PARAMETER_VALUE`

**Symptom**

You retried a paginated list with the previous response's
`next_page_token` and got `400`.

**Cause**

Keyset cursors encode the sort key of the last item returned. If items
were deleted between calls, the cursor may point at a tombstoned row.
soyuz returns `400` rather than silently skipping.

**Fix**

Restart from the beginning of the list (omit the token). For most use
cases this is acceptable; for cases where stable enumeration matters,
use `max_results=1000` and a single call when the total is small.

The decision to use keyset over offset is
[ADR-0003](../adr/0003-keyset-pagination.md). Offset would have the same
class of bug (skipping items when reads race writes), worse: silent
data loss rather than a clear `400`.

## `max_results=0` returns 100 results, not 0

**Symptom**

```bash
curl "$BASE/catalogs?max_results=0"
# returns up to 100 catalogs
```

**Cause**

The spec's pagination convention treats `0` as "use server default".
The JVM `unitycatalog-spark` connector sends `max_results=0` for
`SHOW CATALOGS`; rejecting it would break Spark catalog discovery.

**Fix**

This is correct behaviour, not a bug. If you genuinely want zero
results, you do not need to make the call.

## Tag survives table rename but disappears when the table is deleted

**Symptom**

Renaming `sales.fact.orders` to `sales.fact.orders_v2` keeps the
`layer=bronze` tag attached. Force-deleting the table then makes the
tag unreachable.

**Cause**

This is the [append-only delete posture](../concepts/securables-and-naming.md).
Tags are anchored on the table's opaque UUID, not its name — so renames
preserve them, but the parent table being gone makes the tag
unreachable through the API.

**Fix**

The orphan row remains in the database (`tags` table) but no
`GET /tags/...` request can reach it. If you need to clean up, query
the database directly. If you are surprised by this, you probably want
to consider whether the delete should have happened.

## `mkdocs build --strict` fails with broken links

**Symptom**

Building the docs site fails on a broken cross-reference between Markdown
files.

**Cause**

A page is referenced but does not exist (typo in the path) or the file
was moved without updating callers.

**Fix**

The error message names the source page and the bad target. Fix the
link. The strict build is the gate that keeps the docs honest;
disabling it would let drift accumulate.

## OpenAPI document at `/openapi.json` returns 404

**Symptom**

`curl http://localhost:8000/openapi.json` returns `404`.

**Cause**

You set `SOYUZ_OPENAPI_ENABLED=0`. This also disables `/docs`.

**Fix**

Re-enable for development with `unset SOYUZ_OPENAPI_ENABLED` or set to
`1`. In production some operators prefer the route off — see
[Settings reference](../reference/settings.md) for the rationale.

## See also

- [Divergences](../divergences.md) — every deliberate behaviour
  difference, with rationale.
- [Spec is the contract](../concepts/spec-is-the-contract.md) — why
  soyuz refuses to silently drop fields.
- [Configuration](../admin/configuration.md) — environment variables
  and what they do.
- [Observability and audit log](../admin/observability.md) — request log
  and audit trail for forensics.
