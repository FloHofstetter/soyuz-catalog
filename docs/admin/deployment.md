# Deployment

soyuz-catalog is a single Python process. Production deployment is
deciding three things: how the process is launched, how it is supervised,
and how TLS is terminated. This page covers each in turn, plus the
healthcheck and the migration story.

The simplest deployment is the
[Quickstart](../getting-started/quickstart.md) command running under a
process manager. Everything below is variations on that theme.

## Process model

A single soyuz process serves all routes. There is no background worker,
no message queue, no second service. soyuz handles concurrent requests
in a thread pool that uvicorn provides; the database connection pool
controls how many of those threads can hold a database connection at
once.

For most deployments a single uvicorn worker is enough. Scale out by
adding **workers** (separate processes) rather than threads — the
SQLAlchemy session is process-local and threads share the connection
pool, so a single worker tops out at the pool size.

```bash
uvicorn soyuz_catalog.api.main:app \
        --host 0.0.0.0 --port 8000 \
        --workers 4
```

Four workers behind a load balancer comfortably handle small/medium
catalogs. Beyond that, profile before adding more — soyuz's bottleneck
is almost always the database, not the worker count.

## Reverse proxy + TLS

soyuz does not terminate TLS. Run it behind nginx, Caddy, Envoy, or your
cloud's L7 load balancer.

Minimal nginx fragment:

```nginx
server {
    listen 443 ssl;
    server_name catalog.example.com;

    ssl_certificate     /etc/letsencrypt/live/catalog.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/catalog.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Principal       $remote_user;
    }
}
```

The `X-Principal` header is picked up by soyuz's `RequestIDMiddleware`
and used as the principal in the audit log. The proxy is also where
authentication should live — soyuz has no auth surface; see
[Concepts → Permissions model](../concepts/permissions-model.md) for the
"why".

## Healthcheck

`GET /healthz` returns `{"status":"ok"}` with `200 OK` when the process
is up and the database is reachable. Wire it into your orchestrator's
liveness probe.

For readiness, the same endpoint is fine — soyuz has no warm-up phase.
If `/healthz` returns `200`, the server is taking traffic.

## systemd unit (single host)

```ini
[Unit]
Description=soyuz-catalog
After=network.target postgresql.service

[Service]
Type=exec
User=soyuz
WorkingDirectory=/opt/soyuz-catalog
Environment="SOYUZ_DATABASE_URL=postgresql+psycopg://soyuz:****@localhost:5432/soyuz"
Environment="SOYUZ_LOG_LEVEL=INFO"
Environment="SOYUZ_STRUCTURED_LOGGING=1"
ExecStart=/opt/soyuz-catalog/.venv/bin/uvicorn \
          soyuz_catalog.api.main:app \
          --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Logs flow to journald. With `SOYUZ_STRUCTURED_LOGGING=1` they are
machine-parseable JSON; a log shipper like Vector or Fluent Bit can
forward them on.

## Docker

A minimal Dockerfile:

```dockerfile
FROM python:3.14-slim

RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY soyuz_catalog ./soyuz_catalog

ENV SOYUZ_LOG_LEVEL=INFO
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=2s \
  CMD curl -f http://127.0.0.1:8000/healthz || exit 1
CMD ["uv", "run", "uvicorn", "soyuz_catalog.api.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Mount a writable directory at `/data` for SQLite (or pass `SOYUZ_DATABASE_URL`
pointing at an external Postgres) and a volume root for `/files` IO if
you use the `file://` volume backend.

## Migrations on deploy

Migrations run automatically inside the FastAPI lifespan handler, so a
new container or a new VM with the soyuz binary always upgrades itself
on first start. The Alembic advisory lock prevents two replicas from
applying the same upgrade twice.

You do *not* need a separate `alembic upgrade head` step in your CI/CD
pipeline. The deployment recipe simplifies to: roll a new image, start
the container, hit `/healthz`.

If you prefer an explicit pre-deploy migration step (audit/compliance
reasons), set `RUN_MIGRATIONS=0` in the runtime and run Alembic from
a sidecar — see [Migrations](../guides/migrations.md).

## Multiple replicas

soyuz tolerates multiple replicas against a shared Postgres database. No
session affinity is needed — every request is independent and reads
freshly from the database.

For SQLite, replicas are *not* safe. SQLite has no networked-write
story; running two soyuz processes against the same SQLite file leads to
"database is locked" errors and the file going read-only under stress.
If you want multiple replicas, switch to Postgres
([guide](../guides/backing-with-postgres.md)).

## See also

- [Backends (SQLite vs Postgres)](backends.md)
- [Configuration](configuration.md)
- [Observability and audit log](observability.md)
- [Migrations](../guides/migrations.md)
- [Settings reference](../reference/settings.md)
