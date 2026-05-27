# Stack and interchangeability

soyuz-catalog is a small set of well-known open-source libraries wired
together. Every choice in the stack has a reason, and most can be swapped
— but not all swaps are equally cheap. This page lists what is in use,
why, and what it would cost to replace.

The foundational decision is [ADR-0001](../adr/0001-stack-and-conventions.md).
This page is the operational view.

## At a glance

| Component | Choice | Why | Swap cost |
|---|---|---|---|
| HTTP framework | [FastAPI](https://fastapi.tiangolo.com/) | Native OpenAPI, route-level Pydantic validation, well-supported sync dependency injection. | High — every route file imports `from fastapi import …` and uses `Depends`. |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org/) 2.0, **sync** | Mature, multi-backend, transactional. Sync over async on purpose; see below. | Very high — every service signature takes a `Session`. |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) | The standard pair to SQLAlchemy. | High in theory, painful in practice — the `revision_id` chain is the canonical history. |
| Validation | [Pydantic v2](https://docs.pydantic.dev/) | Drives FastAPI request/response shape. `extra="forbid"` central to the spec-conformance posture. | Bound to FastAPI; cannot be swapped without the framework. |
| ASGI server | [`uvicorn`](https://www.uvicorn.org/) | Default, well-tuned. | Trivial — any ASGI server (`hypercorn`, `daphne`) works. |
| Database (dev) | SQLite (file or in-memory) | Zero-setup, fast for tests, [ADR-0004](../adr/0004-postgres-as-supported-backend.md). | First-class; no swap needed. |
| Database (prod) | [PostgreSQL](https://www.postgresql.org/) | First-class, ADR-0004. | MySQL / MariaDB are possible but untested. |
| Test runner | [`pytest`](https://docs.pytest.org/) + [`httpx`](https://www.python-httpx.org/) TestClient | Standard. | Trivial. |
| Linter | [`ruff`](https://docs.astral.sh/ruff/) | Single-binary, fast, covers what `flake8`+`black`+`isort` used to. | Trivial — rules transfer. |
| Type checker | [`pyright`](https://microsoft.github.io/pyright/) | Strict, fast, IDE-friendly. | `mypy` works as a drop-in; trivial swap. |
| Docstring linter | [`pydoclint`](https://github.com/jsh9/pydoclint) | Enforces Google-style sections match the signature. | Trivial. |
| Python client | OpenAPI-generated via [`openapi-python-client`](https://pypi.org/project/openapi-python-client/) | [ADR-0007](../adr/0007-generated-client-over-hand-written-sdk.md) — hand-written clients drift. | Trivial — swap the generator. |
| Docs site | [`mkdocs-material`](https://squidfunk.github.io/mkdocs-material/) + [`mkdocstrings`](https://mkdocstrings.github.io/) | Standard for Python projects; renders Google-style docstrings as API reference. | Trivial; content is plain Markdown. |
| Dependency manager | [`uv`](https://docs.astral.sh/uv/) | Fast, lockfile-driven, single-binary. | Trivial — `pip-tools` or `poetry` would work. |

## Why sync over async

This is the most opinionated choice in the stack and worth explaining.
FastAPI supports both sync (`def`) and async (`async def`) route handlers.
SQLAlchemy supports both classical sessions and async sessions. soyuz
uses sync throughout.

Three reasons:

1. **There is no long-tail IO.** soyuz is a metadata server. Every route
   is a single transaction against a local-ish database. There is no
   external HTTP call inside a request path, no cloud SDK call, no
   websocket. Async only pays off when threads spend most of their time
   waiting on IO that is too long to block on; soyuz's routes do not.

2. **Sync code is easier to read, debug, and test.** The full call stack
   in a service function is visible to every IDE and every debugger.
   Async colors every function: a single `async def` deep in the tree
   forces every caller to be async too. That is real maintenance tax
   for a project whose entire IO surface is one DB connection.

3. **SQLAlchemy 2.0 sync is the most mature path.** The async path is
   newer, has fewer documented patterns, and forces explicit `await` on
   every relationship access. The sync path is the one the SQLAlchemy
   docs assume.

The flip side: if a future requirement adds genuinely long-tail IO
(streaming, websocket fanout, calling out to a remote indexer), sync
becomes the wrong default. At that point the right move is a different
server, not a partial async migration. There is no half-async mode that
makes sense.

## What "interchangeable" actually means

In a project that hangs off a wire-level REST spec, *the spec is the
real contract*. Every library above can be replaced, in principle,
without any external client noticing — provided the replacement still
serves the spec correctly. That is the meaning of interchangeability
here.

In practice the cost of a swap depends on how deeply the library has
woven into the codebase:

- **Trivial** swaps touch one or two configuration files. uvicorn,
  pytest, ruff, pyright, uv, the OpenAPI generator are all trivial.
- **High** swaps mean rewriting every route module or every service
  module. FastAPI, SQLAlchemy, Alembic are all high.
- **Bound** swaps require a coordinated framework change. Pydantic
  cannot be swapped without leaving FastAPI; SQLAlchemy's session
  semantics cannot be swapped without leaving the service layer's
  signature contract.

The decision in [ADR-0001](../adr/0001-stack-and-conventions.md) was to
pick mature, opinionated libraries and lean into them — *not* to write
the code as if each library could be replaced tomorrow. That keeps the
service-layer logic readable; the trade-off is acknowledged.

## What is not in the stack

A few things one might expect but soyuz deliberately does not use:

- **No celery / dramatiq / RQ.** There are no background jobs. Audit-log
  writes happen inline; migrations run on startup.
- **No Redis / memcached.** No cache layer; effective-permission
  computations and pagination cursors are computed on demand.
- **No GraphQL.** The spec is REST; soyuz is the REST implementation.
- **No SQLAlchemy plugins (sqlalchemy-utils, sqlalchemy-history).**
  Audit log is implemented manually because the behaviour (best-effort
  write, no rollback on failure) does not match what off-the-shelf
  plugins offer.

## See also

- [Architecture](architecture.md) — how these libraries are wired
  together at runtime.
- [Backends (SQLite vs Postgres)](../admin/backends.md) — operational
  view of the database choice.
- [ADR-0001](../adr/0001-stack-and-conventions.md) — the foundational
  decision.
- [ADR-0004](../adr/0004-postgres-as-supported-backend.md) — when to use
  which database.
- [ADR-0007](../adr/0007-generated-client-over-hand-written-sdk.md) —
  why the in-tree client is generated.
