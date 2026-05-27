# ADR-0007: Generated Python client over hand-written SDK

- **Status:** Accepted
- **Date:** 2026-04-15
- **Deciders:** @FloHofstetter
- **Supersedes:** —

## Context

Three different test-client patterns were used for driving the soyuz
REST API end-to-end before this decision:

1. **Upstream `unitycatalog` Python SDK.** Drop-in for the CRUD core —
   catalog, schema, table, volume. It exists on PyPI, has its own
   release cadence, and covers the four resources most consumers touch
   first. Coverage spans every CRUD verb on those four resources
   (`tests/test_sdk_crud_roundtrip.py`).
2. **Raw `httpx` round-trips.** The upstream SDK does **not** cover
   credentials, external locations, functions, registered models, model
   versions, metastore summary, staging tables, temporary path
   credentials, or permissions. Each namespace that landed wrote its
   integration coverage as a hand-crafted `httpx.Client` sequence against
   the `live_server` fixture, accumulating eight raw-httpx round-trips
   alongside the five upstream-SDK ones in `test_sdk_crud_roundtrip.py`.
3. **delta-rs + pyspark.** Orthogonal — these tests exercise specific
   wire shapes (Delta log reads, managed-table creation through the JVM
   UC connector) that are not CRUD and do not belong in a
   generated-client surface.

The raw-httpx tests were the weak link. They cannot fail at collection
time: a namespace removed from `/openapi.json` still lets a manually
composed `http.post("/api/2.1/unity-catalog/credentials", ...)`
succeed (or, worse, return a 404 that the test happily masks with an
assertion rewrite). Field renames on the response side only surface
if the test explicitly asserts on the field — which the raw-httpx
tests sometimes did not, because they were written as "smoke" checks.
This is exactly the bug class soyuz exists to fix upstream, but inside
our own test suite we were repeating it.

A second pressure point is **consumer ergonomics**. Downstream users
who need the full soyuz surface today must either hand-write httpx
code against the URLs in `docs/reference/api.md`, or use the upstream
SDK and accept that credentials/external-locations/etc. are simply
unavailable. Neither is a credible story for a project whose
value proposition is spec fidelity.

`openapi-python-client` closes both gaps. It consumes the FastAPI
`/openapi.json` we already emit (gated on `SOYUZ_OPENAPI_ENABLED`),
emits an attrs-based typed client with one module per path × method,
and supports the GET-with-body shape that `GET /delta/preview/commits`
relies on — we verified that before committing, because historic
releases of the generator choked on GET-with-body and that was the
single risk that could have killed the decision.

A scheduled drift check (upstream `all.yaml` vs. our `/openapi.json`)
and a PyPI publishing path for the generated package are tracked
separately; this ADR only records the shape decision for the
in-tree client.

## Decision

**Ship a generated Python client as a second, additive SDK track
alongside the upstream `unitycatalog` package. Neither replaces the
other.**

Concretely:

1. **In-tree subpackage.** The generated client lives at
   `soyuz-catalog-client/` in this monorepo. It has its own
   `pyproject.toml` (hatchling, PyPI name `soyuz-catalog-client`,
   version `0.1.0`), its own `README.md`, and a single package
   directory `soyuz_catalog_client/` that is the regeneration target.
   Wired as a uv workspace member so `uv sync` at the root installs
   it editable and `uv run` picks it up without a second venv.
2. **Generation is a script, not manual work.**
   `scripts/regen_client.sh` dumps `/openapi.json` via
   `scripts/dump_openapi.py` (direct `app.openapi()` call, no uvicorn
   detour, no port allocation, deterministic) and feeds it to
   `openapi-python-client generate --meta=none`. The `--meta=none`
   flag means the generator only writes the package directory; the
   hand-maintained `pyproject.toml` and `README.md` sit at the
   subpackage root and are **outside** the drift check.
3. **Post-hooks pinned explicitly.** The default post-hooks run
   `ruff check --fix` and `ruff format` inside the generated
   directory, which picks up the root `pyproject.toml`'s ruff config
   and formats inconsistently between local dev and CI. The
   `.openapi-python-client.yaml` config file pins post-hooks to
   `ruff check --isolated --select=I --fix-only` and
   `ruff format --isolated`, so formatting is reproducible across
   machines regardless of local ruff settings.
4. **Drift is the enemy, gate it.** `scripts/check_client_drift.sh`
   regenerates into a tmp directory and diffs the result against
   the committed package. It runs as the `client-drift` CI job on
   every PR and as a pre-push pre-commit hook. Same rule that applies
   to `docs/reference/api.md`: if the committed client disagrees with
   the live `/openapi.json`, the build fails with a readable diff.
5. **Upstream SDK stays for the CRUD core.**
   `tests/test_sdk_crud_roundtrip.py` keeps its five upstream-SDK
   round-trips (catalog / schema / table / volume, plus the
   `table.update` absence regression). They are cheap, they prove
   the drop-in story for the most common case, and they would gain
   nothing from being rewritten against a generated client that
   calls the same endpoints.
6. **Every raw-httpx round-trip moves to the generated client.**
   `tests/test_generated_client_roundtrip.py` holds the 10 tests
   (8 namespaces + 2 extra parametrised variants) that used to be
   raw-httpx in `test_sdk_crud_roundtrip.py`. The `from
   soyuz_catalog_client.api.<ns>` imports at module top fail at
   pytest-collection time if a namespace is missing from the
   generated client, which is exactly the completeness lackmus
   the raw-httpx tests could not provide.

### Exit ramp

The decision is reversible. If the generator's coverage turns out
to be materially worse than the upstream SDK for the CRUD core —
or if the drift-gate churn outweighs the coverage gain — the
workspace member can be dropped, the regen scripts deleted, the
`test_generated_client_roundtrip.py` module rewritten against
either raw httpx or a future upstream-SDK release, and this ADR
marked **Superseded**. No ORM change, no migration, no wire-shape
dependency.

## Consequences

**1. Completeness lackmus.** A namespace removed from
`/openapi.json` fails the `client-drift` job immediately, and any
test that imports the removed namespace fails at pytest collection
before a single assertion runs. This closes the silent-regression
hole that the raw-httpx pattern had.

**2. No coverage lost.** The unit tests under
`tests/test_{credentials,external_locations,functions,registered_models,
metastore_summary,staging_tables,permissions,temporary_credentials}.py`
still pin the full wire shape against soyuz' own Pydantic schemas
via `TestClient`. The integration tests were never the only
contract tests; they were smoke checks on top of unit coverage.
The migration to `test_generated_client_roundtrip.py` preserves
the smoke-check layer with stricter typing.

**3. Two-track dev experience.** `tests/_sdk.py` (upstream SDK
wrapper) and `tests/_generated_client.py` (generated client
wrapper) both exist. New tests picking a side is a judgement call
per namespace: use the upstream SDK only when it actually owns the
namespace; use the generated client otherwise. The `README.md` of
`soyuz-catalog-client/` documents the rule for downstream
consumers.

**4. GET-with-body works.** The `openapi-python-client` 0.28.3
release we pinned emits the `GET /delta/preview/commits` module
without complaint — it serialises the request body into the
httpx call's `json=` kwarg even on a GET verb. Validated by
inspecting the generated
`api/delta_commits/get_commits_api_...get.py` module and by running
`soyuz_catalog_client.api.delta_commits.get_commits_....sync(...)`
against a live server during development. Fallback path
(manual override or post-gen patch) was not needed.

**5. Regen is a dev step, not a CI step.** Developers who change
`soyuz_catalog/api/` or `soyuz_catalog/api/schemas.py` must run
`bash scripts/regen_client.sh` and commit the result. The pre-push
hook reminds them if they forget; the CI `client-drift` job is the
hard gate on merges. This adds one extra step to the PR flow, in
exchange for making drift impossible to ship.

**6. No PyPI release in scope here.** `soyuz-catalog-client` is
installable from the monorepo but not yet published. Whether and when
to ship it on PyPI is a separate release-engineering decision.

**7. Five files under `scripts/` are now script-rather-than-module.**
`dump_openapi.py` is the only Python; `regen_client.sh` and
`check_client_drift.sh` are bash. No `justfile` is introduced —
the plan originally called for one, but `just` is not in the
default dev stack and forcing an extra tool purely for two
convenience aliases was not worth the friction. Bash scripts under
`scripts/` match the existing `scripts/check_*.py` pattern the
pre-commit hooks already use.
