# Walkthrough — Catalog → Schema → Table

> **Goal:** build a three-level securable hierarchy, read it back, then
> tear it down. Verify the rename invariants and the cascade gate along
> the way.
>
> **Surface:** `/api/2.1/unity-catalog/{catalogs,schemas,tables}`
>
> **Prereqs:** soyuz running on `:8000` against an empty database. If
> not, see [Quickstart](../../getting-started/quickstart.md).

```bash
BASE=http://127.0.0.1:8000/api/2.1/unity-catalog
H="content-type:application/json"
```

## 1. Create a catalog

**Action**

```bash
curl -sX POST "$BASE/catalogs" -H $H -d '{"name":"sales"}'
```

**Expect**

`200 OK`. Response body has `"name":"sales"`, a UUID `id`, `created_at`,
`updated_at`. `properties` is absent (omitted when empty by
`response_model_exclude_none`).

## 2. Create a schema

**Action**

```bash
curl -sX POST "$BASE/schemas" -H $H \
     -d '{"name":"fact","catalog_name":"sales"}'
```

**Expect**

`200 OK`. `"full_name":"sales.fact"`.

## 3. Create a table

**Action**

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
    {"name":"customer_id","type_text":"long","type_json":"{}","type_name":"LONG","position":1}
  ]
}'
```

**Expect**

`200 OK`. `"full_name":"sales.fact.orders"` and a `columns` array with
your two entries plus server-assigned column IDs.

## 4. Read it back by full name

**Action**

```bash
curl -s "$BASE/tables/sales.fact.orders" | jq -r '.full_name'
```

**Expect**

`sales.fact.orders`.

## 5. List with pagination

**Action**

```bash
curl -s "$BASE/tables?catalog_name=sales&schema_name=fact" \
   | jq '{tables: [.tables[].name], next_page_token}'
```

**Expect**

```json
{"tables":["orders"], "next_page_token":null}
```

`next_page_token` is null because the list fits in one page. With more
items the cursor would carry the keyset position; see
[ADR-0003](../../adr/0003-keyset-pagination.md).

## 6. Rename the catalog

**Action**

```bash
curl -sX PATCH "$BASE/catalogs/sales" -H $H \
     -d '{"new_name":"sales_v2"}'
```

**Expect**

`200 OK`. The response now has `"name":"sales_v2"`. The `id` is
unchanged.

## 7. The full table name moved with it

**Action**

```bash
curl -s "$BASE/tables/sales_v2.fact.orders" | jq -r '.full_name'
```

**Expect**

`sales_v2.fact.orders`. The table itself was not renamed, only its
parent catalog — but because `full_name` is computed from the chain of
names, the table is now addressed under the new catalog name. Its `id`
is unchanged.

This is the rename-invariance discussed in
[Concepts → Securables and naming](../../concepts/securables-and-naming.md).

## 8. Try to drop a non-empty schema (cascade gate)

**Action**

```bash
curl -sX DELETE "$BASE/schemas/sales_v2.fact"
```

**Expect**

`400 BAD_REQUEST` with an `INVALID_STATE` error code. The schema still
contains the table.

## 9. Drop with force

**Action**

```bash
curl -sX DELETE "$BASE/schemas/sales_v2.fact?force=true"
```

**Expect**

`200 OK`. Schema and table both gone.

## 10. Drop the empty catalog

**Action**

```bash
curl -sX DELETE "$BASE/catalogs/sales_v2"
```

**Expect**

`200 OK`. Catalog gone. The database is back to empty.

## What this walkthrough exercised

| Step | Concept |
|---|---|
| 1–3 | Hierarchy creation |
| 4   | Lookup by `full_name` |
| 5   | Keyset list shape |
| 6–7 | Rename invariance |
| 8–9 | Cascade gate + `force=true` |
| 10  | Plain delete |

## See also

- [Concepts → Securables and naming](../../concepts/securables-and-naming.md)
- [REST API reference](../../reference/api.md)
- [Walkthrough: tags](tags.md) — the next thing to try.
