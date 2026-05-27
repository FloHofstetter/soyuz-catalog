"""Shared non-fixture helpers for Spark integration tests.

This module hosts the plain constants and functions that the Spark test
modules need at import time — things that must be importable normally
without dragging the pytest plugin machinery along. Keeping them
separate from :mod:`tests._spark_fixtures` (which is loaded via
``pytest_plugins = ("tests._spark_fixtures",)``) avoids a chicken-and-
egg: if a test module imported a helper from the fixture module before
listing it in ``pytest_plugins``, pytest would already have the module
in ``sys.modules`` and emit
``PytestAssertRewriteWarning: Module already imported so cannot be
rewritten``. Splitting helpers out dodges the warning entirely.
"""

from __future__ import annotations

import httpx

CONNECTOR_PACKAGES = "io.delta:delta-spark_2.13:4.0.0,io.unitycatalog:unitycatalog-spark_2.13:0.3.0"
"""Maven coordinates for the Delta + UC Spark connectors.

Pinned to a single validated combo. Bumping either version is a
Spark-compatibility-affecting change and should be done as an
explicit decision, not as drive-by maintenance.
"""

CATALOG_NAME = "soyuz"
"""Catalog name used throughout the Spark fixtures and test modules.

Exported as a constant so test modules parametrise SQL statements
against a single source of truth — renaming the catalog is a one-line
change here.
"""


def bootstrap_catalog(base_url: str, storage_root: str, schema_name: str) -> None:
    """Seed the shared catalog plus a test-scoped schema via raw httpx.

    The module-scoped live server persists state across tests, so the
    catalog is created once (409 on subsequent calls is swallowed) and
    each test brings its own unique schema to isolate its tables.
    Spark's ``CREATE SCHEMA`` would also work — the connector maps it
    to ``POST /schemas`` — but seeding from the test driver keeps the
    arrange/act/assert boundary clean: a failure in the Spark SQL parse
    phase can never be mistaken for a soyuz bug.

    Args:
        base_url: ``http://127.0.0.1:<port>`` live-server base URL.
        storage_root: ``file:///...`` root to attach to the catalog
            so the storage-URI gate accepts the create. Ignored if
            the catalog already exists.
        schema_name: Schema name to create under the shared catalog.
            409 is swallowed so the helper is idempotent across runs.
    """
    api = f"{base_url}/api/2.1/unity-catalog"
    r = httpx.post(f"{api}/catalogs", json={"name": CATALOG_NAME, "storage_root": storage_root})
    assert r.status_code in (200, 409), r.text
    r = httpx.post(
        f"{api}/schemas",
        json={"name": schema_name, "catalog_name": CATALOG_NAME},
    )
    assert r.status_code in (200, 409), r.text
