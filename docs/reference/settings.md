# Settings

Every soyuz-catalog setting is one environment variable with a
documented default. Variables are loaded via
[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
from the process environment; there is no `.env` file loading and no
config file. All variable names are prefixed `SOYUZ_`.

The table below is the canonical reference. The auto-generated block
underneath is a drift guard: a new field added to the
`Settings` class without an entry in this table surfaces there
immediately.

For task-oriented configuration recipes ("I want to switch to
Postgres", "I want JSON logs") see
[Admin → Configuration](../admin/configuration.md).

## Variables

| Variable | Type | Default | Description |
|---|---|---|---|
| `SOYUZ_DATABASE_URL` | string | `sqlite:///<repo>/soyuz.db` | SQLAlchemy database URL. Defaults to a SQLite file at the soyuz repository root so a fresh checkout always finds the same database regardless of working directory. Override for Postgres. |
| `SOYUZ_API_PREFIX` | string | `/api/2.1/unity-catalog` | URL prefix for the spec-conformant UC REST routes. Matches the upstream UC OSS path so existing clients work without configuration. Over-the-spec routes (`/tags`, `/lineage`, `/audit-log`, `/connections`, `/effective-permissions`, `/volumes/{name}/files`) are mounted at root and are not affected. |
| `SOYUZ_LOG_LEVEL` | string | `INFO` | Python logging level name (`DEBUG`, `INFO`, `WARNING`, `ERROR`). `DEBUG` includes per-statement SQLAlchemy SQL logs. |
| `SOYUZ_STRUCTURED_LOGGING` | bool | `false` | When `true`, emit one JSON object per log line via the project's `JsonFormatter`. Gated rather than always-on because the text format is the nicer DX for local development; structured mode is meant for containerised deployments behind a log shipper. |
| `SOYUZ_OPENAPI_ENABLED` | bool | `true` | When `true`, serve `/openapi.json` and `/docs`. Default-on because soyuz has no auth layer (the deployment punts authentication to a front proxy) so an operator who can reach `/openapi.json` can already reach every CRUD endpoint — information-disclosure is not a meaningful threat, and the polish value of the generated docs outweighs it. Paranoid operators can still flip it off with `SOYUZ_OPENAPI_ENABLED=0`. |
| `SOYUZ_MODEL_ARTIFACT_ROOT` | string | `<repo>/model_artifacts` | Base path (file URL or filesystem path) under which model-version artifacts are stored. `create_model_version` populates `ModelVersion.storage_location` as `{model_artifact_root}/{model_id}/{version}`. The MLflow UC-OSS client uploads to that URL before flipping the version status from `PENDING_REGISTRATION` to `READY`. Anchored at the repo root by default so MLflow uploads land next to `soyuz.db` regardless of working directory; override for persistent-volume deployments. |

Bools accept `1` / `0`, `true` / `false`, `yes` / `no` (pydantic-settings
defaults). Unknown environment variables under the `SOYUZ_` prefix are
**ignored**, not rejected — the model is configured with
`extra="ignore"` so a forgotten-to-clean-up env var from an old version
does not block startup.

## Reading the resolved settings

```bash
uv run python -c "from soyuz_catalog.settings import get_settings; \
                   print(get_settings().model_dump_json(indent=2))"
```

This loads the same settings object the running server uses, against
the current environment. `get_settings` is `lru_cache`d, so production
code never re-reads env vars after first access; tests that need to
flip a variable mid-process use `reset_settings_cache()`.

## Drift guard — full Pydantic model

::: soyuz_catalog.settings.Settings
    options:
      show_bases: false

## See also

- [Admin → Configuration](../admin/configuration.md) — task-oriented
  recipes ("I want to switch to Postgres", "I want JSON logs").
- [Admin → Deployment](../admin/deployment.md) — process model and
  reverse-proxy patterns.
- [Admin → Backends (SQLite vs Postgres)](../admin/backends.md) — when
  to use which database URL scheme.
