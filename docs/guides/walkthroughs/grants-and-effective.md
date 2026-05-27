# Walkthrough — Grants and effective permissions

> **Goal:** grant a privilege on a catalog and observe it inherit down
> to a table.
>
> **Surface:** `/api/2.1/unity-catalog/permissions/<type>/<full_name>`
> and `/api/2.1/unity-catalog/effective-permissions/<type>/<full_name>`.
>
> **Prereqs:** soyuz running on `:8000`.

```bash
BASE=http://127.0.0.1:8000/api/2.1/unity-catalog
H="content-type:application/json"
```

## 1. Seed a hierarchy

**Action**

```bash
curl -sX POST "$BASE/catalogs" -H $H -d '{"name":"sales"}' > /dev/null
curl -sX POST "$BASE/schemas"  -H $H -d '{"name":"fact","catalog_name":"sales"}' > /dev/null
curl -sX POST "$BASE/tables"   -H $H -d '{
  "name":"orders","catalog_name":"sales","schema_name":"fact",
  "table_type":"MANAGED","data_source_format":"DELTA",
  "storage_location":"file:///tmp/sales/fact/orders",
  "columns":[{"name":"id","type_text":"long","type_json":"{}","type_name":"LONG","position":0}]
}' > /dev/null
```

**Expect**

No output.

## 2. Read empty permissions

**Action**

```bash
curl -s "$BASE/permissions/catalog/sales"
```

**Expect**

```json
{"privilege_assignments":[]}
```

## 3. Grant `SELECT` on the catalog to `alice@example.com`

**Action**

```bash
curl -sX PATCH "$BASE/permissions/catalog/sales" -H $H -d '{
  "changes": [
    {"principal":"alice@example.com","add":["SELECT"]}
  ]
}'
```

**Expect**

`200 OK`. Response lists alice with `["SELECT"]`.

## 4. Direct permissions on the catalog show the grant

**Action**

```bash
curl -s "$BASE/permissions/catalog/sales" | jq
```

**Expect**

```json
{
  "privilege_assignments":[
    {"principal":"alice@example.com","privileges":["SELECT"]}
  ]
}
```

## 5. Direct permissions on the table are still empty

**Action**

```bash
curl -s "$BASE/permissions/table/sales.fact.orders" | jq
```

**Expect**

```json
{"privilege_assignments":[]}
```

The direct grant is on the catalog, not the table.

## 6. *Effective* permissions on the table show the inherited grant

**Action**

```bash
curl -s "$BASE/effective-permissions/table/sales.fact.orders" | jq
```

**Expect**

```json
{
  "privilege_assignments":[
    {
      "principal":"alice@example.com",
      "privileges":[
        {"privilege":"SELECT","inherited_from_type":"catalog","inherited_from_name":"sales"}
      ]
    }
  ]
}
```

`inherited_from_*` identifies the ancestor the grant came from. A
direct grant would have those fields null.

## 7. Add a direct grant at the schema level — both show up

**Action**

```bash
curl -sX PATCH "$BASE/permissions/schema/sales.fact" -H $H -d '{
  "changes":[{"principal":"alice@example.com","add":["MODIFY"]}]
}' > /dev/null
curl -s "$BASE/effective-permissions/table/sales.fact.orders" \
   | jq '.privilege_assignments[0].privileges'
```

**Expect**

```json
[
  {"privilege":"SELECT","inherited_from_type":"catalog","inherited_from_name":"sales"},
  {"privilege":"MODIFY","inherited_from_type":"schema","inherited_from_name":"sales.fact"}
]
```

Both grants are visible at the table level, each tagged with its origin.

## 8. Revoke the catalog grant — `SELECT` disappears immediately

**Action**

```bash
curl -sX PATCH "$BASE/permissions/catalog/sales" -H $H -d '{
  "changes":[{"principal":"alice@example.com","remove":["SELECT"]}]
}' > /dev/null
curl -s "$BASE/effective-permissions/table/sales.fact.orders" \
   | jq '.privilege_assignments[0].privileges'
```

**Expect**

```json
[{"privilege":"MODIFY","inherited_from_type":"schema","inherited_from_name":"sales.fact"}]
```

No caching layer between the revoke and the effective query. The next
call sees the new state.

## 9. Clean up

```bash
curl -sX DELETE "$BASE/tables/sales.fact.orders"       > /dev/null
curl -sX DELETE "$BASE/schemas/sales.fact?force=true"  > /dev/null
curl -sX DELETE "$BASE/catalogs/sales"                  > /dev/null
```

## A note on enforcement

soyuz **stored** the grant and **computed** the inheritance. soyuz did
*not* refuse any request based on the grant — there is no enforcement
layer. The expected deployment is: auth proxy authenticates the request,
calls soyuz's effective endpoint to decide whether to proxy the call,
forwards or rejects.

See [Concepts → Permissions model](../../concepts/permissions-model.md)
and [ADR-0005](../../adr/0005-permissions-without-enforcement.md).

## See also

- [Concepts → Permissions model](../../concepts/permissions-model.md)
- [REST API reference](../../reference/api.md)
- [Observability and audit log](../../admin/observability.md) — the
  audit log records the principal header for traceability.
