# ADR-0001: Stack and conventions

- **Status:** Accepted
- **Date:** 2026-04-14
- **Deciders:** @FloHofstetter

## Context

soyuz-catalog is a fresh Python implementation of the Unity Catalog REST API.
The project needs a coherent stack picked up-front so that the first vertical
slice (Catalogs CRUD) does not have to revisit infrastructure decisions, and
so that the conventions match the author's other Python services for
consistency and shared muscle memory.

The constraints:

1. Pure Python (no JVM) — that is the *raison d'être* of the project relative
   to UC OSS Java.
2. Same conventions as the sister project
   [shoreguard](https://github.com/FloHofstetter/shoreguard) so that
   contributors and tools can move between the repos without retraining.
3. Easy local development against SQLite, real production deployment against
   PostgreSQL.

## Decision

- **Language:** Python 3.14+, `from __future__ import annotations` everywhere.
- **HTTP framework:** FastAPI, lifespan-based startup, routes mounted under
  `/api/2.1/unity-catalog` to match UC OSS clients out of the box.
- **Persistence:** SQLAlchemy 2.0 with `DeclarativeBase` + typed `Mapped[]`,
  **sync** sessions, route handlers as `def` (FastAPI threadpool). Embedded
  Alembic migrations under `soyuz_catalog/alembic/`, programmatic config (no
  `alembic.ini` at the repo root).
- **Validation:** Pydantic v2 models with `extra="forbid"` on every request
  body to surface unknown fields immediately instead of dropping them.
- **Configuration:** `pydantic-settings` with `env_prefix="SOYUZ_"`.
- **Packaging:** `hatchling`, flat layout (`soyuz_catalog/` at repo root, no
  `src/`), `uv` for dependency management.
- **Quality gates** (enforced by pre-commit, mirroring shoreguard): ruff,
  pyright, pydoclint (Google docstring style), pytest on every commit;
  pip-audit, bandit, `mkdocs build --strict` on every push.
- **Docs:** mkdocs-material with the mkdocstrings Python handler.

## Consequences

- **Positive:** zero context-switching cost between soyuz-catalog and
  shoreguard. New contributors can copy patterns instead of inventing them.
  Sync SQLAlchemy is simpler to test, debug, and reason about than async,
  and the workload (metadata CRUD) is not latency-bound.
- **Negative:** sync sessions on `def` endpoints are run in a threadpool by
  FastAPI. Under heavy concurrent load with PostgreSQL, an async stack
  (`asyncpg`) would scale better. We accept this — the workload is not
  expected to be CPU- or connection-bound at the scale soyuz targets.
- **Neutral:** the embedded-alembic + programmatic-config style is unusual
  in the wider FastAPI ecosystem but has worked well in shoreguard. The
  upside is that migrations ship with the wheel.

## Alternatives considered

- **Async SQLAlchemy + asyncpg.** Idiomatic for FastAPI, but doubles the test
  fixture surface (sync engine for pytest sessions, async engine for routes)
  and adds complexity that the workload does not justify.
- **SQLModel.** Wraps SQLAlchemy + Pydantic into one class, but the
  abstraction leaks at the edges (relationships, hybrid properties), and
  the explicit two-layer split has been more robust in shoreguard.
- **Standalone `alembic.ini` at the repo root.** The conventional layout, but
  shoreguard has shown that programmatic config is cleaner: there is exactly
  one source of truth for the database URL, namely `Settings.database_url`.
