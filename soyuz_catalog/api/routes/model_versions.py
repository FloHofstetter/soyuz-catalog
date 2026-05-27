"""HTTP routes for the Model Versions sub-resource.

Shares the ``/models`` URL prefix with the registered-models router.
The two routers do not collide because model versions all live at
either ``/models/versions`` (the unnested create path from the UC
spec) or ``/models/{full_name}/versions`` and below, and path
parameters do not span slashes so ``/models/{full_name}`` on the
parent router never matches a multi-segment child path.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    CreateModelVersion,
    ListModelVersionsResponse,
    ModelVersionInfo,
    UpdateModelVersion,
)
from soyuz_catalog.models import ModelVersion
from soyuz_catalog.services import model_version_service

router = APIRouter(prefix="/models", tags=["model_versions"])


def _to_info(row: ModelVersion) -> ModelVersionInfo:
    """Assemble a :class:`ModelVersionInfo` response from an ORM row.

    The parent-triple (``catalog_name``, ``schema_name``,
    ``model_name``) is reconstructed from the live parent registered
    model and its schema at response time, so a rename of any
    ancestor propagates without a fan-out UPDATE.

    Args:
        row: The model-version ORM row. Its
            ``registered_model.schema`` chain must be loadable.

    Returns:
        ModelVersionInfo: The wire-format response.
    """
    model = row.registered_model
    schema = model.schema
    return ModelVersionInfo(
        model_name=model.name,
        catalog_name=schema.catalog.name,
        schema_name=schema.name,
        version=row.version,
        source=row.source,
        run_id=row.run_id,
        status=row.status,  # type: ignore[arg-type]
        storage_location=row.storage_location,
        comment=row.comment,
        created_at=row.created_at,
        created_by=row.created_by,
        updated_at=row.updated_at,
        updated_by=row.updated_by,
        id=row.id,
    )


@router.post(
    "/versions",
    response_model=ModelVersionInfo,
    response_model_exclude_none=True,
    summary="Create model version",
)
def create_model_version(
    payload: CreateModelVersion,
    db: Session = Depends(get_db),
) -> ModelVersionInfo:
    """Create a new model version under an existing registered model.

    The UC spec addresses the parent via three separate body fields
    (``catalog_name``, ``schema_name``, ``model_name``) rather than a
    URL path parameter — see :func:`_resolve_model_from_triple` in
    the service module for the rebuild-to-full_name dance.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        ModelVersionInfo: The created row.
    """
    row = model_version_service.create_model_version(db, payload)
    return _to_info(row)


@router.get(
    "/{full_name}/versions",
    response_model=ListModelVersionsResponse,
    summary="List model versions",
)
def list_model_versions(
    full_name: str,
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListModelVersionsResponse:
    """List model versions of a registered model with keyset pagination.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListModelVersionsResponse: One page of versions plus the next
            page token.
    """
    rows, next_token = model_version_service.list_model_versions(
        db,
        full_name,
        max_results,
        page_token,
    )
    return ListModelVersionsResponse(
        model_versions=[_to_info(r) for r in rows],
        next_page_token=next_token,
    )


@router.get(
    "/{full_name}/versions/{version}",
    response_model=ModelVersionInfo,
    response_model_exclude_none=True,
    summary="Get model version",
)
def get_model_version(
    full_name: str,
    version: int,
    db: Session = Depends(get_db),
) -> ModelVersionInfo:
    """Fetch a single model version by parent full name and version number.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        version: Integer version number, 1-indexed.
        db: Database session dependency.

    Returns:
        ModelVersionInfo: The requested row.
    """
    row = model_version_service.get_model_version(db, full_name, version)
    return _to_info(row)


@router.patch(
    "/{full_name}/versions/{version}",
    response_model=ModelVersionInfo,
    response_model_exclude_none=True,
    summary="Update model version",
)
def update_model_version(
    full_name: str,
    version: int,
    payload: UpdateModelVersion,
    db: Session = Depends(get_db),
) -> ModelVersionInfo:
    """Update an existing model version.

    The UC spec permits only ``comment`` on update; any other field
    is rejected with 422 by
    :class:`soyuz_catalog.api.schemas.UpdateModelVersion`.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        version: Integer version number.
        payload: Patch body.
        db: Database session dependency.

    Returns:
        ModelVersionInfo: The updated row.
    """
    row = model_version_service.update_model_version(
        db,
        full_name,
        version,
        payload,
        set(payload.model_fields_set),
    )
    return _to_info(row)


@router.delete("/{full_name}/versions/{version}", summary="Delete model version")
def delete_model_version(
    full_name: str,
    version: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a model version.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        version: Integer version number.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    model_version_service.delete_model_version(db, full_name, version)
    return {}


@router.patch(
    "/{full_name}/versions/{version}/finalize",
    response_model=ModelVersionInfo,
    response_model_exclude_none=True,
    summary="Finalize model version",
)
def finalize_model_version(
    full_name: str,
    version: int,
    db: Session = Depends(get_db),
) -> ModelVersionInfo:
    """Finalize a model version after artifact upload.

    Implements MLflow UC-OSS ``finalizeModelVersion`` RPC: transitions
    status from ``PENDING_REGISTRATION`` to ``READY``. The MLflow
    client calls this after uploading artifacts to the
    ``storage_location`` returned by ``createModelVersion``.
    Idempotent on already-``READY`` versions; rejects
    ``FAILED_REGISTRATION`` with 400.

    Args:
        full_name: Parent ``catalog.schema.model`` path parameter.
        version: Integer version number.
        db: Database session dependency.

    Returns:
        ModelVersionInfo: The finalized row in ``READY`` status.
    """
    row = model_version_service.finalize_model_version(db, full_name, version)
    return _to_info(row)
