# JVM unitycatalog client

The
[`unitycatalog-client`](https://github.com/unitycatalog/unitycatalog/tree/main/clients/java)
project ships an official Java client alongside Unity Catalog OSS. It
targets the spec routes; soyuz speaks the same wire contract, so the
client works without modification.

This page is the integration note: what works, what does not, how to
configure the client to point at soyuz.

## Setup

The client is on Maven Central:

```xml
<dependency>
    <groupId>io.unitycatalog</groupId>
    <artifactId>unitycatalog-client</artifactId>
    <version>0.4.0</version>
</dependency>
```

Pointing it at soyuz is one line:

```java
ApiClient client = new ApiClient();
client.setBasePath("http://localhost:8000/api/2.1/unity-catalog");

CatalogsApi catalogs = new CatalogsApi(client);
CatalogInfo info = catalogs.createCatalog(
    new CreateCatalog().name("sales").comment("sales-domain")
);
```

Authentication is bearer-token via `client.setBearerToken("...")`. soyuz
has no auth surface; production deployments terminate auth at the proxy
in front of soyuz.

## What works

Every resource the JVM client knows about is implemented in soyuz:

- `CatalogsApi`
- `SchemasApi`
- `TablesApi`
- `VolumesApi`
- `FunctionsApi`
- `RegisteredModelsApi`
- `ModelVersionsApi`
- `GrantsApi` (permissions)
- `TemporaryCredentialsApi` (returns stub shape — see below)
- `MetastoresApi`

CRUD operations round-trip cleanly. The
`tests/test_sdk_crud_roundtrip.py` suite — which uses the upstream
Python `unitycatalog` client, generated from the same spec as the JVM
client — pins this.

## What requires attention

**Temporary credentials return a stub.** soyuz implements the spec
shape for `POST /temporary-table-credentials` and friends, but the body
is a placeholder rather than real STS/SAS/OAuth tokens. A JVM client
that expects real credentials and tries to use them will fail at the
cloud SDK call. See [Concepts → Credentials](../concepts/credentials.md)
for the design rationale and how to plug in a credential broker.

**`extra="forbid"` rejects unknown fields.** soyuz refuses request
bodies with fields not defined in the spec; the JVM client only sends
spec fields, so this should not bite — but custom builders or manual
JSON construction might. If you see a `422` with `extra_forbidden`, the
client is sending something it should not.

**Spark connector caveats** apply separately — see
[Apache Spark integration](spark.md) for the JVM-Spark-specific
limitations like `ALTER TABLE` not being implemented in the connector.

## Extensions are not in the client

The JVM client is generated against the upstream UC OpenAPI document,
which does not include soyuz's over-the-spec extensions (tags, lineage,
audit log, connections). To call those endpoints from Java:

- Use a generic HTTP client (`HttpClient` from JDK 11+, or OkHttp) and
  hit the route directly.
- Or generate a second client against soyuz's own `/openapi.json`. The
  OpenAPI Generator project supports Java targets; the pattern is
  identical to what [`soyuz-catalog-client/`](python-sdk.md) does for
  Python.

Pull requests upstream to add these resources to the JVM client are out
of scope — they would only make sense if the upstream spec adopted the
extensions.

## When to use the JVM client

- Existing Java/Scala codebase that already speaks Unity Catalog.
- Spark integration where the Spark connector handles most calls but
  you need direct catalog access for setup, metadata management, or
  governance tooling.
- Integration testing soyuz against a non-Python client to catch
  Java-side serialization quirks.

## When the Python SDK fits better

- New code starting from scratch.
- Need to drive the over-the-spec routes (tags, lineage, connections,
  audit log).
- No existing JVM toolchain to amortise.

See [Python SDK](python-sdk.md) for the in-tree generated Python client.

## See also

- [Apache Spark integration](spark.md) — the most common JVM consumer.
- [Concepts → Credentials](../concepts/credentials.md) — why temporary
  credentials are a stub.
- [REST API reference](../reference/api.md) — the contract the JVM
  client is generated against.
- [unitycatalog Java client source](https://github.com/unitycatalog/unitycatalog/tree/main/clients/java)
