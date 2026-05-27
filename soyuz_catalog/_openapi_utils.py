"""Shared helpers for OpenAPI path introspection.

Extracted from :mod:`tests.test_openapi_conformance` so both the
conformance test and the spec-drift checker (``scripts/check_spec_drift.py``)
share one canonical definition of "what counts as a comparable route".
Keeping the HTTP method
whitelist and the path-parameter normaliser in one place means a spec-shape
change (e.g. upstream starting to emit ``trace`` operations) only needs a
single edit.

This module is intentionally import-light: no FastAPI, no SQLAlchemy, no
network. The drift script imports it without triggering the full app.
"""

from __future__ import annotations

import re

HTTP_METHODS = frozenset({"get", "post", "patch", "delete", "put"})
"""OpenAPI operation keys we treat as real HTTP methods.

Excludes ``parameters``, ``summary``, ``description`` and the ``trace`` /
``head`` / ``options`` verbs — none of which soyuz or upstream UC emit today.
"""

_PARAM_RE = re.compile(r"\{[^}]+\}")


def normalise_path(path: str) -> str:
    """Collapse path-parameter placeholders to a neutral ``{}`` token.

    OpenAPI-generator chains do not guarantee that placeholder *names* match
    between soyuz and the upstream spec — soyuz uses ``{full_name}`` on
    volumes where the spec uses ``{name}`` — but the shape of the path
    (segment count, prefix, position of the parameter) is what actually
    matters for routing. Replacing every ``{…}`` with ``{}`` lets subset and
    drift checks focus on shape rather than incidental parameter names.

    Args:
        path: A raw OpenAPI path template, e.g. ``/catalogs/{name}``.

    Returns:
        str: The path with every ``{param}`` collapsed to ``{}``.
    """
    return _PARAM_RE.sub("{}", path)
