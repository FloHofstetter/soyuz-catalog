"""Generated OpenAPI conformance against the UC source-of-truth spec.

Exposes ``/openapi.json`` and ``/docs`` (FastAPI defaults, threaded
through a settings flag so an operator can disable them) and pairs
those with a smoke test: every ``(path, method)`` tuple soyuz
registers must appear in ``unitycatalog/api/all.yaml``.

Why path+method and not full schema conformance? Full schema diffing
needs ``$ref`` resolution, ``oneOf`` / ``allOf`` handling, and a
pydantic↔JSON-Schema crosswalk that rots on every pydantic upgrade.
Path+method catches the "route renamed / route dropped" class of bugs
that bit early development (the reference docs drifted because
nothing compared them against the spec). The SDK CRUD round-trip
matrix in ``tests/test_sdk_crud_roundtrip.py`` carries the actual
response-shape guarantee.

The subset direction matters: we check that **every soyuz path is
present in the spec**, not the reverse. The reverse would fail on
every spec-defined-but-unimplemented endpoint.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from soyuz_catalog._openapi_utils import HTTP_METHODS as _HTTP_METHODS
from soyuz_catalog._openapi_utils import normalise_path as _normalise
from soyuz_catalog.api.main import create_app
from soyuz_catalog.settings import reset_settings_cache

PREFIX = "/api/2.1/unity-catalog"


def _extract_soyuz_routes(app) -> set[tuple[str, str]]:  # noqa: ANN001
    spec = app.openapi()
    out: set[tuple[str, str]] = set()
    for path, methods in spec["paths"].items():
        for method in methods:
            if method in _HTTP_METHODS:
                out.add((path, method))
    return out


def test_openapi_json_is_served() -> None:
    with TestClient(create_app()) as client:
        r = client.get("/openapi.json")
    assert r.status_code == 200
    body = r.json()
    assert "openapi" in body
    assert "info" in body
    assert "paths" in body


def test_docs_page_is_served() -> None:
    with TestClient(create_app()) as client:
        r = client.get("/docs")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


def test_openapi_disabled_when_flag_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """With ``openapi_enabled=False`` both ``/openapi.json`` and ``/docs`` 404."""
    monkeypatch.setenv("SOYUZ_OPENAPI_ENABLED", "0")
    reset_settings_cache()
    try:
        with TestClient(create_app()) as client:
            assert client.get("/openapi.json").status_code == 404
            assert client.get("/docs").status_code == 404
    finally:
        reset_settings_cache()


def test_expected_soyuz_paths_present() -> None:
    """Generated spec contains every route soyuz claims to implement.

    Catches accidental route drops — historically the class of bug a
    reference-docs catch-up had to fix after the fact.
    """
    routes = _extract_soyuz_routes(create_app())
    expected = {
        ("/healthz", "get"),
        (f"{PREFIX}/catalogs", "get"),
        (f"{PREFIX}/catalogs", "post"),
        (f"{PREFIX}/catalogs/{{name}}", "get"),
        (f"{PREFIX}/catalogs/{{name}}", "patch"),
        (f"{PREFIX}/catalogs/{{name}}", "delete"),
        (f"{PREFIX}/schemas", "get"),
        (f"{PREFIX}/schemas", "post"),
        (f"{PREFIX}/schemas/{{full_name}}", "get"),
        (f"{PREFIX}/schemas/{{full_name}}", "patch"),
        (f"{PREFIX}/schemas/{{full_name}}", "delete"),
        (f"{PREFIX}/tables", "get"),
        (f"{PREFIX}/tables", "post"),
        (f"{PREFIX}/tables/{{full_name}}", "get"),
        (f"{PREFIX}/tables/{{full_name}}", "delete"),
        (f"{PREFIX}/volumes", "get"),
        (f"{PREFIX}/volumes", "post"),
        (f"{PREFIX}/volumes/{{full_name}}", "get"),
        (f"{PREFIX}/volumes/{{full_name}}", "patch"),
        (f"{PREFIX}/volumes/{{full_name}}", "delete"),
        (f"{PREFIX}/temporary-table-credentials", "post"),
        (f"{PREFIX}/temporary-volume-credentials", "post"),
        (f"{PREFIX}/temporary-model-version-credentials", "post"),
        (f"{PREFIX}/models", "get"),
        (f"{PREFIX}/models", "post"),
        (f"{PREFIX}/models/{{full_name}}", "get"),
        (f"{PREFIX}/models/{{full_name}}", "patch"),
        (f"{PREFIX}/models/{{full_name}}", "delete"),
        (f"{PREFIX}/models/versions", "post"),
        (f"{PREFIX}/models/{{full_name}}/versions", "get"),
        (f"{PREFIX}/models/{{full_name}}/versions/{{version}}", "get"),
        (f"{PREFIX}/models/{{full_name}}/versions/{{version}}", "patch"),
        (f"{PREFIX}/models/{{full_name}}/versions/{{version}}", "delete"),
        (f"{PREFIX}/models/{{full_name}}/versions/{{version}}/finalize", "patch"),
    }
    missing = expected - routes
    assert not missing, f"routes disappeared from soyuz: {missing}"


def test_soyuz_paths_are_subset_of_uc_spec() -> None:
    """Every soyuz (path, method) must be present in UC ``all.yaml``.

    Skipped gracefully when the upstream checkout is absent (CI, or a
    contributor who has not cloned ``unitycatalog``). Also skipped if
    ``pyyaml`` is not importable — it lives in the ``dev`` extras but
    a minimal install may not have it.
    """
    spec_path = Path.home() / "git" / "unitycatalog" / "api" / "all.yaml"
    if not spec_path.exists():
        pytest.skip(f"UC spec not found at {spec_path}")
    try:
        import yaml
    except ImportError:
        pytest.skip("pyyaml not installed")

    spec = yaml.safe_load(spec_path.read_text())
    spec_routes: set[tuple[str, str]] = set()
    for path, methods in spec.get("paths", {}).items():
        for method in methods:
            if method in _HTTP_METHODS:
                spec_routes.add((_normalise(path), method))

    soyuz_routes = _extract_soyuz_routes(create_app())
    # Strip the API prefix + normalise placeholders so the comparison is
    # apples-to-apples with the spec (whose server URL already embeds
    # the ``/api/2.1/unity-catalog`` prefix).
    soyuz_on_spec_side: set[tuple[str, str]] = set()
    for path, method in soyuz_routes:
        if path == "/healthz":
            # /healthz is a soyuz-specific liveness probe, not in the UC spec.
            continue
        if path.startswith("/lineage/"):
            # Lineage is an over-the-spec extension (ADR-0008).
            # Upstream UC OSS has no lineage API at all; these endpoints
            # live at the root (not under the UC prefix) and are
            # documented in DIVERGENCES.md under "Lineage".
            continue
        if path.startswith("/tags/"):
            # Tags are an over-the-spec extension (ADR-0010).
            # Databricks has a tags API; UC OSS / all.yaml do not. These
            # endpoints live at the root (not under the UC prefix) and
            # are documented in DIVERGENCES.md under "Tags".
            continue
        if path == "/audit-log" or path.startswith("/audit-log/"):
            # Audit log is an over-the-spec extension. Upstream UC OSS
            # has no audit surface; soyuz adds the table + GET endpoint
            # so agent-driven clients can cross-reference UC mutations
            # by ``X-Agent-Run-Id``. Documented in DIVERGENCES.md under
            # "Audit log".
            continue
        if path.startswith(f"{PREFIX}/connections"):
            # Connections + foreign catalogs are an over-the-spec
            # extension (ADR-0013). Databricks ships Lakehouse Federation;
            # UC OSS / all.yaml do not. Documented in DIVERGENCES.md
            # under "Connections and foreign catalogs".
            continue
        if path.startswith(f"{PREFIX}/metric-views"):
            # Metric views are an over-the-spec extension (ADR-0014).
            # Databricks ships a semantic layer; UC OSS / all.yaml do
            # not. Mounted under the UC prefix (like connections)
            # because metric views live in the same
            # catalog.schema.name hierarchy as tables. Documented in
            # DIVERGENCES.md under "Metric views".
            continue
        if path.startswith(f"{PREFIX}/shares"):
            # Delta Sharing management surface (ADR-0015). Databricks
            # ships shares as UC securables; UC OSS / all.yaml do not.
            # Documented in DIVERGENCES.md under "Delta Sharing".
            continue
        if path.startswith(f"{PREFIX}/recipients"):
            # Delta Sharing recipients (ADR-0015) — the bearer-token
            # identities of the protocol surface. Same posture as
            # /shares above.
            continue
        if path.startswith("/delta-sharing/"):
            # The open Delta Sharing protocol surface (ADR-0015).
            # Root-mounted like lineage because the path layout is an
            # external wire contract (PROTOCOL.md), not a UC spec
            # path. Documented in DIVERGENCES.md under "Delta
            # Sharing".
            continue
        if path.startswith(f"{PREFIX}/effective-permissions/"):
            # Effective permissions is an over-the-spec extension.
            # Upstream ``all.yaml`` defines only the direct-grant
            # ``GET /permissions/{type}/{name}`` form; soyuz adds the
            # inheritance-walking sibling as a first-class endpoint.
            # Documented in DIVERGENCES.md under "Permissions:
            # effective computation".
            continue
        if path.startswith(f"{PREFIX}/delta/v1/"):
            # Delta REST Catalog routes (ADR-0009) live in
            # ``delta.yaml``, not ``all.yaml``. They are validated
            # against that second spec file by
            # ``test_delta_rest_paths_are_subset_of_delta_yaml``
            # below. Skipping them here keeps the all.yaml subset
            # check accurate. Note the trailing slash:
            # ``/delta/preview/commits`` is NOT skipped — it lives in
            # all.yaml.
            continue
        if "/volumes/" in path and "/files" in path:
            # Volume file IO is an over-the-spec extension. Upstream
            # UC OSS / all.yaml describe only the five volume-metadata
            # endpoints; soyuz adds upload / browse / download / delete
            # under the existing ``/volumes`` root so single-node
            # deployments can store and serve files without S3.
            # Documented in DIVERGENCES.md under "Volumes: file IO".
            continue
        stripped = path.removeprefix(PREFIX)
        soyuz_on_spec_side.add((_normalise(stripped), method))

    missing = soyuz_on_spec_side - spec_routes
    assert not missing, (
        f"soyuz registers routes the UC spec does not define: {missing}. "
        "Either the spec drifted or soyuz added a non-spec endpoint — "
        "document it in DIVERGENCES.md."
    )


def test_delta_rest_paths_are_subset_of_delta_yaml() -> None:
    """Every soyuz Delta REST route must be present in ``delta.yaml``.

    Mirror of :func:`test_soyuz_paths_are_subset_of_uc_spec` for the
    secondary spec surface (ADR-0009). The Delta REST Catalog API
    is defined by ``delta.yaml``, not
    ``all.yaml``, and is mounted under ``/api/2.1/unity-catalog/delta``
    — so after stripping the UC prefix + the ``/delta`` router prefix
    the remaining path (``/v1/config``, ``/v1/catalogs/{catalog}/…``)
    should appear verbatim in ``delta.yaml``.
    """
    spec_path = Path.home() / "git" / "unitycatalog" / "api" / "delta.yaml"
    if not spec_path.exists():
        pytest.skip(f"Delta REST spec not found at {spec_path}")
    try:
        import yaml
    except ImportError:
        pytest.skip("pyyaml not installed")

    spec = yaml.safe_load(spec_path.read_text())
    spec_routes: set[tuple[str, str]] = set()
    for path, methods in spec.get("paths", {}).items():
        for method in methods:
            if method in _HTTP_METHODS:
                spec_routes.add((_normalise(path), method))

    soyuz_routes = _extract_soyuz_routes(create_app())
    soyuz_delta_side: set[tuple[str, str]] = set()
    # Only the Delta REST Catalog routes (``/delta/v1/...``) belong
    # to delta.yaml. The ``/delta/preview/commits`` endpoints live in
    # ``all.yaml`` and must not leak into this subset check.
    delta_rest_prefix = f"{PREFIX}/delta/v1"
    for path, method in soyuz_routes:
        if not path.startswith(delta_rest_prefix):
            continue
        stripped = path.removeprefix(f"{PREFIX}/delta")
        soyuz_delta_side.add((_normalise(stripped), method))

    missing = soyuz_delta_side - spec_routes
    assert not missing, (
        f"soyuz registers Delta REST routes not in delta.yaml: {missing}. "
        "Either the spec drifted or soyuz added a non-spec endpoint — "
        "document it in DIVERGENCES.md under 'Delta REST Catalog API'."
    )
