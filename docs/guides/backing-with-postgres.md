# Backing soyuz with Postgres

soyuz-catalog defaults to a local SQLite file. SQLite is fine for
development, single-user setups, and most CI fixtures, but production
deployments usually want Postgres for concurrent writes, replication, and
operational tooling. This guide covers the switch.

The rationale for first-class Postgres support is
[ADR-0004](../adr/0004-postgres-as-supported-backend.md). Operational
considerations are in [Backends](../admin/backends.md). Here we focus on
the mechanics of switching.

## What you need

- A running Postgres 14+ instance.
- A database, a role, and that role's credentials.
- A bit of free disk on the Postgres host (soyuz schemas are small).

Postgres 13 likely works but is not tested. Earlier versions miss
features Alembic uses.

## Create the database and role

```sql
CREATE ROLE soyuz LOGIN PASSWORD 'change-me';
CREATE DATABASE soyuz OWNER soyuz;
GRANT ALL PRIVILEGES ON DATABASE soyuz TO soyuz;
```

If you are co-locating soyuz with another application on the same
Postgres instance, give it its own database rather than a schema —
Alembic operates on the default schema and a shared database is more
trouble than it is worth.

## Point soyuz at it

soyuz reads `SOYUZ_DATABASE_URL`:

```bash
export SOYUZ_DATABASE_URL="postgresql+psycopg://soyuz:change-me@db.internal:5432/soyuz"
uv run uvicorn soyuz_catalog.api.main:app
```

The URL is a standard SQLAlchemy URL. Use the `psycopg` driver
(`postgresql+psycopg://`) which ships with `psycopg[binary]` already in
soyuz's dependency set.

On the first start the lifespan handler runs Alembic migrations
automatically. Every replica that boots against the same database is
safe to run concurrently — Alembic acquires an advisory lock before
applying any upgrade.

## Connection pool sizing

By default SQLAlchemy uses a small pool (5 connections + 10 overflow).
That is enough for a single uvicorn worker doing typical metadata work.
If you run multiple workers, multiply: a 4-worker deployment expects
roughly `4 × (pool_size + max_overflow)` Postgres connections at peak.

To tune, set the URL with query parameters:

```bash
export SOYUZ_DATABASE_URL="postgresql+psycopg://soyuz:change-me@db.internal:5432/soyuz?application_name=soyuz-catalog"
```

For pool settings, the cleanest path is a small wrapper script that calls
`create_engine` with `pool_size=` / `max_overflow=` overrides. The
runtime config does not expose these directly because most deployments
do not need them.

## Verify

```bash
curl http://127.0.0.1:8000/healthz
# {"status":"ok"}

# A round-trip through Postgres
BASE=http://127.0.0.1:8000/api/2.1/unity-catalog
curl -sX POST "$BASE/catalogs" -H content-type:application/json \
     -d '{"name":"smoke-test"}'
curl -s "$BASE/catalogs/smoke-test"
curl -sX DELETE "$BASE/catalogs/smoke-test"
```

If all four return `200 OK`, the switch is complete.

## Migrating an existing SQLite database

Two options.

**Option 1 — Start fresh.** Recommended for non-production data. Drop
the SQLite file, point at Postgres, recreate the catalogs.

**Option 2 — Dump and reload.** SQLite and Postgres do not share a wire
format. Use [`pgloader`](https://pgloader.io/) or a small Python script
that reads from one SQLAlchemy session and writes to another. There is
no soyuz-supplied tool because the right answer depends on what data
must be preserved (audit log? lineage? just catalogs?).

If the existing SQLite data is purely operational metadata (catalogs,
schemas, tables), the disconnect-and-reconnect cost is typically
lower than building a one-time migration tool.

## See also

- [Backends](../admin/backends.md) — operational tradeoffs.
- [Migrations](migrations.md) — running and generating Alembic
  migrations.
- [Backup and restore](backup-restore.md) — patterns for both backends.
- [ADR-0004](../adr/0004-postgres-as-supported-backend.md) — the
  decision.
