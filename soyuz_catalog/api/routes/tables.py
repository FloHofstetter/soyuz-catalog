"""HTTP routes for the Tables resource."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from soyuz_catalog.api.deps import get_db
from soyuz_catalog.api.schemas import (
    ColumnInfo,
    CreateTable,
    ListTablesResponse,
    TableInfo,
)
from soyuz_catalog.models import Table
from soyuz_catalog.services import audit_service, constraints_service, table_service

router = APIRouter(prefix="/tables", tags=["tables"])


def _to_info(table: Table, db: Session) -> TableInfo:
    """Assemble a :class:`TableInfo` response from an ORM row.

    ``full_name``, ``catalog_name``, and ``schema_name`` are not columns on
    ``Table`` — they are computed from the live parent schema's (and the
    schema's parent catalog's) names so that a rename of either parent
    propagates for free. ``columns`` is rebuilt from the live
    ``table_columns`` rows, which the ORM loads in position order thanks
    to the relationship's ``order_by``.

    Args:
        table: The table ORM row. Its ``schema`` and ``columns``
            relationships must be loadable — the session that fetched
            ``table`` must still be active.
        db: Active SQLAlchemy session, used to fetch declared
            constraints (ADR-0012) via
            :func:`soyuz_catalog.services.constraints_service.list_constraints`
            and stitch them onto the response.

    Returns:
        TableInfo: The wire-format response.
    """
    schema = table.schema
    catalog_name = schema.catalog.name
    schema_name = schema.name
    constraints = constraints_service.list_constraints(db, table.id)
    return TableInfo(
        name=table.name,
        catalog_name=catalog_name,
        schema_name=schema_name,
        full_name=f"{catalog_name}.{schema_name}.{table.name}",
        table_type=table.table_type,
        data_source_format=table.data_source_format,
        columns=[ColumnInfo.model_validate(c) for c in table.columns],
        storage_location=table.storage_location,
        comment=table.comment,
        properties=table.properties,
        owner=table.owner,
        created_at=table.created_at,
        created_by=table.created_by,
        updated_at=table.updated_at,
        updated_by=table.updated_by,
        table_id=table.id,
        table_constraints=constraints or None,
    )


@router.post("", response_model=TableInfo, summary="Create table")
def create_table(payload: CreateTable, db: Session = Depends(get_db)) -> TableInfo:
    """Create a new table under an existing schema.

    Args:
        payload: Create request body.
        db: Database session dependency.

    Returns:
        TableInfo: The created table.
    """
    table = table_service.create_table(db, payload)
    audit_service.log_action(
        db,
        action="table.created",
        target=f"{payload.catalog_name}.{payload.schema_name}.{payload.name}",
        detail={"table_id": table.id, "table_type": getattr(payload, "table_type", None)},
    )
    return _to_info(table, db)


@router.get("", response_model=ListTablesResponse, summary="List tables")
def list_tables(
    catalog_name: str,
    schema_name: str,
    max_results: int | None = Query(default=None, ge=0, le=1000),
    page_token: str | None = None,
    db: Session = Depends(get_db),
) -> ListTablesResponse:
    """List tables under a schema with keyset pagination.

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
        ListTablesResponse: One page of tables under the schema plus
            the next page token (``None`` on the last page).
    """
    rows, next_token = table_service.list_tables(
        db,
        catalog_name,
        schema_name,
        max_results,
        page_token,
    )
    return ListTablesResponse(
        tables=[_to_info(r, db) for r in rows],
        next_page_token=next_token,
    )


@router.get("/{full_name}", response_model=TableInfo, summary="Get table by full name")
def get_table(full_name: str, db: Session = Depends(get_db)) -> TableInfo:
    """Fetch a single table by full name.

    Args:
        full_name: ``catalog_name.schema_name.table_name`` path parameter.
        db: Database session dependency.

    Returns:
        TableInfo: The requested table.
    """
    table = table_service.get_table(db, full_name)
    return _to_info(table, db)


@router.delete("/{full_name}", summary="Delete table")
def delete_table(
    full_name: str,
    force: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Delete a table and cascade through its columns.

    No PATCH verb is registered on this router: the UC OpenAPI spec
    defines no ``UpdateTable`` request model, and silently accepting
    unknown fields is the UC OSS Java bug this project exists to fix.
    FastAPI therefore returns 405 Method Not Allowed for any PATCH to a
    table, which is a deliberate and tested divergence — see
    ``DIVERGENCES.md``.

    Args:
        full_name: ``catalog_name.schema_name.table_name`` path parameter.
        force: Cascade flag (accepted for spec stability; currently
            a no-op — columns always cascade unconditionally because
            they have no independent existence).
        db: Database session dependency.

    Returns:
        dict[str, str]: Empty success payload.
    """
    table_service.delete_table(db, full_name, force=force)
    audit_service.log_action(
        db,
        action="table.deleted",
        target=full_name,
        detail={"force": force},
    )
    return {}
