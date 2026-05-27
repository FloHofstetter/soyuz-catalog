"""HTTP routes for the Schemas resource."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    CreateSchema,
    ListSchemasResponse,
    SchemaInfo,
    UpdateSchema,
)
from soyuz_catalog.models import Schema
from soyuz_catalog.services import audit_service, schema_service

router = APIRouter(prefix="/schemas", tags=["schemas"])


def _to_info(schema: Schema) -> SchemaInfo:
    """Assemble a :class:`SchemaInfo` response from an ORM row.

    ``full_name`` and ``catalog_name`` are not columns on ``Schema`` — they
    are computed from the live parent catalog's name so that a catalog
    rename propagates for free. That is why this function exists instead of
    a straight ``SchemaInfo.model_validate(schema)``: the Pydantic model's
    ``from_attributes`` path would miss those two fields.

    Args:
        schema: The schema ORM row. Its ``catalog`` relationship must be
            loadable — the session that fetched ``schema`` must still be
            active.

    Returns:
        SchemaInfo: The wire-format response.
    """
    catalog_name = schema.catalog.name
    return SchemaInfo(
        name=schema.name,
        catalog_name=catalog_name,
        full_name=f"{catalog_name}.{schema.name}",
        comment=schema.comment,
        properties=schema.properties,
        owner=schema.owner,
        created_at=schema.created_at,
        created_by=schema.created_by,
        updated_at=schema.updated_at,
        updated_by=schema.updated_by,
        schema_id=schema.id,
        storage_root=schema.storage_root,
        storage_location=schema.storage_location,
    )


@router.post("", response_model=SchemaInfo, summary="Create schema")
def create_schema(payload: CreateSchema, db: Session = Depends(get_db)) -> SchemaInfo:
    """Create a new schema under an existing catalog.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        SchemaInfo: The created schema.
    """
    schema = schema_service.create_schema(db, payload)
    audit_service.log_action(
        db,
        action="schema.created",
        target=f"{payload.catalog_name}.{payload.name}",
        detail={"schema_id": schema.id},
    )
    return _to_info(schema)


@router.get("", response_model=ListSchemasResponse, summary="List schemas")
def list_schemas(
    catalog_name: str,
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListSchemasResponse:
    """List schemas under a catalog with keyset pagination.

    Args:
        catalog_name: Required query parameter — name of the parent catalog.
        max_results: Page size hint, 1..1000. Defaults to 100 when
            omitted.
        page_token: Opaque cursor from a previous ``next_page_token``,
            or ``None`` for the first page.
        db: Database session dependency.

    Returns:
        ListSchemasResponse: One page of schemas under the catalog
            plus the next page token (``None`` on the last page).
    """
    rows, next_token = schema_service.list_schemas(
        db,
        catalog_name,
        max_results,
        page_token,
    )
    return ListSchemasResponse(
        schemas=[_to_info(r) for r in rows],
        next_page_token=next_token,
    )


@router.get("/{full_name}", response_model=SchemaInfo, summary="Get schema by full name")
def get_schema(full_name: str, db: Session = Depends(get_db)) -> SchemaInfo:
    """Fetch a single schema by full name.

    Args:
        full_name: ``catalog_name.schema_name`` path parameter.
        db: Database session dependency.

    Returns:
        SchemaInfo: The requested schema.
    """
    schema = schema_service.get_schema(db, full_name)
    return _to_info(schema)


@router.patch("/{full_name}", response_model=SchemaInfo, summary="Update schema")
def update_schema(
    full_name: str,
    payload: UpdateSchema,
    db: Session = Depends(get_db),
) -> SchemaInfo:
    """Update an existing schema.

    Args:
        full_name: Current ``catalog_name.schema_name`` path parameter.
        payload: Patch body. Only fields explicitly present are applied;
            ``properties={}`` clears all properties.
        db: Database session dependency.

    Returns:
        SchemaInfo: The updated schema.
    """
    schema = schema_service.update_schema(
        db,
        full_name,
        payload,
        set(payload.model_fields_set),
    )
    audit_service.log_action(
        db,
        action="schema.updated",
        target=full_name,
        detail={"changed_fields": sorted(payload.model_fields_set)},
    )
    return _to_info(schema)


@router.delete("/{full_name}", summary="Delete schema")
def delete_schema(
    full_name: str,
    force: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a schema.

    Args:
        full_name: ``catalog_name.schema_name`` path parameter.
        force: When true, cascade-delete child tables, volumes,
            functions and registered models before removing the
            schema. Defaults to false, in which case a non-empty
            schema rejects the delete with 409.
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    schema_service.delete_schema(db, full_name, force=force)
    audit_service.log_action(
        db,
        action="schema.deleted",
        target=full_name,
        detail={"force": force},
    )
    return {}
