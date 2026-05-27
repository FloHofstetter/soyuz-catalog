"""HTTP routes for the Lakehouse-Federation Connections resource.

Over-the-spec addition (ADR-0013). Upstream UC OSS ``all.yaml``
defines no ``/connections`` surface, so the spec conformance
subset check in :mod:`tests.test_openapi_conformance` explicitly
skips this prefix — same posture as the effective-permissions
endpoint, which is the other UC-extension surface mounted under
``api_prefix``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    ConnectionInfo,
    CreateConnection,
    ListConnectionsResponse,
    UpdateConnection,
)
from soyuz_catalog.services import connection_service

router = APIRouter(prefix="/connections", tags=["connections"])


@router.post(
    "",
    response_model=ConnectionInfo,
    response_model_exclude_none=True,
    summary="Create connection",
)
def create_connection(
    payload: CreateConnection,
    db: Session = Depends(get_db),
) -> ConnectionInfo:
    """Create a new federation connection.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ConnectionInfo: The created connection.
    """
    connection = connection_service.create_connection(db, payload)
    return ConnectionInfo.model_validate(connection)


@router.get(
    "",
    response_model=ListConnectionsResponse,
    response_model_exclude_none=True,
    summary="List connections",
)
def list_connections(
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListConnectionsResponse:
    """List connections with keyset pagination.

    Args:
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListConnectionsResponse: One page of connections plus the next
            page token (``None`` on the last page).
    """
    rows, next_token = connection_service.list_connections(
        db,
        max_results=max_results,
        page_token=page_token,
    )
    return ListConnectionsResponse(
        connections=[ConnectionInfo.model_validate(r) for r in rows],
        next_page_token=next_token,
    )


@router.get(
    "/{name}",
    response_model=ConnectionInfo,
    response_model_exclude_none=True,
    summary="Get connection by name",
)
def get_connection(name: str, db: Session = Depends(get_db)) -> ConnectionInfo:
    """Fetch a single connection by name.

    Args:
        name: Connection name.
        db: Database session dependency.

    Returns:
        ConnectionInfo: The requested connection.
    """
    connection = connection_service.get_connection(db, name)
    return ConnectionInfo.model_validate(connection)


@router.patch(
    "/{name}",
    response_model=ConnectionInfo,
    response_model_exclude_none=True,
    summary="Update connection",
)
def update_connection(
    name: str,
    payload: UpdateConnection,
    db: Session = Depends(get_db),
) -> ConnectionInfo:
    """Update an existing connection.

    Args:
        name: Current connection name.
        payload: Patch body. Only fields explicitly present are applied;
            ``options={}`` clears the options dict.
        db: Database session dependency.

    Returns:
        ConnectionInfo: The updated connection.
    """
    connection = connection_service.update_connection(
        db,
        name,
        payload,
        set(payload.model_fields_set),
    )
    return ConnectionInfo.model_validate(connection)


@router.delete("/{name}", summary="Delete connection")
def delete_connection(
    name: str,
    force: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a connection.

    Args:
        name: Connection name.
        force: Cascade flag. Without ``force``, referencing foreign
            catalogs cause a 409; with ``force=true`` every referencing
            foreign catalog is deleted (cascading through its schemas,
            tables, volumes, functions, and models) before the
            connection row itself is removed.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    connection_service.delete_connection(db, name, force=force)
    return {}
