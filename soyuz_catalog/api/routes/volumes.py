"""HTTP routes for the Volumes resource."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    CreateVolume,
    ListVolumesResponse,
    UpdateVolume,
    VolumeInfo,
)
from soyuz_catalog.models import Volume
from soyuz_catalog.services import volume_service

router = APIRouter(prefix="/volumes", tags=["volumes"])


def _to_info(volume: Volume) -> VolumeInfo:
    """Assemble a :class:`VolumeInfo` response from an ORM row.

    ``full_name``, ``catalog_name``, and ``schema_name`` are not columns
    on ``Volume`` — they are computed from the live parent schema's (and
    the schema's parent catalog's) names so that a rename of either
    parent propagates for free, same trick as the Tables router uses.

    Args:
        volume: The volume ORM row. Its ``schema`` relationship must be
            loadable — the session that fetched ``volume`` must still be
            active.

    Returns:
        VolumeInfo: The wire-format response.
    """
    schema = volume.schema
    catalog_name = schema.catalog.name
    schema_name = schema.name
    return VolumeInfo(
        name=volume.name,
        catalog_name=catalog_name,
        schema_name=schema_name,
        full_name=f"{catalog_name}.{schema_name}.{volume.name}",
        volume_type=volume.volume_type,
        storage_location=volume.storage_location,
        comment=volume.comment,
        owner=volume.owner,
        created_at=volume.created_at,
        created_by=volume.created_by,
        updated_at=volume.updated_at,
        updated_by=volume.updated_by,
        volume_id=volume.id,
    )


@router.post("", response_model=VolumeInfo, summary="Create volume")
def create_volume(payload: CreateVolume, db: Session = Depends(get_db)) -> VolumeInfo:
    """Create a new volume under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        VolumeInfo: The created volume.
    """
    volume = volume_service.create_volume(db, payload)
    return _to_info(volume)


@router.get("", response_model=ListVolumesResponse, summary="List volumes")
def list_volumes(
    catalog_name: str,
    schema_name: str,
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListVolumesResponse:
    """List volumes under a schema with keyset pagination.

    Args:
        catalog_name: Required query parameter — name of the parent catalog.
        schema_name: Required query parameter — name of the parent schema,
            relative to its catalog.
        max_results: Page size hint, 1..1000. Defaults to 100 when
            omitted.
        page_token: Opaque cursor from a previous ``next_page_token``,
            or ``None`` for the first page.
        db: Database session dependency.

    Returns:
        ListVolumesResponse: One page of volumes under the schema plus
            the next page token (``None`` on the last page).
    """
    rows, next_token = volume_service.list_volumes(
        db,
        catalog_name,
        schema_name,
        max_results,
        page_token,
    )
    return ListVolumesResponse(
        volumes=[_to_info(r) for r in rows],
        next_page_token=next_token,
    )


@router.get("/{full_name}", response_model=VolumeInfo, summary="Get volume by full name")
def get_volume(full_name: str, db: Session = Depends(get_db)) -> VolumeInfo:
    """Fetch a single volume by full name.

    Args:
        full_name: ``catalog_name.schema_name.volume_name`` path parameter.
        db: Database session dependency.

    Returns:
        VolumeInfo: The requested volume.
    """
    volume = volume_service.get_volume(db, full_name)
    return _to_info(volume)


@router.patch("/{full_name}", response_model=VolumeInfo, summary="Update volume")
def update_volume(
    full_name: str,
    payload: UpdateVolume,
    db: Session = Depends(get_db),
) -> VolumeInfo:
    """Update an existing volume.

    The UC spec restricts volume updates to ``new_name`` and ``comment``
    only; the request schema's ``extra="forbid"`` rejects any other
    field with HTTP 422.

    Args:
        full_name: Current ``catalog.schema.volume`` path parameter.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        VolumeInfo: The updated volume.
    """
    volume = volume_service.update_volume(
        db,
        full_name,
        payload,
        set(payload.model_fields_set),
    )
    return _to_info(volume)


@router.delete("/{full_name}", summary="Delete volume")
def delete_volume(
    full_name: str,
    force: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a volume.

    Args:
        full_name: ``catalog.schema.volume`` path parameter.
        force: Cascade flag (accepted but a no-op — volumes have no
            child resources).
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    volume_service.delete_volume(db, full_name, force=force)
    return {}
