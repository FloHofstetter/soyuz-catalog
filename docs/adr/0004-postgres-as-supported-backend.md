# ADR-0004: Postgres as a supported backend alongside SQLite

- **Status:** Accepted
- **Date:** 2026-04-14
- **Deciders:** @FloHofstetter

## Context

soyuz-catalog has shipped Phases 1–2 running exclusively on SQLite, which
keeps the test loop fast (in-memory database per test) and the dev
environment zero-config. Real deployments, however, will never run on
SQLite — every consumer that plugs into soyuz (Delta Lake writers, the
`unitycatalog` Python SDK, Spark connectors) expects a multi-process
backend. This decision validates that Postgres works unchanged against
the existing models, Alembic migrations, services, and routes, and
locks that property down with CI so it does not silently regress.

The engine wiring in `soyuz_catalog/db.py` already branched on
`url.startswith("sqlite")` (SQLite-only PRAGMA listener, only SQLite
sets `check_same_thread`), so this ADR is less about new code and more
about recording the design choices taken to keep the codebase
dialect-agnostic going forward.

## Decision

Postgres is a **first-class supported backend** alongside SQLite. The
service ships a `postgres` optional dependency group (`psycopg[binary]`),
a `docker-compose.yml` for local Postgres, a pytest `--db-backend` option
that re-runs the full unit suite against a real Postgres, and a GitHub
Actions `unit + postgres` matrix.

The following deliberate choices flow from that decision:

1. **`JSON` stays portable, no `JSONB` variant.** The ORM keeps
   `sqlalchemy.JSON` on the `properties` columns of catalogs, schemas,
   and tables. We only ever replace the whole object — never execute a
   JSON-path query — so JSONB's GIN-index advantages are unused, and
   `JSON().with_variant(JSONB(), "postgresql")` would only add dialect
   branching for no behavioural win. Revisit if indexed property filters
   ever become a real requirement.
2. **Names stay case-sensitive; no `CITEXT`.** The UC REST spec treats
   catalog / schema / table / volume names as case-sensitive identifiers,
   and UC OSS Java does the same. Using `CITEXT` on Postgres would be a
   silent divergence from the spec and from the SQLite backend. Stay on
   `varchar(n)` everywhere.
3. **`render_as_batch` is gated on SQLite only.** Alembic's batch-mode
   ALTER is a workaround for SQLite's missing `ALTER TABLE` support;
   applying it on Postgres triggers a full table rewrite on every future
   column change. The dialect gate lives in
   `soyuz_catalog/alembic/env.py` and is keyed off the connection's
   dialect name (online) or the URL prefix (offline).
4. **ORM and migration types stay in sync on `BigInteger`.** The models
   used to declare `Mapped[int]` (which SQLAlchemy binds as `::INTEGER`
   / int4) for the ms-epoch `created_at` / `updated_at` columns even
   though the Alembic migrations already used `BigInteger` on disk. On
   SQLite the mismatch was invisible; on Postgres the first insert from
   the smoke test blew up with
   `psycopg.errors.NumericValueOutOfRange` because the current ms-epoch
   (~1.78e12) does not fit in int4. Fixed by annotating the four
   timestamp columns with `mapped_column(BigInteger, ...)`. The smoke
   test `tests/test_postgres_smoke.py::test_postgres_reports_bigint_timestamps`
   locks the invariant down against the real `information_schema`.
5. **Test isolation on Postgres is session-scoped schema reset +
   `TRUNCATE ... RESTART IDENTITY CASCADE` between tests**, not a
   drop/recreate per test and not a savepoint rollback. Drop/recreate per
   test paid Alembic cost 150+ times per run; savepoint rollback is
   fragile with FastAPI's `get_db` dependency which commits mid-request.

## Consequences

- **Positive:** deployments on Postgres are actually tested, not just
  assumed to work; the CI matrix catches any dialect drift the instant a
  migration or column type change lands; the `docker compose up -d
  postgres` loop is identical locally and in CI, so "works on my
  machine" and "fails in CI" cannot diverge for backend reasons; and
  `--db-backend=postgres` re-runs the whole suite against a real
  Postgres with one command.
- **Negative:** one more moving part in the dev environment —
  contributors who touch migrations or column types are expected to run
  both backends locally; the Postgres CI job adds ~30 s to the wall
  clock of a PR check; `psycopg[binary]` adds a compiled dependency to
  the dev environment.
- **Neutral:** async SQLAlchemy is still explicitly out of scope
  ([ADR-0001](0001-stack-and-conventions.md)); psycopg3 is used in sync
  mode via the `postgresql+psycopg://` URL.

## Alternatives considered

- **Keep SQLite-only and add Postgres later.** Rejected: the longer
  soyuz ships without a Postgres canary, the more dialect-specific drift
  accumulates silently. Catching it now is cheap.
- **Switch to JSONB on Postgres via `with_variant`.** Rejected: no
  current query benefits from it, and it would be the first place in the
  codebase where a model file cares which dialect it is on. Revisit when
  indexed property filters are a real requirement.
- **Use `asyncpg` + async SQLAlchemy.** Rejected outright by
  [ADR-0001](0001-stack-and-conventions.md); this ADR does not
  relitigate that.
- **Drop and recreate the database per test on Postgres.** Rejected: 2 s
  of Alembic per test × 150 tests ≈ 5 minutes of CI time for no
  isolation benefit over `TRUNCATE ... RESTART IDENTITY CASCADE`.
