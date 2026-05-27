# Origin and relationship to Unity Catalog

soyuz-catalog is a Python reimplementation of the
[Unity Catalog](https://github.com/unitycatalog/unitycatalog) REST API. This
page explains what that means, why a second implementation exists, and who
the project is — and is not — for.

## What Unity Catalog is

Unity Catalog (UC) is an open table-metadata service published by
Databricks. At its core it is two artifacts:

- An **OpenAPI document** — [`unitycatalog/api/all.yaml`](https://github.com/unitycatalog/unitycatalog/blob/main/api/all.yaml)
  — defining a REST contract for catalogs, schemas, tables, volumes,
  functions, models, grants, credentials, and a few auxiliary resources.
- A **Java reference server** under `unitycatalog/server/` that implements
  the contract on top of Hibernate.

Compute engines (Spark, Trino, delta-rs, MLflow) call the REST API to ask
*"where does table X live, what schema does it have, what format is it
in?"*. They then read the files themselves. UC never sits in the data
path — it is metadata only.

## What the spec says vs what the Java server does

The OpenAPI document is the spec. The Java server is a *behaviour
reference*, not an authority. In practice the two have drifted: several
endpoints implement only part of the spec or behave inconsistently with
the JSON shapes the spec declares.

Documented examples (see [Divergences](../divergences.md) for the full
list, each pinned by a regression test):

- `PATCH /catalogs/{name}` with `{"properties": {}}` is a **no-op** in
  UC OSS Java rather than clearing properties as replace-style PATCH
  semantics would imply. There is no documented way to clear all
  properties without dropping and recreating the catalog.
- `PATCH /catalogs/{name}` with `{"owner": "..."}` returns `200 OK` in
  UC OSS Java but **silently ignores** the owner field.
- The Tables resource has no spec-defined `PATCH`, and the Java server
  matches — but several callers expect a `405 Method Not Allowed` for
  unsupported verbs and instead get a `404` because the route simply does
  not exist.

These are not deal-breakers for engines that only do lookups, but they
make UC OSS Java unsuitable as the backend for **interactive metadata
management** — exactly the use case where a clean implementation pays for
itself.

## Why a Python reimplementation

Three reasons, in order of importance.

1. **The Python data ecosystem is the largest UC client population.**
   delta-rs, MLflow, the official `unitycatalog` SDK, OpenLineage producers,
   and most data-platform tooling speak Python first. A server written in
   the same language collapses the integration distance — debugging, type
   stubs, packaging, deployment all share one toolchain.

2. **Spec-conformance is the contract.** soyuz treats the OpenAPI document
   as authoritative. Where the Java server deviates, soyuz diverges
   *toward* the spec. See [Spec is the contract](spec-is-the-contract.md)
   for how that is enforced day-to-day, and [ADR-0002](../adr/0002-spec-is-the-contract.md)
   for the formal decision.

3. **Extensions that real clients expect.** Databricks-aware clients expect
   tags, lineage, table constraints, and connections (Lakehouse Federation)
   even though those surfaces are not in the open spec. soyuz mirrors the
   Databricks-side shape so the clients work end-to-end, while being
   explicit about which routes are spec and which are extensions. See
   [Extensions over the spec](extensions-over-spec.md).

## Who soyuz is for

| Persona | Fit |
|---|---|
| Building a metadata UI or admin tool against UC | ✅ Strong fit — soyuz is what UC OSS Java would be if PATCH semantics were taken seriously. |
| Running a small/medium lakehouse with Spark + Delta + Python | ✅ Strong fit — Postgres backend, audit log, no JVM dependency. |
| Need cloud credential vending for STS/SAS/OAuth tokens | ❌ Out of scope — soyuz is metadata-only by design. Use a dedicated credential broker or wait for the production Databricks UC. |
| Need a fully managed multi-region UC | ❌ Out of scope — soyuz is a single-process server. Use Databricks UC. |
| Want to learn what UC actually is | ✅ The reference Java server's source tree is the canonical text, soyuz is the *clean* example. |

## The name

*Soyuz* (Russian Союз, "union") is the Russian crewed spacecraft that has
been in continuous service since 1967. Solid, unglamorous, just keeps
flying. That is the bar for this project.

## See also

- [Spec is the contract](spec-is-the-contract.md) — how spec-conformance
  is enforced.
- [Architecture](architecture.md) — how a request flows through soyuz.
- [Spec coverage map](../reference/spec-coverage.md) — which spec
  endpoints are implemented.
- [Divergences](../divergences.md) — exact behaviour differences from
  the Java reference, with rationale.
- [ADR-0002](../adr/0002-spec-is-the-contract.md) — the decision that
  the spec, not the Java server, is the contract.
