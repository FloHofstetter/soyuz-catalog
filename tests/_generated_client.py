"""Shared helper for integration tests that drive the generated client.

Per ADR-0007: ``soyuz-catalog-client`` is the generated Python
client for the soyuz REST API. It exists alongside the upstream
``unitycatalog`` SDK (see :mod:`tests._sdk`) as a second, additive
track — this helper is the single call site so the drop-in point is
trivial if the generator's constructor surface ever changes.

The leading underscore prevents pytest from collecting the module.
"""

from __future__ import annotations

from soyuz_catalog_client import Client


def make_generated_client(live_server: str) -> Client:
    """Return a generated-client instance pointed at a live server.

    Args:
        live_server: Base URL of a running soyuz-catalog server (as
            produced by the ``live_server`` fixture).

    Returns:
        Client: A configured ``soyuz_catalog_client.Client``. soyuz has
            no auth layer, so the unauthenticated variant is correct —
            using ``AuthenticatedClient`` would require a bearer token
            soyuz would then ignore.
    """
    return Client(base_url=live_server, raise_on_unexpected_status=True)
