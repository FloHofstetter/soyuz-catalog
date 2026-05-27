# Configuration

soyuz-catalog reads configuration from environment variables. There is no
config file — every option is one env var with a documented default.
This page groups the variables by task. The exhaustive per-variable list
is in the [Settings reference](../reference/settings.md), generated
directly from the Pydantic settings model.

All variables are prefixed `SOYUZ_`.

## Where soyuz looks

soyuz uses [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
Sources, in priority order:

1. Process environment variables.
2. Defaults defined in `soyuz_catalog/settings.py`.

There is no `.env` file loading by default and no config file. That
keeps the configuration surface obvious to inspect with `env | grep SOYUZ_`.

## "I want to..."

### ...switch to Postgres

```bash
export SOYUZ_DATABASE_URL="postgresql+psycopg://soyuz:****@db.internal:5432/soyuz"
```

See [Backing soyuz with Postgres](../guides/backing-with-postgres.md) for
the full walkthrough including pool sizing.

### ...change the URL prefix

```bash
export SOYUZ_API_PREFIX="/v1"
```

Default is `/api/2.1/unity-catalog` (matches the UC spec). The over-the-
spec routes (`/tags`, `/lineage`, `/audit-log`) are mounted at root and
are *not* affected by this setting.

### ...turn off the OpenAPI documentation

```bash
export SOYUZ_OPENAPI_ENABLED=0
```

This disables both `/openapi.json` and `/docs`. The default is on — the
rationale (no meaningful information-disclosure threat in soyuz's
metadata-only stance) is in the `Settings` docstring.

### ...emit JSON logs for a log shipper

```bash
export SOYUZ_STRUCTURED_LOGGING=1
export SOYUZ_LOG_LEVEL=INFO
```

soyuz emits one JSON object per log line. The text format (default) is
nicer for local development; `STRUCTURED_LOGGING=1` is for any deployment
where a log aggregator reads stdout.

### ...change the log level

```bash
export SOYUZ_LOG_LEVEL=DEBUG   # or INFO, WARNING, ERROR
```

Default is `INFO`. `DEBUG` includes SQL query logs (verbose).

### ...relocate the SQLite file

```bash
export SOYUZ_DATABASE_URL="sqlite:////var/lib/soyuz/soyuz.db"
```

Note the four slashes — `sqlite:` + `//` (URL scheme) + `//` (absolute
path). Three slashes is interpreted as a relative path.

The default SQLite location is anchored to the soyuz repository root, so
a fresh checkout always finds the same database regardless of which
directory the server was started from. In production, override.

### ...relocate model artifacts

```bash
export SOYUZ_MODEL_ARTIFACT_ROOT="/var/lib/soyuz/model_artifacts"
```

Default is `model_artifacts/` next to the database file. For containerized
deployments, point this at a persistent volume.

## Configuration in a containerized deployment

Everything via environment variables — no config file. A typical Docker
Compose service:

```yaml
services:
  soyuz:
    image: ghcr.io/flohofstetter/soyuz-catalog:latest
    environment:
      SOYUZ_DATABASE_URL: "postgresql+psycopg://soyuz:${SOYUZ_PG_PASSWORD}@postgres:5432/soyuz"
      SOYUZ_LOG_LEVEL: "INFO"
      SOYUZ_STRUCTURED_LOGGING: "1"
      SOYUZ_OPENAPI_ENABLED: "0"
      SOYUZ_MODEL_ARTIFACT_ROOT: "/data/model_artifacts"
    volumes:
      - artifacts:/data/model_artifacts
    depends_on: [postgres]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1:8000/healthz"]
      interval: 10s
      timeout: 2s
    ports: ["8000:8000"]
```

## Verifying configuration

soyuz prints the resolved settings at startup when `SOYUZ_LOG_LEVEL=DEBUG`.
For a quick check without restarting:

```bash
uv run python -c "from soyuz_catalog.settings import get_settings; \
                   print(get_settings().model_dump_json(indent=2))"
```

This loads the same settings object soyuz uses, against the current
environment.

## What is *not* configurable

A few things are intentionally hardcoded:

- The OpenAPI route paths (`/openapi.json`, `/docs`).
- The healthcheck route (`/healthz`).
- The over-the-spec route prefixes (`/tags`, `/lineage`, `/audit-log`).
- Pydantic's `extra="forbid"` setting on request models.

These are part of soyuz's contract — changing them would break either
the spec or the documented over-the-spec extensions.

## See also

- [Settings reference](../reference/settings.md) — auto-generated full
  list with types and defaults.
- [Deployment](deployment.md) — process model and reverse-proxy patterns.
- [Backends (SQLite vs Postgres)](backends.md) — when to use which.
- [Observability and audit log](observability.md) — what logs look like.
