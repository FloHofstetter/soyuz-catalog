# Credentials

Unity Catalog defines two resources whose names both contain the word
*credential*. They are unrelated to each other in function. soyuz
implements both with intentionally different shapes that reflect their
different jobs:

- **Storage Credentials** (persistent) — named pointers to credential
  material that a client retrieves out-of-band.
- **Temporary Credentials** (ephemeral) — short-lived credentials minted
  per resource access.

This page disambiguates the two, explains soyuz's metadata-only stance,
and explains what clients should do instead of asking soyuz to vend
credentials.

## Storage Credentials

A *storage credential* is a named, persistent record describing how to
authenticate against a storage backend. The spec defines a credential as
a label + a `principal` reference (a service principal, IAM role, or
managed identity), plus a `read_only` flag and metadata.

What it is **not**: actual key material. The spec stores the *reference*
to credentials, not the credentials themselves. soyuz takes this
literally — the storage backend tables hold names and principal
identifiers; no AWS secret keys, no Azure connection strings.

Routes:

- `POST` / `GET` / `LIST` / `PATCH` / `DELETE` `/credentials`

The matching service is
[`soyuz_catalog/services/credential_service.py`](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/services/credential_service.py)
(singular `credential`).

A typical flow:

1. Operator creates a storage credential `s3-data-prod` referencing the
   IAM role `arn:aws:iam::…:role/data-prod`.
2. External Location `prod-warehouse` references credential `s3-data-prod`.
3. Tables created under `prod-warehouse`'s scope inherit that credential
   reference in their metadata.
4. A client that wants to read a table sees the credential *name* in the
   table response, then asks its cloud SDK to assume the IAM role.

soyuz never participates in step 4. It hands out names; the cloud SDK
handles authentication.

## Temporary Credentials

A *temporary credential* is a short-lived secret minted on demand for a
specific securable: "give me a 15-minute token to read table X". In
Databricks UC, this endpoint returns AWS STS tokens, Azure SAS URLs, or
GCP OAuth tokens.

soyuz implements the **spec shape** for these endpoints — they accept
the right request, return the right response shape, return the right
status codes — but the implementation is a **stub**. The response
contains placeholder credential fields rather than real STS/SAS/OAuth
material.

Routes:

- `POST /temporary-table-credentials`
- `POST /temporary-volume-credentials`
- `POST /temporary-path-credentials`
- `POST /temporary-model-version-credentials`

The matching service is
[`soyuz_catalog/services/credentials_service.py`](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/services/credentials_service.py)
(plural `credentials`).

The naming collision with the Storage Credentials service is intentional
— it matches the spec's own naming. The disambiguation is in
[`soyuz_catalog/services/__init__.py`](https://github.com/FloHofstetter/soyuz-catalog/blob/main/soyuz_catalog/services/__init__.py).

## Why stub and not full implementation

A real temporary-credentials implementation would mean:

1. Embedding AWS STS, Azure AD, and GCP IAM clients in the soyuz
   process.
2. Storing the assume-role / impersonation chain configuration per
   credential.
3. Running an STS audit trail.
4. Caching tokens with refresh logic.

Each is a large surface area. More importantly, every one of them is
*cloud-specific* — there is no portable "vend a credential" abstraction
that does not collapse into per-cloud implementations.

soyuz's [README design principle 3](https://github.com/FloHofstetter/soyuz-catalog/blob/main/README.md)
("metadata only, no compute, no credential vending") rules this out by
design. The endpoint exists in stub form because:

- The shape is part of the spec — clients that round-trip metadata
  through this route need it to exist.
- A future deployment that needs real vending can plug a credential
  broker behind the route without breaking clients.

## What clients should do

For local-filesystem and single-machine deployments, no credential
vending is needed. The client reads files directly. soyuz's responses
include the storage location and the storage-credential *name*; the
client uses its own cloud SDK to authenticate.

For multi-tenant production deployments where clients should not see the
storage backend's credentials at all, run a credential broker as a
separate service. soyuz's temporary-credentials routes can be replaced
or proxied to that broker without affecting any other surface.

## Code reference

| Concern | Module |
|---|---|
| Storage Credentials CRUD | `soyuz_catalog/services/credential_service.py` |
| Temporary Credentials stubs | `soyuz_catalog/services/credentials_service.py` |
| Naming disambiguation | `soyuz_catalog/services/__init__.py` |
| External Location attachment | `soyuz_catalog/services/external_location_service.py` |

## See also

- [REST API reference: credentials](../reference/api.md) — full request/
  response shapes.
- [Spec coverage map](../reference/spec-coverage.md) — credentials row.
- [Extensions over the spec](extensions-over-spec.md) — for context on
  what soyuz adds beyond the spec.
- [Origin and relationship to Unity Catalog](origin.md) — design
  principle 3.
