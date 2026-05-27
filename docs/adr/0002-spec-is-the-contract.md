# ADR-0002: Spec is the contract

- **Status:** Accepted
- **Date:** 2026-04-14
- **Deciders:** @FloHofstetter

## Context

soyuz-catalog implements the Unity Catalog REST API. Two artifacts claim to
define what that API is:

1. The **OpenAPI YAML** at
   [`unitycatalog/api/all.yaml`](https://github.com/unitycatalog/unitycatalog/blob/main/api/all.yaml)
   — a machine-readable description of the wire contract.
2. The **UC OSS Java reference implementation** under `unitycatalog/server/`
   — the only running server most clients have ever talked to.

These disagree in several places. The most concrete examples found while
building a UI on top of UC OSS v0.4.0:

- `PATCH /catalogs/{name}` with `{"properties": {}}` is a no-op in UC OSS
  Java — there is no documented way to clear all properties at all.
- `PATCH /catalogs/{name}` with `{"owner": "..."}` returns 200 OK but
  silently ignores the `owner` field, even though `UpdateCatalog` does not
  define an `owner` field at all.
- The `Tables` resource has no update endpoint in UC OSS Java; comments,
  properties, and owner are immutable after create.

soyuz needs an explicit policy: when the spec and UC OSS disagree, which
wins?

## Decision

**The OpenAPI spec is the source of truth.** Where soyuz diverges from UC
OSS Java behaviour, it diverges *toward* the spec, never away from it.

Every divergence is recorded in `DIVERGENCES.md` at the repo root, mirrored
on the docs site, and tracked by a regression test in
`tests/test_<resource>.py`. The regression test name should make the bug
class searchable (e.g. `test_patch_empty_properties_clears`).

When the spec is itself silent or ambiguous, soyuz picks the choice that
respects replace-style PATCH semantics and rejects malformed requests
explicitly instead of silently dropping data — and that choice is also
recorded in `DIVERGENCES.md`.

## Consequences

- **Positive:** clients written against the OpenAPI spec — including
  generated code from `openapi-generator` — work against soyuz without
  per-implementation workarounds. The behaviour of the server is a function
  of one document, not of two contradictory ones.
- **Positive:** divergences are explicit, version-controlled, and testable.
  A reader can answer "why does soyuz do X?" by `grep`-ing one file.
- **Negative:** clients that rely on UC OSS Java *bugs* (e.g. assume
  `properties: {}` is a no-op) break against soyuz. We accept this cost —
  those clients are already broken, they just do not know it.
- **Negative:** soyuz cannot pass a hypothetical "matches UC OSS Java
  byte-for-byte" conformance suite. The relevant suite is the spec, not the
  reference implementation.

## Alternatives considered

- **UC OSS Java behaviour wins.** Maximises drop-in compatibility today, but
  inherits every bug we set out to fix and makes the project pointless.
- **No written policy, decide case-by-case.** Optimises for short-term
  flexibility, but every contributor would relitigate the same question and
  the divergence list would drift. Not worth the chaos.
