# Table constraints

soyuz-catalog stores declared `PRIMARY KEY`, `FOREIGN KEY`, `CHECK`, and
named `NOT NULL` constraints on tables and returns them on read. It does
**not** validate row data against them — the query engine (Spark,
delta-rs, dbt's adapter) does that. Constraints in soyuz are
*declarations*, not enforcement; their value is interoperability with
the wider catalog tooling ecosystem that already reads declared
constraints to render ER diagrams, pick join strategies, or flag tables
missing a primary key.

The full design rationale lives in
[ADR-0012](../adr/0012-table-constraints.md).

## What gets stored

Four constraint kinds, all flat rows in one `table_constraints` table
keyed on the opaque `Table.id`:

| Kind | Carries |
|---|---|
| `PRIMARY_KEY` | One or more `child_columns`. At most one PK per table; a second declaration is `409 ALREADY_EXISTS`. |
| `FOREIGN_KEY` | `child_columns` on this table, a three-part `parent_table` reference, plus `parent_columns` on the parent. The parent is resolved to its opaque id at write time, so renaming either side does not break the declaration. |
| `CHECK` | `child_columns` (informational) plus a verbatim `sql_text` predicate. soyuz never parses or runs the predicate. |
| `NOT_NULL` | A single `child_column`. This is a **named** declaration that is orthogonal to the column's own `nullable` flag — see "Named NOT NULL vs Column.nullable" below. |

Each row carries a user-chosen `name` that is unique per table.
Cross-table reuse is legal.

## How they appear on the wire

Reads come back on the main UC REST `GET /tables/{full_name}` as an
optional `table_constraints` array on the table response. The field is
`None` when the table has no declared constraints, not `[]` — so
existing fixtures that don't populate it stay stable.

A primary-key declaration looks like:

```json
{
  "table_constraints": [
    {
      "name": "orders_pk",
      "primary_key_constraint": {"child_columns": ["order_id"]}
    }
  ]
}
```

The envelope is a thin discriminated union: exactly one of
`primary_key_constraint`, `foreign_key_constraint`, `check_constraint`,
`named_table_constraint` is populated. Zero or more than one is a 400
`INVALID_ARGUMENT` at the service layer.

## How to add and remove them

Mutations ride on the **Delta REST `UpdateTable`** discriminated union,
not on the main UC REST `/tables` surface:

```text
POST /delta/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}
{
  "actions": [
    {"type": "add-constraint", "constraint": { ... }},
    {"type": "drop-constraint", "name": "old_pk", "if_exists": true}
  ]
}
```

This is deliberate. The main UC REST `/tables` route has no `PATCH`
(`405 Method Not Allowed`) and reopening that invariant for a
net-new feature would have undone the protection it bought in the
first place. Both surfaces share the same storage, so a constraint
added via Delta REST shows up immediately on the UC REST table read.

Multiple actions in a single `UpdateTable` request apply
transactionally — a validation failure on the third action rolls back
the first two.

## Why declared, not enforced

soyuz is a metadata server. Enforcing a `CHECK` would require parsing
SQL in whatever dialect the client picked, running the predicate over
data soyuz never sees, and integrating with the storage layer to
intercept writes — three large surfaces, none of them what a catalog
is for. The engine (Spark, delta-rs) already owns the write path and
can enforce against the declarations soyuz returns.

The Java reference implementation makes the same trade-off — declared
constraints are widely supported by Databricks tooling precisely
because nobody assumes the catalog itself enforces them.

## Named `NOT NULL` vs `Column.nullable`

Columns have a `nullable` boolean directly on the column shape. A
named `NOT_NULL` constraint is a *second*, separately-addressed row
that carries a user-chosen name. Adding or dropping the named
constraint deliberately does not flip the column flag, and vice versa.

This mirrors Databricks' shape — the two represent different
concepts (column-level vs table-level, anonymous vs named, immutable
vs mutable) and folding them would re-introduce the silent
side-effect class that the "no table PATCH" invariant blocks. See
ADR-0012 § "Named `NOT NULL` is orthogonal to `Column.nullable`".

## What happens on rename and delete

- **Rename a column** the constraint references → declaration stays;
  the rehydrated payload still names the old column. Constraint rows
  store column **names**, not column ids, because the spec models
  columns by name. A producer that later re-emits the declaration
  with the new column name lands a new row beside the old one.
- **Rename a table** the constraint lives on → declaration stays;
  rows key on opaque `Table.id`, not full_name.
- **Delete a table** → `delete_table` cascades to its own
  constraints. Foreign-key declarations on *other* tables that
  reference the deleted one are kept as append-only orphans and
  rehydrate with `parent_table` rendered as the sentinel
  `<deleted>.<deleted>.<deleted>`. Same posture as orphaned tags and
  lineage rows.

## See also

- [Walkthrough: declared table constraints](../guides/walkthroughs/declared-constraints.md)
  — concrete HTTP example, including the `POST /tables` 422 that
  guards the UC-surface invariant.
- [Extensions over the spec](extensions-over-spec.md) — where this
  fits in the broader extension picture.
- [Spec coverage map](../reference/spec-coverage.md) — at-a-glance
  status for spec + extensions.
- [ADR-0012](../adr/0012-table-constraints.md) — full decision
  record, including the alternatives that were rejected.
- [ADR-0009](../adr/0009-delta-rest-catalog-as-secondary-surface.md)
  — the Delta REST surface that carries the mutations.
