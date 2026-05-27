"""HTTP routes for the Delta REST Catalog API (ADR-0009).

This module registers the 14 endpoints defined by
``unitycatalog/api/delta.yaml`` under the router prefix
``/delta``. The full effective paths are ``/api/2.1/unity-catalog``
+ ``/delta`` + ``/v1/…``, because :func:`main.create_app` includes
this router under the UC API prefix just like every other spec
router. The ``/v1`` segment is part of each route literal (not
a FastAPI prefix layer) because the spec treats it as part of
the route identity, not a version shim the server would negotiate.

Endpoints:

* ``GET /delta/v1/config`` — protocol + endpoint advertisement.
* ``POST /delta/v1/catalogs/{c}/schemas/{s}/staging-tables``
* ``POST /delta/v1/catalogs/{c}/schemas/{s}/tables``
* ``GET  /delta/v1/catalogs/{c}/schemas/{s}/tables``
* ``GET  /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}``
* ``POST /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}``
* ``DELETE /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}``
* ``HEAD /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}``
* ``POST /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}/rename``
* ``GET  /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}/credentials``
* ``POST /delta/v1/catalogs/{c}/schemas/{s}/tables/{t}/metrics``
* ``GET  /delta/v1/staging-tables/{table_id}/credentials``
* ``GET  /delta/v1/temporary-path-credentials``

Heavy lifting lives in
:mod:`soyuz_catalog.services.delta_rest_service`; the route layer
is intentionally thin — just path param binding, dependency
injection, and a couple of explicit ``Response`` objects for the
204 / HEAD endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from soyuz_catalog.api.delta_schemas import (
    CatalogConfig,
    CreateStagingTableRequest,
    CreateTableRequest,
    CredentialsResponse,
    DeltaListTablesResponse,
    LoadTableResponse,
    RenameTableRequest,
    ReportMetricsRequest,
    StagingTableResponse,
    UpdateTableRequest,
)
from soyuz_catalog.api.deps import get_db
from soyuz_catalog.services import delta_rest_service

router = APIRouter(prefix="/delta", tags=["delta-rest-catalog"])


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@router.get(
    "/v1/config",
    response_model=CatalogConfig,
    response_model_by_alias=True,
    summary="Get Delta REST Catalog config",
)
def get_config(
    catalog: str = Query(..., description="Catalog name (required per spec; not used)"),
    protocol_versions: str = Query(
        ...,
        alias="protocol-versions",
        description="Comma-separated list of client-supported protocol versions",
    ),
) -> CatalogConfig:
    """Advertise the supported Delta REST Catalog endpoints and version.

    Args:
        catalog: Required by spec; soyuz has one implementation and
            does not branch on catalog name.
        protocol_versions: Required by spec; soyuz only implements
            version ``"1.0"`` so the response is the same regardless
            of the client's request.

    Returns:
        CatalogConfig: Fixed list of implemented endpoints plus
            protocol version ``"1.0"``.
    """
    del catalog, protocol_versions
    return delta_rest_service.build_config()


# ---------------------------------------------------------------------------
# Table CRUD
# ---------------------------------------------------------------------------


@router.post(
    "/v1/catalogs/{catalog}/schemas/{schema}/tables",
    response_model=LoadTableResponse,
    response_model_by_alias=True,
    summary="Create Delta table",
)
def create_table(
    catalog: str,
    schema: str,
    payload: CreateTableRequest,
    db: Session = Depends(get_db),
) -> LoadTableResponse:
    """Create a new Delta table under ``catalog.schema``.

    Args:
        catalog: Catalog path segment.
        schema: Schema path segment.
        payload: Validated Delta create request body.
        db: Database session dependency.

    Returns:
        LoadTableResponse: The freshly-created table's load
            response, matching a subsequent ``loadTable`` call
            byte-for-byte.
    """
    return delta_rest_service.create_delta_table(db, catalog, schema, payload)


@router.get(
    "/v1/catalogs/{catalog}/schemas/{schema}/tables",
    response_model=DeltaListTablesResponse,
    response_model_by_alias=True,
    summary="List Delta tables",
)
def list_tables(
    catalog: str,
    schema: str,
    max_results: int | None = Query(default=None, alias="maxResults"),
    page_token: str | None = Query(default=None, alias="pageToken"),
    db: Session = Depends(get_db),
) -> DeltaListTablesResponse:
    """Return one page of tables under a schema.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        max_results: Client-side page size hint, capped by the
            existing pagination helper.
        page_token: Opaque keyset token from a previous call.
        db: Database session dependency.

    Returns:
        DeltaListTablesResponse: One page of Delta-shaped identifiers.
    """
    return delta_rest_service.list_delta_tables(db, catalog, schema, max_results, page_token)


@router.get(
    "/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}",
    response_model=LoadTableResponse,
    response_model_by_alias=True,
    summary="Load Delta table",
)
def load_table(
    catalog: str,
    schema: str,
    table: str,
    db: Session = Depends(get_db),
) -> LoadTableResponse:
    """Load a single table's full Delta metadata.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        db: Database session dependency.

    Returns:
        LoadTableResponse: Full Delta wire metadata for the table.
    """
    return delta_rest_service.load_table_response(db, catalog, schema, table)


@router.post(
    "/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}",
    response_model=LoadTableResponse,
    response_model_by_alias=True,
    summary="Update Delta table",
)
def update_table(
    catalog: str,
    schema: str,
    table: str,
    payload: UpdateTableRequest,
    db: Session = Depends(get_db),
) -> LoadTableResponse:
    """Apply a batch of updates to a table.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        payload: Validated update request body. Requirements run
            first and a failure short-circuits with 409; updates
            are applied in order and commit-coordinator actions
            surface as 501.
        db: Database session dependency.

    Returns:
        LoadTableResponse: Post-update state with the bumped etag.
    """
    return delta_rest_service.update_delta_table(db, catalog, schema, table, payload)


@router.delete(
    "/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}",
    status_code=204,
    summary="Delete Delta table",
)
def delete_table(
    catalog: str,
    schema: str,
    table: str,
    db: Session = Depends(get_db),
) -> Response:
    """Delete a table. Returns 204 No Content per spec.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        db: Database session dependency.

    Returns:
        Response: Empty 204 body.
    """
    delta_rest_service.delete_delta_table(db, catalog, schema, table)
    return Response(status_code=204)


@router.head(
    "/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}",
    status_code=204,
    summary="Probe Delta table existence",
)
def head_table(
    catalog: str,
    schema: str,
    table: str,
    db: Session = Depends(get_db),
) -> Response:
    """Return 204 if the table exists, 404 otherwise.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        db: Database session dependency.

    Returns:
        Response: Empty body with the appropriate status code.
    """
    if delta_rest_service.table_exists(db, catalog, schema, table):
        return Response(status_code=204)
    return Response(status_code=404)


@router.post(
    "/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}/rename",
    status_code=204,
    summary="Rename Delta table",
)
def rename_table(
    catalog: str,
    schema: str,
    table: str,
    payload: RenameTableRequest,
    db: Session = Depends(get_db),
) -> Response:
    """Rename a table in place. Returns 204 No Content.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Current table segment.
        payload: Validated rename request body.
        db: Database session dependency.

    Returns:
        Response: Empty 204 body.
    """
    delta_rest_service.rename_delta_table(db, catalog, schema, table, payload)
    return Response(status_code=204)


# ---------------------------------------------------------------------------
# Staging tables
# ---------------------------------------------------------------------------


@router.post(
    "/v1/catalogs/{catalog}/schemas/{schema}/staging-tables",
    response_model=StagingTableResponse,
    response_model_by_alias=True,
    summary="Allocate Delta staging table",
)
def create_staging_table(
    catalog: str,
    schema: str,
    payload: CreateStagingTableRequest,
    db: Session = Depends(get_db),
) -> StagingTableResponse:
    """Allocate a staging-table UUID and storage location.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        payload: Validated staging-table create body.
        db: Database session dependency.

    Returns:
        StagingTableResponse: The allocated UUID + location with
            Delta-shaped protocol and credential stubs.
    """
    return delta_rest_service.create_delta_staging_table(db, catalog, schema, payload)


# ---------------------------------------------------------------------------
# Credentials (stubs — ADR-0009)
# ---------------------------------------------------------------------------


@router.get(
    "/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}/credentials",
    response_model=CredentialsResponse,
    response_model_by_alias=True,
    summary="Get Delta table credentials",
)
def get_table_credentials(
    catalog: str,
    schema: str,
    table: str,
    operation: str = Query(..., description="READ or READ_WRITE"),
    db: Session = Depends(get_db),
) -> CredentialsResponse:
    """Return an empty credentials list.

    soyuz does not vend cloud credentials (ADR-0009, consistent
    with the existing temporary-credentials stub posture). Empty
    list keeps Delta clients progressing through their write
    paths when they use a storage URL directly.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        operation: Required by spec; ignored by soyuz.
        db: Database session dependency; used only to verify the
            table exists so a 404 surfaces for an unknown address.

    Returns:
        CredentialsResponse: Always ``{"storage-credentials": []}``.
    """
    del operation
    # Probe existence so unknown-table requests 404 instead of
    # quietly returning an empty credential list.
    delta_rest_service.load_table_response(db, catalog, schema, table)
    return CredentialsResponse()


@router.get(
    "/v1/staging-tables/{table_id}/credentials",
    response_model=CredentialsResponse,
    response_model_by_alias=True,
    summary="Get Delta staging table credentials",
)
def get_staging_table_credentials(
    table_id: str,
    db: Session = Depends(get_db),
) -> CredentialsResponse:
    """Return an empty credentials list for a staging table.

    soyuz verifies the staging table exists so an unknown UUID
    surfaces as 404; otherwise returns the same empty stub as
    :func:`get_table_credentials`.

    Args:
        table_id: Staging table opaque id.
        db: Database session dependency.

    Returns:
        CredentialsResponse: Always ``{"storage-credentials": []}``.
    """
    from soyuz_catalog.services import staging_table_service

    staging_table_service.get_staging_table_by_id(db, table_id)
    return CredentialsResponse()


@router.get(
    "/v1/temporary-path-credentials",
    response_model=CredentialsResponse,
    response_model_by_alias=True,
    summary="Get Delta temporary path credentials",
)
def get_temporary_path_credentials(
    location: str = Query(..., description="Storage location path"),
    operation: str = Query(..., description="READ or READ_WRITE"),
) -> CredentialsResponse:
    """Return an empty credentials list for an arbitrary path.

    Exists so Delta clients that walk the ``/config`` endpoint
    list and check for path-credential support see a spec-shaped
    200 instead of a 404. soyuz vends nothing; the empty list is
    the same stub posture as every other credential endpoint.

    Args:
        location: Storage path from the query string.
        operation: Required by spec; ignored by soyuz.

    Returns:
        CredentialsResponse: Always ``{"storage-credentials": []}``.
    """
    del location, operation
    return CredentialsResponse()


# ---------------------------------------------------------------------------
# Metrics (accept-and-discard — ADR-0009)
# ---------------------------------------------------------------------------


@router.post(
    "/v1/catalogs/{catalog}/schemas/{schema}/tables/{table}/metrics",
    status_code=204,
    summary="Report Delta table metrics",
)
def report_metrics(
    catalog: str,
    schema: str,
    table: str,
    payload: ReportMetricsRequest,
    db: Session = Depends(get_db),
) -> Response:
    """Accept a metrics report and discard it.

    soyuz has no metrics sink; rejecting these would make every
    Delta write log a client-side error over a non-feature. The
    body is still parsed (a malformed payload surfaces as 422)
    and the path is still probed (an unknown table surfaces as
    404) so well-behaved clients still get a useful error on a
    real bug. ADR-0009.

    Args:
        catalog: Catalog segment.
        schema: Schema segment.
        table: Table segment.
        payload: Validated metrics report body.
        db: Database session dependency.

    Returns:
        Response: Empty 204 body.
    """
    del payload
    delta_rest_service.load_table_response(db, catalog, schema, table)
    return Response(status_code=204)
