# soyuz-catalog-client

Generated Python client for the [soyuz-catalog](../README.md) REST API.

This package is **generated** from the live FastAPI `/openapi.json`
document via `openapi-python-client`. Do not edit files under
`soyuz_catalog_client/` by hand — they are overwritten on every
regeneration and the CI drift gate will reject any manual drift.

## When to use this vs. the upstream `unitycatalog` SDK

- **`unitycatalog`** (upstream, on PyPI): drop-in SDK for the Unity
  Catalog CRUD core (Catalog / Schema / Table / Volume). Use this if
  your code already targets upstream UC.
- **`soyuz-catalog-client`** (this package): covers every namespace the
  soyuz server exposes — credentials, external locations, functions,
  registered models, model versions, metastore, staging tables, path
  credentials, permissions, and Delta commits preview. Used as the
  completeness lackmus test for soyuz' spec implementation: if a
  namespace is missing from `/openapi.json`, importing the test
  module already fails.

See [ADR-0007](../docs/adr/0007-generated-client-over-hand-written-sdk.md)
for the decision rationale, the regeneration flow, and the CI drift
gate that keeps this package in lockstep with the server.

## Regeneration

```bash
just regen-client
```

Runs `scripts/dump_openapi.py` (calls `app.openapi()` directly, no
uvicorn detour) and feeds the output to
`openapi-python-client generate --meta=none`. Only the
`soyuz_catalog_client/` package directory is overwritten; this file,
`pyproject.toml`, and any custom additions at the top level are left
alone.
