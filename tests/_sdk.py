"""Shared helpers for integration tests that drive the `unitycatalog` SDK.

The Stainless-generated SDK on PyPI (0.0.1-alpha at the pinned version)
constructs its default ``httpx.Client`` with the ``proxies=`` kwarg, which
was removed in httpx >=0.28. Passing a pre-built ``httpx.Client`` via
``http_client=`` side-steps the incompatible code path without forcing a
global httpx downgrade for the rest of the suite.

This module keeps that workaround in one place so every integration test
imports the same construction — drop it here, once, if upstream ships a
real fix. The leading underscore in the filename prevents pytest from
collecting it as a test module.
"""

from __future__ import annotations

import httpx
from unitycatalog import Unitycatalog


def make_uc_client(live_server: str) -> Unitycatalog:
    """Return an SDK client pointed at a live soyuz-catalog process.

    Args:
        live_server: Base URL of a running soyuz-catalog server (as
            produced by the ``live_server`` fixture).

    Returns:
        Unitycatalog: A configured SDK client. The bearer token is a
            placeholder — soyuz has no auth layer today, so any
            non-empty value is accepted.
    """
    return Unitycatalog(
        base_url=f"{live_server}/api/2.1/unity-catalog",
        default_headers={"Authorization": "Bearer not-a-real-token"},
        http_client=httpx.Client(),
    )
