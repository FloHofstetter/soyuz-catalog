"""HTTP routes for the Registered Models resource."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    CreateRegisteredModel,
    ListRegisteredModelsResponse,
    RegisteredModelInfo,
    UpdateRegisteredModel,
)
from soyuz_catalog.models import RegisteredModel
from soyuz_catalog.services import registered_model_service

router = APIRouter(prefix="/models", tags=["registered_models"])


def _to_info(model: RegisteredModel) -> RegisteredModelInfo:
    """Assemble a :class:`RegisteredModelInfo` response from an ORM row.

    ``full_name`` / ``catalog_name`` / ``schema_name`` are computed
    at response time from the live parent schema's and catalog's
    names so a rename of either parent propagates to every registered
    model for free.

    Args:
        model: The registered-model ORM row. Its ``schema``
            relationship must be loadable.

    Returns:
        RegisteredModelInfo: The wire-format response.
    """
    schema = model.schema
    catalog_name = schema.catalog.name
    schema_name = schema.name
    return RegisteredModelInfo(
        name=model.name,
        catalog_name=catalog_name,
        schema_name=schema_name,
        full_name=f"{catalog_name}.{schema_name}.{model.name}",
        storage_location=model.storage_location,
        comment=model.comment,
        owner=model.owner,
        created_at=model.created_at,
        created_by=model.created_by,
        updated_at=model.updated_at,
        updated_by=model.updated_by,
        id=model.id,
    )


@router.post(
    "",
    response_model=RegisteredModelInfo,
    response_model_exclude_none=True,
    summary="Create registered model",
)
def create_registered_model(
    payload: CreateRegisteredModel,
    db: Session = Depends(get_db),
) -> RegisteredModelInfo:
    """Create a new registered model under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        RegisteredModelInfo: The created row.
    """
    model = registered_model_service.create_registered_model(db, payload)
    return _to_info(model)


@router.get(
    "",
    response_model=ListRegisteredModelsResponse,
    summary="List registered models",
)
def list_registered_models(
    catalog_name: str | None = None,
    schema_name: str | None = None,
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListRegisteredModelsResponse:
    """List registered models with keyset pagination and optional parent filters.

    Both ``catalog_name`` and ``schema_name`` are optional per the
    UC spec — a metastore-wide listing is legal. ``schema_name``
    alone without ``catalog_name`` is 400 because schema names are
    not metastore-unique.

    Args:
        catalog_name: Optional parent catalog filter.
        schema_name: Optional parent schema filter.
        max_results: Page size hint, 1..1000.
        page_token: Opaque cursor from a previous ``next_page_token``.
        db: Database session dependency.

    Returns:
        ListRegisteredModelsResponse: One page of rows plus the next
            page token.
    """
    rows, next_token = registered_model_service.list_registered_models(
        db,
        catalog_name=catalog_name,
        schema_name=schema_name,
        max_results=max_results,
        page_token=page_token,
    )
    return ListRegisteredModelsResponse(
        registered_models=[_to_info(r) for r in rows],
        next_page_token=next_token,
    )


@router.get(
    "/{full_name}",
    response_model=RegisteredModelInfo,
    response_model_exclude_none=True,
    summary="Get registered model by full name",
)
def get_registered_model(
    full_name: str,
    db: Session = Depends(get_db),
) -> RegisteredModelInfo:
    """Fetch a single registered model by full name.

    Args:
        full_name: ``catalog_name.schema_name.model_name`` path parameter.
        db: Database session dependency.

    Returns:
        RegisteredModelInfo: The requested row.
    """
    model = registered_model_service.get_registered_model(db, full_name)
    return _to_info(model)


@router.patch(
    "/{full_name}",
    response_model=RegisteredModelInfo,
    response_model_exclude_none=True,
    summary="Update registered model",
)
def update_registered_model(
    full_name: str,
    payload: UpdateRegisteredModel,
    db: Session = Depends(get_db),
) -> RegisteredModelInfo:
    """Update an existing registered model.

    Args:
        full_name: Current ``catalog.schema.model`` path parameter.
        payload: Patch body. Only fields explicitly present are applied.
        db: Database session dependency.

    Returns:
        RegisteredModelInfo: The updated row.
    """
    model = registered_model_service.update_registered_model(
        db,
        full_name,
        payload,
        set(payload.model_fields_set),
    )
    return _to_info(model)


@router.delete("/{full_name}", summary="Delete registered model")
def delete_registered_model(
    full_name: str,
    force: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a registered model.

    Args:
        full_name: ``catalog.schema.model`` path parameter.
        force: Cascade flag. Without ``force``, child model versions
            cause a 409; with ``force=true`` every child version is
            deleted first.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    registered_model_service.delete_registered_model(db, full_name, force=force)
    return {}
