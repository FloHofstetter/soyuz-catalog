# First catalog

A guided end-to-end tour that builds a small but realistic hierarchy: a
catalog containing a schema containing a table containing typed columns.
Every step is a single curl. The whole sequence runs in under a minute
against a fresh server.

If you have not started a server yet, see
[Quickstart](quickstart.md) first.

```bash
BASE=http://127.0.0.1:8000/api/2.1/unity-catalog
H="content-type:application/json"
```

## 1. Create a catalog

```bash
curl -sX POST "$BASE/catalogs" -H $H \
     -d '{"name":"sales","comment":"sales-domain data"}'
```

Expect `200 OK` with a JSON body containing `"name":"sales"`, a UUID
`id`, and `created_at` / `updated_at` timestamps.

## 2. Create a schema

```bash
curl -sX POST "$BASE/schemas" -H $H \
     -d '{"name":"fact","catalog_name":"sales","comment":"fact tables"}'
```

Expect `200 OK` with `"full_name":"sales.fact"`.

## 3. Create a table

```bash
curl -sX POST "$BASE/tables" -H $H -d '{
  "name": "orders",
  "catalog_name": "sales",
  "schema_name": "fact",
  "table_type": "MANAGED",
  "data_source_format": "DELTA",
  "storage_location": "file:///tmp/sales/fact/orders",
  "columns": [
    {"name":"id","type_text":"long","type_json":"{}","type_name":"LONG","position":0},
    {"name":"customer_id","type_text":"long","type_json":"{}","type_name":"LONG","position":1},
    {"name":"total_cents","type_text":"int","type_json":"{}","type_name":"INT","position":2}
  ]
}'
```

Expect `200 OK` with `"full_name":"sales.fact.orders"` and the three
column entries echoed in the response.

## 4. Read it back

```bash
curl -s "$BASE/tables/sales.fact.orders"
```

Expect the same structure you wrote, now with the server-assigned `id`,
`created_at`, and `updated_at` fields populated.

## 5. List everything

```bash
curl -s "$BASE/catalogs"
curl -s "$BASE/schemas?catalog_name=sales"
curl -s "$BASE/tables?catalog_name=sales&schema_name=fact"
```

Each call returns a list shape with `catalogs` / `schemas` / `tables` and
a `next_page_token` (null for short lists). See
[ADR-0003](../adr/0003-keyset-pagination.md) for how pagination works
when lists grow large.

## 6. Attach a tag (over-the-spec extension)

Tags live outside the UC spec but are a first-class soyuz feature:

```bash
curl -sX PATCH "$BASE/../../tags/table/sales.fact.orders" -H $H \
     -d '{"changes":[{"op":"set","key":"layer","value":"bronze"}]}'
```

Note that `/tags` is mounted at the API root, not under
`/api/2.1/unity-catalog`. See [Concepts → Securables and naming](../concepts/securables-and-naming.md)
for how the four-part column route works as well.

## 7. Clean up

```bash
curl -sX DELETE "$BASE/tables/sales.fact.orders"
curl -sX DELETE "$BASE/schemas/sales.fact"
curl -sX DELETE "$BASE/catalogs/sales"
```

Deletes are not cascading by default. Dropping a non-empty schema or
catalog returns `400 BAD_REQUEST` unless you pass `?force=true`. See
[Concepts → Securables and naming](../concepts/securables-and-naming.md)
for the rationale.

## What you just exercised

| Step | What it shows |
|---|---|
| 1–3 | Three-level hierarchy creation |
| 4   | Read-by-full_name |
| 5   | List with the keyset-pagination wrapper |
| 6   | Over-the-spec tag extension |
| 7   | Cascade gate on delete |

## Where to go next

- [HTTP walkthroughs](../guides/walkthroughs/catalog-schema-table.md) —
  more deterministic sequences, including lineage, grants, and Delta
  commits.
- [Concepts → Architecture](../concepts/architecture.md) — what happens
  inside soyuz when one of these calls lands.
- [REST API reference](../reference/api.md) — exhaustive endpoint list.
- [Integrations](../integrations/index.md) — using soyuz from Spark,
  delta-rs, MLflow, or the Python SDK.
