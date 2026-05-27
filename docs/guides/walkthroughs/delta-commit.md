# Walkthrough — Posting a Delta commit

> **Goal:** drive the Delta commit coordinator through its happy path and
> its `409 Conflict` path.
>
> **Surface:** `POST /api/2.1/unity-catalog/delta/preview/commits`
>
> **Prereqs:** soyuz running on `:8000`.

```bash
BASE=http://127.0.0.1:8000/api/2.1/unity-catalog
H="content-type:application/json"
```

## 1. Create a managed Delta table

The coordinator binds to a table by `table_id`, so the table must exist
first.

**Action**

```bash
curl -sX POST "$BASE/catalogs" -H $H -d '{"name":"lake"}' > /dev/null
curl -sX POST "$BASE/schemas"  -H $H -d '{"name":"bronze","catalog_name":"lake"}' > /dev/null
TABLE=$(curl -sX POST "$BASE/tables" -H $H -d '{
  "name":"events","catalog_name":"lake","schema_name":"bronze",
  "table_type":"MANAGED","data_source_format":"DELTA",
  "storage_location":"file:///tmp/lake/bronze/events",
  "columns":[
    {"name":"ts","type_text":"timestamp","type_json":"{}","type_name":"TIMESTAMP","position":0},
    {"name":"payload","type_text":"string","type_json":"{}","type_name":"STRING","position":1}
  ]
}')
TABLE_ID=$(echo "$TABLE" | jq -r '.table_id')
echo "table_id=$TABLE_ID"
```

**Expect**

A UUID printed.

## 2. Post version 0 — happy path

**Action**

```bash
curl -sX POST "$BASE/delta/preview/commits" -H $H -d "{
  \"table_id\":\"$TABLE_ID\",
  \"commit_info\":{
    \"version\":0,
    \"timestamp\":1735689600000,
    \"operation\":\"CREATE TABLE\",
    \"operation_parameters\":{}
  }
}"
```

**Expect**

`200 OK`. soyuz has recorded the commit attempt and assigned version 0
to your writer. *You* (the client) now write the actual Delta log file at
`file:///tmp/lake/bronze/events/_delta_log/00000000000000000000.json`.
soyuz never touches that file.

## 3. Post version 1 — also happy

**Action**

```bash
curl -sX POST "$BASE/delta/preview/commits" -H $H -d "{
  \"table_id\":\"$TABLE_ID\",
  \"commit_info\":{
    \"version\":1,
    \"timestamp\":1735689700000,
    \"operation\":\"WRITE\",
    \"operation_parameters\":{\"mode\":\"Append\"}
  }
}"
```

**Expect**

`200 OK`.

## 4. Re-post version 1 — `409 Conflict`

The coordinator's job is to serialize version numbers. Two writers
asking for the same version do not both win.

**Action**

```bash
curl -sX POST "$BASE/delta/preview/commits" -H $H -d "{
  \"table_id\":\"$TABLE_ID\",
  \"commit_info\":{
    \"version\":1,
    \"timestamp\":1735689701000,
    \"operation\":\"WRITE\",
    \"operation_parameters\":{\"mode\":\"Append\"}
  }
}"
```

**Expect**

`409 Conflict`. The error body identifies that version 1 is already
taken. The client should retry with version 2.

## 5. Get the list of commits

**Action**

```bash
curl -s "$BASE/delta/preview/commits?table_id=$TABLE_ID" \
   | jq '.commits[] | {version: .version, operation: .commit_info.operation}'
```

**Expect**

```json
{"version":0,"operation":"CREATE TABLE"}
{"version":1,"operation":"WRITE"}
```

Only two entries — the conflicting third attempt was rejected at step 4
and not stored.

## 6. Post a malformed commit — `400 BAD_REQUEST`

**Action**

```bash
curl -sX POST "$BASE/delta/preview/commits" -H $H -d "{
  \"table_id\":\"$TABLE_ID\",
  \"commit_info\":{
    \"version\":-1,
    \"timestamp\":1735689700000,
    \"operation\":\"WRITE\"
  }
}"
```

**Expect**

`400 BAD_REQUEST`. Negative versions are invalid.

## 7. Clean up

```bash
curl -sX DELETE "$BASE/tables/lake.bronze.events"           > /dev/null
curl -sX DELETE "$BASE/schemas/lake.bronze?force=true"      > /dev/null
curl -sX DELETE "$BASE/catalogs/lake"                       > /dev/null
```

## What you did *not* do

You did not write any Parquet or Delta log files. soyuz tracked the
coordination metadata; the file IO is the client's job. This is the
passthrough coordinator pattern documented in
[Concepts → Delta commit handling](../../concepts/delta-commits.md) and
formalized in [ADR-0011](../../adr/0011-delta-commit-coordinator.md).

In a real workflow, a Delta-Kernel-aware client like
[`delta-rs`](../../integrations/delta-rs.md) interleaves these
`POST /delta/preview/commits` calls with `_delta_log/` file writes
automatically.

## See also

- [Concepts → Delta commit handling](../../concepts/delta-commits.md)
- [ADR-0011](../../adr/0011-delta-commit-coordinator.md)
- [delta-rs integration](../../integrations/delta-rs.md)
- [Spark integration](../../integrations/spark.md) — note that Spark
  reaches the coordinator only via the external-Delta path; managed
  Delta is currently intercepted upstream.
