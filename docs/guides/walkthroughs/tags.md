# Walkthrough — Attaching tags

> **Goal:** attach tags to a catalog, schema, table, and column. Verify
> the additive PATCH shape and the rename invariance.
>
> **Surface:** `/tags/<type>/<full_name>` (root-mounted, not under
> `/api/2.1/unity-catalog`).
>
> **Prereqs:** soyuz running on `:8000`. Run
> [Catalog → Schema → Table](catalog-schema-table.md) steps 1–3 first,
> or use this one-shot seed:

```bash
BASE=http://127.0.0.1:8000/api/2.1/unity-catalog
TAGS=http://127.0.0.1:8000/tags
H="content-type:application/json"

curl -sX POST "$BASE/catalogs" -H $H -d '{"name":"sales"}' > /dev/null
curl -sX POST "$BASE/schemas"  -H $H -d '{"name":"fact","catalog_name":"sales"}' > /dev/null
curl -sX POST "$BASE/tables"   -H $H -d '{
  "name":"orders","catalog_name":"sales","schema_name":"fact",
  "table_type":"MANAGED","data_source_format":"DELTA",
  "storage_location":"file:///tmp/sales/fact/orders",
  "columns":[
    {"name":"id","type_text":"long","type_json":"{}","type_name":"LONG","position":0},
    {"name":"email","type_text":"string","type_json":"{}","type_name":"STRING","position":1}
  ]
}' > /dev/null
```

## 1. Tag the catalog

**Action**

```bash
curl -sX PATCH "$TAGS/catalog/sales" -H $H \
     -d '{"changes":[{"op":"set","key":"owner","value":"data-team"}]}'
```

**Expect**

`200 OK`.

```json
{"tags":[{"key":"owner","value":"data-team","created_at":..., "updated_at":...}]}
```

## 2. GET mirrors the PATCH response

**Action**

```bash
curl -s "$TAGS/catalog/sales"
```

**Expect**

Identical body to step 1's response.

## 3. Tag the table with two keys, one without a value

**Action**

```bash
curl -sX PATCH "$TAGS/table/sales.fact.orders" -H $H -d '{
  "changes": [
    {"op":"set","key":"layer","value":"bronze"},
    {"op":"set","key":"pii"}
  ]
}'
```

**Expect**

`200 OK`. Tags are returned sorted by key:

```json
{"tags":[
  {"key":"layer","value":"bronze",...},
  {"key":"pii","value":null,...}
]}
```

A tag without a value is meaningful — `pii` here is a presence marker,
common in governance use cases.

## 4. Tag a column (four-part name)

**Action**

```bash
curl -sX PATCH "$TAGS/column/sales.fact.orders.email" -H $H \
     -d '{"changes":[{"op":"set","key":"mask","value":"sha256"}]}'
```

**Expect**

`200 OK`. The four-part path is only valid for `column`.

## 5. Mix set and remove in one batch

**Action**

```bash
curl -sX PATCH "$TAGS/table/sales.fact.orders" -H $H -d '{
  "changes": [
    {"op":"remove","key":"pii"},
    {"op":"set","key":"sla","value":"tier-1"}
  ]
}'
curl -s "$TAGS/table/sales.fact.orders" | jq '.tags[] | .key'
```

**Expect**

`"layer"`, `"sla"`. `pii` is gone; `sla` was added in the same batch.

## 6. `set` wins over `remove` in the same batch

If you `remove` and `set` the same key in one PATCH, `set` wins. This is
the documented tiebreaker.

**Action**

```bash
curl -sX PATCH "$TAGS/table/sales.fact.orders" -H $H -d '{
  "changes": [
    {"op":"remove","key":"layer"},
    {"op":"set","key":"layer","value":"silver"}
  ]
}'
```

**Expect**

`layer` is still present, with value `silver`.

## 7. Rename the catalog — tags survive

**Action**

```bash
curl -sX PATCH "$BASE/catalogs/sales" -H $H -d '{"new_name":"sales_v2"}'
curl -s "$TAGS/table/sales_v2.fact.orders" | jq '.tags[].key'
```

**Expect**

`"layer"`, `"sla"`. The tag is still attached because it lives on the
table's opaque UUID, not its full name.

## 8. Drop the table — orphan rows are unreachable

**Action**

```bash
curl -sX DELETE "$BASE/tables/sales_v2.fact.orders"
curl -s "$TAGS/table/sales_v2.fact.orders"
```

**Expect**

The DELETE returns `200`. The subsequent GET returns `404` — the
underlying tag rows are still in the database, but they are no longer
reachable through the API. This is the append-only delete posture; see
[Concepts → Securables and naming](../../concepts/securables-and-naming.md).

## Clean up

```bash
curl -sX DELETE "$BASE/schemas/sales_v2.fact?force=true" > /dev/null
curl -sX DELETE "$BASE/catalogs/sales_v2"                > /dev/null
```

## See also

- [Concepts → Securables and naming](../../concepts/securables-and-naming.md)
  — why tags survive renames.
- [Concepts → Extensions over the spec](../../concepts/extensions-over-spec.md)
  — where tags fit in the broader extension picture.
- [ADR-0010](../../adr/0010-tags-as-extension.md) — the design decision.
