# Quickstart

This page assumes the [installation](installation.md) is complete. It
walks you from "fresh checkout" to a healthcheck and a `GET /catalogs`
call against a running server in about two minutes.

## Start the server

```bash
uv run uvicorn soyuz_catalog.api.main:app --reload
```

!!! tip "Why `uv run`"

    soyuz uses [uv](https://github.com/astral-sh/uv) for dependency
    resolution and venv management. `uv run` executes the command
    inside the project's locked environment without an explicit
    `uv sync` step.

`--reload` watches the source tree and restarts on file changes — useful
for development, off in production. The server listens on
`http://127.0.0.1:8000` and mounts the Unity Catalog routes under the
spec's standard prefix `/api/2.1/unity-catalog`.

Startup runs Alembic migrations automatically, so a fresh SQLite file
becomes a usable database without an out-of-band step.

## Healthcheck

In a second terminal:

```bash
curl http://127.0.0.1:8000/healthz
# {"status":"ok"}
```

## Make your first call

```bash
BASE=http://127.0.0.1:8000/api/2.1/unity-catalog

# List catalogs (empty on a fresh server)
curl "$BASE/catalogs"
# {"catalogs":[],"next_page_token":null}

# Create one
curl -X POST "$BASE/catalogs" \
     -H content-type:application/json \
     -d '{"name":"main","comment":"primary catalog","properties":{"env":"dev"}}'

# List again
curl "$BASE/catalogs"
```

The second `GET` returns the catalog you just created. The `id` field is
an opaque UUID; the `name` field is what you address the catalog by.

## OpenAPI documentation

soyuz publishes the live OpenAPI document at `/openapi.json` and a
human-readable Swagger view at `/docs`:

- <http://127.0.0.1:8000/docs>
- <http://127.0.0.1:8000/openapi.json>

The `/docs` page lists every route and lets you execute requests in the
browser.

## Stop the server

`Ctrl-C` in the terminal running `uvicorn`. The SQLite file
(`soyuz.db` in the working directory by default) persists.

## What to read next

- [First catalog](first-catalog.md) — a deeper guided tour through
  creating a hierarchy.
- [Concepts → Architecture](../concepts/architecture.md) — what just
  happened under the hood.
- [HTTP walkthroughs](../guides/walkthroughs/catalog-schema-table.md) —
  scripted sequences that reproduce reliably against a fresh server.
- [Configuration](../admin/configuration.md) — change the database URL,
  port, log level.

## See also

- [Installation](installation.md)
- [REST API reference](../reference/api.md)
- [Divergences](../divergences.md) — note that `PATCH` with empty
  `properties={}` clears all properties (a deliberate fix vs UC OSS).
