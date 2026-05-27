# Python SDK (generated client)

soyuz-catalog ships an in-tree Python client generated from its own
OpenAPI document via
[`openapi-python-client`](https://pypi.org/project/openapi-python-client/).
It lives at `soyuz-catalog-client/` in the repository and covers every
route soyuz exposes — both the spec routes and the over-the-spec
extensions.

The decision to ship a generated client instead of writing one by hand is
[ADR-0007](../adr/0007-generated-client-over-hand-written-sdk.md).

## When to use which client

There are two Python clients in the ecosystem; pick by use case.

| Client | When to use |
|---|---|
| [`unitycatalog`](https://pypi.org/project/unitycatalog/) (upstream PyPI) | You target generic Unity Catalog and want the same client to work against Databricks UC, UC OSS Java, and soyuz. Covers the CRUD core: catalog / schema / table / volume. |
| `soyuz-catalog-client` (in-tree) | You need everything: credentials, external locations, functions, registered models, model versions, permissions, effective permissions, lineage, tags, connections, delta commits. The upstream SDK covers only a slice. |

Both clients work; using both in the same code base is fine — they have
different module paths and do not conflict.

## Install the in-tree client

The client is a separate package living in `soyuz-catalog-client/`. From
the soyuz repo:

```bash
cd soyuz-catalog-client/
uv build
pip install dist/soyuz_catalog_client-*.whl
```

Or in a script:

```bash
pip install /path/to/soyuz-catalog/soyuz-catalog-client
```

The client is not on PyPI today — the canonical distribution channel is
the repository itself.

## Use it

```python
from soyuz_catalog_client import Client
from soyuz_catalog_client.api.catalogs import create_catalog, list_catalogs, get_catalog
from soyuz_catalog_client.models import CreateCatalog, CatalogInfo

client = Client(base_url="http://localhost:8000")

# Create
new = create_catalog.sync(
    client=client,
    body=CreateCatalog(name="sales", comment="sales-domain"),
)
print(new.id, new.name)

# Read
got = get_catalog.sync(client=client, name="sales")
assert got.name == "sales"

# List
all_cats = list_catalogs.sync(client=client)
print([c.name for c in all_cats.catalogs])
```

Every endpoint exposes both `sync()` and `asyncio()` callables (the
client wraps `httpx` and supports both transports). Soyuz's server is
sync, but a calling client can be async; the generated client handles
the bridge.

## How it stays in sync with the server

A CI gate regenerates the client against the live OpenAPI document and
compares to the checked-in tree. Any backwards-incompatible change to a
route or schema breaks the regeneration test. The script is at
`bash scripts/regen_client.sh`.

The companion runtime check is `tests/test_generated_client_roundtrip.py`,
which exercises every resource through the generated client against a
live server. A wire-shape regression that survives the regeneration
gate is caught there.

This double-gate means the client and the server cannot quietly
diverge. The cost is that a server-side breaking change is also a
client-side breaking change; the benefit is that clients written
against the soyuz Python SDK see the same shape as the wire.

## When to regenerate locally

Most contributors never need to. The CI gate keeps the checked-in
client current with `main`. Regenerate locally only when:

- You changed a request/response schema in `soyuz_catalog/api/schemas.py`.
- You added or removed a route.
- You want to check that an OpenAPI change actually round-trips
  through the generator before pushing.

```bash
# From the repo root
bash scripts/regen_client.sh
```

Inspect the diff under `soyuz-catalog-client/` and commit it alongside
the schema change.

## What the generator does not do

A few areas where you may want to wrap the generated client:

- **Authentication.** The generated client takes a `base_url` and
  defaults to no authentication. Production calls go through your auth
  proxy; either run the proxy at the URL the client points at, or wrap
  the client with a small `Client` subclass that injects headers.
- **Retries.** The generator emits plain HTTP calls. Retries are the
  caller's responsibility — use `httpx.Client(transport=httpx.HTTPTransport(retries=...))`
  by constructing the client manually.
- **Logging.** No request/response logging by default. Wrap `httpx`'s
  event hooks if you need it.

## See also

- [ADR-0007](../adr/0007-generated-client-over-hand-written-sdk.md) — the
  decision.
- [REST API reference](../reference/api.md) — what the generated client
  is generated from.
- [Spec coverage map](../reference/spec-coverage.md) — what the client
  can talk to.
- [openapi-python-client docs](https://github.com/openapi-generators/openapi-python-client)
