# Changelog

All notable changes to soyuz-catalog are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- `DELETE /schemas/{name}?force=true` and
  `DELETE /catalogs/{name}?force=true` drop child tables via the ORM
  cascade but skipped the FK-free `table_constraints` side table that
  `delete_table` cleans up explicitly — leaving unreachable orphan
  rows behind. Both cascade paths now call the new
  `constraints_service.delete_constraints_for_tables` bulk hook
  (single `DELETE ... WHERE table_id IN (...)`).
- `POST /delta/preview/commits` carrying both `commit_info` and
  `latest_backfilled_version` documents that the registered commit's
  persistence does not depend on the prune half of the request — but
  the write path only flushed, so a prune rejection (e.g.
  `latest_backfilled_version` past the new latest) rolled the
  freshly-registered row back with the request session. The write
  path now commits before the prune path runs, matching the
  documented contract.
- The `Settings.model_artifact_root` docstring still described the
  default as "cwd-relative" after the default paths were anchored to
  the repository root. Docstring only — no behaviour change.

### Added

- Mutation-testing harness (mutmut 3.x): `[mutmut]` config in
  `setup.cfg` scoped to the unit-tested seams (`services/`,
  `storage/`, `pagination.py`), a `scripts/mutation/run_mutmut.py`
  wrapper that hardens the generated trampoline and caps workers at
  `cpu_count // 2`, a committed kill-count baseline with
  `snapshot_baseline.py` diffing, a known-equivalent survivor
  allowlist, a PR-incremental gate
  (`scripts/check-mutation-budget.sh`) that mutates only the changed
  modules, and an informational nightly full sweep
  (`.github/workflows/mutation-nightly.yml`).

## [0.2.0] - 2026-06-08

### Fixed

- GitHub Pages was serving the raw markdown in `docs/` via the legacy
  Jekyll build instead of the mkdocs-material site, so none of the
  hero, grid-cards, content-tabs, or mermaid diagrams rendered on
  `flohofstetter.github.io/soyuz-catalog`. Added `.github/workflows/docs.yml`
  that builds `mkdocs build --strict` and deploys via the official
  `actions/upload-pages-artifact` + `actions/deploy-pages` pair, and
  flipped the Pages source from `branch=main, path=/docs` (legacy) to
  `build_type=workflow` (GitHub Actions).
- Postgres `unit (postgres)` CI lane failed on `tests/test_lineage.py`
  with `DatatypeMismatch: recursive query "walk" column 1 has type
  text in non-recursive term but type character varying overall`.
  The non-recursive seed of the lineage-traversal CTE bound `:root`
  as `text` (psycopg's default for Python `str`), while the recursive
  term supplied `character varying` from `lineage_edges`. Added an
  explicit `CAST(:root AS VARCHAR)` so the two terms agree.
  SQLite uses type-affinity so the cast is a no-op there.

### Added

- Documentation quality pass for the OSS release. Four new concept
  pages give each previously-thin over-the-spec feature a canonical
  semantic home (table constraints, audit log, volume files, plus
  keyset pagination as a cross-cutting concern); two new HTTP
  walkthroughs (declared constraints, querying the audit log) cover
  the previously walkthrough-less extensions; and
  `reference/settings.md` is expanded from a one-line mkdocstrings
  stub into a curated env-var reference table with the mkdocstrings
  block kept underneath as drift guard. Effective permissions is
  now listed explicitly in the spec-coverage extensions table and
  gets its own section in `extensions-over-spec.md` — previously
  folded into the permissions row, which obscured that the dedicated
  route is over-spec. `extensions-over-spec.md` is reshaped into an
  index: each sub-section is one paragraph that delegates to the
  appropriate concept page, walkthrough, or ADR, and the opener
  leads with the answer (eight extensions, ADR-anchored,
  prefix-isolated) rather than the setup. `admin/observability.md`
  drops the duplicate "what is covered / not covered" prose and
  points to the audit-log concept page; the operator-facing
  fields-table, curl examples, and forensics walkthrough stay.
  `concepts/index.md` is split into a linear reading path and a
  topic-deep-dive set so the new pages join without expanding the
  required-reading list.
- OpenAPI metadata polish for the upcoming OSS release: `info.contact`,
  `info.license` (Apache-2.0), a fleshed-out `info.description` with
  ADR backlinks, and `info.version` now read dynamically from the
  installed package metadata via `importlib.metadata` so the live
  spec tracks `pyproject.toml` without manual sync (the hardcoded
  literal had already drifted to `"0.1.0"` versus the actual
  `0.2.0rc4`). 20 grouped `openapi_tags` with one-line descriptions
  per resource — UC core, UC extensions (lineage, tags, audit,
  effective-permissions, connections), Delta surfaces, and
  operational — and `summary=` on all 83 route operations so
  Swagger/ReDoc render a scannable endpoint list instead of bare
  HTTP method + path. The lone PascalCase `DeltaCommits` tag is
  normalised to `delta-commits` to match the rest of the kebab-case
  tag set.

### Changed

- README second heroic pass — replaced the stock satellite hero with a
  banner-shaped terminal SVG (`docs/assets/demo.svg`, ~4 KB, 1000×277)
  generated via `asciinema` + `svg-term-cli --at` (single static
  frame at the recording's end timestamp, not an animation). The
  banner shows soyuz booting on SQLite + alembic-head and
  `POST /catalogs {"name":"sales"}` returning a spec-shaped JSON
  body. Static was chosen over animated after the first push showed
  the animated SVG had a dead lower half on GitHub: at most loop
  positions the bottom rows were empty terminal background, which
  read as a giant black void below the demo. The static end-frame
  has every line visible immediately, no animation policy quirks
  across GitHub dark mode / Camo proxy / browser SVG handling.
  Recording is reproducible via the committed `scripts/record_demo.sh`.
  The satellite
  hero (`docs/assets/hero.webp`) stays on the mkdocs frontpage but is no
  longer referenced from the README. The marketing stats row (`14 / 8 /
  0 / MIT`) and the 3-cell emoji value grid are gone, replaced by a
  single centered `> Spec-first. JVM-free. Drop-in.` pull-quote — an
  earlier draft also shipped a 22-chip spec-coverage strip (14 core +
  8 extensions) under the pull-quote, but the chips read as a hobbyist
  shields.io collection and were redundant with the `Spec-conformance`
  section's "14/14 implemented" bullet linking the canonical
  `docs/reference/spec-coverage.md`, so they were dropped. The `Why
  this exists` prose-bullets became a 3-row side-by-side divergence
  table
  (`<table>` + `<pre>` cells): UC OSS Java behaviour vs soyuz behaviour
  for `PATCH /catalogs {"properties":{}}`, `PATCH /catalogs {garbage:1}`,
  and `POST /tables` with garbage in a column — each row sourced from
  `DIVERGENCES.md`. A new `Spec-conformance` section gives three linked
  proofs (14/14 coverage, the spec-drift CI gate, regression tests per
  divergence). `Works with these clients` switched from a 5-cell emoji
  table to a 6-badge row using `shields.io` `for-the-badge` shields with
  embedded `simple-icons` brand logos (Apache Spark, delta-rs, MLflow,
  FastAPI, Pydantic, SQLAlchemy) — no logo files committed, no licence
  attribution required. `Quick start` moved above `Why this exists`
  (action before context) and the launch command corrected to
  `uv run uvicorn soyuz_catalog.api.main:app --reload` on port 8000 to
  match `docs/getting-started/quickstart.md`. Design principles,
  documentation index, project artifacts, and contributing / security /
  license footer unchanged.
- Pre-OSS hygiene pass: removed internal sprint / phase / bug-tracker
  identifiers from docstrings and inline comments in
  `soyuz_catalog/storage/volume_files.py`,
  `soyuz_catalog/api/routes/volume_files.py`,
  `soyuz_catalog/services/catalog_service.py`,
  `soyuz_catalog/settings.py`, the matching
  `tests/test_volume_files.py` + `tests/test_settings_paths.py`,
  the `Phase-1` reference in `docs/adr/0003-keyset-pagination.md`,
  and the pip-audit comment in `.pre-commit-config.yaml`. Behaviour
  unchanged — the affected docstrings describe the same code, just
  without the private milestone names.
- Native UX overhaul of the documentation site. Three markdown
  extensions (`attr_list`, `md_in_html`, `pymdownx.emoji`) plus a
  `pymdownx.superfences` mermaid fence are enabled in `mkdocs.yml` —
  zero new Python dependencies, `mkdocs-material>=9.6` already ships
  the underlying primitives. The frontpage gains a 3-card hero
  (spec-conformant / metadata-only / eight extensions) and a button
  CTA row above the existing prose. Five section landings (concepts,
  guides, admin, integrations, plus the extensions-over-spec index)
  become grid-card layouts with a consistent material-icon palette.
  Five concept pages gain topic-appropriate mermaid diagrams: the
  securables hierarchy (replacing the ASCII tree), the Delta
  passthrough commit sequence, the permission inheritance walk, the
  three-gate spec-drift flow, and the lineage traversal direction.
  Four targeted admonitions surface previously-prose-buried sharp
  edges (no enforcement, single-node-only volume files, best-effort
  audit writes, the `uv run` rationale).
- Frontpage gains three additive native-primitive sections between the
  CTA buttons and the existing prose: a four-tile stats row (14
  resources, 8 extensions, 0 silently-dropped fields, MIT pure-Python),
  a content-tabbed "Try it" code showcase (cURL / Python SDK / Spark
  SQL), and a five-card compatibility teaser linking into the
  integrations index. CSS-only via `.soyuz-stats` in
  `docs/stylesheets/hero.css`, uses mkdocs-material palette variables
  for dark/light parity.
- README hero pass — the GitHub README mirrors the docs site's heroic
  frontpage with GitHub-native primitives: a centered hero banner
  reusing `docs/assets/hero.webp`, a four-shield badge row (Python,
  Apache-2.0, tests CI, spec-drift gate), a 4-column stats table
  (14 / 8 / 0 / MIT), a 3-cell value grid (spec-conformant /
  metadata-only / eight extensions), a "Try it" block with cURL
  up-front and Python SDK + Spark SQL behind `<details>` toggles,
  and a 5-cell compatibility teaser. Existing "Why this exists" prose
  trimmed from ~250 to ~150 words; design principles, Python clients,
  documentation index, and footer boilerplate unchanged.
- Introduced two transaction context managers in
  `soyuz_catalog.db` and migrated the 20 most common write sites
  across 13 service modules: `commit_or_conflict(session, message)`
  collapses the recurring `add → try/commit/except IntegrityError →
  rollback → raise ConflictError` pattern into one `with`, and
  `commit_or_raise(session)` covers the three race-tolerant sites
  (permissions, tags, lineage) that re-raise IntegrityError so the
  client can retry. Delete-path bare commits and the multi-step
  Delta-commit / metastore-bootstrap outliers are intentionally left
  unchanged.
- Test suite: replaced 15 `time.sleep(0.002)` keyset-disambiguation
  sleeps across 10 test files with a single autouse
  `deterministic_clock` fixture that monkeypatches
  `soyuz_catalog.models._base._epoch_ms` with a monotonic
  millisecond counter. End-to-end pytest now runs ~30 ms faster per
  affected file and is deterministic across re-runs (no more
  millisecond-collision flakes on fast hardware).
- Split `soyuz_catalog/models.py` (1263 lines, 24 classes) into a
  `soyuz_catalog/models/` subpackage with one submodule per domain
  (catalog, column, credentials, federation, governance, lineage,
  metastore, ml, staging) plus a `_base.py` for shared SQLAlchemy
  plumbing. The top-level `__init__.py` re-exports every public
  symbol, so existing `from soyuz_catalog.models import …` imports
  keep working without change.
- Consolidated nine duplicate `_now_ms` definitions in the service
  layer onto the single canonical helper in
  `soyuz_catalog.models._base`. The new `_epoch_ms` indirection is
  the seam a test-time deterministic-clock fixture can monkeypatch
  to cover both column defaults and service-layer `updated_at`
  writes.

## [0.1.0] — 2026-05-27

### Added

- Initial OSS release of soyuz-catalog — a Python reimplementation of
  the Unity Catalog REST API.
- Full coverage of the upstream `unitycatalog/api/all.yaml` surface:
  catalogs, schemas, tables, columns, volumes, functions, registered
  models, model versions, metastore summary, staging tables, storage
  credentials, external locations, temporary credentials (stub),
  permissions, and Delta commits preview.
- Delta REST Catalog secondary surface (`/delta/v1/...`) translating
  the upstream `delta.yaml` against the same storage as the main UC
  REST API. See [ADR-0009](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0009-delta-rest-catalog-as-secondary-surface.md).
- Passthrough Delta commit coordinator for `file://` tables. See
  [ADR-0011](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0011-delta-commit-coordinator.md).
- Over-the-spec extensions:
  - OpenLineage ingest + traversal
    ([ADR-0008](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0008-openlineage-as-lineage-contract.md)).
  - Tags on catalogs / schemas / tables / columns
    ([ADR-0010](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0010-tags-as-extension.md)).
  - Declared table constraints (PK / FK / CHECK / named NOT NULL)
    ([ADR-0012](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0012-table-constraints.md)).
  - Lakehouse Federation connections and `type=FOREIGN` catalogs
    ([ADR-0013](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0013-connections-and-foreign-catalogs.md)).
  - Effective permissions traversal endpoint.
  - Audit log read API.
- Generated Python client (`soyuz-catalog-client`) via
  openapi-python-client. See
  [ADR-0007](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0007-generated-client-over-hand-written-sdk.md).
- FastAPI + SQLAlchemy 2.0 (sync) + Alembic + Pydantic v2 stack
  ([ADR-0001](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0001-stack-and-conventions.md)). SQLite for
  development, Postgres for production
  ([ADR-0004](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0004-postgres-as-supported-backend.md)).
- Keyset pagination on every list endpoint
  ([ADR-0003](https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0003-keyset-pagination.md)).
- Spec-conformance regression suite plus a recurring spec-drift gate
  comparing upstream `all.yaml` against a committed baseline.
- Documentation site (mkdocs-material) at `docs/`, covering concepts,
  guides, walkthroughs, admin runbooks, and integrations.

[Unreleased]: https://github.com/FloHofstetter/soyuz-catalog/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/FloHofstetter/soyuz-catalog/releases/tag/v0.1.0
