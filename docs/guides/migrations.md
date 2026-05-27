# Migrations with Alembic

soyuz-catalog uses [Alembic](https://alembic.sqlalchemy.org/) for schema
migrations. Migrations run **automatically** on server startup, so most
operators never need to invoke Alembic by hand. This guide covers the
cases where you do: rolling back, inspecting, and generating new
revisions.

## How migrations run

The `lifespan` handler in `soyuz_catalog/api/main.py` calls
`run_migrations()` immediately after `init_db()`. The migrator opens a
transactional connection, acquires an advisory lock (Postgres) or
file lock (SQLite), and applies every revision from the current head to
`head`. On clean shutdown the lock is released; on a crashed startup the
lock times out and the next process retries.

The behaviour for fresh databases:

- SQLite — the file is created if absent, migrations populate the
  schema.
- Postgres — the role must already have rights on an existing database
  (`CREATE DATABASE` is not soyuz's job). Migrations create every table
  and index.

The behaviour for already-migrated databases:

- Both backends — startup is a no-op (Alembic checks the
  `alembic_version` table and finds head).

## Inspect the current revision

The fastest way to check what revision your database is at:

```bash
uv run alembic -c soyuz_catalog/alembic.ini current
```

Output is the `revision_id` of the most recently applied migration.
Comparing it against `head` tells you whether an upgrade is pending.

```bash
uv run alembic -c soyuz_catalog/alembic.ini history --rev-range='-5:'
```

shows the most recent five migrations with their human-readable
descriptions.

## Manual upgrade

If you have suppressed the automatic startup migration (e.g. running
the server with `RUN_MIGRATIONS=0` in a custom setup), apply pending
revisions manually:

```bash
uv run alembic -c soyuz_catalog/alembic.ini upgrade head
```

Stop the server first if it is running against the same database.

## Manual downgrade

Downgrades exist for every soyuz migration, but they are **not
production-safe** by default. A downgrade that drops a column drops the
data along with it.

```bash
# Roll back one revision
uv run alembic -c soyuz_catalog/alembic.ini downgrade -1

# Roll back to a specific revision
uv run alembic -c soyuz_catalog/alembic.ini downgrade <revision_id>

# Roll back to empty (DESTRUCTIVE)
uv run alembic -c soyuz_catalog/alembic.ini downgrade base
```

Before downgrading in production, take a backup ([Backup and
restore](backup-restore.md)).

## Generating a new migration

When you add a new table or column to `soyuz_catalog/models.py`,
generate a migration:

```bash
uv run alembic -c soyuz_catalog/alembic.ini revision \
    --autogenerate -m "add foo column to bar"
```

Autogenerate compares the declared model graph against the live
database schema and writes a Python file with the diff. **Always read
it before committing** — autogenerate has well-known blind spots:

- It does not catch column-type changes that look identical at the SQL
  level (e.g. `Integer` → `BigInteger` on SQLite).
- It does not catch reordering of columns.
- It generates verbose default-value handling that often needs trimming.

The generated file lands in `soyuz_catalog/alembic/versions/` with the
next sequence number prefix. The filename pattern is
`NNN_short_description.py`.

## Squashing history

soyuz does not squash migrations. The `revision_id` chain is the
canonical history of every schema change — including the ones written
during early development. Read it like git log for the database. A new
contributor cloning the repo applies the full chain in seconds, so
there is no operational reason to squash.

## See also

- [Backing soyuz with Postgres](backing-with-postgres.md)
- [Backup and restore](backup-restore.md)
- [Alembic documentation](https://alembic.sqlalchemy.org/en/latest/)
- The migration files themselves under
  [`soyuz_catalog/alembic/versions/`](https://github.com/FloHofstetter/soyuz-catalog/tree/main/soyuz_catalog/alembic/versions)
  — read them top to bottom to see how the schema grew.
