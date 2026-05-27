# Backends (SQLite vs Postgres)

soyuz-catalog runs against either backend out of the box. They are
first-class — the schema is identical, the test suite runs against both
in CI, and there is no soyuz-side feature that only one supports. The
choice is operational: how many writers, how much concurrency, what the
backup/replication story should be.

The formal decision to support both is
[ADR-0004](../adr/0004-postgres-as-supported-backend.md). This page is
the operational guide.

## At a glance

| Concern | SQLite | Postgres |
|---|---|---|
| Setup | One file. Zero config. | Install Postgres, create db + role. |
| Concurrent writers | Serialized through one file lock | Full MVCC, many writers |
| Multiple soyuz replicas | ❌ Not safe | ✅ Safe (advisory lock on migrations) |
| Backup | `sqlite3 .backup` | `pg_dump` |
| PITR | Not possible | Standard Postgres WAL + barman/pgBackRest/wal-g |
| Replication | Not really | Streaming replication, logical replication |
| Network | Local file only | Wherever you can reach Postgres |
| Disk size | Same as data | Same as data + WAL |
| Operational tooling | None beyond `sqlite3` | psql, pg_dump, pg_restore, pgAdmin, etc. |

## When to use which

**SQLite is the right choice when:**

- You are developing or running tests.
- The deployment is single-process, single-host, lightly used.
- Backup is "copy a file".
- You want zero operational overhead.

**Postgres is the right choice when:**

- You run more than one soyuz replica.
- The catalog backs a production lakehouse with many concurrent writers.
- You need PITR, replication, or any standard Postgres ops feature.
- Your platform already has Postgres and adding another db is free.

## Switching between them

There is no one-step migration tool. Two options:

1. **Start fresh** — drop the SQLite file, point at Postgres, recreate
   the catalogs.
2. **Dump and reload** — write a small Python script that streams rows
   from one SQLAlchemy session to another, or use
   [`pgloader`](https://pgloader.io/).

For most deployments, the "start fresh" path is cheaper than building a
one-off migration. soyuz's data is metadata, not raw business data;
recreating catalogs and re-registering tables takes minutes, not weeks.

## Connection string

soyuz reads `SOYUZ_DATABASE_URL`. It is a standard SQLAlchemy URL:

```bash
# SQLite (default — points at <repo>/soyuz.db)
export SOYUZ_DATABASE_URL="sqlite:////absolute/path/to/soyuz.db"

# Postgres
export SOYUZ_DATABASE_URL="postgresql+psycopg://soyuz:****@db.internal:5432/soyuz"
```

The default points the SQLite file at the soyuz repository root rather
than the current working directory, so a server started from any
directory finds the same database. Override the default for any
production deployment.

## SQLite tuning

soyuz applies two PRAGMAs on every SQLite connection:

- `journal_mode = WAL` — write-ahead log, allowing concurrent reads while
  a write is in progress. Without it, every write blocks every reader.
- `foreign_keys = ON` — SQLite ships with foreign-key enforcement off by
  default. soyuz turns it on so cascade rules behave like Postgres.

These are wired in `soyuz_catalog/db.py` and applied per connection,
which is the only way SQLite PRAGMAs propagate.

Limitations to be aware of:

- **WAL mode requires the journal file and the database file to be on
  the same filesystem.** Network filesystems break WAL guarantees; do
  not put a soyuz SQLite on NFS or SMB.
- **One writer at a time.** Concurrent writes serialize. For a metadata
  server with mostly reads this is fine; for high-write workloads,
  switch to Postgres.

## Postgres tuning

`pool_size` defaults to 5 with 10 overflow, set by SQLAlchemy. For a
4-worker uvicorn deployment this means up to 60 connections at peak,
which sits comfortably in the default `max_connections=100` on a stock
Postgres.

For larger deployments, raise both. soyuz does not expose pool overrides
through environment variables today — set them by wrapping
`soyuz_catalog.api.main` with a small launcher script that calls
`create_engine(...)` with the desired sizing. There is a tracking issue
to surface pool tuning through env vars; until then, the launcher path
is the supported escape hatch.

## Performance characteristics

A few rough numbers for sizing intuition (small server, single worker):

| Operation | SQLite | Postgres |
|---|---|---|
| `GET /catalogs/{name}` cold | ~5 ms | ~10 ms |
| `POST /catalogs` cold | ~20 ms | ~25 ms |
| `GET /tables?...` page of 100 | ~20 ms | ~30 ms |
| `PATCH /tags/...` batch of 10 | ~25 ms | ~35 ms |

SQLite is faster on small workloads because there is no network hop and
no transaction-isolation overhead. Postgres pulls ahead under
concurrency and at scale; if you ever need both numbers in the same
sentence, you are already past the point where SQLite is the right
backend.

## See also

- [ADR-0004](../adr/0004-postgres-as-supported-backend.md)
- [Backing soyuz with Postgres](../guides/backing-with-postgres.md)
- [Backup and restore](../guides/backup-restore.md)
- [Deployment](deployment.md)
- [Settings reference](../reference/settings.md)
