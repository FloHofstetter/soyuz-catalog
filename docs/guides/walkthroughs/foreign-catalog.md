# Walkthrough — Foreign catalog from a connection

> **Goal:** create a Connection pointing at an external metadata source,
> derive a foreign catalog from it, and inspect the result.
>
> **Surface:** `/api/2.1/unity-catalog/connections` and the foreign-catalog
> variant of `/catalogs`.
>
> **Prereqs:** soyuz running on `:8000`. This walkthrough does not need
> an actual external database — soyuz stores the connection metadata; the
> external resolution happens elsewhere.

```bash
BASE=http://127.0.0.1:8000/api/2.1/unity-catalog
H="content-type:application/json"
```

## 1. Create a connection

A connection is a typed reference: it says "this is the connection
metadata for a Postgres instance over there". soyuz does not validate
that the target is reachable.

**Action**

```bash
curl -sX POST "$BASE/connections" -H $H -d '{
  "name": "analytics_pg",
  "connection_type": "POSTGRESQL",
  "options": {
    "host": "analytics.db.internal",
    "port": "5432",
    "user": "soyuz_reader",
    "password": "redacted"
  },
  "comment": "Read-only analytics Postgres"
}'
```

**Expect**

`200 OK`. Response echoes the connection with a server-assigned `id`
and timestamps. `options` is round-tripped verbatim — soyuz stores it
as opaque metadata.

## 2. List connections

**Action**

```bash
curl -s "$BASE/connections" | jq '.connections[] | {name, connection_type}'
```

**Expect**

```json
{"name":"analytics_pg","connection_type":"POSTGRESQL"}
```

## 3. Derive a foreign catalog from the connection

A foreign catalog is a catalog row whose `connection_name` field
references the connection. To downstream clients it looks like any
other catalog, but the schemas/tables underneath would be resolved
through the connection (by a federation engine, not by soyuz).

**Action**

```bash
curl -sX POST "$BASE/catalogs" -H $H -d '{
  "name": "analytics",
  "connection_name": "analytics_pg",
  "comment": "Federated view of analytics Postgres"
}'
```

**Expect**

`200 OK`. The catalog's response body now carries
`"connection_name":"analytics_pg"` in addition to the usual catalog
fields.

## 4. Distinguish foreign from native catalogs

**Action**

```bash
curl -s "$BASE/catalogs" | jq '.catalogs[] | {name, connection_name}'
```

**Expect**

```json
{"name":"analytics","connection_name":"analytics_pg"}
```

A native catalog (no connection) would show `"connection_name":null` or
omit the field, depending on response-model trimming.

## 5. Update the connection — options PATCH semantics

The `options` map on a connection follows the same
replace-style PATCH semantics as `properties` on a catalog. An empty
map clears the options.

**Action**

```bash
curl -sX PATCH "$BASE/connections/analytics_pg" -H $H -d '{
  "options": {
    "host": "analytics-failover.db.internal",
    "port": "5432",
    "user": "soyuz_reader",
    "password": "redacted"
  }
}'
```

**Expect**

`200 OK` with the new options echoed back.

## 6. Drop the foreign catalog

**Action**

```bash
curl -sX DELETE "$BASE/catalogs/analytics"
```

**Expect**

`200 OK`. The foreign catalog is gone; the connection it derived from
is unaffected.

## 7. Drop the connection

**Action**

```bash
curl -sX DELETE "$BASE/connections/analytics_pg"
```

**Expect**

`200 OK`.

## What the federation engine does (out of scope here)

soyuz stores the connection and the foreign-catalog binding. The actual
resolution — querying the Postgres metadata, listing schemas, materialising
tables — is the job of a separate federation engine (a JVM connector or a
Python service). soyuz's responsibility ends at storing and serving the
metadata.

This separation lets soyuz support arbitrary connection types
(MySQL, Snowflake, BigQuery, Redshift, MongoDB, …) without baking
per-source code into the catalog server.

## See also

- [Concepts → Extensions over the spec](../../concepts/extensions-over-spec.md)
  — Connections are a Databricks extension mirrored by soyuz.
- [ADR-0013](../../adr/0013-connections-and-foreign-catalogs.md) — the
  design.
- [REST API reference](../../reference/api.md) — connection-specific
  request/response shapes.
