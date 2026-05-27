# Contributing

## Development setup

```bash
git clone https://github.com/FloHofstetter/soyuz-catalog
cd soyuz-catalog
uv sync
uv run pre-commit install --hook-type pre-commit --hook-type pre-push --hook-type commit-msg
```

## Quality gates

soyuz-catalog runs the same set of quality checks on every commit and push as
its sister project [shoreguard](https://github.com/FloHofstetter/shoreguard).

### On every commit (`pre-commit` stage)

| Tool             | What it does                                       |
|------------------|----------------------------------------------------|
| `trailing-whitespace`, `end-of-file-fixer` | File hygiene             |
| `check-yaml`, `check-json`, `check-toml`   | Syntax validation         |
| `check-merge-conflict`                     | Catch unresolved markers  |
| `check-added-large-files` (max 500 KB)     | Prevent accidental binaries |
| `detect-private-key`                       | Stop key leakage at the door |
| `ruff` (lint + format)                     | Style and import order    |
| `yamllint`                                 | YAML semantics            |
| `markdownlint-cli2`                        | Markdown style            |
| `actionlint`                               | GitHub Actions workflows  |
| `detect-secrets`                           | Secret scanning vs baseline |
| `pyright`                                  | Static type checking      |
| `pydoclint`                                | Google-style docstring linting |
| `pytest`                                   | Full test suite           |

### On every commit message (`commit-msg` stage)

| Tool                       | What it does                                  |
|----------------------------|-----------------------------------------------|
| `conventional-pre-commit`  | Reject messages not matching Conventional Commits |

The accepted types are the Angular set: `feat`, `fix`, `docs`, `style`,
`refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`. Scope is
optional but recommended (`feat(catalog): ...`).

### On every push (`pre-push` stage)

| Tool        | What it does                                 |
|-------------|----------------------------------------------|
| `pip-audit` | Scan dependencies for known vulnerabilities  |
| `bandit`    | Source-level security linter                 |
| `mkdocs build --strict` | Docs build, fail on warnings     |

Run all hooks against the full repo at any time:

```bash
uv run pre-commit run --all-files
```

## Running the tests

```bash
uv run pytest                # all tests
uv run pytest -k catalogs    # subset
uv run pytest --cov          # with coverage
```

Tests use an in-memory SQLite database via a `sessionmaker` fixture in
`tests/conftest.py`. No external services are required for the default
loop.

### Running the suite against Postgres

Postgres is a supported backend
([ADR-0004](../adr/0004-postgres-as-supported-backend.md)). The pytest
harness can re-parametrize the whole unit suite onto a real Postgres with
two commands:

```bash
docker compose up -d postgres                     # local pg 17 on :5432
uv sync --group dev --extra postgres              # pulls psycopg[binary]
uv run pytest --db-backend=postgres -m "not integration"
```

To only run the Postgres-specific smoke tests (schema inspection, BIGINT
invariant, HTTP round-trip), use the `postgres` marker:

```bash
uv run pytest -m postgres
```

Both invocations skip cleanly if the database at
`SOYUZ_TEST_POSTGRES_URL` (default
`postgresql+psycopg://soyuz:soyuz@localhost:5432/soyuz`) is unreachable,  <!-- pragma: allowlist secret -->
so forgetting to start docker does not wedge the test loop.

## Building the docs locally

```bash
uv run --group docs mkdocs serve
```

Open <http://127.0.0.1:8000>.

## Code style

- Python 3.14+, `from __future__ import annotations` everywhere.
- Google-style docstrings, enforced by `pydoclint`.
- Line length 100, enforced by `ruff`.
- Type annotations on every public function, enforced by `pyright`.
- No silent fallbacks. Validate at boundaries; trust internal code.

## Spec is the contract

The OpenAPI YAML at `unitycatalog/api/all.yaml` is the source of truth. Where
soyuz diverges from UC OSS Java behaviour, it diverges *toward* the spec, not
away from it. New divergences must be documented in
[`DIVERGENCES.md`](https://github.com/FloHofstetter/soyuz-catalog/blob/main/DIVERGENCES.md)
with a regression test.
