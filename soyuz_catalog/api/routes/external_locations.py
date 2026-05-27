"""HTTP routes for the External Locations resource."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    CreateExternalLocation,
    ExternalLocationInfo,
    ListExternalLocationsResponse,
    UpdateExternalLocation,
)
from soyuz_catalog.models import ExternalLocation
from soyuz_catalog.services import external_location_service

router = APIRouter(prefix="/external-locations", tags=["external-locations"])


def _to_info(location: ExternalLocation) -> ExternalLocationInfo:
    """Assemble an :class:`ExternalLocationInfo` response from an ORM row.

    ``credential_name`` is reconstructed from the live credential
    relationship rather than read from a stored column — this is the
    rename-invariance trick: renaming a credential propagates to every
    bound external location for free, without a fan-out UPDATE.
    ``location.credential`` must be loadable, so the session that
    fetched ``location`` must still be active.

    Args:
        location: The external location ORM row.

    Returns:
        ExternalLocationInfo: The wire-format response.
    """
    return ExternalLocationInfo(
        name=location.name,
        id=location.id,
        url=location.url,
        credential_name=location.credential.name,
        credential_id=location.credential_id,
        comment=location.comment,
        owner=location.owner,
        created_at=location.created_at,
        created_by=location.created_by,
        updated_at=location.updated_at,
        updated_by=location.updated_by,
    )


@router.post("", response_model=ExternalLocationInfo, summary="Create external location")
def create_external_location(
    payload: CreateExternalLocation,
    db: Session = Depends(get_db),
) -> ExternalLocationInfo:
    """Create a new external location.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ExternalLocationInfo: The created row.
    """
    location = external_location_service.create_external_location(db, payload)
    return _to_info(location)


@router.get(
    "",
    response_model=ListExternalLocationsResponse,
    summary="List external locations",
)
def list_external_locations(
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListExternalLocationsResponse:
    """List external locations with keyset pagination.

    Args:
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListExternalLocationsResponse: One page of rows plus the next
            page token (``None`` on the last page).
    """
    rows, next_token = external_location_service.list_external_locations(
        db,
        max_results=max_results,
        page_token=page_token,
    )
    return ListExternalLocationsResponse(
        external_locations=[_to_info(r) for r in rows],
        next_page_token=next_token,
    )


@router.get(
    "/{name}",
    response_model=ExternalLocationInfo,
    summary="Get external location by name",
)
def get_external_location(name: str, db: Session = Depends(get_db)) -> ExternalLocationInfo:
    """Fetch a single external location by name.

    Args:
        name: External location name.
        db: Database session dependency.

    Returns:
        ExternalLocationInfo: The requested row.
    """
    location = external_location_service.get_external_location(db, name)
    return _to_info(location)


@router.patch(
    "/{name}",
    response_model=ExternalLocationInfo,
    summary="Update external location",
)
def update_external_location(
    name: str,
    payload: UpdateExternalLocation,
    db: Session = Depends(get_db),
) -> ExternalLocationInfo:
    """Update an existing external location.

    Args:
        name: Current external location name.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        ExternalLocationInfo: The updated row.
    """
    location = external_location_service.update_external_location(
        db,
        name,
        payload,
        set(payload.model_fields_set),
    )
    return _to_info(location)


@router.delete("/{name}", summary="Delete external location")
def delete_external_location(
    name: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete an external location.

    Args:
        name: External location name.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    external_location_service.delete_external_location(db, name)
    return {}
