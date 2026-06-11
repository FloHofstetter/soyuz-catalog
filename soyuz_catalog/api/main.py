"""FastAPI application entry point for soyuz-catalog."""

from __future__ import annotations

import importlib.metadata
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from soyuz_catalog.api.error_envelope import envelope, flatten_validation_message
from soyuz_catalog.api.middleware import RequestIDMiddleware
from soyuz_catalog.api.routes.audit import router as audit_router
from soyuz_catalog.api.routes.catalogs import router as catalogs_router
from soyuz_catalog.api.routes.connections import router as connections_router
from soyuz_catalog.api.routes.credentials import router as credentials_router
from soyuz_catalog.api.routes.delta_commits import router as delta_commits_router
from soyuz_catalog.api.routes.delta_rest import router as delta_rest_router
from soyuz_catalog.api.routes.effective_permissions import router as effective_permissions_router
from soyuz_catalog.api.routes.external_locations import router as external_locations_router
from soyuz_catalog.api.routes.functions import router as functions_router
from soyuz_catalog.api.routes.lineage import router as lineage_router
from soyuz_catalog.api.routes.metastore import router as metastore_router
from soyuz_catalog.api.routes.metric_views import router as metric_views_router
from soyuz_catalog.api.routes.model_versions import router as model_versions_router
from soyuz_catalog.api.routes.permissions import router as permissions_router
from soyuz_catalog.api.routes.registered_models import router as registered_models_router
from soyuz_catalog.api.routes.schemas import router as schemas_router
from soyuz_catalog.api.routes.staging_tables import router as staging_tables_router
from soyuz_catalog.api.routes.tables import router as tables_router
from soyuz_catalog.api.routes.tags import router as tags_router
from soyuz_catalog.api.routes.temporary_credentials import router as temporary_credentials_router
from soyuz_catalog.api.routes.volume_files import router as volume_files_router
from soyuz_catalog.api.routes.volumes import router as volumes_router
from soyuz_catalog.db import init_db, run_migrations
from soyuz_catalog.exceptions import SoyuzError
from soyuz_catalog.logging_config import configure_logging
from soyuz_catalog.settings import get_settings

logger = logging.getLogger(__name__)


def _read_version() -> str:
    """Read the installed package version.

    Pulled at import time from the package metadata so the live
    OpenAPI ``info.version`` tracks ``pyproject.toml`` without manual
    sync. A hardcoded literal here would drift the moment a release
    bumps the project version, which is exactly the bug this helper
    exists to prevent. Falls back to ``"0.0.0+unknown"`` for editable
    or non-installed source checkouts so an importlib exception never
    breaks app construction.

    Returns:
        str: Installed package version, or the unknown-fallback.
    """
    try:
        return importlib.metadata.version("soyuz-catalog")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0+unknown"


_DESCRIPTION = """\
A clean Python reference implementation of the
[Unity Catalog REST API](https://github.com/unitycatalog/unitycatalog).

soyuz-catalog implements the upstream UC spec
(`api/all.yaml`) plus a small set of over-the-spec extensions
([OpenLineage ingest][adr-08], [tags][adr-10],
[table constraints][adr-12], [Lakehouse Federation][adr-13],
[metric views][adr-14], effective-permissions traversal, audit-log
read) and a secondary [Delta REST Catalog][adr-09] surface against
the same storage.

- **Spec source of truth:** `unitycatalog/api/all.yaml` ([ADR-0002][adr-02]).
- **Stack:** FastAPI + SQLAlchemy 2.0 (sync) + Pydantic v2 + Alembic.
- **Storage:** SQLite for development, Postgres for production.
- **Divergences** from UC OSS Java are documented in
  [`DIVERGENCES.md`](https://github.com/FloHofstetter/soyuz-catalog/blob/main/DIVERGENCES.md).

[adr-02]: https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0002-spec-is-the-contract.md
[adr-08]: https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0008-openlineage-as-lineage-contract.md
[adr-09]: https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0009-delta-rest-catalog-as-secondary-surface.md
[adr-10]: https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0010-tags-as-extension.md
[adr-12]: https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0012-table-constraints.md
[adr-13]: https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0013-connections-and-foreign-catalogs.md
[adr-14]: https://github.com/FloHofstetter/soyuz-catalog/blob/main/docs/adr/0014-metric-views.md
"""


_OPENAPI_TAGS: list[dict[str, str]] = [
    # UC core (spec-driven)
    {"name": "catalogs", "description": "Top-level namespaces (UC core)."},
    {"name": "schemas", "description": "Schemas within a catalog (UC core)."},
    {"name": "tables", "description": "Managed and external tables (UC core)."},
    {"name": "volumes", "description": "File-backed volumes (UC core)."},
    {"name": "functions", "description": "User-defined functions (UC core)."},
    {"name": "registered_models", "description": "ML registered models (UC core)."},
    {"name": "model_versions", "description": "Versions of registered models (UC core)."},
    {"name": "credentials", "description": "Storage credentials (UC core)."},
    {"name": "external-locations", "description": "External storage locations (UC core)."},
    {"name": "metastore", "description": "Metastore root summary (UC core)."},
    {"name": "permissions", "description": "Direct grants on a securable (UC core)."},
    {
        "name": "temporary-credentials",
        "description": "Short-lived vended credentials (UC core).",
    },
    # UC extensions (over-spec)
    {
        "name": "connections",
        "description": "Lakehouse Federation connections (extension; ADR-0013).",
    },
    {
        "name": "metric-views",
        "description": "Semantic-layer metric view definitions (extension; ADR-0014).",
    },
    {
        "name": "tags",
        "description": "Tag CRUD on catalog/schema/table/column (extension; ADR-0010).",
    },
    {"name": "lineage", "description": "OpenLineage ingest + traversal (extension; ADR-0008)."},
    {"name": "audit", "description": "Audit-log read API (extension)."},
    {
        "name": "effective-permissions",
        "description": "Inherited-grants traversal (extension).",
    },
    # Delta surfaces
    {
        "name": "delta-commits",
        "description": "Passthrough Delta commit coordinator (ADR-0011).",
    },
    {
        "name": "delta-rest-catalog",
        "description": "Delta REST Catalog secondary surface (ADR-0009).",
    },
    # Operations
    {"name": "health", "description": "Liveness probe."},
]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialise the database on startup.

    Migrations run *inside* the lifespan rather than as a separate CLI step
    because soyuz-catalog ships as a single process: a fresh container with
    a fresh SQLite file should be self-healing without an out-of-band Alembic
    invocation. For PostgreSQL deployments where multiple replicas share a
    database, this is still safe — Alembic's advisory lock prevents two
    replicas from running the same upgrade twice.

    Args:
        _app: The FastAPI application instance (unused).

    Yields:
        None: Control is yielded once startup is complete.
    """
    settings = get_settings()
    configure_logging(settings.log_level, settings.structured_logging)
    init_db(settings.database_url)
    run_migrations(settings.database_url)
    logger.info("soyuz-catalog ready")
    yield


def create_app() -> FastAPI:
    """Build the FastAPI application.

    Returns:
        FastAPI: The configured application instance.
    """
    settings = get_settings()
    openapi_url = "/openapi.json" if settings.openapi_enabled else None
    docs_url = "/docs" if settings.openapi_enabled else None
    app = FastAPI(
        title="soyuz-catalog",
        summary="Python reference implementation of the Unity Catalog REST API.",
        description=_DESCRIPTION,
        version=_read_version(),
        contact={
            "name": "Florian Hofstetter",
            "url": "https://github.com/FloHofstetter/soyuz-catalog",
            "email": "flo.max.hofstetter@gmail.com",
        },
        license_info={
            "name": "Apache-2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0",
        },
        openapi_tags=_OPENAPI_TAGS,
        lifespan=lifespan,
        openapi_url=openapi_url,
        docs_url=docs_url,
        redoc_url=None,
    )
    app.add_middleware(RequestIDMiddleware)

    @app.get("/healthz", tags=["health"], summary="Liveness probe")
    def healthz() -> dict[str, str]:
        """Return liveness status.

        Returns:
            dict[str, str]: Static OK payload.
        """
        return {"status": "ok"}

    @app.exception_handler(SoyuzError)
    async def _soyuz_error_handler(_request: Request, exc: SoyuzError) -> JSONResponse:
        return envelope(exc.status_code, exc.error_code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        errors: list[dict[str, Any]] = [dict(e) for e in exc.errors()]
        return envelope(
            422,
            "INVALID_ARGUMENT",
            flatten_validation_message(errors),
            details=jsonable_encoder(errors),
        )

    app.include_router(catalogs_router, prefix=settings.api_prefix)
    app.include_router(schemas_router, prefix=settings.api_prefix)
    app.include_router(tables_router, prefix=settings.api_prefix)
    app.include_router(volumes_router, prefix=settings.api_prefix)
    # Volume file IO — POST/GET/DELETE under
    # ``{prefix}/volumes/{full_name}/files[/{path}]``.
    app.include_router(volume_files_router, prefix=settings.api_prefix)
    app.include_router(credentials_router, prefix=settings.api_prefix)
    app.include_router(external_locations_router, prefix=settings.api_prefix)
    # Connections are an over-the-spec extension (ADR-0013) — Databricks
    # Lakehouse Federation, not in UC OSS ``all.yaml``. Mounted under
    # the UC prefix (unlike lineage / tags which sit at the root)
    # because foreign catalogs created against this resource live
    # under the same ``/catalogs`` surface as managed ones; keeping
    # the connection CRUD next to catalogs minimises URL surprises.
    app.include_router(connections_router, prefix=settings.api_prefix)
    # Metric views are an over-the-spec extension (ADR-0014) — a
    # semantic-layer definition store, not in UC OSS ``all.yaml``.
    # Mounted under the UC prefix (like connections) because metric
    # views live in the same catalog.schema.name hierarchy as tables;
    # keeping the CRUD next to the other three-part resources
    # minimises URL surprises.
    app.include_router(metric_views_router, prefix=settings.api_prefix)
    app.include_router(functions_router, prefix=settings.api_prefix)
    app.include_router(registered_models_router, prefix=settings.api_prefix)
    app.include_router(model_versions_router, prefix=settings.api_prefix)
    app.include_router(temporary_credentials_router, prefix=settings.api_prefix)
    app.include_router(staging_tables_router, prefix=settings.api_prefix)
    app.include_router(metastore_router, prefix=settings.api_prefix)
    app.include_router(permissions_router, prefix=settings.api_prefix)
    app.include_router(effective_permissions_router, prefix=settings.api_prefix)
    app.include_router(delta_commits_router, prefix=settings.api_prefix)
    # Delta REST Catalog API (ADR-0009): secondary spec surface defined
    # in unitycatalog ``delta.yaml``. Nested under ``api_prefix`` so
    # the full paths resolve as ``/api/2.1/unity-catalog/delta/v1/...``.
    app.include_router(delta_rest_router, prefix=settings.api_prefix)
    # Lineage is an over-the-spec extension (ADR-0008) and is
    # deliberately *not* nested under the UC API prefix: OpenLineage
    # producers point at a base URL with a fixed ``/lineage/v1/events``
    # path, and the spec-conformance test skips this prefix explicitly.
    app.include_router(lineage_router)
    # Tags are an over-the-spec extension (ADR-0010) — Databricks has
    # them, UC OSS / ``all.yaml`` do not. Mounted at the root for the
    # same reason as lineage: the spec-conformance test skips this
    # prefix explicitly, and keeping it off ``api_prefix`` makes the
    # divergence obvious in URL logs.
    app.include_router(tags_router)
    # Audit-log read API — an over-the-spec extension. Mounted at the
    # root, like lineage / tags, because it lives outside the UC spec
    # and the spec-conformance test skips that prefix explicitly.
    app.include_router(audit_router)
    return app


app = create_app()
