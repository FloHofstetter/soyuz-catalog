# Installation

soyuz-catalog is a Python application managed with
[`uv`](https://docs.astral.sh/uv/). Installation is two commands.

## Requirements

- Python 3.14 or newer.
- `uv` for dependency management. Install instructions:
  [docs.astral.sh/uv/getting-started/installation](https://docs.astral.sh/uv/getting-started/installation/).
- A C toolchain is **not** required — soyuz has no compiled dependencies.

The default SQLite backend needs no further setup. For Postgres, see
[Backends](../admin/backends.md).

## Install from source

```bash
git clone https://github.com/FloHofstetter/soyuz-catalog
cd soyuz-catalog
uv sync
```

`uv sync` resolves the lockfile, creates a virtual environment under
`.venv/`, and installs every runtime dependency. The first run takes a
minute or two; subsequent runs are seconds.

## Optional extras

soyuz ships a couple of optional extras for integration testing. None are
needed for the server itself.

```bash
# Spark compatibility tests (needs JVM + pyspark)
uv sync --group spark

# Documentation site (needs mkdocs + plugins)
uv sync --group docs
```

If you are only running soyuz, ignore both.

## Verify the install

```bash
uv run python -c "import soyuz_catalog; print('ok')"
```

If that prints `ok`, the install is complete. Continue to
[Quickstart](quickstart.md) to start the server and make your first
request.

## See also

- [Quickstart](quickstart.md) — start the server and exercise it.
- [First catalog](first-catalog.md) — a guided end-to-end tour.
- [Backends (SQLite vs Postgres)](../admin/backends.md) — when to switch.
- [Deployment](../admin/deployment.md) — production process model.
