# Walkthrough — Declared table constraints

> **Goal:** declare a primary key, a foreign key, and a named `NOT NULL`
> on tables through the Delta REST surface, then read them back from
> the UC REST `GET /tables` response. Confirm the main UC `POST
> /tables` rejects constraint fields so the spec-surface invariant
> stays intact.
>
> **Surface:** `POST /api/2.1/unity-catalog/delta/v1/catalogs/{c}/schemas/{s}/tables/{t}`
> for mutations, `GET /api/2.1/unity-catalog/tables/{full_name}` for reads.
>
> **Prereqs:** soyuz running on `:8000`.

```bash
BASE=http://127.0.0.1:8000/api/2.1/unity-catalog
DELTA=$BASE/delta/v1
H="content-type:application/json"
```

## 1. Seed a catalog, schema, and two tables

The parent table for the foreign key is needed before the FK can be
declared, so set both tables up first.

**Action**

```bash
curl -sX POST "$BASE/catalogs" -H $H -d '{"name":"sales"}' > /dev/null
curl -sX POST "$BASE/schemas"  -H $H -d '{"name":"fact","catalog_name":"sales"}' > /dev/null

curl -sX POST "$BASE/tables" -H $H -d '{
  "name":"customers","catalog_name":"sales","schema_name":"fact",
  "table_type":"MANAGED","data_source_format":"DELTA",
  "storage_location":"file:///tmp/sales/fact/customers",
  "columns":[
    {"name":"customer_id","type_text":"long","type_json":"{}","type_name":"LONG","position":0},
    {"name":"email",      "type_text":"string","type_json":"{}","type_name":"STRING","position":1}
  ]
}' > /dev/null

curl -sX POST "$BASE/tables" -H $H -d '{
  "name":"orders","catalog_name":"sales","schema_name":"fact",
  "table_type":"MANAGED","data_source_format":"DELTA",
  "storage_location":"file:///tmp/sales/fact/orders",
  "columns":[
    {"name":"order_id",   "type_text":"long","type_json":"{}","type_name":"LONG","position":0},
    {"name":"customer_id","type_text":"long","type_json":"{}","type_name":"LONG","position":1},
    {"name":"amount",     "type_text":"double","type_json":"{}","type_name":"DOUBLE","position":2}
  ]
}' > /dev/null
```

**Expect**

All three calls return `200 OK`. The `customers` table will be the FK
parent.

## 2. Declare a primary key on `customers`

Constraints mutate via the Delta REST `UpdateTable` action union,
not via UC REST `POST /tables`.

**Action**

```bash
curl -sX POST "$DELTA/catalogs/sales/schemas/fact/tables/customers" -H $H -d '{
  "updates": [{
    "action": "add-constraint",
    "constraint": {
      "name": "customers_pk",
      "primary_key_constraint": {"child_columns": ["customer_id"]}
    }
  }]
}' > /dev/null
```

**Expect**

`200 OK`. The body comes back as a Delta `LoadTableResponse`; verify
the declaration via the UC REST read in the next step.

## 3. Read the constraint back via UC REST

**Action**

```bash
curl -s "$BASE/tables/sales.fact.customers" \
  | jq '.table_constraints'
```

**Expect**

```json
[
  {
    "name": "customers_pk",
    "primary_key_constraint": {"child_columns": ["customer_id"]}
  }
]
```

A primary-key constraint is rendered with `primary_key_constraint`
populated and the other three per-type fields absent.

## 4. Declare a foreign key on `orders` referencing `customers`

**Action**

```bash
curl -sX POST "$DELTA/catalogs/sales/schemas/fact/tables/orders" -H $H -d '{
  "updates": [{
    "action": "add-constraint",
    "constraint": {
      "name": "orders_customer_fk",
      "foreign_key_constraint": {
        "child_columns": ["customer_id"],
        "parent_table": "sales.fact.customers",
        "parent_columns": ["customer_id"]
      }
    }
  }]
}' > /dev/null
```

**Expect**

`200 OK`. The service resolves `parent_table` to the opaque
`Table.id` of `customers` and stores that — so the FK survives a
rename of either table.

## 5. Declare a named `NOT NULL` on `orders.amount`

**Action**

```bash
curl -sX POST "$DELTA/catalogs/sales/schemas/fact/tables/orders" -H $H -d '{
  "updates": [{
    "action": "add-constraint",
    "constraint": {
      "name": "amount_required",
      "named_table_constraint": {"child_column": "amount"}
    }
  }]
}' > /dev/null
```

**Expect**

`200 OK`. The named constraint is a *second* row alongside the
column's own `nullable` flag — it does not flip
`columns[*].nullable`. Verify:

```bash
curl -s "$BASE/tables/sales.fact.orders" \
  | jq '{constraints: .table_constraints, amount_nullable: .columns[2].nullable}'
```

```json
{
  "constraints": [
    {"name": "orders_customer_fk", "foreign_key_constraint": {...}},
    {"name": "amount_required",    "named_table_constraint": {"child_column": "amount"}}
  ],
  "amount_nullable": true
}
```

`amount_nullable` is still `true` even with a `NOT NULL` declaration —
the two concepts are orthogonal. See
[Concepts → Table constraints § Named `NOT NULL` vs `Column.nullable`](../../concepts/table-constraints.md).

## 6. UC REST `POST /tables` rejects constraint fields

The main UC surface has no `PATCH /tables` (`405 Method Not Allowed`)
and `POST /tables` does not accept `table_constraints`. Try sending
one anyway.

**Action**

```bash
curl -isX POST "$BASE/tables" -H $H -d '{
  "name":"bad","catalog_name":"sales","schema_name":"fact",
  "table_type":"MANAGED","data_source_format":"DELTA",
  "storage_location":"file:///tmp/sales/fact/bad",
  "columns":[
    {"name":"k","type_text":"long","type_json":"{}","type_name":"LONG","position":0}
  ],
  "table_constraints": [{
    "name":"bad_pk","primary_key_constraint":{"child_columns":["k"]}
  }]
}' | head -1
```

**Expect**

`HTTP/1.1 422 Unprocessable Entity`. The `CreateTable` body sets
`extra="forbid"`, so an unknown field on the spec surface is rejected
loudly rather than silently dropped.

## 7. Drop the FK on `orders` idempotently

**Action**

```bash
curl -sX POST "$DELTA/catalogs/sales/schemas/fact/tables/orders" -H $H -d '{
  "updates": [
    {"action": "drop-constraint", "name": "orders_customer_fk"},
    {"action": "drop-constraint", "name": "orders_customer_fk", "if_exists": true}
  ]
}' > /dev/null
```

**Expect**

`200 OK`. The first drop removes the FK; the second is a no-op
because `if_exists` is true. Without `if_exists`, the second call
would be `404 NOT_FOUND`.

## 8. Clean up

```bash
curl -sX DELETE "$BASE/tables/sales.fact.orders"     > /dev/null
curl -sX DELETE "$BASE/tables/sales.fact.customers"  > /dev/null
curl -sX DELETE "$BASE/schemas/sales.fact?force=true" > /dev/null
curl -sX DELETE "$BASE/catalogs/sales"               > /dev/null
```

Deleting a table cascades to its own declared constraints. A
foreign-key declaration on *another* table that referenced the
deleted one stays behind and rehydrates with `parent_table` rendered
as the sentinel `<deleted>.<deleted>.<deleted>` — append-only delete
posture, same as orphaned tags and lineage edges.

## See also

- [Concepts → Table constraints](../../concepts/table-constraints.md)
  — the *why* behind metadata-only declarations.
- [ADR-0012](../../adr/0012-table-constraints.md) — full design
  decision.
- [ADR-0009](../../adr/0009-delta-rest-catalog-as-secondary-surface.md)
  — why constraint mutations ride on the Delta REST surface.
- [Concepts → Securables and naming](../../concepts/securables-and-naming.md)
  — how rename invariance via opaque ids works.
