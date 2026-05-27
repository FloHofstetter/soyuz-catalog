# Backup and restore

soyuz-catalog stores everything in one SQL database. Backup is therefore
backup of the database. This guide gives the standard patterns for both
backends and notes where soyuz-specific care helps.

## What needs to be backed up

| Asset | Where it lives | Backup strategy |
|---|---|---|
| Catalog / schema / table / volume / function / model metadata | Database | Standard DB backup |
| Tags, lineage, audit log, constraints, connections | Database | Same — they are extra tables in the same DB |
| Storage Credential references | Database | Same. Actual cloud keys are *not* in soyuz; back those up at the cloud-IAM layer. |
| Volume file IO content (if you use the `file://` backend) | Filesystem under `volume_root` | Filesystem backup, separately |
| Model artifacts (if you use the local `file://` model store) | `SOYUZ_MODEL_ARTIFACT_ROOT` (defaults to `model_artifacts/` next to the DB) | Filesystem backup, separately |

The metadata database is the primary target. Volume content and model
artifacts are stored *outside* soyuz, on the same machine or in cloud
object storage — they have their own backup story.

## SQLite

A SQLite database is a single file (plus `*-shm` and `*-wal` during
active writes). Two backup approaches:

### Hot backup with `sqlite3 .backup`

```bash
sqlite3 /path/to/soyuz.db ".backup '/path/to/backup/soyuz-$(date +%F).db'"
```

This is the only safe online backup mechanism for SQLite — it copies the
database with an internal page-locking pass that survives concurrent
writes. Plain `cp` of a hot SQLite file can capture an inconsistent
state.

### Cold backup

If the soyuz process is stopped:

```bash
cp /path/to/soyuz.db /path/to/backup/soyuz-$(date +%F).db
```

Restore is `cp` in the other direction, with the server stopped.

## Postgres

Use `pg_dump`. The default plain-SQL output is human-readable and
restores into any Postgres of the same major version or newer.

```bash
pg_dump --format=custom --no-owner --no-privileges \
        --file=soyuz-$(date +%F).dump \
        postgresql://soyuz:****@db.internal:5432/soyuz
```

`--format=custom` gives a compressed binary dump that `pg_restore` can
read in parallel. `--no-owner` and `--no-privileges` make the dump
portable across roles.

Restore into a fresh database:

```bash
createdb -O soyuz soyuz_restore
pg_restore --no-owner --no-privileges --jobs=4 \
           --dbname=postgresql://soyuz:****@db.internal:5432/soyuz_restore \
           soyuz-2026-05-26.dump
```

## Volume files and model artifacts

If you use the `file://` volume backend, the files live under
`SOYUZ_VOLUME_FILE_ROOT` (or whichever path you configured). Standard
filesystem backup (rsync, restic, borg, your existing backup tool) is
the right answer.

Model artifacts default to a directory next to `soyuz.db`. Same story.

For cloud-backed volumes (S3, ABFSS, GCS), the cloud's own
versioning/replication features are typically the right backup story —
soyuz never wrote those files, so there is nothing soyuz-specific to do.

## Point-in-time recovery

soyuz does not run a write-ahead-log shipping or logical-decoding
process. If you need PITR (recover to a specific timestamp), drive it at
the Postgres layer with WAL archiving + `barman` /
`pgBackRest` / `wal-g` — the standard Postgres PITR toolchain. soyuz has
no opinion on which one.

## What to test

A backup that has never been restored is not a backup. Practise:

1. Take a backup.
2. Spin up an empty soyuz environment.
3. Restore the backup.
4. Run the [Quickstart](../getting-started/quickstart.md) calls against
   the restored data — list a known catalog, fetch a known table.

That dry run is the only way to know the backup is correct.

## See also

- [Backing soyuz with Postgres](backing-with-postgres.md)
- [Migrations](migrations.md) — a downgrade in production should always
  be preceded by a backup.
- [Concepts → Architecture](../concepts/architecture.md) — what soyuz
  stores and where.
