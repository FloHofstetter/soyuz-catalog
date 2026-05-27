"""HTTP routes for the Catalogs resource."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    CatalogInfo,
    CreateCatalog,
    ListCatalogsResponse,
    UpdateCatalog,
)
from soyuz_catalog.services import catalog_service

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


@router.post("", response_model=CatalogInfo, summary="Create catalog")
def create_catalog(payload: CreateCatalog, db: Session = Depends(get_db)) -> CatalogInfo:
    """Create a new catalog.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        CatalogInfo: The created catalog.
    """
    catalog = catalog_service.create_catalog(db, payload)
    return CatalogInfo.model_validate(catalog)


@router.get("", response_model=ListCatalogsResponse, summary="List catalogs")
def list_catalogs(
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListCatalogsResponse:
    """List catalogs with keyset pagination.

    Args:
        max_results: Page size hint, 1..1000. Defaults to 100 when
            omitted. Out-of-range values surface as 422 via FastAPI's
            query validation.
        page_token: Opaque cursor from a previous ``next_page_token``,
            or ``None`` for the first page. Tampered / unparseable
            tokens surface as 400 ``INVALID_ARGUMENT``.
        db: Database session dependency.

    Returns:
        ListCatalogsResponse: One page of catalogs plus the next page
            token (``None`` on the last page).
    """
    rows, next_token = catalog_service.list_catalogs(db, max_results, page_token)
    return ListCatalogsResponse(
        catalogs=[CatalogInfo.model_validate(r) for r in rows],
        next_page_token=next_token,
    )


@router.get("/{name}", response_model=CatalogInfo, summary="Get catalog by name")
def get_catalog(name: str, db: Session = Depends(get_db)) -> CatalogInfo:
    """Fetch a single catalog by name.

    Args:
        name: Catalog name.
        db: Database session dependency.

    Returns:
        CatalogInfo: The requested catalog.
    """
    catalog = catalog_service.get_catalog(db, name)
    return CatalogInfo.model_validate(catalog)


@router.patch("/{name}", response_model=CatalogInfo, summary="Update catalog")
def update_catalog(
    name: str,
    payload: UpdateCatalog,
    db: Session = Depends(get_db),
) -> CatalogInfo:
    """Update an existing catalog.

    Args:
        name: Current catalog name.
        payload: Patch body. Only fields explicitly present are applied;
            ``properties={}`` clears all properties.
        db: Database session dependency.

    Returns:
        CatalogInfo: The updated catalog.
    """
    catalog = catalog_service.update_catalog(db, name, payload, set(payload.model_fields_set))
    return CatalogInfo.model_validate(catalog)


@router.delete("/{name}", summary="Delete catalog")
def delete_catalog(
    name: str,
    force: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a catalog.

    Args:
        name: Catalog name.
        force: When true, cascade-delete child schemas (and the
            tables, volumes, functions, and registered models they
            own) before removing the catalog. Defaults to false, in
            which case a non-empty catalog rejects the delete with 409.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    catalog_service.delete_catalog(db, name, force=force)
    return {}
