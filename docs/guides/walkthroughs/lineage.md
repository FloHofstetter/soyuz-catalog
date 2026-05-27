# Walkthrough — Posting and traversing lineage

> **Goal:** ingest an OpenLineage RunEvent, then traverse the resulting
> graph upstream and downstream.
>
> **Surface:** `/lineage/v1/events`, `/lineage/upstream/<full_name>`,
> `/lineage/downstream/<full_name>` (root-mounted).
>
> **Prereqs:** soyuz running on `:8000`. The walkthrough is
> self-contained — it creates the catalogs/schemas/tables it needs.

```bash
BASE=http://127.0.0.1:8000/api/2.1/unity-catalog
LINEAGE=http://127.0.0.1:8000/lineage
H="content-type:application/json"
```

## 1. Seed the securables

A lineage edge has two endpoints; soyuz needs both to exist as tables.

**Action**

```bash
curl -sX POST "$BASE/catalogs" -H $H -d '{"name":"warehouse"}' > /dev/null
curl -sX POST "$BASE/schemas"  -H $H -d '{"name":"raw",   "catalog_name":"warehouse"}' > /dev/null
curl -sX POST "$BASE/schemas"  -H $H -d '{"name":"bronze","catalog_name":"warehouse"}' > /dev/null
for t in raw.events bronze.events_enriched; do
  IFS=. read schema name <<<"$t"
  curl -sX POST "$BASE/tables" -H $H -d "{
    \"name\":\"$name\",\"catalog_name\":\"warehouse\",\"schema_name\":\"$schema\",
    \"table_type\":\"MANAGED\",\"data_source_format\":\"DELTA\",
    \"storage_location\":\"file:///tmp/warehouse/$schema/$name\",
    \"columns\":[{\"name\":\"id\",\"type_text\":\"long\",\"type_json\":\"{}\",\"type_name\":\"LONG\",\"position\":0}]
  }" > /dev/null
done
```

**Expect**

No output. Each call returns `200 OK`.

## 2. Post an OpenLineage RunEvent

This event says: a job called `enrich-events` read from
`warehouse.raw.events` and wrote to `warehouse.bronze.events_enriched`.

**Action**

```bash
RUN_ID=$(uuidgen)
curl -sX POST "$LINEAGE/v1/events" -H $H -d "{
  \"eventType\": \"COMPLETE\",
  \"eventTime\": \"2026-05-26T10:00:00Z\",
  \"producer\": \"https://example.com/walkthrough\",
  \"schemaURL\": \"https://openlineage.io/spec/2-0-0/OpenLineage.json#/definitions/RunEvent\",
  \"run\": {\"runId\": \"$RUN_ID\"},
  \"job\": {\"namespace\": \"analytics\", \"name\": \"enrich-events\"},
  \"inputs\": [
    {\"namespace\": \"unitycatalog\", \"name\": \"warehouse.raw.events\"}
  ],
  \"outputs\": [
    {\"namespace\": \"unitycatalog\", \"name\": \"warehouse.bronze.events_enriched\"}
  ]
}"
```

**Expect**

`201 Created` with the ingested run summary echoed back.

## 3. Walk downstream from `raw.events`

**Action**

```bash
curl -s "$LINEAGE/downstream/warehouse.raw.events" | jq '.edges[] | {from: .from, to: .to}'
```

**Expect**

```json
{"from": "warehouse.raw.events", "to": "warehouse.bronze.events_enriched"}
```

## 4. Walk upstream from `bronze.events_enriched`

**Action**

```bash
curl -s "$LINEAGE/upstream/warehouse.bronze.events_enriched" | jq '.edges[] | {from: .from, to: .to}'
```

**Expect**

The same edge, observed from the consumer side.

## 5. Re-post the same run — dedupe by run UUID

**Action**

```bash
curl -sX POST "$LINEAGE/v1/events" -H $H -d "{
  \"eventType\": \"COMPLETE\",
  \"eventTime\": \"2026-05-26T10:00:01Z\",
  \"producer\": \"https://example.com/walkthrough\",
  \"schemaURL\": \"https://openlineage.io/spec/2-0-0/OpenLineage.json#/definitions/RunEvent\",
  \"run\": {\"runId\": \"$RUN_ID\"},
  \"job\": {\"namespace\": \"analytics\", \"name\": \"enrich-events\"},
  \"inputs\": [
    {\"namespace\": \"unitycatalog\", \"name\": \"warehouse.raw.events\"}
  ],
  \"outputs\": [
    {\"namespace\": \"unitycatalog\", \"name\": \"warehouse.bronze.events_enriched\"}
  ]
}"
curl -s "$LINEAGE/downstream/warehouse.raw.events" | jq '.edges | length'
```

**Expect**

The second post returns `201` with the same `runId`. The downstream
query still returns **one** edge — the duplicate event is merged with the
existing run by UUID, not double-counted.

## 6. Clean up

```bash
curl -sX DELETE "$BASE/schemas/warehouse.raw?force=true"    > /dev/null
curl -sX DELETE "$BASE/schemas/warehouse.bronze?force=true" > /dev/null
curl -sX DELETE "$BASE/catalogs/warehouse"                   > /dev/null
```

Lineage rows referencing the dropped tables remain in the database as
orphans (append-only delete posture).

## See also

- [Concepts → Lineage](../../concepts/lineage.md) — the data model.
- [ADR-0008](../../adr/0008-openlineage-as-lineage-contract.md) — why
  OpenLineage.
- [OpenLineage spec](https://openlineage.io/docs/) — RunEvent shape.
