# Contributing to soyuz-catalog

Thank you for your interest in soyuz-catalog — a clean Python
reference implementation of the Unity Catalog REST API spec.
Contributions of all sizes are welcome.

## Before you start

By contributing, you agree that your contribution will be licensed
under the same terms as the project (Apache License, Version 2.0).
A bot will ask you to sign the Individual CLA on your first pull
request — this is a one-time step that lets the project relicense
in the future if needed.

## The non-negotiable: spec is the contract

soyuz-catalog implements the Unity Catalog OpenAPI spec at
`unitycatalog/api/all.yaml` verbatim. Where soyuz diverges from
the UC OSS Java reference, it diverges *toward* the spec, not
away from it. Documented divergences live in `DIVERGENCES.md`.

PRs that introduce new spec-divergent behaviour without explicit
discussion will be sent back for revision.

## Reporting issues

- **Bug reports** and **feature requests** go through GitHub
  Issues — pick the right template from the *New Issue* picker.
- **Security vulnerabilities** must NOT be filed as public issues.
  See [`SECURITY.md`](SECURITY.md) for the responsible-disclosure
  path.

## Development environment

soyuz-catalog is a Python 3.14 project managed with
[`uv`](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:FloHofstetter/soyuz-catalog.git
cd soyuz-catalog
uv sync
uv run soyuz-catalog       # serves http://127.0.0.1:8080
```

The generated client lives in `soyuz-catalog-client/` and is a
hatch-managed sub-project. If you change the OpenAPI surface,
regenerate the client with `bash scripts/regen_client.sh` and
commit the resulting diff.

## Local gates

```bash
uv run pytest -m 'not integration'         # unit tests
uv run pytest -m integration               # integration (needs live DB)
uv run ruff check . && uv run ruff format --check .
uv run pyright                             # type-check
uv run pydoclint soyuz_catalog             # docstring lint
bash scripts/check-spec-conformance.sh     # spec conformance gate
bash scripts/check-client-drift.sh         # generated-client drift gate
```

## Branch and commit conventions

- **Branch**: any descriptive name.
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/)
  format — `feat(scope): …`, `fix(scope): …`, etc. Scope is the
  subsystem (`schema`, `volumes`, `lineage`, `client`, `alembic`,
  `docs`, `ci`, …).

## Pull request process

1. Open a draft PR early.
2. Fill in the PR template. Tick every gate that applies.
3. If the change touches the public REST surface, regenerate the
   client and commit the diff in the same PR.
4. One reviewer signs off. CI must be green.
5. Update `CHANGELOG.md` under `## [Unreleased]` in the same PR
   whenever the change touches `soyuz_catalog/`.

## Code of conduct

Be kind. Disagree with code, not with people. The project follows
the spirit of the Contributor Covenant; the formal text will be
added before the public visibility flip.
